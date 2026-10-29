from pathlib import Path
import geopandas as gpd, pandas as pd, json,hashlib
from shapely.geometry import box
P=Path(__file__).resolve().parents[1];REPO=P.parents[1];V3=REPO/'planning_v3';M=V3/'outputs/gis/reference_v2.gpkg';D=V3/'outputs/gis/refined_analysis_v3.gpkg';O=P/'data/location_context.gpkg'
if O.exists():O.unlink()
def read(l):return gpd.read_file(M,layer=l)
def put(d,l):
 d.to_file(O,layer=l,driver='GPKG');return d
site=gpd.read_file(D,layer='DESIGN_SITE');line=gpd.read_file(D,layer='DESIGN_SITE_BOUNDARY');put(site,'DESIGN_SITE');put(line,'DESIGN_SITE_BOUNDARY');S=site.geometry.iloc[0]
aoi=put(read('aoi_boundary'),'study_area');C=aoi.geometry.iloc[0].buffer(1800)
manifest=[]
for layer in ['buildings_enriched','road_network_vehicle','green_spaces_all','blue_network','waterway_centerlines','green_parks','transit_lines','transit_stations','poi_all']:
 d=read(layer);d=d[d.intersects(C)].copy()
 if layer=='transit_lines':d=d[d.route_mode=='subway']
 if layer=='transit_stations':d=d[(d['mode']=='subway') & (d.station_type=='station')].drop_duplicates('name')
 cols=[k for k in ['name','highway','ref','route_mode','mode','station_type','category','height_m','height_source','height_is_measured','height_quality','height_explanation','upstream_dataset','is_inferred','processing_steps','feature_observation_date','access','public_access_status','source','source_date','canonical_id','source_url','license','snapshot_date','provider','dataset','confidence'] if k in d]
 put(d[cols+['geometry']],layer);manifest.append({'layer':layer,'features':len(d),'origin':str(M.relative_to(REPO)),'source_layer':layer,'selection':'intersects study area +1800 m; subway only for rail layer; station only and deduplicated names for station points','geometry_preserved':True,'providers':sorted(d.provider.dropna().unique().tolist()) if 'provider' in d else [],'licenses':sorted(d.license.dropna().unique().tolist()) if 'license' in d else []})
roads=read('road_network_vehicle');names=['江场西路','江场路','万荣路','共和新路','南北高架路','沪太路','汶水路','中环路','场中路'];r=roads[roads.name.isin(names)].dissolve(by='name').reset_index()[['name','geometry']];put(r,'road_labels')
w=read('waterway_centerlines');w=w[w.name.isin(['走马塘','彭越浦','东茭泾'])].dissolve(by='name').reset_index()[['name','geometry']];put(w,'water_labels')
parks=read('green_parks');poi=read('poi_all');station=read('transit_stations');nodes=[]
for id,n,typ,df in [('01','彭浦公园','park',parks),('02','静安青年体育公园','park',parks),('03','半里绿廊','park',parks),('04','市北高新商务中心','resource',poi),('05','汶水路','metro',station),('06','彭浦新村','metro',station)]:
 t=df[df.name==n].copy();assert len(t)>0,n
 if typ=='metro':t=t[(t['mode']=='subway')&(t.station_type=='station')]
 row=t.iloc[0];point=row.geometry.representative_point();nodes.append({'id':id,'name':n+('站' if typ=='metro' else ''),'label':id+' '+n+('站' if typ=='metro' else ''),'kind':typ,'source_url':row.get('source_url',''),'distance_to_site_m':row.geometry.distance(S),'geometry':point})
put(gpd.GeoDataFrame(nodes,crs=32651),'resource_nodes')
put(gpd.GeoDataFrame([{'name':'核心设计地块','geometry':S.centroid}],crs=32651),'site_locator')
sh=gpd.read_file(P/'data/shanghai_osm_reference.gpkg',layer='shanghai_land');put(sh,'shanghai_land_reference');put(gpd.read_file(P/'data/shanghai_osm_reference.gpkg',layer='regional_land'),'regional_land_reference');put(gpd.read_file(P/'data/shanghai_osm_reference.gpkg',layer='shanghai_boundary'),'shanghai_admin_reference')
# Source layer administrative evidence supports name, but not current legal boundary certification.
a=read('admin_units');overlap=a[a.name=='静安区'].intersection(S).area.sum();assert abs(overlap-S.area)<.05
stats={'site_area_m2':S.area,'site_area_ha':S.area/1e4,'study_area_km2':aoi.area.sum()/1e6,'crs':'EPSG:32651','site_geometry_sha256':hashlib.sha256(S.wkb).hexdigest(),'source_site_geometry_sha256':hashlib.sha256(gpd.read_file(D,layer='DESIGN_SITE').geometry.iloc[0].wkb).hexdigest(),'design_extent_m':list(S.bounds),'site_centroid_wgs84':list(gpd.GeoSeries([S.centroid],crs=32651).to_crs(4326).iloc[0].coords)[0],'source_admin_site_jingan_overlap_m2':overlap,'nodes':[{k:v for k,v in n.items() if k!='geometry'} for n in nodes],'macro_boundary_snapshot':'2026-10-29','macro_boundary_use':'OSM administrative reference intersected with Natural Earth 1:10m land for city orientation, not certified legal or coastal survey boundary; 2019 coarse alternative rejected','road_line_widths':'cartographic hierarchy, not measured road width','proposed_connections':'textual recommendations only; no invented network links or travel time isochrones'}
assert stats['site_geometry_sha256']==stats['source_site_geometry_sha256']
(P/'reports/data_validation.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2));(P/'reports/layer_sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Prepared',len(manifest),'context layers; exact site',stats['site_area_ha'],'ha')
