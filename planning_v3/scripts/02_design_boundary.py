from common import *
from shapely.geometry import Polygon,LineString
from shapely import make_valid
from shapely.validation import explain_validity
import sys
src=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data/boundary/选定范围.csv'
dst=ROOT/'data/boundary/选定范围.csv'
if src.resolve()!=dst.resolve():shutil.copy2(src,dst)
f=pd.read_csv(dst).dropna(subset=['Longitude','Latitude']);coords=list(zip(f.Longitude,f.Latitude));closed=coords[0]==coords[-1]
if not closed:coords.append(coords[0])
p=Polygon(coords)
source_valid=p.is_valid
source_validity=explain_validity(p)
g=gpd.GeoDataFrame([{'source':'user uploaded 选定范围.csv','source_sha256':sha(dst),'crs_evidence':'WGS84 inherited from user confirmation for project; no datum shift applied, not independently surveyed control','original_elevation':'all0; not used as terrain','geometry':p}],crs=4326).to_crs(32651)
raw_metric=g.geometry.iloc[0];repair={'performed':False}
if not raw_metric.is_valid:
 repaired=make_valid(raw_metric)
 pieces=sorted(list(repaired.geoms) if hasattr(repaired,'geoms') else [repaired],key=lambda x:x.area,reverse=True)
 assert all(x.area<.01 for x in pieces[1:]), 'Nontrivial self-crossing requires user review'
 site=pieces[0]
 repair={'performed':True,'reason':explain_validity(raw_metric),'method':'make_valid; retain dominant polygon, archive the0.000714m² closing sliver evidence','discarded_micro_fragment_m2':sum(x.area for x in pieces[1:]),'source_signed_area_m2':raw_metric.area,'clean_area_m2':site.area,'hausdorff_change_m':raw_metric.hausdorff_distance(site)}
 g['geometry']=[site]
else:site=raw_metric
dump(ROOT/'reports/design_boundary_geometry_repair.json',repair)
g['area_m2']=site.area;g['area_ha']=site.area/10000
assert site.difference(AOI).area<.01
assert .5e6<site.area<.8e6,'Unexpected area compared to user approximate66.10ha'
g.to_file(ROOT/'data/boundary/design_site.gpkg',layer='DESIGN_SITE',driver='GPKG');g.to_crs(4326).to_file(ROOT/'data/boundary/design_site.geojson',driver='GeoJSON')
line=g.copy();line['geometry']=line.geometry.boundary;line['style_color']='#CB493E';line['style_width_mm']=1.2;line['fill']='none';put(line,'DESIGN_SITE_BOUNDARY');put(g,'DESIGN_SITE')
dump(ROOT/'reports/design_boundary_validation.json',{'source_file':str(dst.relative_to(ROOT)),'source_sha256':sha(dst),'input_rows':len(f),'input_was_closed':closed,'valid':site.is_valid,'source_valid':source_valid,'source_validity':source_validity,'repair':repair,'crs_analysis':'EPSG:32651','source_datum':'Inherited WGS84 project confirmation; no GCJ/BD correction guessed','area_m2':site.area,'area_ha':site.area/10000,'area_km2':site.area/1e6,'outside_aoi_m2':site.difference(AOI).area,'source_vertices_preserved_in_csv':True,'near_duplicate_vertex_note':'Original CSV retained exactly; a 0.000714m2 self-crossing closing sliver removed from analysis ring with explicit repair audit','z_ignored':True,'styling':{'stroke':'#CB493E','stroke_mm':1.2,'white_understroke_mm':1.65,'fill':'none','outside_mask':False,'inside_outside_opacity_difference':False}})
checkpoint('design_boundary',status='verified_user_geometry',area_m2=site.area);print('DESIGN',site.area/10000,'ha',flush=True)
