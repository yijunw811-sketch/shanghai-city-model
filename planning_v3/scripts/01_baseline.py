from common import *
import zipfile,pyogrio
rows=[]
for base in [V2,REPO/'上海城市模型_Codex云端起步包',REPO/'downloads']:
 for p in sorted(base.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts:continue
  if base.name=='downloads' and 'planning-v2' not in p.name:continue
  rows.append({'path':str(p.relative_to(REPO)),'bytes':p.stat().st_size,'sha256':sha(p)})
pd.DataFrame(rows).to_csv(ROOT/'reports/protected_v2_baseline.csv',index=False)
for src,dst in [(V2/'outputs/gis/planning_enriched.gpkg',M),(V2/'outputs/gis/analysis_layers.gpkg',A)]:
 if not dst.exists():shutil.copy2(src,dst)
 assert sha(src)==sha(dst)
rasters=ROOT/'data/rasters_v2';rasters.mkdir(exist_ok=True)
for src in (V2/'outputs/gis/rasters').glob('*.tif'):
 dst=rasters/src.name
 if not dst.exists():shutil.copy2(src,dst)
 assert sha(src)==sha(dst)
# Search filenames AND embedded spatial layer names / archive members. No guessed boundary from area.
candidates=[]
for p in REPO.rglob('*'):
 if ROOT in p.parents or '.git' in p.parts or not p.is_file():continue
 if any(t in p.name.lower() for t in ['选定','设计','design_site','design_boundary']):candidates.append(str(p.relative_to(REPO)))
 if p.suffix=='.gpkg':
  for name,typ in pyogrio.list_layers(p):
   if any(t in name.lower() for t in ['design','选定','设计']):candidates.append(str(p.relative_to(REPO))+'|layer='+name)
 if p.suffix=='.zip':
  try:
   with zipfile.ZipFile(p) as z:
    for name in z.namelist():
     if any(t in name.lower() for t in ['选定','design_site','design_boundary']):candidates.append(str(p.relative_to(REPO))+'!'+name)
  except zipfile.BadZipFile:pass
status={'state':'awaiting_actual_design_boundary' if not candidates else 'candidates_need_validation','candidates':candidates,'aoi_km2':AOI.area/1e6,'design_area_approx_user_only_km2':.661,'not_substituted_by_aoi':True,'blocked':['DESIGN_SITE_BOUNDARY','S02 Design Site Aerial Map','design-specific grid statistics and final scale selection','design boundary overlay on all maps'],'can_continue':['true color imagery','whole AOI scale sensitivity','28-map color system','S01 and S03 context maps','independent V3 QGIS with explicit missing-boundary status']}
dump(ROOT/'reports/design_boundary_search.json',status)
checkpoint('baseline',files_protected=len(rows),reference_copies_verified=True,design_boundary=status['state']);print('BASELINE',len(rows),status['state'],flush=True)
