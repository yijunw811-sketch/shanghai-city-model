from common import *
import rasterio,shapely,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from matplotlib.colors import ListedColormap,BoundaryNorm
from PIL import Image,ImageDraw
from scipy.ndimage import sobel
fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','axes.unicode_minus':False})
style=json.loads((ROOT/'styles/COLOR_STYLE_SYSTEM.json').read_text());site=read('DESIGN_SITE',D).geometry.iloc[0];g100=read('grid_100m',D);g200=read('grid_200m',D);original=read('planning_grid_500m',A)
# Exact intersection weights compare piecewise fields; reaggregation is diagnostic, never fine-data generation.
records=[]
for size,f in [(100,g100),(200,g200)]:
 for field in ['building_density','volume_proxy_m','vehicle_density_km_km2','research_amenity_priority']:
  a=[];b=[]
  for r in original.itertuples():
   matches=f.iloc[f.sindex.query(r.geometry,predicate='intersects')];areas=matches.intersection(r.geometry).area;valid=matches[field].notna();val=np.average(matches.loc[valid,field],weights=areas[valid]) if valid.any() and areas[valid].sum()>0 else np.nan;a.append(val);b.append(getattr(r,field))
  a=np.array(a);b=np.array(b);valid=np.isfinite(a)&np.isfinite(b)
  records.append({'scale_m':size,'field':field,'comparison':'area-weighted piecewise reaggregation toV2 500m for diagnostic only','valid_cells':int(valid.sum()),'pearson_r':float(np.corrcoef(a[valid],b[valid])[0,1]),'mean_absolute_difference':float(abs(a[valid]-b[valid]).mean()),'max_abs_difference':float(abs(a[valid]-b[valid]).max()),'not_change_over_time':True})
pd.DataFrame(records).to_csv(ROOT/'reports/scale_stability_vs_v2.csv',index=False)
kde=[]
for h in [100,200,400]:
 f=g100[g100.site_intersection_m2>0];v=f[f'commercial_kde_h{h}_km2'];center=f.geometry.iloc[int(np.argmax(v.to_numpy()))].centroid;kde.append({'bandwidth_m':h,'site_context_units':len(f),'min_observed_intensity_km2':v.min(),'median':v.median(),'max':v.max(),'peak_center_x':center.x,'peak_center_y':center.y,'meaning':'kernel observation density, not commerce completeness or footfall'})
pd.DataFrame(kde).to_csv(ROOT/'reports/kde_bandwidth_sensitivity.csv',index=False)
# Same color thresholds in side-by-side scale views, with actual rather than interpolated intersections.
for field,title,sizes in [('building_density','建筑密度：真实几何相交的尺度差异',[50,100,200]),('commercial_kde','商业观察核强度：带宽敏感性',[100,200,400])]:
 fig,axes=plt.subplots(1,3,figsize=(18,6),facecolor='#F8F7F2');extent=site.buffer(250).bounds
 for ax,size in zip(axes,sizes):
  if field=='building_density':frame=read(f'grid_{size}m',D);key=field;sty=style['metric_styles'][field];caption=f'{size}m真实网格'
  else:frame=g100;key=f'commercial_kde_h{size}_km2';sty=style['metric_styles']['commercial_kde_h200_km2'];caption=f'高斯带宽 h={size}m'
  frame.plot(ax=ax,column=key,cmap=ListedColormap(style['palettes'][sty['palette']]),norm=BoundaryNorm(sty['breaks'],5),edgecolor='none');gpd.GeoSeries([site.boundary],crs=32651).plot(ax=ax,color='#CB493E',linewidth=2);ax.set(xlim=(extent[0],extent[2]),ylim=(extent[1],extent[3]),title=caption);ax.set_axis_off()
 fig.suptitle(title+'｜同一数值分级；设计红线不改变统计单元',fontsize=15);fig.tight_layout();fig.savefig(ROOT/f'outputs/comparisons/{field}_sensitivity.png',dpi=160);plt.close(fig)
