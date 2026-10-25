"""Build a separate, provenance-rich planning geodatabase from actual sources."""
import copy
import collections
import json
import math
import re
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import shapely
from shapely.geometry import Point,LineString,MultiLineString
import osmnx as ox
from common import *

MASTER=ROOT/'outputs/gis/planning_enriched.gpkg'
CONTEXT_GDF=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).iloc[0]
progress('standardization','master','running')
raw={};timestamps=[];source_conflicts=[]
for path in sorted((RAW/'osm_context').glob('tile_*.json')):
    data=json.loads(path.read_text());timestamps.append(data.get('osm3s',{}).get('timestamp_osm_base',''))
    for element in data['elements']:
        key=(element['type'],element['id'])
        if key in raw and element.get('tags') and raw[key].get('tags') and raw[key]['tags']!=element['tags']:
            source_conflicts.append({'source':'OSM tile snapshots','feature':str(key),'conflict':'different tags during acquisition window','resolution':'latest full-tagged tile record retained; raw responses preserved'})
        if key not in raw or (element.get('tags') and len(element.get('tags',{}))>=len(raw[key].get('tags',{}))):raw[key]=element
if not raw:raise RuntimeError('No OSM context data; baseline-only fallback must be explicit')
keys=['highway','footway','cycleway','railway','public_transport','amenity','shop','office','tourism','leisure','landuse','natural','waterway','historic','barrier','entrance','emergency','healthcare','social_facility','power','man_made','place','addr:housenumber']
features=ox.features._create_gdf([{'elements':copy.deepcopy(list(raw.values()))}],CONTEXT_GDF,{k:True for k in keys})
features=source_context(features).reset_index()
def missing(value):return value is None or (isinstance(value,(float,np.floating)) and not math.isfinite(value))
def value(row,key,default=''):
    x=row.get(key,default)
    return default if missing(x) else str(x)
def primitive(x):
    if isinstance(x,np.ndarray):return [primitive(v) for v in x]
    if isinstance(x,(list,tuple)):return [primitive(v) for v in x]
    if isinstance(x,dict):return {k:primitive(v) for k,v in x.items()}
    if isinstance(x,np.generic):return primitive(x.item())
    if missing(x):return None
    return x
def json_text(x):return json.dumps(primitive(x),ensure_ascii=False)
def make(records):return gpd.GeoDataFrame(records if records else {'geometry':[]},geometry='geometry',crs=32651)
def meta_osm(kind,ident):
    return {**provenance('OpenStreetMap contributors','OSM context structured extract',f'https://www.openstreetmap.org/{kind}/{ident}','ODbL-1.0'), 'canonical_id':f'osm:{kind}:{ident}','osm_type':kind,'osm_id':int(ident),'snapshot_date':max(timestamps),'release_date':max(timestamps),'feature_observation_date':'unknown; dataset snapshot is not survey date'}
def fields(row):return {k:value(row,k) for k in ['name','name:en','amenity','shop','office','tourism','leisure','landuse','natural','waterway','highway','railway','public_transport','historic','heritage','entrance','barrier','access','foot','bicycle','sidewalk','cycleway','wheelchair','surface','operator','network','ref','addr:street','addr:housenumber','addr:city','opening_hours']}
feature_records=[]
for _,row in features.iterrows():
    kind=row.element;ident=row.id
    tags={str(k):primitive(v) for k,v in row.items() if k not in ('geometry','element','id') and not missing(v)}
    feature_records.append({**meta_osm(kind,ident),**fields(row),'tags_json':json_text(tags),'in_aoi':bool(row.geometry.intersects(AOI)),'geometry':row.geometry})
f=make(feature_records)
if MASTER.exists():MASTER.unlink()  # only this task's generated master, originals protected
write_layer(make([{**provenance('用户提供','Study boundary',str(BASE/'data/boundary.geojson'),'user-provided project use',crs_original='EPSG:4326'),'area_km2':AOI.area/1e6,'geometry':AOI}]),MASTER,'aoi_boundary')
write_layer(make([{'context_buffer_m':2000,'statistical_scope':'not_AOI; do not add to AOI denominator','geometry':CONTEXT}]),MASTER,'context_boundary')
write_layer(f,MASTER,'osm_features_context')

