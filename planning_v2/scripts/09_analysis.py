"""Evidence-conservative functional partitions, source-node networks, native-grid summaries."""
from common import *
import numpy as np, networkx as nx
from shapely.geometry import Point,LineString,box
from shapely import union_all, get_parts, make_valid
from pyproj import Transformer
from scipy.spatial import cKDTree
import rasterio
from rasterio.features import geometry_mask
from shapely.ops import polygonize
M=ROOT/'outputs/gis/planning_enriched.gpkg'; OUT=ROOT/'outputs/gis/analysis_layers.gpkg'
def read(l):return gpd.read_file(M,layer=l)
def put(rows,layer,master=False):
 f=rows if isinstance(rows,gpd.GeoDataFrame) else gpd.GeoDataFrame(rows,geometry='geometry',crs=32651)
 if len(f):
  write_layer(f,OUT,layer)
  if master:write_layer(f,M,layer)
 return f
# Topology uses source node identity, never projected geometric crossings.
elements={}
for p in sorted((RAW/'osm_context').glob('tile*.json')):
 for e in json.loads(p.read_text())['elements']:
  key=(e['type'],e['id'])
  if key not in elements or len(e.get('tags',{}))>=len(elements[key].get('tags',{})):elements[key]=e
nodes={i:e for (typ,i),e in elements.items() if typ=='node' and 'lon'in e}
transform=Transformer.from_crs(4326,32651,always_xy=True)
xy={i:transform.transform(e['lon'],e['lat']) for i,e in nodes.items()}
walkclasses={'footway','path','pedestrian','steps','living_street','residential','service','unclassified','tertiary','tertiary_link','secondary','secondary_link','primary','primary_link','track','cycleway'}
vehicleclasses={'motorway','motorway_link','trunk','trunk_link','primary','primary_link','secondary','secondary_link','tertiary','tertiary_link','unclassified','residential','service','living_street'}
segments=[]
for (typ,i),e in elements.items():
 t=e.get('tags',{});h=t.get('highway','')
 if typ!='way' or not h or h in {'construction','proposed','abandoned','platform'}:continue
 ids=e.get('nodes',[])
 for k,(u,v) in enumerate(zip(ids,ids[1:])):
  if u not in xy or v not in xy or u==v:continue
  line=LineString([xy[u],xy[v]])
  if line.length<.01 or not line.intersects(CONTEXT):continue
  access=t.get('access','');foot=t.get('foot','');bicycle=t.get('bicycle','');private=access in ['no','private']
  walk=(h in walkclasses and not private and foot not in ['no','private'] and (h!='cycleway' or foot in ['yes','designated','permissive'])) or foot in ['yes','designated','permissive']
  cycle=h in vehicleclasses|{'cycleway','path','track','living_street'} and h not in {'motorway','motorway_link','trunk','trunk_link'} and not private and bicycle not in ['no','private']
  vehicle=h in vehicleclasses and not private and t.get('motor_vehicle') not in ['no','private']
  row={'way_id':i,'u':u,'v':v,'segment_index':k,'highway':h,'name':t.get('name',''),'length_m':line.length,'walk':walk,'cycle':cycle,'vehicle':vehicle,'layer':t.get('layer','0'),'bridge':t.get('bridge',''),'tunnel':t.get('tunnel',''),'oneway':t.get('oneway',''),'width':t.get('width',''),'lanes':t.get('lanes',''),'sidewalk':t.get('sidewalk',''),'cycleway':t.get('cycleway',''),'foot':foot,'bicycle':bicycle,'access':access,'wheelchair':t.get('wheelchair',''),'surface':t.get('surface',''),'source_url':f'https://www.openstreetmap.org/way/{i}','license':'ODbL-1.0','access_method':'source permission tags; public street default if unspecified','geometry':line,'in_aoi':line.intersects(AOI)}
  segments.append(row)
net=gpd.GeoDataFrame(segments,geometry='geometry',crs=32651)
for mode in ['vehicle','walk','cycle']:put(net[net[mode]].copy(),'road_network_'+mode,True)
walk=net[net.walk].reset_index(drop=True);G=nx.Graph()
for r in walk.itertuples():G.add_edge(r.u,r.v,weight=r.length_m)
# Explicit closed barriers disallow traversal; unknown gates remain review items.
blocked=[]
for n in list(G):
 t=nodes.get(n,{}).get('tags',{})
 if t.get('access') in ['no','private'] or t.get('foot') in ['no','private'] or t.get('barrier') in ['wall','fence']:
  G.remove_node(n);blocked.append(n)
