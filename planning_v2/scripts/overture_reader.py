"""Read official Overture GeoParquet over verified HTTPS byte ranges, spatially pruned."""
import io
import hashlib
import json
import time
import datetime as dt
from pathlib import Path
import geopandas as gpd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import requests
from common import ROOT,BASE,RAW,register,attempt,progress,export_registry,now,boundary_path

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'cache/overture';RANGES=ROOT/'cache/overture_ranges';DATA=RAW/'overture'
CACHE.mkdir(parents=True,exist_ok=True);DATA.mkdir(parents=True,exist_ok=True)
RANGES.mkdir(parents=True,exist_ok=True)
RELEASE='2026-10-21.0'
session=requests.Session()
session.headers['User-Agent']='ShanghaiCityMassingResearch/1.0 (spatially filtered cached research)'
boundary=gpd.read_file(boundary_path).to_crs(32651)
study=gpd.GeoSeries([boundary.geometry.iloc[0].buffer(2000)],crs=32651).to_crs(4326).iloc[0]
w,s,e,n=study.bounds
def intersects(b):return b[0]<=e and b[2]>=w and b[1]<=n and b[3]>=s

class RangeFile(io.RawIOBase):
    def __init__(self,url,size):
        self.url=url;self.size=size;self.pos=0;self.downloaded=0;self.calls=0
        self.key=hashlib.sha256(url.encode()).hexdigest()[:20]
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        return self.pos
    def read(self,size=-1):
        if size<0:size=self.size-self.pos
        size=min(size,self.size-self.pos)
        if size<=0:return b''
        if size>64*1024*1024:raise RuntimeError('Single range exceeds 64MiB budget; catalog contribution must justify alternate read strategy')
        if self.downloaded+size>384*1024*1024:raise RuntimeError('Per-partition range budget exceeded; retain metadata and continue other topics')
        path=RANGES/f'{self.key}_{self.pos}_{size}.bin'
        if path.exists():data=path.read_bytes()
        else:
            for attempt in range(3):
                try:
                    r=session.get(self.url,headers={'Range':f'bytes={self.pos}-{self.pos+size-1}','Accept-Encoding':'identity'},timeout=90)
                    r.raise_for_status()
                    if r.status_code!=206 or r.headers.get('Content-Range')!=f'bytes {self.pos}-{self.pos+size-1}/{self.size}':
                        raise RuntimeError('Server did not honor exact byte range; refusing full partition download')
                    data=r.content
                    if len(data)!=size:raise RuntimeError('Truncated range response')
                    path.write_bytes(data);self.downloaded+=len(data);self.calls+=1
                    break
                except requests.HTTPError as exc:
                    if exc.response is not None and exc.response.status_code in (401,403,404):raise
                    if attempt==2:raise
                    time.sleep(2**attempt)
        if len(data)!=size:raise RuntimeError('Invalid cached range size')
        self.pos+=size
        return data

def get_json(url,path):
    if path.exists():return json.loads(path.read_text())
    r=session.get(url,timeout=45);r.raise_for_status();d=r.json();path.write_text(json.dumps(d));return d

