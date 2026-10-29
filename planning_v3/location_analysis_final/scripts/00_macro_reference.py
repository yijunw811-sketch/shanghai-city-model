"""Prepare public macro reference; clip global geographic land before UTM projection."""
from pathlib import Path
import json,geopandas as g,requests,zipfile,hashlib
from shapely.geometry import LineString,box
from shapely.ops import polygonize,unary_union
P=Path(__file__).resolve().parents[1];p=P/'data';src=p/'osm_shanghai_full.json';u='https://www.openstreetmap.org/api/0.6/relation/913067/full.json'
if not src.exists():
 r=requests.get(u,timeout=60);r.raise_for_status();src.write_bytes(r.content)
d=json.loads(src.read_text());nodes={n['id']:(n['lon'],n['lat']) for n in d['elements'] if n['type']=='node'};ways={w['id']:w for w in d['elements'] if w['type']=='way'};r=next(r for r in d['elements'] if r['type']=='relation' and r['id']==913067);assert r['tags']['name']=='上海市';geoms={}
for role in ['outer','inner']:
 lines=[LineString([nodes[i] for i in ways[m['ref']]['nodes']]) for m in r['members'] if m['type']=='way' and m['role']==role];geoms[role]=unary_union(list(polygonize(unary_union(lines)))) if lines else None
geom=geoms['outer'];geom=geom.difference(geoms['inner']) if geoms['inner'] is not None else geom;assert geom.is_valid
adm=g.GeoDataFrame([{'name':'上海市','source_url':'https://www.openstreetmap.org/relation/913067','license':'ODbL-1.0','snapshot_date':'2026-10-29','relation_modified':r['timestamp'],'geometry':geom}],crs=4326).to_crs(32651)
z=p/'ne_10m_land.zip';nu='https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip'
if not z.exists():
 re=requests.get(nu,timeout=60);re.raise_for_status();z.write_bytes(re.content)
with zipfile.ZipFile(z) as zi:zi.extractall(p/'ne_land_cache')
# Critical: global land polygons must be clipped in WGS84 before local UTM projection.
land=g.read_file(p/'ne_land_cache/ne_10m_land.shp',bbox=(120.3,30.0,124,32.4));land.geometry=land.intersection(box(120.3,30.0,124,32.4));land=land[~land.is_empty].to_crs(32651);assert land.is_valid.all()
region=adm.union_all().envelope.buffer(15000);land.geometry=land.intersection(region);land=land[~land.is_empty]
sl=g.GeoDataFrame([{'name':'上海陆域制图参考','geometry':land.union_all().intersection(adm.union_all())}],crs=32651)
assert 4000<sl.area.sum()/1e6<12000,sl.area.sum()/1e6
site=g.read_file(P.parents[0]/'outputs/gis/refined_analysis_v3.gpkg',layer='DESIGN_SITE').union_all();assert sl.union_all().covers(site)
out=p/'shanghai_osm_reference.gpkg'
if out.exists():out.unlink()
adm.to_file(out,layer='shanghai_boundary',driver='GPKG');land[['geometry']].to_file(out,layer='regional_land',driver='GPKG');sl.to_file(out,layer='shanghai_land',driver='GPKG')
report={'source_url':u,'license':'ODbL-1.0','snapshot_date':'2026-10-29','relation_modified':r['timestamp'],'admin_area_including_marine_km2':adm.area.sum()/1e6,'land_reference_km2':sl.area.sum()/1e6,'land_geometry_valid':bool(sl.is_valid.all()),'contains_exact_design_site':True,'natural_earth_url':nu,'natural_earth_license':'Public domain','natural_earth_scale':'1:10 million cartographic reference, not a survey','source_osm_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_natural_earth_sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'rejected_source':'geoBoundaries CHN ADM1 2019 (35 vertices in Shanghai; too coarse for selected design)','overpass_attempt':'HTTP 406; switched to standard public OSM API, no bypass'}
(P/'reports/macro_source_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