# Preserve original model heights as estimates; add explicit quality fields, not invented floors.
b=gpd.read_file(CITY,layer='buildings').copy()
b['provider']=b['source'];b['dataset']='Existing v3 source-grounded model GIS';b['source_url']=b.apply(lambda r:'https://stac.overturemaps.org/2026-10-21.0/buildings/building/collection.json' if pd.notna(r.get('overture_id')) else f'https://www.openstreetmap.org/{r.osm_type}/{int(r.osm_id)}',axis=1)
b['retrieved_at']=now();b['release_date']=b.source_date;b['crs_original']='EPSG:4326';b['processing_steps']='Read-only copy of v3 GIS, retain height provenance, metric footprint statistics';b['is_inferred']=True;b['evidence']='Source footprints; height_source explicitly estimated or levels-derived';b['spatial_accuracy_m']=None;b['footprint_m2']=b.area
b['height_is_measured']=False;b['height_quality']=b.height_source.map({'osm_levels_times_3m':'levels_derived_not_measured','type_default_estimate':'type_default_low_confidence','landuse_context_default_estimate':'context_default_very_low_confidence'})
b['height_class']=pd.cut(b.height_m,[0,12,24,54,500],labels=['≤12 m','12–24 m','24–54 m','>54 m'],include_lowest=True).astype(str)
points=gpd.GeoSeries(b.representative_point(),crs=32651).to_crs(4326);b['longitude']=points.x;b['latitude']=points.y;b['coordinate_meaning']='representative footprint point, not mapped entrance'
write_layer(b,MASTER,'buildings_enriched');write_layer(b[['height_m','height_source','height_quality','height_class','height_is_measured','geometry']],MASTER,'building_height_class')
for layer in ['road_surfaces','road_building_conflicts','road_dangling_review','road_schematic_steep_review','mapped_trees']:
    frame=gpd.read_file(CITY,layer=layer)
    frame['baseline_reference']='Original v3 layer read-only; conflicts/slopes are QA not measured faults'
    write_layer(frame,MASTER,layer)

def category(tags):
    amenity=value(tags,'amenity');shop=value(tags,'shop');office=value(tags,'office');leisure=value(tags,'leisure');tourism=value(tags,'tourism');health=value(tags,'healthcare');name=value(tags,'name');basic=value(tags,'basic_category')
    text=' '.join([amenity,shop,office,leisure,tourism,health,basic]).lower()
    if amenity in ['kindergarten','school','college','university','music_school','driving_school','language_school'] or any(v in basic for v in ['school','university','college','kindergarten','child_care','education']):
        subtype=amenity or basic
        if '幼儿园' in name:subtype='kindergarten'
        elif '小学' in name:subtype='primary_school'
        elif '中学' in name or '高中' in name:subtype='secondary_school'
        return 'education',subtype
    if amenity in ['hospital','clinic','doctors','dentist','pharmacy','veterinary'] or health or any(v in basic for v in ['hospital','clinic','pharmacy','doctor','dentist','medical','health_center']):
        subtype=amenity or health or basic
        if '社区卫生' in name:subtype='community_health'
        return 'health',subtype
    if value(tags,'social_facility') in ['nursing_home','assisted_living','group_home','day_care'] or any(v in basic for v in ['retirement','nursing_home','senior_centre','senior_center']) or re.search('养老|老年日间照料',name):return 'elderly',value(tags,'social_facility') or basic or 'name_evidence_elderly'
    if amenity in ['library','theatre','cinema','arts_centre','community_centre'] or tourism in ['museum','gallery'] or leisure in ['sports_centre','stadium','fitness_centre','pitch','swimming_pool','playground','fitness_station'] or any(v in basic for v in ['library','museum','theater','theatre','cinema','stadium','sports','fitness','gym','cultural','art_gallery']):return 'culture_sports',amenity or tourism or leisure or basic
    if value(tags,'emergency') in ['assembly_point','fire_station'] or amenity in ['police','fire_station'] or basic in ['police_station','fire_station','emergency_shelter']:return 'safety',amenity or value(tags,'emergency') or basic
    if amenity in ['toilets','post_office','parcel_locker','recycling','marketplace','drinking_water','public_bath','social_facility'] or shop in ['supermarket','convenience','greengrocer','butcher','bakery'] or office=='government' or any(v in basic for v in ['supermarket','convenience_store','post_office','post_box','grocery','market','public_toilet','community_service']):return 'daily_service',amenity or shop or office or basic
    if amenity in ['restaurant','cafe','fast_food','bar','pub','food_court','bank','atm','bureau_de_change'] or shop or tourism in ['hotel','motel','hostel','guest_house'] or any(v in basic for v in ['restaurant','cafe','coffee','bar','retail','store','shopping','bank','hotel','lodging','market']):return 'commercial',amenity or shop or tourism or basic
    if office or basic in ['corporate_office','business_center','industrial_park','factory']:return 'employment_proxy',office or basic
    if amenity or basic:return 'other_service',amenity or basic
    return None,None

