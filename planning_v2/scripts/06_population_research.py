"""Population alternatives and small licensed research archives; no giant country fetch."""
import hashlib
import io
import re
import runpy
import zipfile
from urllib.parse import urljoin
import rasterio
import numpy as np
from bs4 import BeautifulSoup
from common import *

tools=runpy.run_path(str(ROOT/'scripts/04_rasters.py'),run_name='raster_tools')
def limited_download(sid,url,path,limit=64*1024*1024,expected_md5=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        r=SESSION.get(url,timeout=90,stream=True);r.raise_for_status()
        length=int(r.headers.get('Content-Length',0))
        if length>limit:r.close();raise RuntimeError(f'Download size {length} exceeds explicit {limit} byte budget')
        temporary=path.with_suffix(path.suffix+'.partial');total=0
        with temporary.open('wb') as dst:
            for chunk in r.iter_content(1024*1024):
                total+=len(chunk)
                if total>limit:r.close();raise RuntimeError('Stream budget exceeded; partial file retained for diagnosis')
                dst.write(chunk)
        temporary.replace(path)
    if expected_md5:
        actual=hashlib.md5(path.read_bytes()).hexdigest()
        if actual!=expected_md5:raise RuntimeError(f'Official metadata checksum mismatch for {sid}; artifact not used')
    register(sid,access_status='fetched_checksum_verified',local_path=str(path.relative_to(ROOT)),checksum=sha(path),round=2)
    return path
def population_worldpop():
    for category,resolution in [(135,100),(136,1000)]:
        sid=f'worldpop2025_{resolution}m';metadata_url=f'https://hub.worldpop.org/ajax/geolisting/category?id={category}'
        register(sid,category='F',dataset_name=f'WorldPop Global2 R2025A v1 constrained China2025 {resolution}m',provider='WorldPop',url=metadata_url,family='scientific_raster',license='CC-BY-4.0',valid_year=2025,spatial_resolution=f'{resolution}m nominal at equator',reuse_allowed=True,api_registration_needed=False,notes='Alpha release. Random-Forest dasymetric population model, not measured AOI resident population',round=2)
        cache=ROOT/f'cache/source_discovery/worldpop_{category}_listing.json'
        if cache.exists():rows=json.loads(cache.read_text())
        else:
            response=SESSION.get(metadata_url,timeout=40);response.raise_for_status();rows=response.json();dump(cache,rows)
        selected=next(v for v in rows if v.get('country')=='China' and v.get('popyear')=='2025')
        summary_url='https://hub.worldpop.org/geodata/summary?id='+str(selected['id'])
        response=SESSION.get(summary_url,timeout=35);response.raise_for_status();soup=BeautifulSoup(response.content,'html.parser')
        urls=[urljoin(summary_url,a['href']) for a in soup.find_all('a',href=True) if '.tif' in a['href'].lower()]
        if not urls:raise RuntimeError('No published raster link in WorldPop country summary')
        url=urls[0];dump(ROOT/f'reports/{sid}_metadata.json',{'public_record':selected,'summary_url':summary_url,'data_url':url,'description':'Alpha population estimates, people per native pixel; not census observation'})
        probe=SESSION.get(url,headers={'Range':'bytes=0-16383'},stream=True,timeout=40)
        status=probe.status_code;size=int(probe.headers.get('Content-Length',0));probe.close()
        if status==206:
            tools['crop'](url,RAW/f'worldpop/worldpop2025_{resolution}m_context.tif',sid,2025,'CC-BY-4.0','Native population count grid; alpha model estimates; no artificial downscaling')
        elif status==200 and 0<size<=32*1024*1024:
            file=limited_download(sid,url,ROOT/f'cache/population/worldpop2025_{resolution}m_country.tif',32*1024*1024)
            tools['crop'](str(file),RAW/f'worldpop/worldpop2025_{resolution}m_context.tif',sid,2025,'CC-BY-4.0','Small bounded country coarse raster used because range reads unsupported; context crop retains native population grid')
        else:
            register(sid,access_status='blocked_range_or_size',reason=f'Range HTTP{status}, declared response {size} bytes; whole high-resolution country file deliberately not downloaded')
            attempt(sid,2,'range_or_size_block',f'{status} {size}')
        print('WORLDPOP',resolution,status,size,flush=True)
def population_ghsl():
    info=json.loads((ROOT/'cache/source_discovery/ghs_population_target.json').read_text());url=info['url'];sid='ghsl_pop2020_100m'
    register(sid,category='F',dataset_name='GHS-POP2020 R2023A 100m R6C30',provider='European Commission JRC',url=url,family='scientific_raster',valid_year=2020,spatial_resolution='100m equal-area native Mollweide grid',license='European Commission GHSL reuse conditions; source copyright.txt archived',reuse_allowed='per_official_GHSL_terms',api_registration_needed=False,notes='Population model; not current measured AOI population',round=2)
    copyright_url=url.rsplit('/tiles/',1)[0]+'/copyright.txt'
    request_public('ghsl_pop_copyright',copyright_url,RAW/'ghsl/copyright.txt',round_number=2)
    archive=limited_download(sid,url,ROOT/'cache/population/GHS_POP2020_R6C30.zip')
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:raise RuntimeError('Population tile ZIP CRC failure')
        members=[v for v in z.infolist() if v.filename.lower().endswith('.tif')]
        if len(members)!=1 or members[0].file_size>1024*1024*1024:raise RuntimeError('Unexpected regional tile structure/size')
        local=ROOT/'cache/population/GHS_POP2020_R6C30.tif'
        if not local.exists():
            with z.open(members[0]) as src,local.open('wb') as dst:
                while chunk:=src.read(1024*1024):dst.write(chunk)
    with rasterio.open(local) as src:
        b=rasterio.warp.transform_bounds(32651,src.crs,*AOI.bounds)
        if not (src.bounds.left<=b[0] and src.bounds.right>=b[2] and src.bounds.bottom<=b[1] and src.bounds.top>=b[3]):raise RuntimeError('Selected official tile does not contain actual AOI; refuse wrong spatial data')
    tools['crop'](str(local),RAW/'ghsl/ghspop2020_100m_context.tif',sid,2020,'GHSL official copyright/reuse statement','AOI+2km native100m population model crop; regional tile31.5MB retained in cache, no global/national giant downloaded')
    dump(ROOT/'reports/ghsl_population_provenance.json',{'source_url':url,'source_archive_sha256':sha(archive),'source_archive_bytes':archive.stat().st_size,'selected_tile_verified_contains_AOI':True,'year':2020,'type':'modeled population count per native100m cell','scope':'native cropped context; do not mistake for measured resident population'})
def research_archives():
    candidates=pd.read_csv(ROOT/'reports/research_dataset_candidates.csv').drop_duplicates('record_id')
    selected=candidates[candidates.title.str.contains('Model-ready monthly NDVI|Air Quality Dataset for Shanghai|bird-related sentiment',case=False,na=False)]
    descriptions=[]
    for _,record in selected.iterrows():
        sid='zenodo_dataset_'+str(int(record.record_id));files=json.loads(record.files_json)
        record_url=record.url if isinstance(record.url,str) and record.url.startswith('http') else 'https://zenodo.org/records/'+str(int(record.record_id))
        register(sid,category=str(record.topic),dataset_name=record.title,provider='Zenodo research authors',url=record_url,family='scientific_dataset',license=record.license,reuse_allowed='declared_archive_license; upstream provenance still reviewed',published_at=record.published_at,notes='Do not treat gap-filled data as observed, sentiment as footfall, or city series as AOI monitoring',round=2)
        for file in files:
            if not file['key'].lower().endswith('.zip') or file['bytes']>64*1024*1024:continue
            checksum=file.get('checksum','');expected=checksum.split(':',1)[1] if checksum.startswith('md5:') else None
            archive=limited_download(sid,file['download'],RAW/f'research/{int(record.record_id)}/{file["key"]}',expected_md5=expected)
            with zipfile.ZipFile(archive) as z:
                if z.testzip() is not None:raise RuntimeError('Research ZIP CRC failure')
                entries=z.infolist()
                if sum(e.file_size for e in entries)>256*1024*1024:raise RuntimeError('Research archive uncompressed size budget exceeded')
                for entry in entries:
                    path=Path(entry.filename)
                    if path.is_absolute() or '..' in path.parts:raise RuntimeError('Unsafe archive member path')
                folder=ROOT/f'cache/research/{int(record.record_id)}';folder.mkdir(parents=True,exist_ok=True)
                z.extractall(folder)
                text=[]
                for entry in entries:
                    if any(token in entry.filename.lower() for token in ['readme','metadata','dictionary','.zattrs']):
                        if entry.file_size<256000:text.append(entry.filename+'\n'+z.read(entry).decode('utf-8',errors='replace')[:18000])
                descriptions.append({'source_id':sid,'title':record.title,'license':record.license,'archive_sha256':sha(archive),'files':[e.filename for e in entries],'metadata_excerpt':'\n'.join(text)[:40000],'status':'downloaded_verified_pending_semantics_and_spatial_review'})
            print('RESEARCH_ARCHIVE',record.title,flush=True)
    dump(ROOT/'reports/research_archive_inspection.json',descriptions)
if __name__=='__main__':
    for name,run in [('worldpop',population_worldpop),('ghsl',population_ghsl),('research_archives',research_archives)]:
        try:run();progress('downloads',name,'acquired_or_recorded_limits')
        except Exception as exc:
            message=tools['clean_error'](exc);register(name,access_status='failed_needs_review',reason=message,round=2);attempt(name,2,'failed',message);print('FAILED',name,message,flush=True)
        export_registry()
