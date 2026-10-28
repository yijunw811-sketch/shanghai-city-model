from common import *
import shapely
from shapely.geometry import box
from shapely import STRtree,union_all,get_parts
from scipy.spatial.distance import cdist
SITE=read('DESIGN_SITE',D).geometry.iloc[0];FINE_CONTEXT=SITE.buffer(500).intersection(AOI)
b=read('buildings_enriched');land=read('landuse_existing');roads=read('road_network_vehicle');walk=read('road_network_walk');green=read('green_spaces_all');poi=read('poi_all');nodes=read('source_node_intersections',A);nodes=nodes[nodes['mode']=='vehicle']
footprint=union_all(b.geometry);greenunion=union_all(green.geometry);assigned=AOI.difference(AOI);vol=[]
for h in sorted(b.height_m.unique(),reverse=True):
 geom=union_all(b.loc[b.height_m==h].geometry).difference(assigned);assigned=union_all([assigned,geom])
 for p in get_parts(geom):
  if p.area>0:vol.append((p,float(h)))
volgeom=np.array([p for p,h in vol],dtype=object);heights=np.array([h for p,h in vol]);footparts=np.array(list(get_parts(footprint)),dtype=object);greenparts=np.array(list(get_parts(greenunion)),dtype=object)
reach=read('access_daily_service',A);reachable=np.array(list(get_parts(union_all(reach.loc[reach.minutes==15].geometry))),dtype=object)
classes=sorted(set(land['class'])-{'unknown'});L={}
for cl in classes:L[cl]=np.array(list(get_parts(union_all(land.loc[land['class']==cl].geometry))),dtype=object)
commercial=poi[poi.category=='commercial'];coordinates=np.array([[p.x,p.y] for p in commercial.geometry]);aoi_commercial=commercial[commercial.in_aoi]
def sums(cells,features,metric='area',weights=None):
 if len(features)==0:return np.zeros(len(cells))
 pair=STRtree(features).query(cells,predicate='intersects')
 if pair.shape[1]==0:return np.zeros(len(cells))
 geom=shapely.intersection(cells[pair[0]],features[pair[1]])
 value=shapely.area(geom) if metric=='area' else shapely.length(geom)
 if weights is not None:value=value*weights[pair[1]]
 return np.bincount(pair[0],weights=value,minlength=len(cells))
def area_entropy(mat):
 total=mat.sum(axis=1);p=np.divide(mat,total[:,None],out=np.zeros_like(mat),where=total[:,None]>0)
 return -np.sum(np.where(p>0,p*np.log(np.where(p>0,p,1)),0),axis=1)/np.log(len(classes))
def metrics(frame):
 cells=np.array(frame.geometry,dtype=object);areas=frame.area.to_numpy();frame['area_m2']=areas
 frame['building_footprint_m2']=sums(cells,footparts);frame['building_density']=frame.building_footprint_m2/areas
 frame['estimated_volume_m3']=sums(cells,volgeom,weights=heights);frame['volume_proxy_m']=frame.estimated_volume_m3/areas
 for key,features in [('vehicle',np.array(roads.geometry,dtype=object)),('walk',np.array(walk.geometry,dtype=object))]:frame[key+'_m']=sums(cells,features,'length');frame[key+'_density_km_km2']=frame[key+'_m']/areas*1000
 frame['mapped_green_m2']=sums(cells,greenparts);frame['mapped_green_fraction']=frame.mapped_green_m2/areas
 frame['reachable_daily_walk_m']=sums(cells,reachable,'length');frame['daily_service_reachable_walk_fraction']=np.minimum(1,np.divide(frame.reachable_daily_walk_m,frame.walk_m,out=np.full(len(frame),np.nan),where=frame.walk_m>0))
 mat=np.column_stack([sums(cells,L[cl]) for cl in classes]);known=mat.sum(axis=1);frame['known_function_m2']=known;frame['known_function_fraction']=known/areas
 ent=area_entropy(mat);frame['land_function_entropy_raw']=np.where(known>0,ent,np.nan);frame['land_function_entropy']=np.where(frame.known_function_fraction>=.5,ent,np.nan)
 for j,cl in enumerate(classes):frame['function_'+cl+'_m2']=mat[:,j]
 mat2=mat.copy()
 if 'construction' in classes:mat2[:,classes.index('construction')]=0
 frame['entropy_excluding_construction']=np.where((frame.known_function_fraction>=.5)&(mat2.sum(axis=1)>0),area_entropy(mat2),np.nan)
 frame['entropy_definition']='Shannon of mapped functional polygon areas / ln(8); unknown excluded, valid known fraction>=50%; not V2 POI entropy'
 points=np.array(aoi_commercial.geometry,dtype=object);pair=STRtree(cells).query(points,predicate='intersects');counts=np.zeros(len(cells),dtype=int)
 # Stable half-open cell ownership prevents points on internal grid boundaries being counted twice.
 for j in range(len(points)):
  matches=pair[1,pair[0]==j]
  if len(matches):counts[min(matches)]+=1
 frame['commercial_poi']=counts;frame['commercial_density_km2']=counts/areas*1e6
 ns=np.array(nodes.geometry,dtype=object);pair=STRtree(cells).query(ns,predicate='intersects');counts=np.zeros(len(cells),dtype=int)
 for j in range(len(ns)):
  matches=pair[1,pair[0]==j]
  if len(matches):counts[min(matches)]+=1
 frame['true_vehicle_junctions']=counts;frame['junction_density_km2']=counts/areas*1e6
 centers=np.array([[p.x,p.y] for p in frame.geometry.centroid]);distance=cdist(centers,coordinates)
 for h in [100,200,400]:frame[f'commercial_kde_h{h}_km2']=np.exp(-distance**2/(2*h*h)).sum(axis=1)/(2*np.pi*h*h)*1e6
 frame['research_amenity_priority']=(frame.building_density.rank(pct=True)+(1-frame.mapped_green_fraction).rank(pct=True)+(1-frame.daily_service_reachable_walk_fraction).rank(pct=True))/3
 frame['score_weights']='equal 1/3 density rank + mapped green deficit rank + daily-service unreachable walk rank; V2 weights retained'
 frame['site_intersection_m2']=frame.intersection(SITE).area
 frame['source_height_status']='ALL height estimates/levels-derived; no measured GFA/FAR'
 return frame