poi=[];transit=[];parks=[];greens=[];water=[];waterlines=[];open_spaces=[];heritage=[];barriers=[];entrances=[]
for _,row in f.iterrows():
    tags=json.loads(row.tags_json);name=row['name'];geometry=row.geometry
    attrs={k:row[k] for k in ['provider','dataset','source_url','retrieved_at','release_date','license','crs_original','processing_steps','is_inferred','evidence','confidence','spatial_accuracy_m','canonical_id','osm_type','osm_id','snapshot_date','name','access','tags_json']}
    primary,subtype=category(tags)
    if primary:
        point=geometry if geometry.geom_type=='Point' else geometry.representative_point()
        poi.append({**attrs,'category':primary,'subcategory':subtype,'category_method':'source_tags_and_explicit_name_keywords','address':' '.join(value(tags,k) for k in ['addr:city','addr:street','addr:housenumber']).strip(),'opening_hours':value(tags,'opening_hours'),'capacity':value(tags,'capacity'),'capacity_status':'source_tag_only_if_present','operating_status':'unknown_unless_tagged','point_method':'mapped_point' if geometry.geom_type=='Point' else 'representative_point_of_mapped_feature','original_geometry_type':geometry.geom_type,'geometry':point})
    railway=value(tags,'railway');pt=value(tags,'public_transport');highway=value(tags,'highway')
    if railway in ['station','halt','tram_stop','subway_entrance'] or pt in ['station','platform','stop_position'] or highway=='bus_stop':
        subtype='subway_entrance' if railway=='subway_entrance' else 'station' if railway in ['station','halt'] or pt=='station' else 'tram_stop' if railway=='tram_stop' else 'bus_stop' if highway=='bus_stop' else pt
        transit.append({**attrs,'station_type':subtype,'mode':'subway' if railway=='subway_entrance' or value(tags,'station')=='subway' else 'bus' if highway=='bus_stop' or value(tags,'bus')=='yes' else 'rail' if railway in ['station','halt'] else 'unknown','operator':value(tags,'operator'),'network':value(tags,'network'),'ref':value(tags,'ref'),'wheelchair':value(tags,'wheelchair'),'counting_unit':'source stop/platform/entrance record, not unique route frequency','geometry':geometry if geometry.geom_type=='Point' else geometry.representative_point()})
    if value(tags,'barrier'):barriers.append({**attrs,'barrier_type':value(tags,'barrier'),'foot':value(tags,'foot'),'geometry':geometry})
    if value(tags,'entrance'):entrances.append({**attrs,'entrance_type':value(tags,'entrance'),'geometry':geometry if geometry.geom_type=='Point' else geometry.representative_point()})
    if geometry.geom_type in ['Polygon','MultiPolygon','GeometryCollection']:
        leisure=value(tags,'leisure');landuse=value(tags,'landuse');natural=value(tags,'natural')
        if leisure in ['park','garden','nature_reserve']:
            parks.append({**attrs,'park_type':leisure,'public_access_status':'excluded_private_or_no' if value(tags,'access') in ['private','no'] else 'public_park_semantics_not_field_verified','geometry':geometry})
        if leisure in ['park','garden','nature_reserve'] or landuse in ['forest','grass','meadow','recreation_ground','orchard','allotments','village_green'] or natural in ['wood','grassland','scrub','heath']:
            greens.append({**attrs,'green_type':leisure or landuse or natural,'interpretation':'mapped extent, not official vegetation coverage','geometry':geometry})
        if natural in ['water','wetland'] or value(tags,'water') or value(tags,'waterway') in ['riverbank','dock'] or leisure=='swimming_pool':water.append({**attrs,'water_type':value(tags,'water') or natural or value(tags,'waterway') or leisure,'geometry':geometry})
        if leisure in ['park','garden','playground','pitch','track'] or value(tags,'amenity') in ['marketplace','parking'] or (highway=='pedestrian' and value(tags,'area')=='yes'):open_spaces.append({**attrs,'space_type':leisure or value(tags,'amenity') or 'pedestrian_area','public_access_status':'private_or_no' if value(tags,'access') in ['private','no'] else 'unknown_unless_tagged','geometry':geometry})
    if value(tags,'waterway') in ['river','canal','stream','drain','ditch'] and geometry.geom_type in ['LineString','MultiLineString']:
        waterlines.append({**attrs,'waterway_type':value(tags,'waterway'),'width_tag':value(tags,'width'),'geometry':geometry})
    if value(tags,'historic') or value(tags,'heritage'):
        heritage.append({**attrs,'heritage_type':value(tags,'historic'),'designation_source_tag':value(tags,'heritage'),'statutory_boundary_verified':False,'geometry':geometry})

