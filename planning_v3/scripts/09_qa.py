from common import *
import pyogrio,rasterio,pymupdf,xml.etree.ElementTree as ET,re
from PIL import Image
from shapely import union_all
# V2 and original models remain byte-for-byte protected; compare actual originals, not only copies.
baseline=pd.read_csv(ROOT/'reports/protected_v2_baseline.csv');protection=[]
for r in baseline.itertuples():
 p=REPO/r.path;actual=sha(p) if p.exists() else None;protection.append({'path':r.path,'baseline_sha256':r.sha256,'current_sha256':actual,'unchanged':actual==r.sha256,'available':p.exists()})
assert all(r['unchanged'] for r in protection),'Protected V2 input changed or missing'
pd.DataFrame(protection).to_csv(ROOT/'reports/protected_v2_verification.csv',index=False)
def reference_content_check(copy,source):
 # QGIS/GDAL opened V3 copies in update-capable mode; only SQLite header counters/version changed.
 # Assert EVERY remaining byte is identical, rather than pretending the copied file SHA is unchanged.
 permitted=set(range(24,28))|set(range(92,100));h1=hashlib.sha256();h2=hashlib.sha256()
 with Path(copy).open('rb') as a,Path(source).open('rb') as b:
  ca=a.read(100);cb=b.read(100);different=[i for i,(x,y) in enumerate(zip(ca,cb)) if x!=y]
  assert set(different)<=permitted,(copy,different)
  while True:
   x=a.read(1048576);y=b.read(1048576)
   if not x and not y:break
   h1.update(x);h2.update(y)
 assert Path(copy).stat().st_size==Path(source).stat().st_size
 assert h1.digest()==h2.digest(), 'Reference data pages changed'
 return {'file':Path(copy).name,'different_header_offsets':different,'all_data_pages_SHA256_identical':True,'data_pages_sha256':h1.hexdigest(),'note':'Only runtime SQLite change counter/version fields may differ; all source geometry/attributes/index pages identical'}
reference_checks=[reference_content_check(M,V2/'outputs/gis/planning_enriched.gpkg'),reference_content_check(A,V2/'outputs/gis/analysis_layers.gpkg')]
dump(ROOT/'reports/reference_copy_content_checks.json',reference_checks)
layers=[]
for path in [M,A,D]:
 with sqlite3.connect(path) as con:assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 for name,typ in pyogrio.list_layers(path):
  if typ is None:continue
  f=read(name,path);record={'database':path.name,'layer':name,'count':len(f),'crs':str(f.crs),'invalid':int((~f.is_valid).sum()),'empty':int(f.is_empty.sum()),'null_geometry':int(f.geometry.isna().sum())};layers.append(record)
  assert f.crs.to_epsg()==32651 and record['invalid']==0 and record['null_geometry']==0,record
pd.DataFrame(layers).to_csv(ROOT/'reports/output_layer_inventory_v3.csv',index=False)
site=read('DESIGN_SITE',D).geometry.iloc[0];assert site.is_valid and site.difference(AOI).area<.01
boundary=read('DESIGN_SITE_BOUNDARY',D);assert all(boundary.geom_type.isin(['LineString','MultiLineString']))
assert boundary.geometry.iloc[0].hausdorff_distance(site.boundary)<1e-7
assert sha(ROOT/'data/boundary/选定范围.csv')==json.loads((ROOT/'reports/design_boundary_validation.json').read_text())['source_sha256']
checks=[];foot=union_all(read('buildings_enriched').geometry);globalvolume=[];globalroad=[];nativepop=read('population_worldpop2025',A)
for size in [50,100,200]:
 f=read(f'grid_{size}m',D);df=read(f'design_grid_{size}m',D);scope=site.buffer(500).intersection(AOI) if size==50 else AOI
 assert f.grid_id.is_unique and all(f.origin_x==0) and all(f.origin_y==0)
 assert abs(f.area.sum()-scope.area)<.1
 assert abs(df.area.sum()-site.area)<.05
 error=abs(f.building_footprint_m2.sum()-foot.intersection(scope).area);assert error<.05
 assert abs(df.building_footprint_m2.sum()-foot.intersection(site).area)<.05
 assert f.building_density.between(-1e-9,1.000001).all()
 assert all(f.loc[f.known_function_fraction<.5,'land_function_entropy'].isna())
 assert f.land_function_entropy.dropna().between(-1e-9,1.000001).all()
 assert not any('population' in col.lower() for col in f.columns),'Population must not be downscaled into fine grid'
 checks.append({'size_m':size,'units':len(f),'design_units':len(df),'scope_area_m2':scope.area,'covered_area_m2':f.area.sum(),'design_area_m2':df.area.sum(),'footprint_conservation_error_m2':error,'known_function_low_coverage_mask_verified':True})
 if size in [100,200]:globalvolume.append(f.estimated_volume_m3.sum());globalroad.append(f.vehicle_m.sum())