summaries=[];thresholds=[]
for size in [50,100,200]:
 scope=FINE_CONTEXT if size==50 else AOI
 rows=[];w,s,e,n=scope.bounds
 for x in np.arange(np.floor(w/size)*size,e,size):
  for y in np.arange(np.floor(s/size)*size,n,size):
   p=box(x,y,x+size,y+size).intersection(scope)
   if p.area>.01:rows.append({'grid_id':f'{size}_{int(x)}_{int(y)}','grid_size_m':size,'origin_x':0.,'origin_y':0.,'scope':'design_site_buffer500m' if size==50 else 'whole_aoi','geometry':p})
 frame=metrics(gpd.GeoDataFrame(rows,crs=32651));put(frame,f'grid_{size}m');frame.to_file(ROOT/f'data/grid_{size}m/grid_{size}m.gpkg',layer=f'grid_{size}m',driver='GPKG')
 # Actual design-clipped geometry gets its own denominators and exact recalculation, never centroid membership.
 siteframe=frame[frame.site_intersection_m2>.01][['grid_id','grid_size_m','origin_x','origin_y','scope','geometry']].copy();siteframe['geometry']=siteframe.intersection(SITE);siteframe['scope']='design_site_exact_intersection';siteframe=metrics(siteframe);put(siteframe,f'design_grid_{size}m')
 for key in ['building_density','volume_proxy_m','land_function_entropy','vehicle_density_km_km2','junction_density_km2','commercial_density_km2','research_amenity_priority']:
  v=frame[key];summaries.append({'scale_m':size,'scope':frame.scope.iloc[0],'indicator':key,'units':len(frame),'design_intersect_units':len(siteframe),'valid_units':int(v.notna().sum()),'zero_fraction':float((v==0).mean()),'min':v.min(),'median':v.median(),'p95':v.quantile(.95),'max':v.max(),'std':v.std()})
 for fraction in [.25,.5,.75]:thresholds.append({'scale_m':size,'known_area_threshold':fraction,'valid_units':int((frame.known_function_fraction>=fraction).sum()),'total_units':len(frame)})
 # Core area conservation and global geometry conservation, all use exact source intersections.
 expected=footprint.intersection(scope).area;assert abs(frame.building_footprint_m2.sum()-expected)<.05
 assert abs(siteframe.area.sum()-SITE.area)<.05
 assert abs(siteframe.building_footprint_m2.sum()-footprint.intersection(SITE).area)<.05
 assert frame.building_density.max()<=1.000001
 print('GRID',size,len(frame),'design',len(siteframe),'footprint conservation error',frame.building_footprint_m2.sum()-expected,flush=True)
 checkpoint('grid_'+str(size),units=len(frame),design_units=len(siteframe),footprint_conserved=True)
pd.DataFrame(summaries).to_csv(ROOT/'reports/scale_sensitivity.csv',index=False);pd.DataFrame(thresholds).to_csv(ROOT/'reports/functional_coverage_threshold_sensitivity.csv',index=False)
selection={'building_density':{'test':[50,100],'selected':100,'reason':'100m improves on500m, with50m design/context comparison retained; source footprints support true intersections'},'volume_proxy_m':{'selected':100,'reason':'Actual clipped footprint×estimated height; max-height overlap assignment; not FAR'},'land_function_entropy':{'test':[100,200],'selected':200,'reason':'Sparse mapped functional coverage; conditional area entropy and known fraction>=50%; construction exclusion sensitivity retained'},'vehicle_density_km_km2':{'test':[100,200],'selected':200,'reason':'100m empty/one-road fluctuations compared with200m; true source node junctions independently retained'},'commercial_density_km2':{'test':[100,200],'selected':200,'reason':'138 observed AOI commercial points are sparse; count-based200m with KDE100/200/400 sensitivity, not inferred jobs/footfall'},'research_amenity_priority':{'selected':100,'reason':'V2 equal weights retained; ranks recomputed per stated analysis domain'},'issues':{'selected':100,'reason':'Grid score plus actual baseline review features, not every issue forced into cells'},'population2025':{'selected':'native~1km','reason':'No licensed/efficient finer2025 subset verified; preserve original48 cells, no interpolation/downscaling'}}
dump(ROOT/'reports/indicator_scale_selection.json',selection)
dump(ROOT/'reports/grid_method.json',{'origin':[0,0],'crs':'EPSG:32651','50m_scope':'design site +500m intersect AOI','100m_200m_scope':'whole AOI, plus separate exact design intersections','boundary_area_correction':True,'population_downscaled':False,'functional_mix_changed_from_V2':'Area entropy of mapped functions; V2 POI entropy remains a different original indicator','KDE':'Observed counts kernel sum/(2*pi*h^2), units observed points/km2; AOI+2km source context; not normalized probability or traffic','score_population':'No population used in scores','topology':'V2 source-node junctions reused unchanged; no geometric crossing nodes created'})
