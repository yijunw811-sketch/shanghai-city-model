from common import *
import requests,rasterio,os
from rasterio.windows import from_bounds,Window
from rasterio.warp import transform_bounds,reproject,Resampling
from rasterio.features import geometry_mask
session=requests.Session();session.headers['User-Agent']='ShanghaiPlanningV3 / limited lawful spatial COG reads'
ENV={'GDAL_CURL_CA_BUNDLE':os.environ.get('REQUESTS_CA_BUNDLE','/etc/ssl/certs/ca-certificates.crt'),'GDAL_DISABLE_READDIR_ON_OPEN':'EMPTY_DIR','GDAL_HTTP_MAX_RETRY':1,'GDAL_HTTP_RETRY_DELAY':1,'GDAL_CACHEMAX':128}
SITE=read('DESIGN_SITE',D).geometry.iloc[0];bounds=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).total_bounds.tolist()
cache=ROOT/'data/satellite';sources=[];candidates=[]
def crop(url,path):
 if path.exists():
  with rasterio.open(path) as ds:return ds.read(),ds.profile.copy()
 with rasterio.Env(**ENV):
  with rasterio.open(url) as ds:
   win=from_bounds(*transform_bounds(32651,ds.crs,*CONTEXT.bounds,densify_pts=21),ds.transform).round_offsets().round_lengths().intersection(Window(0,0,ds.width,ds.height))
   assert win.width*win.height<8e6
   a=ds.read(window=win);p=ds.profile.copy();p.update(width=a.shape[2],height=a.shape[1],transform=ds.window_transform(win),compress='deflate',tiled=True,blockxsize=256,blockysize=256)
 with rasterio.open(path,'w',**p) as ds:ds.write(a)
 return a,p
# Actual high-resolution discovery attempts, no map-tile extraction or guessed reuse rights.
for name,url,reason in [('OpenAerialMap','https://api.openaerialmap.org/meta?bbox='+','.join(map(str,bounds)),'Public imagery metadata; per-image license must be checked'),('Shanghai open data','https://data.sh.gov.cn/view/','Official orthophoto/open data catalogue; no assumption that display services allow offline export')]:
 try:
  rr=session.get(url,timeout=25);sources.append({'source':name,'url':url,'http':rr.status_code,'offline_reuse':'not_verified','notes':reason})
 except Exception as exc:sources.append({'source':name,'url':url,'status':type(exc).__name__,'offline_reuse':'not_verified','notes':reason})
for season in ['summer','winter']:
 selection=json.loads((V2/f'reports/sentinel_{season}_selection.json').read_text());items=json.loads((V2/f'cache/source_discovery/s2_{season}_stac.json').read_text())['features'];candidates.extend([i for i in items if i['id']==selection['scene_id']])
search=cache/'latest_sentinel_stac.json'
try:
 if search.exists():j=json.loads(search.read_text())
 else:
  response=session.post('https://earth-search.aws.element84.com/v1/search',json={'collections':['sentinel-2-l2a'],'bbox':bounds,'datetime':'2026-09-01T00:00:00Z/2026-10-28T00:00:00Z','limit':12,'query':{'eo:cloud_cover':{'lt':20}},'sortby':[{'field':'properties.datetime','direction':'desc'}]},timeout=45);response.raise_for_status();j=response.json();dump(search,j)
 candidates+=j.get('features',[])[:6]
except Exception as exc:sources.append({'source':'latest Sentinel search','status':type(exc).__name__,'fallback':'existing lawful Sentinel scenes'})
checks=[];lookup={i['id']:i for i in candidates}
for id,item in lookup.items():
 try:
  a,p=crop(item['assets']['scl']['href'],cache/f'{id}_SCL.tif');a=a[0];bad=np.isin(a,[0,1,3,8,9,10,11]);
  masks={k:geometry_mask([g],out_shape=a.shape,transform=p['transform'],invert=True) for k,g in [('aoi',AOI),('site',SITE)]}
  checks.append({'id':id,'datetime':item['properties']['datetime'],'aoi_bad_fraction':float(bad[masks['aoi']].mean()),'site_bad_fraction':float(bad[masks['site']].mean()),'stac_scene_cloud_percent':item['properties'].get('eo:cloud_cover')});print('SCENE',checks[-1],flush=True)
 except Exception as exc:sources.append({'source':id,'status':type(exc).__name__})
if not checks:raise RuntimeError('No verified RGB candidate; never substitute thematic raster')
clear=[r for r in checks if r['aoi_bad_fraction']<.01 and r['site_bad_fraction']<.01];chosen=sorted(clear,key=lambda r:r['datetime'],reverse=True)[0] if clear else sorted(checks,key=lambda r:r['aoi_bad_fraction']+r['site_bad_fraction'])[0]
item=lookup[chosen['id']];url=item['assets']['visual']['href'];a,p=crop(url,cache/'sentinel_truecolor_10m_context.tif');assert a.shape[0]==3 and p['crs'].to_epsg()==32651
# TCI is the official display RGB asset, not NDVI/LST and not synthetic super-resolution.
with rasterio.open(cache/'sentinel_truecolor_10m_context.tif','r+') as ds:
 ds.colorinterp=(rasterio.enums.ColorInterp.red,rasterio.enums.ColorInterp.green,rasterio.enums.ColorInterp.blue)
 ds.update_tags(provider='Copernicus Sentinel-2 / Earth Search',scene_id=item['id'],acquisition_datetime=item['properties']['datetime'],resolution='native10m; no invented finer detail',license='Copernicus Sentinel open data terms',source_url=url)
 ds.build_overviews([2,4,8,16],Resampling.average);ds.update_tags(ns='rio_overview',resampling='average')
# Relative GDAL VRT keeps display/analysis pixels separate; no source geometry alignment shifts.
report={'dataset':'Sentinel-2 L2A true colour TCI','scene_id':item['id'],'acquisition_datetime':item['properties']['datetime'],'native_resolution_m':10,'output_crs':'EPSG:32651','source_url':url,'license':'Copernicus Sentinel open data terms; attribution Contains modified Copernicus Sentinel data (2026)','offline_save':True,'redistribution_with_attribution':True,'rendering':'official TCI RGB; context-wide display adjustment only','selected_quality':chosen,'all_candidates':checks,'sha256':sha(cache/'sentinel_truecolor_10m_context.tif'),'higher_resolution_status':'No verified licensed 0.5–2m orthophoto obtained; never advertised as high resolution survey','acquisition_not_download_date':True,'registration':'Same native UTM51N scene and existing GIS overlay; manual overlays provided; no independently surveyed control points, no absolute accuracy claim'}
dump(ROOT/'reports/satellite_provenance.json',report);dump(ROOT/'reports/satellite_source_discovery.json',sources);dump(cache/'selected_scene_stac.json',item);checkpoint('satellite',status='rgb_cog_read_verified',scene=item['id']);print('SELECTED',chosen,flush=True)