# Read all actual Overture themes, exact-filter in WGS84 before projection.
overture_summary=[];ovdata={}
for file in sorted((RAW/'overture').glob('*_context.parquet')):
    kind=file.name.removesuffix('_context.parquet');table=pq.read_table(file).to_pandas()
    frame=gpd.GeoDataFrame(table.drop(columns='geometry'),geometry=shapely.from_wkb(table.geometry),crs=4326)
    if 'country' in frame:frame=frame[frame.country.fillna('CN').isin(['CN','CHN'])]
    frame=source_context(frame);ovdata[kind]=frame
    collection_file=ROOT/f'cache/overture/overture_{kind}_collection.json'
    collection=json.loads(collection_file.read_text()) if collection_file.exists() else {}
    license=collection.get('license','unknown')
    serialized=[]
    for _,row in frame.iterrows():
        meta=provenance('Overture Maps Foundation',f'Overture {kind} 2026-10-21.0',f'https://stac.overturemaps.org/2026-10-21.0/{"places" if kind=="place" else "divisions" if kind.startswith("division") else "buildings" if kind.startswith("building") else "transportation" if kind in ["segment","connector"] else "base"}/{kind}/collection.json',license,release_date='2026-10-21')
        serialized.append({**meta,'canonical_id':'gers:'+row.id,'gers_id':row.id,'name':(row.names or {}).get('primary','') if isinstance(row.get('names'),dict) else '', 'source_properties_json':json_text(row.drop('geometry').to_dict()),'in_aoi':bool(row.in_aoi),'geometry':row.geometry})
        if kind=='place':
            tags={'basic_category':value(row,'basic_category'),'name':(row.names or {}).get('primary','') if isinstance(row.get('names'),dict) else ''}
            primary,subtype=category(tags)
            if not primary:primary='other_service';subtype=tags['basic_category']
            status=value(row,'operating_status')
            if status in ['permanently_closed','closed']:continue
            addr=primitive(row.get('addresses')) or []
            address='; '.join(' '.join(str(v) for v in a.values() if v) for a in addr)
            poi.append({**meta,'canonical_id':'gers:'+row.id,'osm_type':None,'osm_id':None,'gers_id':row.id,'name':tags['name'],'category':primary,'subcategory':subtype,'category_method':'Overture basic_category plus explicit name keywords','address':address,'opening_hours':'','capacity':'','capacity_status':'not_available','operating_status':status or 'unknown','point_method':'mapped_provider_point','original_geometry_type':row.geometry.geom_type,'provider_confidence':row.get('confidence'),'access':'unknown','tags_json':json_text(row.drop('geometry').to_dict()),'geometry':row.geometry if row.geometry.geom_type=='Point' else row.geometry.representative_point()})
    layer=make(serialized)
    if len(layer):write_layer(layer,MASTER,'overture_'+kind)
    count_aoi=int(layer.intersects(AOI).sum()) if len(layer) else 0
    overture_summary.append({'kind':kind,'context_exact_count':len(layer),'aoi_intersection_count':count_aoi,'license':license})
    register('overture_'+kind,access_status='verified_exact_context_clip',feature_count_aoi=count_aoi,notes=f'{len(layer)} exact AOI+2km features; counts distinguish buffer and AOI',license=license)
    if kind=='division_area' and len(layer):
        attrs=frame[['id','subtype','admin_level','names','division_id','geometry']].copy();attrs['name']=attrs.names.map(lambda v:(v or {}).get('primary','') if isinstance(v,dict) else '')
        attrs.drop(columns='names',inplace=True);attrs['authority']='Overture/OSM administrative reference, not certified cadastral boundary';write_layer(attrs,MASTER,'admin_units')

