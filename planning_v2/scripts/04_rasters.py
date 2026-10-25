"""Small-window verified-TLS COG reads and reproducible physical raster products."""
import os
import re
import json
import numpy as np
import rasterio
from rasterio.windows import from_bounds,Window
from rasterio.warp import transform_bounds,reproject,Resampling,calculate_default_transform
from rasterio.features import geometry_mask
from shapely.geometry import mapping
from common import *

RASTERS=ROOT/'outputs/gis/rasters';RASTERS.mkdir(parents=True,exist_ok=True)
NODATA=-9999.
CA=os.environ.get('REQUESTS_CA_BUNDLE',os.environ.get('SSL_CERT_FILE','/etc/ssl/certs/ca-certificates.crt'))
ENV={'GDAL_CURL_CA_BUNDLE':CA,'GDAL_DISABLE_READDIR_ON_OPEN':'EMPTY_DIR','GDAL_HTTP_MAX_RETRY':2,'GDAL_HTTP_RETRY_DELAY':1,'GDAL_CACHEMAX':128}
box4326=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).iloc[0]
def clean_error(exc):return re.sub(r'https?://[^\s\"\']+',lambda m:safe_url(m.group()),str(exc))[:1500]
def https_asset(url):
    if url.startswith('s3://copernicus-dem-30m/'):
        return url.replace('s3://copernicus-dem-30m/','https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/')
    if url.startswith('s3://usgs-landsat/'):
        return url.replace('s3://usgs-landsat/','https://usgs-landsat.s3.us-west-2.amazonaws.com/')
    return url
def crop(url,path,source_id,year,license,description):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        with rasterio.open(path) as src:return src.read(1),src.profile.copy()
    progress('downloads',source_id,'window_read_started')
    with rasterio.Env(**ENV):
        with rasterio.open(url) as src:
            bounds=transform_bounds(32651,src.crs,*CONTEXT.bounds,densify_pts=21)
            win=from_bounds(*bounds,src.transform).round_offsets().round_lengths().intersection(Window(0,0,src.width,src.height))
            if win.width*win.height>8_000_000:raise RuntimeError('AOI window exceeds 8M pixels; refuse memory-heavy read')
            array=src.read(1,window=win)
            profile=src.profile.copy();profile.update(width=array.shape[1],height=array.shape[0],transform=src.window_transform(win),count=1,driver='GTiff',compress='deflate',tiled=True,blockxsize=256,blockysize=256)
            original={'crs':str(src.crs),'width':src.width,'height':src.height,'res':src.res,'nodata':src.nodata,'is_tiled':src.is_tiled,'scales':src.scales,'offsets':src.offsets}
    with rasterio.open(path,'w',**profile) as dst:
        dst.write(array,1);dst.update_tags(source_url=safe_url(url),source_year=str(year),license=license,method=description,scope='AOI + 2000m context; original pixel grid')
    dump(path.with_suffix('.json'),{'source_id':source_id,'url':safe_url(url),'year':year,'license':license,'method':description,'original':original,'context_shape':list(array.shape),'context_transform':list(profile['transform']),'sha256':sha(path)})
    register(source_id,access_status='fetched_window_verified',format='GeoTIFF',valid_year=str(year),license=license,spatial_resolution=str(original['res']),reuse_allowed='per_product_terms',local_path=str(path.relative_to(ROOT)),checksum=sha(path),notes=description)
    progress('downloads',source_id,'fetched_window',shape=list(array.shape),bytes=path.stat().st_size)
    return array,profile
def align(array,profile,reference,resampling=Resampling.nearest):
    out=np.full((reference['height'],reference['width']),NODATA,dtype=np.float32)
    reproject(array,out,src_transform=profile['transform'],src_crs=profile['crs'],src_nodata=profile.get('nodata'),dst_transform=reference['transform'],dst_crs=reference['crs'],dst_nodata=NODATA,resampling=resampling)
    return out
def metric_reference(profile,resolution):
    bounds=rasterio.transform.array_bounds(profile['height'],profile['width'],profile['transform'])
    transform,width,height=calculate_default_transform(profile['crs'],32651,profile['width'],profile['height'],*bounds,resolution=resolution)
    return {**profile,'crs':rasterio.crs.CRS.from_epsg(32651),'transform':transform,'width':width,'height':height,'dtype':'float32','nodata':NODATA}
