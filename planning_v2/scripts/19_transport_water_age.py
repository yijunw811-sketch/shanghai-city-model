from common import *
from range_io import PublicRange
import tifffile,numpy as np,rasterio,runpy,re
from rasterio.transform import from_origin
from rasterio.windows import from_bounds
from shapely.geometry import Point,LineString
# Inspect actual WorldPop age file links without country-zip bulk acquisition.
links=json.loads((ROOT/'reports/worldpop_age_download_links.json').read_text());first=next(r['url'] for r in links if r['url'].endswith('.tif'))
r=SESSION.get(first,headers={'Range':'bytes=0-16383'},stream=True,timeout=45);result={'url':first,'status':r.status_code,'content_length':r.headers.get('Content-Length'),'content_range':r.headers.get('Content-Range')};r.close();dump(ROOT/'reports/worldpop_age_range_probe.json',result)
register('worldpop_agesex2025_1km',access_status='individual_files_range_probe_'+str(result['status']),reason='Entire dataset 1.19GB; do not bulk-download country agesex archive; age composition not downscaled from totals',notes=str(result))
# Obtain explicit turn-restriction relations omitted by geometry-only highway queries.
bounds=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).total_bounds;w,s,e,n=bounds
query=f'[out:json][timeout:90];rel["type"="restriction"]({s},{w},{n},{e});out body;>;out skel qt;'
sid='osm_turn_restrictions';url='https://overpass-api.de/api/interpreter';register(sid,category='C',provider='OpenStreetMap contributors',dataset_name='OSM explicit turn restrictions context',url=url,license='ODbL-1.0',family='open_geography',round=3)
p=request_public(sid,url,RAW/'osm_context/turn_restrictions.json',3,'data',method='POST',data={'data':query},timeout=120)
if p:
 j=json.loads(p.read_text());elements=j.get('elements',[]);nodes={v['id']:v for v in elements if v['type']=='node' and 'lon' in v};rows=[]
 for rel in elements:
  if rel['type']!='relation' or rel.get('tags',{}).get('type')!='restriction':continue
  vias=[v for v in rel.get('members',[]) if v['role']=='via' and v['type']=='node' and v['ref'] in nodes]
  for v in vias:
   nd=nodes[v['ref']];rows.append({'osm_relation_id':rel['id'],'via_node_id':v['ref'],'restriction':rel['tags'].get('restriction',''),'except':rel['tags'].get('except',''),'conditional':rel['tags'].get('restriction:conditional',''),'members_json':json.dumps(rel['members']),'tags_json':json.dumps(rel['tags']),'source_url':f'https://www.openstreetmap.org/relation/{rel["id"]}','license':'ODbL-1.0','routing_status':'recorded_not_applied_to_descriptive_density_or_walk_graph','geometry':Point(nd['lon'],nd['lat'])})
 if rows:
  frame=source_context(gpd.GeoDataFrame(rows,crs=4326));write_layer(frame,ROOT/'outputs/gis/planning_enriched.gpkg','turn_restrictions');register(sid,access_status='verified_source_relations',feature_count_aoi=int(frame.in_aoi.sum()),notes='Via-way restrictions retained in raw; point layer only explicit via-node relations')
 dump(ROOT/'reports/turn_restrictions_download.json',{'query':query,'snapshot':j.get('osm3s'),'relations':sum(v['type']=='relation' for v in elements),'via_node_records':len(rows),'raw_sha256':sha(p)})
# Official download script URL pattern; both observed original script and underscore typo correction checked.
urls=['https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/occurrence_120E_40Nv1_4_2021.tif','https://storage.googleapis.com/global-surface-water/downloads2021/occurrence/occurrence_120E_40N_v1_4_2021.tif']
sid='jrc_water_occurrence2021';register(sid,category='G H',provider='EC JRC Global Surface Water',dataset_name='GSW occurrence1984-2021 v1.4',url=urls[-1],license='Copernicus open data terms; cite Pekel et al / EC JRC',spatial_resolution='30m nominal',valid_year='1984-2021',family='remote_sensing',round=3)
for url in urls:
 r=SESSION.get(url,headers={'Range':'bytes=0-16383'},stream=True,timeout=45);status=r.status_code;cr=r.headers.get('Content-Range');r.close();attempt(sid,3,'range_'+str(status),url)
 if status!=206 or not cr:continue
 try:
  stream=PublicRange(url,int(cr.split('/')[-1]));out=RAW/'jrc_water/occurrence1984_2021_context.tif';out.parent.mkdir(exist_ok=True)
  with tifffile.TiffFile(stream) as tif:
   page=tif.pages[0];scale=page.tags['ModelPixelScaleTag'].value;tie=page.tags['ModelTiepointTag'].value;transform=from_origin(tie[3],tie[4],scale[0],scale[1]);window=from_bounds(*bounds,transform=transform).round_offsets().round_lengths();x0,y0=int(window.col_off),int(window.row_off);x1=x0+int(window.width);y1=y0+int(window.height)
   if not page.is_tiled:raise RuntimeError('No validated bounded strip path for this JRC release')
   tw,th=page.tilewidth,page.tilelength;nx=(page.imagewidth+tw-1)//tw;indices=[ty*nx+tx for ty in range(y0//th,(y1-1)//th+1) for tx in range(x0//tw,(x1-1)//tw+1)];cost=sum(page.databytecounts[i] for i in indices)
   if cost>48*1024*1024:raise RuntimeError('JRC selected tiles exceed48MiB budget')
   array=np.full((y1-y0,x1-x0),255,dtype=page.dtype)
   for i in indices:
    stream.seek(page.dataoffsets[i]);raw=stream.read(page.databytecounts[i]);tile,pos,shape=page.decode(raw,i);tile=np.squeeze(tile);ty=i//nx*th;tx=i%nx*tw;left=max(tx,x0);right=min(tx+tw,x1);top=max(ty,y0);bottom=min(ty+th,y1);array[top-y0:bottom-y0,left-x0:right-x0]=tile[top-ty:bottom-ty,left-tx:right-tx]
   profile={'driver':'GTiff','count':1,'width':array.shape[1],'height':array.shape[0],'dtype':str(array.dtype),'crs':'EPSG:4326','transform':rasterio.windows.transform(window,transform),'nodata':255,'compress':'deflate'}
   with rasterio.open(out,'w',**profile) as ds:ds.write(array,1)
   helper=runpy.run_path(str(ROOT/'scripts/04_rasters.py'),run_name='raster_tools');ref=helper['metric_reference'](profile,30);aligned=helper['align'](array,profile,ref);helper['save_product']('jrc_water_occurrence1984_2021_30m',aligned,ref,{'source_url':url,'license':'Copernicus open data / EC JRC','year':'1984-2021','method':'Historical water observation frequency percent; NOT current water polygon; selected native tiles only'})
   dump(ROOT/'reports/jrc_water_window.json',{'url':url,'tile_bytes':cost,'selected_tiles':len(indices),'total_range_bytes':stream.total,'national_or_global_file_not_downloaded':True,'meaning':'Historical occurrence percentage1984-2021, not2026 flood probability'})
   register(sid,access_status='verified_native_tiles',local_path=str(out.relative_to(ROOT)),checksum=sha(out));break
 except Exception as exc:register(sid,access_status='bounded_read_failed',reason=str(exc));attempt(sid,3,'window_failed',str(exc))
export_registry()