walk=walk[walk.u.isin(G)&walk.v.isin(G)].copy()
validnodes=list(G);tree=cKDTree(np.array([xy[n] for n in validnodes]))
barrier=read('barriers');water=read('blue_network');build=read('buildings_enriched')
obstacles=union_all(list(water.geometry)+list(barrier[barrier.geom_type.isin(['LineString','MultiLineString'])].geometry))
seedlog=[]
def seed_point(p,source,kind):
 if p.is_empty:return None
 d,j=tree.query([p.x,p.y]);n=validnodes[j]
 if d<=2:method='mapped_node_coincidence_2m'
 elif d<=12:
  connector=LineString([p,Point(xy[n])])
  if connector.crosses(obstacles) or connector.intersection(obstacles).length>.1:return None
  candidates=build.iloc[build.sindex.query(connector,predicate='intersects')]
  if any(connector.crosses(g) for g in candidates.geometry):return None
  method='short_snap_le12m_barrier_building_screened_not_verified_entrance'
 else:return None
 seedlog.append({'source_id':source,'kind':kind,'node_id':n,'snap_m':float(d),'method':method,'geometry':Point(xy[n])});return n
poi=read('poi_all');transit=read('transit_stations');parks=read('green_parks')
seeds={}
for category in sorted(poi.category.unique()):
 seeds[category]=set()
 for r in poi[poi.category==category].itertuples():
  n=seed_point(r.geometry,r.canonical_id,category)
  if n is not None:seeds[category].add(n)
seeds['transit']=set()
for r in transit.itertuples():
 if r.station_type not in ['subway_entrance','entrance','platform','bus_stop','stop_position']:continue
 p=r.geometry if r.geometry.geom_type=='Point' else r.geometry.representative_point()
 n=seed_point(p,r.canonical_id,'transit')
 if n is not None:seeds['transit'].add(n)
seeds['parks']=set()
for r in parks.itertuples():
 if str(r.access) in ['private','no']:continue
 # Evidence-based approximate entrance: mapped walk edge really intersects park boundary.
 for idx in walk.sindex.query(r.geometry.boundary,predicate='intersects'):
  e=walk.iloc[idx]
  for n in [int(e.u),int(e.v)]:
   if Point(xy[n]).distance(r.geometry.boundary)<=20:
    seeds['parks'].add(n);seedlog.append({'source_id':r.canonical_id,'kind':'parks','node_id':n,'snap_m':Point(xy[n]).distance(r.geometry.boundary),'method':'mapped_walk_edge_crosses_park_boundary_nearest_endpoint_le20m_open_status_unverified','geometry':Point(xy[n])})
put(seedlog,'access_seed_audit')
coverage=[]
for kind,ss in seeds.items():
 if not ss:continue
 distances=nx.multi_source_dijkstra_path_length(G,ss,cutoff=1125,weight='weight')
 rows=[]
 for r in walk.itertuples():
  a=distances.get(r.u,float('inf'));b=distances.get(r.v,float('inf'));length=r.length_m
  # Exact partial edge costs for display; reachability never an Euclidean circle.
  intervals=[]
  for minutes,limit in [(5,375),(10,750),(15,1125)]:
   from shapely.ops import substring
   pieces=[]
   left_end=min(length,max(0,limit-a));right_start=max(0,min(length,length-(limit-b)))
   if left_end<=0 and right_start>=length:continue
   # Merge scalar intervals before geometry construction; floating-line union can duplicate overlaps.
   if left_end>=right_start:geom=r.geometry
   else:
    if left_end>0:pieces.append(substring(r.geometry,0,left_end))
    if right_start<length:pieces.append(substring(r.geometry,right_start,length))
    from shapely.geometry import MultiLineString
    geom=MultiLineString(pieces) if len(pieces)>1 else pieces[0]
   geom=geom.intersection(AOI)
   if geom.is_empty or geom.length==0:continue
   rows.append({'kind':kind,'minutes':minutes,'way_id':r.way_id,'speed_kmh':4.5,'coverage_unit':'reachable mapped walk-edge length, not population/land coverage','geometry':geom,'reachable_m':geom.length})
  
 if rows:
  f=put(rows,'access_'+kind)
  for mins in [5,10,15]:coverage.append({'kind':kind,'minutes':mins,'seed_nodes_context':len(ss),'reachable_walk_m_aoi':f.loc[f.minutes==mins].geometry.length.sum(),'denominator_walk_m_aoi':walk.intersection(AOI).length.sum()})