def save_product(name,array,reference,metadata):
    path=RASTERS/(name+'.tif');profile=reference.copy();profile.update(driver='GTiff',dtype='float32',count=1,nodata=NODATA,compress='deflate',tiled=True,blockxsize=256,blockysize=256)
    mask=geometry_mask([mapping(AOI)],out_shape=array.shape,transform=reference['transform'],invert=True)
    values=np.where(mask & np.isfinite(array) & (array!=NODATA),array,NODATA).astype('float32')
    with rasterio.open(path,'w',**profile) as dst:dst.write(values,1);dst.update_tags(**{k:str(v) for k,v in metadata.items()})
    valid=values[values!=NODATA]
    report={**metadata,'path':str(path.relative_to(ROOT)),'sha256':sha(path),'crs':'EPSG:32651','resolution_m':list(reference['transform'])[0],'valid_pixels':len(valid),'aoi_center_pixels':int(mask.sum()),'valid_pixel_fraction':len(valid)/max(1,int(mask.sum())),'min':float(valid.min()) if len(valid) else None,'max':float(valid.max()) if len(valid) else None,'mean':float(valid.mean()) if len(valid) else None}
    dump(path.with_suffix('.json'),report)
    progress('layer_validation',name,'verified',**report)
    return path
def stac_search(label,collection,dates=None,cloud=None,provider='earthsearch'):
    path=ROOT/f'cache/source_discovery/{label}_stac.json'
    if path.exists():return json.loads(path.read_text())
    body={'collections':[collection],'bbox':list(box4326.bounds),'limit':8}
    if dates:body['datetime']=dates
    if cloud is not None:body['query']={'eo:cloud_cover':{'lt':cloud}}
    url='https://earth-search.aws.element84.com/v1/search' if provider=='earthsearch' else 'https://planetarycomputer.microsoft.com/api/stac/v1/search'
    response=SESSION.post(url,json=body,timeout=60);response.raise_for_status();data=response.json();dump(path,data)
    return data
def worldcover():
    sid='worldcover2021_window';url='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N30E120_Map.tif'
    register(sid,category='B G',dataset_name='ESA WorldCover 2021 v200 10m AOI window',provider='ESA',url=url,family='remote_sensing',api_registration_needed=False)
    a,p=crop(url,RAW/'worldcover/worldcover2021_context.tif',sid,2021,'CC-BY-4.0','Native categorical land-cover model, not legal land use')
    ref=metric_reference(p,10);out=align(a,p,ref)
    save_product('worldcover2021_10m',out,ref,{'dataset':'ESA WorldCover 2021 v200','year':2021,'license':'CC-BY-4.0','meaning':'physical cover classification; not statutory or functional land use','is_inferred':True,'source_url':url})
    classes={10:'树木覆盖',20:'灌木',30:'草地',40:'耕作地表',50:'建成地表',60:'裸地稀疏植被',70:'冰雪',80:'永久水体',90:'草本湿地',95:'红树林',100:'苔藓地衣'}
    pd.DataFrame([{'code':k,'class_cn':v,'year':2021,'license':'CC-BY-4.0','classification_type':'physical_land_cover_not_functional_land_use'} for k,v in classes.items()]).to_csv(ROOT/'standards/worldcover_codebook.csv',index=False)
def dem():
    data=stac_search('dem','cop-dem-glo-30')
    if not data.get('features'):raise RuntimeError('No public DSM item intersects context')
    item=data['features'][0];url=https_asset(item['assets']['data']['href']);sid='copdem_dsm2021_window'
    register(sid,category='A H',dataset_name=item['id'],provider='Copernicus / Sinergise AWS public',url=url,family='remote_sensing',api_registration_needed=False)
    a,p=crop(url,RAW/'copdem/copdem_dsm_context.tif',sid,2021,'Copernicus DEM free public product terms; see AWS registry','DSM includes buildings and vegetation; not bare-earth surveyed terrain')
    ref=metric_reference(p,30);out=align(a,p,ref,Resampling.bilinear)
    save_product('dsm_copernicus2021_30m',out,ref,{'dataset':'Copernicus DEM GLO-30 public DSM','year':2021,'unit':'m','is_inferred':True,'meaning':'digital surface elevation, includes buildings/trees; not bare terrain','source_url':url})
    valid=out!=NODATA;filled=np.where(valid,out,np.nan)
    gy,gx=np.gradient(filled,30,30);slope=np.degrees(np.arctan(np.hypot(gx,gy)))
    save_product('dsm_slope2021_30m',slope,ref,{'dataset':'DSM-derived surface slope','year':2021,'unit':'degrees','formula':'atan(sqrt((dz/dx)^2+(dz/dy)^2)), 30m central differences','meaning':'DSM surface slope, not street longitudinal grade or hydraulic terrain slope','source_url':url})