def download(kind,theme):
    output=DATA/f'{kind}_context.parquet'
    manifest_path=ROOT/f'reports/overture_{kind}_download.json'
    sid='overture_'+kind
    register(sid,category=theme,dataset_name=f'Overture {kind} {RELEASE} AOI+2km',provider='Overture Maps Foundation',url=f'https://stac.overturemaps.org/{RELEASE}/{theme}/{kind}/collection.json',family='open_geography',valid_year=RELEASE[:4],published_at=RELEASE[:10],format='GeoParquet',round=1)
    if output.exists() and manifest_path.exists():
        print('CACHED',kind,pq.read_metadata(output).num_rows,flush=True);return
    url=f'https://stac.overturemaps.org/{RELEASE}/{theme}/{kind}/collection.json'
    collection=get_json(url,CACHE/f'overture_{kind}_collection.json')
    register(sid,license=collection.get('license'),reuse_allowed='per_declared_collection_license',api_registration_needed=False)
    items=[link for link in collection['links'] if link['rel']=='item']
    bboxes=collection['extent']['spatial']['bbox']
    if len(bboxes)==len(items)+1:partition_bboxes=bboxes[1:]
    elif len(bboxes)==len(items):partition_bboxes=bboxes
    else:raise RuntimeError(f'Unsupported catalog bbox/item shape: {len(bboxes)}/{len(items)}')
    parts=[];evidence=[]
    for index,(bbox,link) in enumerate(zip(partition_bboxes,items)):
        if not intersects(bbox):continue
        item=get_json(link['href'],CACHE/f'overture_{kind}_selected_{index}.json')
        assert item['bbox']==bbox,'Collection bbox ordering must agree with authoritative selected item'
        asset=item['assets']['azure']
        remote=RangeFile(asset['href'],asset['file:size'])
        parquet=pq.ParquetFile(remote)
        print(kind,'partition',index,'rowgroups',parquet.num_row_groups,flush=True)
        cols={parquet.schema.column(i).path:i for i in range(len(parquet.schema))}
        selected=[]
        for rowgroup in range(parquet.num_row_groups):
            rg=parquet.metadata.row_group(rowgroup)
            stats={axis:rg.column(cols['bbox.'+axis]).statistics for axis in ('xmin','ymin','xmax','ymax')}
            if any(stat is None or not stat.has_min_max for stat in stats.values()):
                selected.append(rowgroup);continue
            if stats['xmin'].min<=e and stats['xmax'].max>=w and stats['ymin'].min<=n and stats['ymax'].max>=s:selected.append(rowgroup)
        print(kind,'selected rowgroups',selected,flush=True)
        rows=0
        for rowgroup in selected:
            table=parquet.read_row_group(rowgroup,use_threads=False)
            bb=table['bbox']
            mask=pc.and_(pc.and_(pc.less_equal(pc.struct_field(bb,'xmin'),e),pc.greater_equal(pc.struct_field(bb,'xmax'),w)),pc.and_(pc.less_equal(pc.struct_field(bb,'ymin'),n),pc.greater_equal(pc.struct_field(bb,'ymax'),s)))
            table=table.filter(mask)
            if table.num_rows:parts.append(table);rows+=table.num_rows
        evidence.append({'stac_item':link['href'],'asset':asset['href'],'file_bytes':asset['file:size'],'rowgroups':selected,'bbox_matched_rows':rows,'new_range_bytes':remote.downloaded,'requests':remote.calls,'license':collection['license']})
    if not parts:
        manifest={'release':RELEASE,'kind':kind,'checked_utc':now(),'bbox_w_s_e_n':[w,s,e,n],'collection_license':collection['license'],'rows_bbox_candidates':0,'partitions':evidence,'outcome':'no_records_after_spatial_filter'}
        manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
        register(sid,access_status='no_records_after_spatial_filter',feature_count_aoi=0,notes='No bbox candidates in this release/context; not proof of real-world absence')
        progress('downloads',sid,'empty_spatial_result');return
    table=pa.concat_tables(parts,promote_options='default')
    pq.write_table(table,output,compression='zstd')
    manifest={'release':RELEASE,'kind':kind,'checked_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'bbox_w_s_e_n':[w,s,e,n],'collection_license':collection['license'],'rows_bbox_candidates':table.num_rows,'partitions':evidence,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    register(sid,access_status='fetched_context_pending_exact_clip',local_path=str(output.relative_to(ROOT)),checksum=manifest['sha256'],notes=f'{table.num_rows} AOI+2km bbox candidates; do not report as AOI feature count')
    progress('downloads',sid,'fetched',rows_context_bbox=table.num_rows,path=str(output.relative_to(ROOT)))
    print('SAVED',kind,table.num_rows,'rows',output.stat().st_size,'bytes',flush=True)

if __name__=='__main__':
    import sys
    root=get_json('https://stac.overturemaps.org/catalog.json',CACHE/'root_catalog.json')
    RELEASE=root.get('latest',RELEASE)
    themes={'building':'buildings','building_part':'buildings','segment':'transportation','connector':'transportation','place':'places','address':'addresses','division':'divisions','division_area':'divisions','division_boundary':'divisions','land':'base','land_cover':'base','land_use':'base','water':'base','infrastructure':'base','bathymetry':'base'}
    for kind in sys.argv[1:] or ['place','address','division_area','division','division_boundary','land_use','infrastructure','segment','connector','land_cover','water','building_part','building','land','bathymetry']:
        try:download(kind,themes[kind])
        except Exception as exc:
            print('FAILED',kind,type(exc).__name__,str(exc)[:400],flush=True)
            register('overture_'+kind,access_status='failed_needs_review',reason=str(exc)[:1500]);attempt('overture_'+kind,1,'failed',str(exc)[:1500]);progress('downloads','overture_'+kind,'failed')
        export_registry()
