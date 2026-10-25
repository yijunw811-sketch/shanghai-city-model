"""Reference points, historical observed-only vegetation, and coarse reanalysis climate."""
from common import *
import numpy as np,zarr,rasterio,re
from shapely import wkt
from shapely.geometry import Point
from rasterio.transform import from_origin
from rasterio.warp import reproject,Resampling,calculate_default_transform
M=ROOT/'outputs/gis/planning_enriched.gpkg'
f=RAW/'wikidata/context.json'
if f.exists():
 rows=[]
 for b in json.loads(f.read_text()).get('results',{}).get('bindings',[]):
  v=lambda k:b.get(k,{}).get('value','')
  try:g=wkt.loads(v('coord'))
  except Exception:continue
  rows.append({'entity':v('item'),'name':v('itemLabel'),'type':v('typeLabel'),'heritage_reference':v('heritageLabel'),'inception_source_value':v('inception'),'provider':'Wikidata contributors','license':'CC0-1.0','source_url':v('item'),'confidence':'community_reference_not_official_designation','geometry':g})
 if rows:
  g=source_context(gpd.GeoDataFrame(rows,crs=4326)).drop_duplicates(['entity','type'])
  write_layer(g,M,'wikidata_reference_points');dump(ROOT/'reports/wikidata_summary.json',{'context':len(g),'aoi':int(g.in_aoi.sum()),'not_official_heritage_boundary':True})
# Coordinate arrays explicitly named latitude/longitude in public dictionary; source CRS not formally tagged.
# Georeferencing follows these geographic coordinates with explicit inferred CRS designation.
z=zarr.open(str(ROOT/'cache/research/21345765/shanghai_ndvi_modelready.zarr'),'r')
a=z['NDVI'][:];obs=z['observed'][:].astype(bool);lon=z['longitude'][:];lat=z['latitude'][:]
times=pd.Timestamp('2000-02-01')+pd.to_timedelta(z['time'][:],unit='D')
mask=(times.year>=2020)&(times.year<=2024);good=obs[mask]&np.isfinite(a[mask]);count=good.sum(axis=0)
mean=np.divide(np.where(good,a[mask],0).sum(axis=0),count,out=np.full(count.shape,np.nan),where=count>0)
# latitude ascends south->north; flip to north-up without reordering longitudes.
array=mean[::-1].astype('float32');dx=float(np.diff(lon).mean());dy=float(np.diff(lat).mean());transform=from_origin(lon[0]-dx/2,lat[-1]+dy/2,dx,dy)
p=RAW/'research/21345765/observed_only_ndvi_2020_2024_geographic.tif'
with rasterio.open(p,'w',driver='GTiff',height=len(lat),width=len(lon),count=1,dtype='float32',crs=4326,transform=transform,nodata=np.nan,compress='deflate') as ds:ds.write(array,1)
# Save per-year observed mask statistics, never present temporal interpolants as observations.
stats=[]
for year in sorted(set(times.year)):
 ix=times.year==year;valid=obs[ix]&np.isfinite(a[ix]);stats.append({'year':year,'observed_pixel_months':int(valid.sum()),'possible_pixel_months':int(valid.size),'observed_mean_ndvi':float(a[ix][valid].mean()) if valid.any() else None})
pd.DataFrame(stats).to_csv(ROOT/'reports/historical_ndvi_observed_statistics.csv',index=False)
coverage=gpd.GeoSeries([__import__('shapely').geometry.box(lon.min()-dx/2,lat.min()-dy/2,lon.max()+dx/2,lat.max()+dy/2)],crs=4326).to_crs(32651).iloc[0]
write_layer(gpd.GeoDataFrame([{'source':'Zenodo 21345765 MODIS-derived','year_range':'2012-2024','resolution':'nominal 250m; geographic supplied grid','crs_status':'EPSG4326 inferred from explicit latitude/longitude coordinates, not formally source-tagged','aoi_coverage_percent':coverage.intersection(AOI).area/AOI.area*100,'value_type':'observed-mask-only; interpolation excluded','geometry':coverage.intersection(CONTEXT)}],crs=32651),M,'historical_ndvi_coverage')
dump(ROOT/'reports/historical_ndvi_method.json',{'source_url':'https://zenodo.org/records/21345765','license':'CC-BY-4.0','aoi_coverage_percent':coverage.intersection(AOI).area/AOI.area*100,'native_coordinate_arrays':'latitude/longitude','crs_inferred':True,'grid_resolution':'nominal250m; geographic spacing in original preserved','observed_only':True,'not_cross_sensor_trend':'MODIS historic and Sentinel2026 cannot directly be compared as vegetation change','output':str(p.relative_to(ROOT))})
# Official Open-Meteo ERA5-Land API: one representative point, never spatially interpolated.
center=gpd.GeoSeries([AOI.centroid],crs=32651).to_crs(4326).iloc[0]
sid='era5land_climate_context';url='https://archive-api.open-meteo.com/v1/archive'
register(sid,category='H',dataset_name='ERA5-Land daily climate point context 2020-2025',provider='Open-Meteo / ECMWF',url=url,license='CC-BY-4.0 attribution Open-Meteo and Copernicus',spatial_resolution='ERA5-Land ~0.1degree ~9km',valid_year='2020-2025',family='reanalysis',round=3,notes='Model reanalysis at representative cell, not on-site measurement or microclimate')
p=request_public(sid,url,RAW/'climate/era5land_daily_context.json',3,'data',params={'latitude':center.y,'longitude':center.x,'start_date':'2020-01-01','end_date':'2025-12-31','daily':'temperature_2m_mean,temperature_2m_max,precipitation_sum','models':'era5_land','timezone':'Asia/Shanghai'})
if p:
 j=json.loads(p.read_text());daily=pd.DataFrame(j['daily']);daily.to_csv(RAW/'climate/era5land_daily_context.csv',index=False)
 daily['year']=pd.to_datetime(daily.time).dt.year;daily.groupby('year').agg(mean_temperature_c=('temperature_2m_mean','mean'),max_daily_temperature_c=('temperature_2m_max','max'),annual_precipitation_mm=('precipitation_sum',lambda s:s.sum(min_count=1))).to_csv(ROOT/'reports/climate_context_yearly.csv')
 register(sid,access_status='verified_reanalysis_not_station',feature_count_aoi=1,coverage_percent=None)
export_registry();progress('additional','references','complete');print('additional evidence complete',flush=True)