# Conservative POI dedup: exact normalized name and compatible class within 25m.
points=make(poi);points['name_norm']=points.name.fillna('').str.lower().str.replace(r'[\s（）()·,，。]','',regex=True)
keep=[];links=[];groups=collections.defaultdict(list)
for index,row in points.iterrows():
    key=(row.name_norm,row.category)
    match=None
    if row.name_norm:
        for candidate in groups[key]:
            if row.geometry.distance(points.loc[candidate].geometry)<=25:match=candidate;break
    if match is None:keep.append(index);groups[key].append(index)
    else:links.append({'retained_id':points.loc[match].canonical_id,'linked_id':row.canonical_id,'match_rule':'exact_normalized_name_and_category_distance_le25m','distance_m':row.geometry.distance(points.loc[match].geometry),'retained_source':points.loc[match].provider,'linked_source':row.provider})
points=points.loc[keep].copy();points['in_aoi']=points.intersects(AOI)
wgs=points.to_crs(4326);points['longitude']=wgs.geometry.x;points['latitude']=wgs.geometry.y
points['facility_capacity_inferred']=False
write_layer(points,MASTER,'poi_all')
for group,name in [('education','poi_education'),('health','poi_health'),('elderly','poi_elderly'),('culture_sports','poi_culture_sports'),('commercial','poi_commercial'),('daily_service','poi_daily_service'),('safety','poi_safety'),('employment_proxy','poi_employment_proxy')]:
    write_layer(points[points.category.eq(group)].copy(),MASTER,name)
pd.DataFrame(links).to_csv(ROOT/'reports/poi_source_matches.csv',index=False)

for layer,records in [('transit_stations',transit),('green_parks',parks),('green_spaces_all',greens),('blue_network',water),('waterway_centerlines',waterlines),('open_spaces',open_spaces),('barriers',barriers),('entrances',entrances),('heritage_sites',heritage)]:
    frame=make(records)
    if len(frame):frame['in_aoi']=frame.intersects(AOI)
    write_layer(frame,MASTER,layer)

# Routes retain disjoint member segments; no line invented across missing members.
node_coords={key[1]:(element['lon'],element['lat']) for key,element in raw.items() if key[0]=='node' and 'lon' in element}
route_records=[]
for (kind,ident),element in raw.items():
    if kind!='relation' or element.get('tags',{}).get('route') not in ['bus','subway','tram','train','trolleybus']:continue
    tags=element['tags'];segments=[];missing_members=0
    for member in element.get('members',[]):
        if member['type']!='way':continue
        way=raw.get(('way',member['ref']))
        if not way:missing_members+=1;continue
        coordinates=[node_coords[n] for n in way.get('nodes',[]) if n in node_coords]
        if len(coordinates)>1:segments.append(LineString(coordinates))
    if not segments:continue
    geometry=shapely.line_merge(MultiLineString(segments));frame=gpd.GeoDataFrame({'geometry':[geometry]},crs=4326);frame=source_context(frame)
    if len(frame):route_records.append({**meta_osm('relation',ident),'name':tags.get('name',''),'route_mode':tags['route'],'ref':tags.get('ref',''),'operator':tags.get('operator',''),'network':tags.get('network',''),'interval_tag':tags.get('interval',''),'frequency_verified':False,'missing_member_ways':missing_members,'geometry':frame.geometry.iloc[0]})
write_layer(make(route_records),MASTER,'transit_lines')

pd.DataFrame(source_conflicts).to_csv(ROOT/'reports/cross_source_conflicts.csv',index=False)
dump(ROOT/'reports/overture_context_summary.json',overture_summary)
summary={'aoi_area_km2':AOI.area/1e6,'context_area_km2':CONTEXT.area/1e6,'context_buffer_m':2000,'osm_raw_elements':len(raw),'osm_features_context':len(f),'poi_context_unique':len(points),'poi_aoi_unique':int(points.in_aoi.sum()),'poi_aoi_categories':points[points.in_aoi].category.value_counts().to_dict(),'poi_matches_merged':len(links),'transit_source_records_aoi':int(make(transit).intersects(AOI).sum()) if transit else 0,'route_relations_context':len(route_records),'building_count_preserved':len(b),'snapshot_dates':timestamps,'design_site':'not provided; no layer fabricated'}
dump(ROOT/'reports/normalization_summary.json',summary)
export_registry();progress('standardization','master','verified_initial',**summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
