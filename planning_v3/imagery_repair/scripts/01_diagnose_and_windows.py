"""Audit actual native data, QGIS XML and source-pixel equality; fix comparison extents, not image detail."""
from pathlib import Path
import json,hashlib,zipfile,xml.etree.ElementTree as ET,os
os.environ.setdefault('MPLCONFIGDIR','/workspace/.cache/matplotlib')
import numpy as np,pandas as pd,geopandas as gpd,rasterio
from rasterio.windows import Window
from shapely import union_all
from shapely.geometry import box
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
import pymupdf
P=Path(__file__).resolve().parents[1];V3=P.parent;REPO=V3.parent;M=V3/'outputs/gis/reference_v2.gpkg';D=V3/'outputs/gis/refined_analysis_v3.gpkg';A=V3/'outputs/gis/reference_analysis_v2.gpkg';TIF=V3/'data/satellite/sentinel_truecolor_10m_context.tif';Q=V3/'outputs/qgis/planning_analysis_v3.qgz'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2,default=str))
protected=[M,D,A,TIF,REPO/'上海城市模型_Codex云端起步包/outputs/gis/city.gpkg',REPO/'上海城市模型_Codex云端起步包/outputs/gis/overture_audit.gpkg',V3/'data/boundary/选定范围.csv']
if not (P/'state/protected_inputs.json').exists():dump(P/'state/protected_inputs.json',{str(p.relative_to(REPO)):sha(p) for p in protected})
backup=P/'state/planning_analysis_v3_before_imagery_repair.qgz'
if not backup.exists():__import__('shutil').copy2(Q,backup)
with zipfile.ZipFile(backup) as z:
 root=ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.qgs'))))
 layers=[]
 for v in root.findall('.//projectlayers/maplayer'):
  source=v.findtext('datasource','');renderer=v.find('pipe/rasterrenderer')
  if 'sentinel_truecolor' in source:layers.append({'name':v.findtext('layername'),'source':source,'provider':v.findtext('provider'),'raster_renderer':renderer.attrib if renderer is not None else None,'resampling_filters':[{'tag':e.tag,**e.attrib} for e in v.iter() if e.tag in ['resampling','rasterresampler','brightnesscontrast']]})
 layouts=[]
 for lay in root.findall('.//Layouts/Layout'):
  if 'S02' in lay.get('name',''):
   layouts.append({'name':lay.get('name'),'dpi_attribute':lay.get('printResolution') or lay.get('dpi'),'map_items':[v.attrib for v in lay.findall('LayoutItem') if v.get('type')=='65639']})
 dump(P/'reports/qgis_source_render_audit.json',{'raster_layers':layers,'S02_layouts':layouts,'XYZ_low_zoom_source_in_use':any(l['provider']=='wms' for l in layers),'note':'Actual active imagery is local GeoTIFF, not an online low-zoom tile'})
site=gpd.read_file(D,layer='DESIGN_SITE').geometry.iloc[0];grid=gpd.read_file(D,layer='design_grid_100m');build=gpd.read_file(M,layer='buildings_enriched');nodes=gpd.read_file(A,layer='source_node_intersections');greens=gpd.read_file(M,layer='green_spaces_all')
windows=[]
dense=grid.loc[grid.building_density.idxmax()];p=dense.geometry.representative_point();windows.append({'id':'P01','type':'建筑密集区','point':p,'basis':'Maximum observed footprint coverage among exact100m design-intersection cells','reference':dense.grid_id})
inside=nodes[(nodes['mode']=='vehicle')&nodes.within(site)]
if len(inside):
 inside=inside.assign(distance_m=inside.distance(p));inside=inside[inside['distance_m']>150] if (inside['distance_m']>150).any() else inside;r=inside.sort_values(['degree','distance_m'],ascending=False).iloc[0];windows.append({'id':'P02','type':'道路交叉口','point':r.geometry,'basis':'Actual mapped vehicle junction inside user design boundary; not surveyed control','reference':r.source_url})
else:
 roads=gpd.read_file(M,layer='road_network_vehicle');r=roads[roads.intersects(site)].sort_values('length_m',ascending=False).iloc[0];windows.append({'id':'P02','type':'道路段','point':r.geometry.intersection(site).interpolate(.5,normalized=True),'basis':'Mapped road segment; no invented junction','reference':r.source_url})
patches=greens[greens.intersects(site)].copy();patches['geometry']=patches.intersection(site);patches=patches[patches.area>1]
if len(patches):
 r=patches.loc[patches.area.idxmax()];windows.append({'id':'P03','type':'已映射绿地','point':r.geometry.representative_point(),'basis':'Largest mapped green polygon intersection inside design boundary; land status not independently surveyed','reference':r.get('source_url','')})
else:
 r=grid.sort_values('building_density').iloc[0];windows.append({'id':'P03','type':'低建筑覆盖开敞候选区','point':r.geometry.representative_point(),'basis':'Low mapped building coverage; not assumed vegetation/water','reference':r.grid_id})
fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','pdf.fonttype':42,'axes.unicode_minus':False})
records=[];comparisons=[]
with rasterio.open(TIF) as ds:
 data=ds.read();profile=ds.profile.copy();source_meta={'path':str(TIF.relative_to(REPO)),'sha256':sha(TIF),'native_resolution':ds.res,'crs':str(ds.crs),'dtype':ds.dtypes,'bands':ds.count,'compression':ds.compression.value,'overview_factors':ds.overviews(1),'shape':ds.shape,'transform':list(ds.transform),'bounds':list(ds.bounds)}
 fig,axes=plt.subplots(1,3,figsize=(16.54,8.27),facecolor='#f8f7f2')
 for ax,w in zip(axes,windows):
  assert site.covers(w['point']);row,col=ds.index(w['point'].x,w['point'].y);win=Window(col-10,row-10,20,20);crop=ds.read(window=win);transform=ds.window_transform(win);bounds=rasterio.windows.bounds(win,ds.transform);center=((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2)
  out=P/f'data/{w["id"]}_old_native10m.tif';pr=profile.copy();pr.update(width=20,height=20,transform=transform,tiled=False);pr.pop('blockxsize',None);pr.pop('blockysize',None)
  with rasterio.open(out,'w',**pr) as dest:dest.write(crop)
  png=P/f'outputs/{w["id"]}_baseline_native10m.png';plt.imsave(png,np.moveaxis(crop,0,-1))
  records.append({'id':w['id'],'type':w['type'],'point_easting':w['point'].x,'point_northing':w['point'].y,'center_inside_design':True,'bounds_32651':bounds,'width_m':200,'height_m':200,'native_pixel_dimensions':[20,20],'old_source_resolution_m':10,'source_row':row-10,'source_col':col-10,'source_reference':w['reference'],'selection_basis':w['basis'],'new_image':None,'comparison_complete':False,'reason':'No legally verified higher-resolution source acquired; this is baseline only'})
  ax.imshow(np.moveaxis(crop,0,-1),extent=[bounds[0],bounds[2],bounds[1],bounds[3]],interpolation='nearest');gpd.GeoSeries([site.boundary],crs=32651).plot(ax=ax,color='#cb493e',linewidth=1.3);ax.set_xlim(bounds[0],bounds[2]);ax.set_ylim(bounds[1],bounds[3]);ax.set_title(w['id']+' '+w['type']+'\n200×200m / 原生20×20像元',fontsize=12);ax.set_axis_off()
 fig.suptitle('现有10m影像的三个固定对照窗口｜不是新旧高清对比结果',fontsize=17,color='#24465b');fig.text(.04,.10,'真实地物信息只有20×20像元。新影像尚未取得；不放大、锐化或生成屋顶细节冒充替换。后续对比必须沿用这三组EPSG:32651范围。',fontsize=11);fig.tight_layout(rect=[0,.15,1,.91]);fig.savefig(P/'outputs/three_fixed_baseline_windows_300dpi.png',dpi=300);fig.savefig(P/'outputs/three_fixed_baseline_windows.pdf');plt.close(fig)
 # Sample local pixels against the original remote native asset once: independently verifies the crop pipeline.
 provenance=json.loads((V3/'reports/satellite_provenance.json').read_text());url=provenance['source_url']
 try:
  with rasterio.Env(GDAL_CURL_CA_BUNDLE=os.environ.get('REQUESTS_CA_BUNDLE','/etc/ssl/certs/ca-certificates.crt'),GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_MAX_RETRY=1):
   with rasterio.open(url) as original:
    for r in records:
     x,y=ds.xy(r['source_row'],r['source_col']);rr,cc=original.index(x,y);a=original.read(window=Window(cc,rr,20,20));b=ds.read(window=Window(r['source_col'],r['source_row'],20,20));comparisons.append({'id':r['id'],'original_native_resolution':original.res,'source_values_identical':bool(np.array_equal(a,b)),'tested_RGB_values':int(b.size),'mean_absolute_DN_difference':float(np.abs(a.astype(float)-b).mean())})
 except Exception as e:comparisons.append({'status':'remote_control_unavailable','error':type(e).__name__,'local_pipeline_evidence':'V3 source script performs native-window copy, no warp or sharpen'})
rows=[]
for id in ['S01','S02','S03']:
 meta=json.loads((V3/f'reports/map_{id}.json').read_text());png=V3/f'outputs/maps/A1/{meta["stem"]}.png';pdf=V3/f'outputs/maps/A1/{meta["stem"]}.pdf'
 with Image.open(png) as im:pixel=im.size;dpi=im.info.get('dpi')
 doc=pymupdf.open(pdf);images=doc[0].get_images(full=True);rows.append({'id':id,'map_scale':meta['A1_scale'],'PNG_pixels':pixel,'PNG_DPI':dpi,'PDF_embedded_images':[{'width':v[2],'height':v[3],'bpc':v[4],'filter':v[8]} for v in images],'ground_extent_width_m':meta['extent'][1]-meta['extent'][0],'independent_native_samples_across_map':(meta['extent'][1]-meta['extent'][0])/10,'source_pixel_on_paper_mm':10/meta['A1_scale']*1000,'source_pixel_screen_pixels_at300dpi':10/meta['A1_scale']*1000/25.4*300});doc.close()
dump(P/'reports/native_raster_diagnosis.json',source_meta);dump(P/'reports/native_source_pixel_control.json',comparisons);dump(P/'reports/fixed_comparison_windows.json',records);dump(P/'reports/export_resolution_diagnosis.json',rows)
gpd.GeoDataFrame([{**{k:v for k,v in r.items() if k not in ['bounds_32651','native_pixel_dimensions']},'bounds_json':json.dumps(r['bounds_32651']),'geometry':w['point']} for r,w in zip(records,windows)],crs=32651).to_file(P/'data/comparison_locations.gpkg',layer='fixed_comparison_locations',driver='GPKG')
print('DIAGNOSIS complete; fixed windows',len(records),'native source controls',comparisons,flush=True)