assert abs(globalvolume[0]-globalvolume[1])<max(.1,abs(globalvolume[0])*1e-9)
assert abs(globalroad[0]-globalroad[1])<.05
nativeorig=read('population_worldpop2025',V2/'outputs/gis/analysis_layers.gpkg');assert len(nativepop)==48 and nativepop.geometry.to_wkb().tolist()==nativeorig.geometry.to_wkb().tolist()
dump(ROOT/'reports/grid_conservation_checks.json',checks)
with rasterio.open(ROOT/'data/satellite/sentinel_truecolor_10m_context.tif') as ds:
 assert ds.count==3 and all(dt=='uint8' for dt in ds.dtypes);assert ds.crs.to_epsg()==32651 and ds.res==(10.,10.);assert len(ds.overviews(1))>=3
 assert __import__('shapely').geometry.box(*ds.bounds).covers(AOI)
 rgbqa={'count':ds.count,'dtype':ds.dtypes,'resolution_m':ds.res,'overviews':ds.overviews(1),'crs':str(ds.crs),'native_product_not_invented_fine_detail':True}
catalog=json.loads((ROOT/'reports/map_catalog_v3.json').read_text());assert len(catalog)==39
sheetqa=[];labelwarnings=[]
for m in catalog:
 pdf=ROOT/f'outputs/maps/A1/{m["stem"]}.pdf';doc=pymupdf.open(pdf);page=doc[0];width,height=page.rect.width/72*25.4,page.rect.height/72*25.4
 assert abs(width-841)<.01 and abs(height-594)<.01
 text=page.get_text();assert 'V3' in text and '66.0948' in text and m['id'] in text
 assert abs((m['extent'][1]-m['extent'][0])/(.73*.841)-m['A1_scale'])<.001
 # Actual SVG paths must include red strokes with no polygon fill; annotations do not make a site mask.
 svg=ROOT/f'outputs/maps/A1/{m["stem"]}.svg';tree=ET.parse(svg);red=[]
 for node in tree.iter():
  st=node.attrib.get('style','').lower()
  if '#cb493e' in st and 'stroke:' in st:
   red.append(st);assert 'fill: none' in st or node.tag.endswith('use'),(m['id'],st)
 assert red,m['id'];assert m['design_fill']=='none' and m['outside_mask'] is False
 assert any('3.4015' in st for st in red),'No1.2mm A1 red stroke found'
 with Image.open(ROOT/f'outputs/maps/A1/{m["stem"]}.png') as im:im.verify()
 review=pymupdf.open(ROOT/f'outputs/maps/A3_review/{m["stem"]}.pdf');rp=review[0];assert abs(rp.rect.width/72*25.4-420)<.01 and abs(rp.rect.height/72*25.4-297)<.01
 sizes=[s['size'] for b in rp.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()];assert sizes and min(sizes)>=6.95,(m['id'],min(sizes))
 fonts=page.get_fonts(full=True);assert fonts
 # Inspect text-line boxes in the map frame; report automatic place-label collisions for editorial review.
 frame=pymupdf.Rect(page.rect.width*.035,page.rect.height*.12,page.rect.width*.765,page.rect.height*.86);lines=[]
 for block in page.get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   content=''.join(span['text'] for span in line['spans']).strip();rect=pymupdf.Rect(line['bbox'])
   if content and frame.contains(rect):lines.append((content,rect))
 for i,(ta,ra) in enumerate(lines):
  for tb,rb in lines[i+1:]:
   inter=ra&rb
   if inter.get_area()>min(ra.get_area(),rb.get_area())*.15:labelwarnings.append({'map':m['id'],'text_a':ta,'text_b':tb,'overlap_fraction':inter.get_area()/min(ra.get_area(),rb.get_area())})
 sheetqa.append({'id':m['id'],'series':m['series'],'A1_mm':[width,height],'A1_scale':m['A1_scale'],'A3_scale':m['A3_scale'],'A3_min_text_pt':min(sizes),'red_line_no_fill_verified':True,'PDF_fonts':len(fonts),'SVG_parsed':True,'PNG_verified':True});doc.close();review.close()