coverage_frame=pd.DataFrame(coverage)
for _,group in coverage_frame.groupby('kind'):
 assert np.all(np.diff(group.sort_values('minutes').reachable_walk_m_aoi)>=-0.001), 'Nonmonotonic network coverage'
pd.DataFrame(coverage).to_csv(ROOT/'reports/network_service_coverage.csv',index=False)
# degree counts source-node identities; multiple parallel directions dedup via simple graph.
intersections=[]
for mode in ['vehicle','walk','cycle']:
 H=nx.Graph()
 for r in net[net[mode]].itertuples():H.add_edge(r.u,r.v)
 for n,degree in H.degree():
  if degree>=3 and AOI.covers(Point(xy[n])):intersections.append({'mode':mode,'node_id':n,'degree':degree,'source_url':f'https://www.openstreetmap.org/node/{n}','geometry':Point(xy[n])})
put(intersections,'source_node_intersections')
dump(ROOT/'reports/network_topology.json',{'segments_context':len(net),'walk_nodes':len(G),'walk_components':nx.number_connected_components(G),'largest_component_node_fraction':len(max(nx.connected_components(G),key=len))/len(G),'explicitly_closed_barrier_nodes_removed':len(blocked),'seed_counts_context':{k:len(v) for k,v in seeds.items()},'limitations':['2km context truncation','Unmapped sidewalks/crossings and opening hours unknown','Vehicle turn restriction relations retained in raw; not applied to descriptive density; no driving routing','Cycle/vehicle permission defaults and directions retained, not a travel-time graph','Unknown gate access remains unverified; not wheelchair routing','Source-node junctions only; no false geometric bridge crossing joins']})
progress('analysis','network','complete')
# Functional mapping: only mapped POLYGON uses, not single POI or physical cover.
labels={'residential':'居住功能','public_service':'公共管理与服务','commercial':'商业商务','industrial':'工业仓储','transport':'交通与停车','green_open':'绿地与开敞','water':'水域','construction':'在建待核实','unknown':'待核实'}
refs={'residential':'07','public_service':'08','commercial':'09','industrial':'10/11','transport':'12','green_open':'14','water':'17','construction':'','unknown':''}
def classify(t):
 lu=t.get('landuse','');am=t.get('amenity','');le=t.get('leisure','');na=t.get('natural','')
 if na=='water' or t.get('water') or t.get('waterway') in ['riverbank','dock']:return 'water'
 if am in ['school','kindergarten','university','college','hospital','clinic','community_centre','library','fire_station','police','townhall']:return 'public_service'
 if am in ['parking','bus_station'] or lu in ['railway','highway']:return 'transport'
 if le in ['park','garden','pitch','playground','sports_centre','recreation_ground'] or lu in ['grass','forest','recreation_ground','village_green','cemetery']:return 'green_open'
 if lu in ['residential']:return 'residential'
 if lu in ['commercial','retail']:return 'commercial'
 if lu in ['industrial','warehouse','depot']:return 'industrial'
 if lu in ['construction','brownfield']:return 'construction'
 return None
def candidates(frame,field):
 rows=[]
 for r in frame.itertuples():
  if r.geometry.geom_type not in ['Polygon','MultiPolygon']:continue
  t=json.loads(getattr(r,field) or '{}') if field else {k:v for k,v in r._asdict().items() if isinstance(v,str)}
  if field=='source_properties_json':t=dict(t.get('source_tags') or [])|{'landuse':t.get('class','')} if t.get('class') in ['residential','commercial','industrial','retail','construction','forest','grass'] else dict(t.get('source_tags') or [])
  cl=classify(t)
  if cl:rows.append({'class':cl,'source':getattr(r,'canonical_id','baseline_osm'),'evidence':json.dumps(t,ensure_ascii=False),'geometry':r.geometry.intersection(AOI)})
 return rows
