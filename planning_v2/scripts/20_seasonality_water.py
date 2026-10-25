from common import *
import rasterio,numpy as np,runpy
from rasterio.warp import reproject,Resampling
from rasterio.features import shapes
from shapely.geometry import shape
from shapely import make_valid
helper=runpy.run_path(str(ROOT/'scripts/04_rasters.py'),run_name='raster_tools')
folder=ROOT/'outputs/gis/rasters'
with rasterio.open(folder/'ndvi_summer2026_10m.tif') as summer:
 a=summer.read(1,masked=True);profile=summer.profile.copy();winter_aligned=np.full(a.shape,-9999,dtype='float32')
 with rasterio.open(folder/'ndvi_winter2026_10m.tif') as winter:
  reproject(winter.read(1),winter_aligned,src_transform=winter.transform,src_crs=winter.crs,src_nodata=winter.nodata,dst_transform=summer.transform,dst_crs=summer.crs,dst_nodata=-9999,resampling=Resampling.nearest)
 valid=(~np.ma.getmaskarray(a))&(winter_aligned!=-9999);diff=np.where(valid,a.data-winter_aligned,-9999)
 helper['save_product']('ndvi_seasonal_difference2026_10m',diff,profile,{'source_url':'https://earth-search.aws.element84.com/v1','license':'Copernicus open data','year':2026,'method':'September14 NDVI minus February21 NDVI on joint valid10m cells. Seasonal/sun-angle/phenological difference, NOT permanent vegetation degradation','joint_valid_cells':int(valid.sum())})
with rasterio.open(folder/'jrc_water_occurrence1984_2021_30m.tif') as ds:
 a=ds.read(1,masked=True);rows=[]
 for geom,value in shapes((a.data>=50).astype('uint8'),mask=(~np.ma.getmaskarray(a))&(a.data>=50),transform=ds.transform):
  g=make_valid(shape(geom)).intersection(AOI)
  if not g.is_empty:rows.append({'threshold_occurrence_percent':50,'observation_period':'1984-2021','source':'EC JRC Global Surface Water v1.4','license':'Copernicus open data','interpretation':'Historical occurrence-derived water proxy, not current bank/flood/control boundary','geometry':g})
 if rows:write_layer(gpd.GeoDataFrame(rows,crs=32651),ROOT/'outputs/gis/planning_enriched.gpkg','historical_water_occurrence_ge50')
progress('crosscheck','seasonality_water','complete')