pd.DataFrame(sheetqa).to_csv(ROOT/'reports/map_export_validation_v3.csv',index=False);pd.DataFrame(labelwarnings,columns=['map','text_a','text_b','overlap_fraction']).to_csv(ROOT/'reports/place_label_overlap_review.csv',index=False)
qgis=json.loads((ROOT/'reports/qgis_validation_v3.json').read_text());assert qgis['project_reopened'] and qgis['V2_reference_layouts']==28 and qgis['new_V3_layouts']==39 and not qgis['missing_layers'];assert len(qgis['map_themes'])==3
for r in qgis['native_exports']:
 with Image.open(ROOT/r['file']) as im:im.verify()
colorqa=json.loads((ROOT/'reports/color_quality_checks.json').read_text());assert all(r['min_deltaE76']>7 for r in colorqa)
qa={'date':'2026-10-28 Asia/Shanghai','protected_files':len(protection),'all_V2_and_old_model_files_unchanged':True,'reference_GPKG_data_pages_exactly_match_V2':True,'reference_header_differences':reference_checks,'spatial_tables_readback':len(layers),'invalid_geometries':sum(r['invalid'] for r in layers),'design_area_ha':site.area/10000,'source_boundary_repair':'0.000714m2 self-crossing closing sliver removed; original CSV unchanged','grid_checks':checks,'population2025_native_cells_preserved':48,'source_topology_preserved':True,'map_count':len(sheetqa),'regional_optimized':28,'refined':8,'satellite_maps':3,'A1_and_A3_verified':True,'A3_min_text_pt':min(r['A3_min_text_pt'] for r in sheetqa),'satellite':rgbqa,'capture_date':json.loads((ROOT/'reports/satellite_provenance.json').read_text())['acquisition_datetime'],'qgis_valid_layers':qgis['valid_layers'],'retained_V2_layouts':28,'new_V3_layouts':39,'map_themes':qgis['map_themes'],'place_label_overlap_review_count':len(labelwarnings),'limitations':['Native RGB10m; no verified0.5–2m orthophoto acquired','Inherited projectWGS84, not independently surveyed control','All building heights estimated/levels-derived; volume proxy notFAR','Function classification missingness retained; entropy changes fromV2 POI semantics','WorldPop2025 ~1kmALPHA kept; no invented population precision','GitHub API authorization/network outcome recorded separately; never imply PR exists without URL']}
dump(ROOT/'reports/final_qa_v3.json',qa);checkpoint('qa',verified=True,protected=len(protection),maps=len(sheetqa),label_warnings=len(labelwarnings));print('QA V3 PASSED',len(protection),len(layers),len(sheetqa),'label overlaps',len(labelwarnings),flush=True)