def partition(rows):
 assigned=AOI.difference(AOI);out=[]
 priority=['water','public_service','transport','green_open','commercial','industrial','residential','construction']
 for cl in priority:
  for r in sorted([x for x in rows if x['class']==cl],key=lambda x:x['geometry'].area):
   geom=make_valid(r['geometry']).difference(assigned)
   if geom.is_empty or geom.area<.1:continue
   assigned=union_all([assigned,geom]);out.append({'class':cl,'class_name':labels[cl],'guide_reference_code':refs[cl],'class_source':r['source'],'class_method':'mapped_polygon_function_crosswalk_priority_partition','evidence':r['evidence'],'confidence':'source_tag_not_field_verified','review_status':'research_function_not_statutory','is_inferred':True,'geometry':geom,'area_m2':geom.area})
 unknown=AOI.difference(assigned)
 out.append({'class':'unknown','class_name':labels['unknown'],'guide_reference_code':'','class_source':'none','class_method':'no_supported_function','evidence':'Not filled from isolated POI or vegetation pixels','confidence':'unknown','review_status':'needs_source_or_field_check','is_inferred':False,'geometry':unknown,'area_m2':unknown.area})
 return gpd.GeoDataFrame(out,geometry='geometry',crs=32651)
base=gpd.read_file(CITY,layer='osm_source_features');basefield=None
basepart=partition(candidates(base,basefield))
features=read('osm_features_context');land=read('overture_land_use')
parts=partition(candidates(features,'tags_json')+candidates(land,'source_properties_json'))
put(parts,'landuse_existing',True);put(parts[parts['class']=='unknown'].copy(),'landuse_inference_review',True)
stats=parts.groupby(['class','class_name']).area_m2.sum().reset_index();stats['percent_aoi']=stats.area_m2/AOI.area*100
stats.to_csv(ROOT/'reports/landuse_statistics.csv',index=False)
with sqlite3.connect(M) as con:stats.to_sql('landuse_statistics',con,if_exists='replace',index=False)
pd.DataFrame([{'analysis_class':k,'class_name':v,'guide_2023_reference':refs[k],'mapping_status':'research reference only; 2023 official original/latest revision could not be verified via accessible official search','is_statutory':False} for k,v in labels.items()]).to_csv(ROOT/'standards/landuse_codebook.csv',index=False)
dump(ROOT/'reports/landuse_partition_qa.json',{'aoi_m2':AOI.area,'partition_sum_m2':parts.area.sum(),'union_m2':union_all(parts.geometry).area,'overlap_m2':parts.area.sum()-union_all(parts.geometry).area,'same_rule_baseline_function_unknown_km2':basepart.loc[basepart['class']=='unknown'].area.sum()/1e6,'enhanced_function_unknown_km2':parts.loc[parts['class']=='unknown'].area.sum()/1e6,'old_physical_unclassified_km2_not_comparable':14.086697685,'classification':'Observed-source polygon functional interpretation, not legal planning land use; unknown preserved'})
# Analysis blocks use ground road source lines + actual water; never legal parcels.
ground=net[(net.vehicle)&(net.layer=='0')&(~net.bridge.isin(['yes','viaduct']))&(~net.tunnel.isin(['yes','building_passage']))]
linework=union_all([AOI.boundary]+list(ground.intersection(AOI).geometry)+list(water.intersection(AOI).boundary))
blocks=[p.intersection(AOI) for p in polygonize(linework) if p.representative_point().within(AOI) and p.area>100]
put([{'block_id':i,'unit_type':'source_ground_road_analysis_block_not_cadastral','area_m2':p.area,'geometry':p} for i,p in enumerate(blocks)],'urban_blocks',True)
# Mutually exclusive max-height surfaces prevent overlapping footprints double-volume.
footprint=union_all(build.geometry);assigned=AOI.difference(AOI);vol=[]
for h,group in build.groupby('height_m',sort=True):pass
for h in sorted(build.height_m.unique(),reverse=True):
 geom=union_all(build.loc[build.height_m==h].geometry).difference(assigned)
 assigned=union_all([assigned,geom]);vol.append((float(h),geom))