def sentinel(season,dates):
    data=stac_search('s2_'+season,'sentinel-2-l2a',dates,20)
    features=sorted(data.get('features',[]),key=lambda f:f['properties'].get('eo:cloud_cover',100))
    chosen=None
    for item in features[:4]:
        date=item['properties']['datetime'];folder=RAW/f'sentinel2/{item["id"]}'
        scl,sp=crop(item['assets']['scl']['href'],folder/'SCL.tif',f's2_{season}_scl',date,'Copernicus Sentinel open data terms','Scene classification, native20m; cloud/shadow mask')
        bad=np.isin(scl,[0,1,3,8,9,10,11]);fraction=float(bad.mean())
        if fraction<.15:chosen=(item,folder,scl,sp,fraction);break
    if chosen is None:raise RuntimeError('No low-cloud context image found among inspected candidates')
    item,folder,scl,sp,cloudfraction=chosen;date=item['properties']['datetime'];arrays={};profiles={};used_calibrations={}
    for band in ['red','nir','green','swir16']:
        asset=item['assets'][band];raw,profile=crop(asset['href'],folder/(band+'.tif'),f's2_{season}_{band}',date,'Copernicus Sentinel open data terms','Native L2A BOA band; scale and offset taken verbatim from STAC')
        calibration=(asset.get('raster:bands') or [{}])[0]
        if 'scale' not in calibration or 'offset' not in calibration:raise RuntimeError('Missing explicit reflectance scale/offset; no guessed calibration')
        effective_offset=calibration['offset']
        control_path=ROOT/'reports/sentinel_radiometry_control.json'
        if control_path.exists():
            controls=json.loads(control_path.read_text());control=controls.get(item['id'])
            if control and control.get('status')=='verified_same_scene_mirror_representation':
                effective_offset=calibration['offset']+calibration['scale']*control['dn_shift_pc_minus_aws']
        scaled=raw.astype('float32')*calibration['scale']+effective_offset;scaled[raw==calibration.get('nodata',0)]=NODATA
        used_calibrations[band]={'scale':calibration['scale'],'catalog_offset':calibration['offset'],'effective_offset':effective_offset,'control_evidence':'reports/sentinel_radiometry_control.json' if effective_offset!=calibration['offset'] else 'STAC raster:bands'}
        arrays[band]=scaled;profiles[band]={**profile,'nodata':NODATA}
    ref10=metric_reference(profiles['red'],10);ref20=metric_reference(profiles['swir16'],20)
    for name,a_band,b_band,ref in [('ndvi','nir','red',ref10),('ndwi','green','nir',ref10),('ndbi','swir16','nir',ref20)]:
        a=align(arrays[a_band],profiles[a_band],ref,Resampling.bilinear);b=align(arrays[b_band],profiles[b_band],ref,Resampling.bilinear)
        cloud=align(scl,sp,ref);valid=(a>=0)&(b>=0)&((a+b)>1e-4)&~np.isin(cloud,[NODATA,0,1,3,8,9,10,11])
        index=np.full(a.shape,np.nan,dtype='float32');index[valid]=(a[valid]-b[valid])/(a[valid]+b[valid])
        save_product(f'{name}_{season}2026_{int(ref["transform"].a)}m',index,ref,{'dataset':'Sentinel-2 L2A','scene_id':item['id'],'acquired':date,'season':season,'formula':f'({a_band}-{b_band})/({a_band}+{b_band}) after documented effective radiometric calibration','calibrations':json.dumps(used_calibrations),'cloud_mask':'SCL exclude0,1,3,8,9,10,11; mask native20m','context_cloud_fraction':cloudfraction,'is_inferred':True,'meaning':'satellite spectral index; not statutory land use or direct vegetation ownership','source_url':'https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a','license':'Copernicus Sentinel open data terms'})
    dump(ROOT/f'reports/sentinel_{season}_selection.json',{'scene_id':item['id'],'datetime':date,'context_cloud_fraction':cloudfraction,'stac_scene_cloud_fraction':item['properties'].get('eo:cloud_cover'),'original_calibrations':{band:item['assets'][band].get('raster:bands') for band in arrays},'effective_calibrations':used_calibrations,'boa_offset_applied_flag':item['properties'].get('earthsearch:boa_offset_applied'),'no_independent_field_measurement':True})