# Rendered image comparisons, V2 panels are read-only references.
for id in ['02','04','06','08','11','15','16','18']:
 old=json.loads((V2/f'reports/map_{id}.json').read_text());new=json.loads((ROOT/f'reports/map_{id}.json').read_text());oldpath=V2/f'outputs/maps/A1/{id}_{old["title"].replace("｜","_").replace("/","_")}.png';newpath=ROOT/f'outputs/maps/A1/{new["stem"]}.png'
 canvas=Image.new('RGB',(2200,820),'#F8F7F2')
 for j,path in enumerate([oldpath,newpath]):
  with Image.open(path) as im:im.thumbnail((1090,780));canvas.paste(im,(j*1100+(1100-im.width)//2,25))
 ImageDraw.Draw(canvas).text((20,5),'V2 reference',fill='#24465B');ImageDraw.Draw(canvas).text((1120,5),'V3 exact geometry / source-resolution preserved',fill='#24465B');canvas.save(ROOT/f'outputs/comparisons/{id}_V2_V3.png')
# Registration evidence is source-frame consistency plus actual overlay previews; no false surveyed controls.
with rasterio.open(ROOT/'data/satellite/sentinel_truecolor_10m_context.tif') as ds:
 rgb=np.moveaxis(ds.read(),0,-1)/255.;bounds=ds.bounds;gray=rgb.mean(axis=2);grad=np.hypot(sobel(gray,axis=0),sobel(gray,axis=1))
 frame=read('buildings_enriched');near=frame[frame.distance(site)<100];samples=[]
 fig,ax=plt.subplots(figsize=(12,6));ax.imshow(rgb,extent=[bounds.left,bounds.right,bounds.bottom,bounds.top],interpolation='nearest');near.boundary.plot(ax=ax,color='#EFEFDF',linewidth=.5);gpd.GeoSeries([site.boundary],crs=32651).plot(ax=ax,color='white',linewidth=3);gpd.GeoSeries([site.boundary],crs=32651).plot(ax=ax,color='#CB493E',linewidth=2);e=site.buffer(100).bounds;ax.set(xlim=(e[0],e[2]),ylim=(e[1],e[3]),title='2026-10-14 原生10m影像与原建筑轮廓｜无拟合平移、无重绘');fig.tight_layout();fig.savefig(ROOT/'outputs/previews/satellite_vector_registration.png',dpi=180);plt.close(fig)
 # Spatially spread real source road nodes for manual overlay review, not surveyed control coordinates.
 points=read('source_node_intersections',A);points=points[points['mode']=='vehicle'];points=points.sort_values('node_id').iloc[::max(1,len(points)//16)].head(16)
 for r in points.itertuples():
  row,col=ds.index(r.geometry.x,r.geometry.y)
  if 0<=row<ds.height and 0<=col<ds.width:samples.append({'node_id':r.node_id,'easting':r.geometry.x,'northing':r.geometry.y,'image_row':row,'image_col':col,'local_RGB_gradient':float(grad[row,col]),'source_url':r.source_url,'status':'overlay_review_reference_not_surveyed_control'})
 pd.DataFrame(samples).to_csv(ROOT/'reports/registration_review_locations.csv',index=False)
 dump(ROOT/'reports/registration_check.json',{'same_crs':'EPSG:32651','native_resolution_m':ds.res,'bounds_cover_aoi':shapely.geometry.box(*ds.bounds).covers(AOI),'data_repositioned':False,'coordinate_accuracy_not_independently_surveyed':True,'preview':'outputs/previews/satellite_vector_registration.png','review_locations':len(samples),'limitations':'10m RGB, model footprint dates and parallax differ; visual/source-frame consistency is not geodetic accuracy proof'})
# Persist precisely the same raster colour settings for QGIS and atlas renderers.
for p in (ROOT/'reports').glob('map_[0-9][0-9].json'):
 m=json.loads(p.read_text())
 if m['kind']!='raster':continue
 id=m['id'];name=m['layer']
 with rasterio.open(ROOT/f'data/rasters_v2/{name}.tif') as ds:
  v=ds.read(1,masked=True).compressed();lo,hi=np.percentile(v,[2,98]);lo,hi=(v.min(),v.max()) if hi<=lo else (lo,hi)
 palette='ndvi' if 'ndvi_' in name else 'water' if 'occurrence' in name else 'ndwi' if 'ndwi' in name else 'ndbi' if 'ndbi' in name else 'temperature' if 'lst_' in name else 'dsm';palette='seasonal' if 'difference' in name else palette
 if palette=='ndvi':lo,hi=-.2,.8
 if palette in ['ndwi','ndbi']:lo,hi=-.8,.8
 if palette=='seasonal':lo,hi=-.5,.5
 rs={'palette':palette,'vmin':float(lo),'vmax':float(hi),'categorical':id in ['19','26']}
 if rs['categorical']:
  rs.update(codes=[10,20,30,40,50,60,70,80,90,95,100] if id=='19' else list(range(1,10)),labels=['树木','灌丛','草地','耕地','建成覆盖','裸地','冰雪','水体','湿地','红树林','苔藓'] if id=='19' else ['耕地','林地','灌丛','草地','水体','冰雪','裸地','不透水','湿地'],colors=['#628568','#A5A56D','#92AE78','#C7B579','#A18C80','#B8AE97','#CBD6D8','#6595A7','#76A28E','#497C72','#A8B29C'] if id=='19' else ['#C7B579','#628568','#A5A56D','#92AE78','#6595A7','#CBD6D8','#B8AE97','#A18C80','#76A28E'])
 m['raster_style']=rs;dump(p,m)
checkpoint('comparisons',styles_shared=True,scale_comparison=True,registration_preview=True)
