"""Cached, sequential AOI+2km public Overpass context acquisition."""
import time
from common import *

folder=RAW/'osm_context';folder.mkdir(parents=True,exist_ok=True)
box4326=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).iloc[0]
w,s,e,n=box4326.bounds
keys=['highway','footway','cycleway','railway','public_transport','amenity','shop','office','tourism','leisure','landuse','natural','waterway','historic','barrier','entrance','emergency','healthcare','social_facility','power','man_made','place','addr:housenumber']
evidence=[]
for iy in range(2):
    for ix in range(4):
        sid=f'osm_context_{iy}_{ix}';path=folder/f'tile_{iy}_{ix}.json'
        bbox=(s+(n-s)*iy/2,w+(e-w)*ix/4,s+(n-s)*(iy+1)/2,w+(e-w)*(ix+1)/4)
        query='[out:json][timeout:180];('+''.join('nwr["'+key+'"]('+','.join(map(str,bbox))+');' for key in keys)+'rel["route"~"^(bus|subway|tram|train|trolleybus)$"]('+','.join(map(str,bbox))+'););out body;>;out skel qt;'
        register(sid,category='A B C D E G H I',dataset_name='OSM structured context AOI+2km tile',provider='OpenStreetMap contributors',url='https://overpass-api.de/api/interpreter',family='open_geography',format='OSM JSON',license='ODbL-1.0',reuse_allowed=True,api_registration_needed=False,notes='Includes full route member geometry where returned; statistics must clip to AOI, context supports network only',round=1)
        if not path.exists():
            for number in range(3):
                try:
                    print('FETCH',sid,'attempt',number+1,flush=True)
                    response=SESSION.post('https://overpass-api.de/api/interpreter',data={'data':query},timeout=240,headers={'Accept':'application/json'})
                    response.raise_for_status();data=response.json()
                    if data.get('remark') or not data.get('elements'):raise RuntimeError(data.get('remark','no source elements'))
                    dump(path,data);attempt(sid,1,'success',f'{len(data["elements"])} elements');break
                except Exception as exc:
                    attempt(sid,1,'failed',str(exc))
                    status=getattr(getattr(exc,'response',None),'status_code',None)
                    if status in (401,403,404,406):
                        register(sid,access_status='blocked_http_'+str(status),reason=str(exc));break
                    if number==2:register(sid,access_status='request_failed',reason=str(exc));break
                    time.sleep(5*(2**number))
            time.sleep(2)
        if path.exists():
            data=json.loads(path.read_text());timestamp=data.get('osm3s',{}).get('timestamp_osm_base')
            register(sid,access_status='fetched_context_pending_exact_clip',local_path=str(path.relative_to(ROOT)),checksum=sha(path),updated_at=timestamp)
            evidence.append({'source_id':sid,'file':str(path.relative_to(ROOT)),'query':query,'bbox_s_w_n_e':bbox,'source_timestamp':timestamp,'elements':len(data['elements']),'sha256':sha(path)})
            progress('downloads',sid,'fetched',elements=len(data['elements']))
            print('SAVED',sid,len(data['elements']),flush=True)
        export_registry()
dump(ROOT/'reports/osm_context_downloads.json',evidence)
progress('downloads','osm_context','complete' if len(evidence)==8 else 'partial',successful_tiles=len(evidence),expected_tiles=8)