def signed_pc(url):
    import time
    for attempt_number in range(3):
        response=SESSION.get('https://planetarycomputer.microsoft.com/api/sas/v1/sign',params={'href':url},timeout=40)
        if response.ok:return response.json()['href']  # transient SAS stays in memory
        if response.status_code in (429,500,502,503,504) and attempt_number<2:
            time.sleep(2**(attempt_number+1));continue
        raise RuntimeError(f'Public PC signing service HTTP {response.status_code}; asset {safe_url(url)}')
def landsat():
    data=stac_search('landsat_pc','landsat-c2-l2','2026-06-01T00:00:00Z/2026-09-30T23:59:59Z',15,provider='planetary')
    features=sorted(data.get('features',[]),key=lambda f:f['properties'].get('eo:cloud_cover',100))
    if not features:raise RuntimeError('No Landsat L2 item in requested season')
    for item in features[:3]:
        if 'lwir11' not in item.get('assets',{}):continue
        folder=RAW/f'landsat/{item["id"]}';date=item['properties']['datetime'];asset=item['assets']['lwir11']
        dn,p=crop(signed_pc(asset['href']),folder/'ST_B10.tif','landsat_st',date,'USGS Landsat public-domain science products','Level2 surface temperature digital numbers; no air-temperature interpretation')
        qa,qp=crop(signed_pc(item['assets']['qa_pixel']['href']),folder/'QA_PIXEL.tif','landsat_qa',date,'USGS public domain','QA bits for cloud, cirrus, shadow and fill')
        qa=align(qa,qp,p).astype('uint16');bad=(qa&((1<<0)|(1<<1)|(1<<2)|(1<<3)|(1<<4)|(1<<5)))!=0
        valid=(dn>0)&~bad
        if valid.mean()<.7:continue
        calibration=(asset.get('raster:bands') or [{}])[0]
        scale=calibration.get('scale',.00341802);offset=calibration.get('offset',149.)
        temperature=np.where(valid,dn.astype('float32')*scale+offset-273.15,NODATA)
        temperature[(temperature<-40)|(temperature>80)]=NODATA
        ref=metric_reference(p,100);out=align(temperature,{**p,'nodata':NODATA},ref,Resampling.average)
        save_product('lst_summer2026_effective100m',out,ref,{'dataset':'Landsat Collection2 Level2 ST_B10','scene_id':item['id'],'acquired':date,'unit':'Celsius','formula':f'DN*{scale}+{offset}-273.15','calibration_evidence':'STAC raster band metadata; USGS Collection2 scale-factor specification fallback .00341802+149K','native_thermal_resolution_m':100,'delivered_product_grid_m':30,'output_aggregation_m':100,'meaning':'satellite estimated land surface temperature; not measured near-surface air temperature','is_inferred':True,'license':'USGS public domain','source_url':safe_url(asset['href'])})
        return
    raise RuntimeError('Inspected Landsat candidates lack valid low-cloud thermal coverage')

if __name__=='__main__':
    jobs=[('worldcover',worldcover),('dem',dem),('sentinel_summer',lambda:sentinel('summer','2026-06-01T00:00:00Z/2026-09-30T23:59:59Z')),('sentinel_winter',lambda:sentinel('winter','2026-01-01T00:00:00Z/2026-03-15T23:59:59Z')),('landsat',landsat)]
    import sys
    for name,run in jobs:
        if len(sys.argv)>1 and name not in sys.argv[1:]:continue
        try:
            print('RASTER',name,flush=True);run();progress('downloads',name,'verified');print('OK',name,flush=True)
        except Exception as exc:
            message=clean_error(exc);register(name,access_status='failed_needs_review',reason=message,round=2);attempt(name,2,'failed',message);progress('downloads',name,'failed',reason=message);print('FAILED',name,type(exc).__name__,message,flush=True)
        export_registry()
