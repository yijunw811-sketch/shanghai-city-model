from common import *
import rasterio,numpy as np
from rasterio.features import shapes
from rasterio.warp import reproject,Resampling
from shapely.geometry import shape
from shapely import make_valid
M=ROOT/'outputs/gis/planning_enriched.gpkg'
lookup={1:'耕地',2:'林地',3:'灌丛',4:'草地',5:'水面',6:'冰雪',7:'裸地',8:'不透水',9:'湿地'}
for name,year,res,provider,license in [('clcd2019_30m',2019,30,'Yang and Huang / CLCD','CC-BY-4.0'),('worldcover2021_10m',2021,10,'ESA WorldCover','CC-BY-4.0')]:
 with rasterio.open(ROOT/f'outputs/gis/rasters/{name}.tif') as ds:
  a=ds.read(1,masked=True);rows=[]
  for geom,value in shapes(a.data.astype('int16'),mask=~np.ma.getmaskarray(a),transform=ds.transform):
   g=make_valid(shape(geom)).intersection(AOI)
   if g.is_empty or g.area<.01:continue
   rows.append({'class_id':int(value),'source_year':year,'native_resolution_m':res,'provider':provider,'license':license,'class_interpretation':'physical_cover_only_not_function_or_statutory','source_url':'https://zenodo.org/records/4417810' if year==2019 else 'https://esa-worldcover.org/','geometry':g})
  f=gpd.GeoDataFrame(rows,crs=32651);write_layer(f,M,'physical_cover_'+name);f.assign(area_m2=f.area).groupby('class_id').area_m2.sum().to_csv(ROOT/f'reports/{name}_areas.csv')
with rasterio.open(ROOT/'outputs/gis/rasters/clcd2019_30m.tif') as src:
 a=src.read(1,masked=True);warped=np.full(a.shape,-9999,dtype='int16')
 with rasterio.open(ROOT/'outputs/gis/rasters/worldcover2021_10m.tif') as other:
  reproject(other.read(1),warped,src_transform=other.transform,src_crs=other.crs,src_nodata=other.nodata,dst_transform=src.transform,dst_crs=src.crs,dst_nodata=-9999,resampling=Resampling.mode)
 valid=(~np.ma.getmaskarray(a))&(warped!=-9999)
 rows=pd.DataFrame({'clcd2019':a.data[valid].astype(int),'worldcover2021':warped[valid].astype(int)}).value_counts().rename('native30m_cells').reset_index();rows.to_csv(ROOT/'reports/physical_cover_cross_product_crosstab.csv',index=False)
 dump(ROOT/'reports/physical_cover_crosscheck.json',{'joint_valid_cells':int(valid.sum()),'method':'WorldCover modal resampling onto CLCD30m; counts reflect coarse-grid comparison, not accuracy truth or change attribution','impervious_built_agreement_fraction':float(((a.data[valid]==8)==(warped[valid]==50)).mean()),'not_same_year':True,'not_functional_landuse':True})
register('clcd_classes',category='B G',provider='Yang and Huang / Zenodo',dataset_name='CLCD official classification workbook',url='https://zenodo.org/records/4417810',license='CC-BY-4.0',access_status='verified_classification_workbook',round=3)
export_registry();progress('crosscheck','physical_cover','complete')