minx,miny,maxx,maxy=AOI.bounds;grids=[]
for x in np.arange(np.floor(minx/500)*500,maxx,500):
 for y in np.arange(np.floor(miny/500)*500,maxy,500):
  g=box(x,y,x+500,y+500).intersection(AOI)
  if g.area<1:continue
  row={'grid_id':f'{int(x)}_{int(y)}','area_m2':g.area,'edge_fraction':g.area/250000,'building_density':footprint.intersection(g).area/g.area,'volume_proxy_m':sum(h*p.intersection(g).area for h,p in vol)/g.area,'geometry':g}
  for mode in ['vehicle','walk','cycle']:row[mode+'_density_km_km2']=net.loc[net[mode]].intersection(g).length.sum()/1000/(g.area/1e6)
  pp=poi[poi.intersects(g)];counts=pp.category.value_counts();probs=counts/counts.sum() if len(counts) else counts
  row['poi_count']=len(pp);row['commercial_poi']=int((pp.category=='commercial').sum());row['poi_entropy']=float(-(probs*np.log(probs)).sum()/np.log(9)) if len(pp)>=5 else np.nan;row['mix_reliability']='sparse_not_reported' if len(pp)<5 else 'mapped_POI_sample_bias'
  row['green_fraction']=union_all(read_green.geometry).intersection(g).area/g.area if False else 0
  grids.append(row)
grid=gpd.GeoDataFrame(grids,geometry='geometry',crs=32651)
green=union_all(read('green_spaces_all').geometry)
grid['mapped_green_fraction']=[green.intersection(g).area/g.area for g in grid.geometry]
grid['mapped_water_fraction']=[union_all(water.geometry).intersection(g).area/g.area for g in grid.geometry]
# Remote raster zonal means use valid native pixels, explicitly not population disaggregation.
for path in (ROOT/'outputs/gis/rasters').glob('*.tif'):
 with rasterio.open(path) as ds:
  geoms=grid.to_crs(ds.crs);a=ds.read(1,masked=True)
  vals=[]
  for g in geoms.geometry:
   mask=geometry_mask([g],a.shape,ds.transform,invert=True)
   good=mask&~np.ma.getmaskarray(a);vals.append(float(np.mean(a.data[good])) if good.any() else np.nan)
  key=path.stem[:50];grid[key]=vals
put(grid,'planning_grid_500m',True)
# Native population cell polygons with counts and area-weighted AOI clipping, no downscaling.
from rasterio.windows import Window
popsummary=[]
for sid,path in [('ghsl2020',RAW/'ghsl/ghspop2020_100m_context.tif'),('worldpop2025',RAW/'worldpop/worldpop2025_1000m_context.tif')]:
 with rasterio.open(path) as ds:
  a=ds.read(1,masked=True);rows=[]
  for y,x in zip(*np.where(~np.ma.getmaskarray(a)&(a.data>=0))):
   b=rasterio.windows.bounds(Window(int(x),int(y),1,1),ds.transform);cell=gpd.GeoSeries([box(*b)],crs=ds.crs).to_crs(32651).iloc[0]
   clip=cell.intersection(AOI)
   if clip.area==0:continue
   rows.append({'native_population_count':float(a[y,x]),'aoi_area_fraction':clip.area/cell.area,'aoi_weighted_count':float(a[y,x])*clip.area/cell.area,'native_resolution_m':100 if sid=='ghsl2020' else 1000,'year':2020 if sid=='ghsl2020' else 2025,'quality':'model_estimate_not_census; boundary_uniform_fraction_assumption','population_density_km2':float(a[y,x])/cell.area*1e6,'geometry':clip})
  f=put(rows,'population_'+sid,True);popsummary.append({'source':sid,'year':2020 if sid=='ghsl2020' else 2025,'cells_intersect_aoi':len(f),'model_estimate_aoi_area_weighted':f.aoi_weighted_count.sum(),'valid_aoi_fraction':union_all(f.geometry).area/AOI.area})
pd.DataFrame(popsummary).to_csv(ROOT/'reports/population_model_summary.csv',index=False)
progress('analysis','metrics','complete');print('ANALYSIS COMPLETE',len(grid),len(parts),len(blocks),flush=True)
