from common import *
import zipfile,subprocess,re
# Small V2 reference metadata makes map/compare rebuilds possible without duplicating the full V2/model archive.
ref=ROOT/'data/v2_reference'
for sub in ['reports','outputs/qgis','cache/source_discovery','outputs/maps/A1']:(ref/sub).mkdir(parents=True,exist_ok=True)
for p in (V2/'reports').glob('map_[0-9][0-9].json'):shutil.copy2(p,ref/'reports'/p.name)
for name in ['satellite_provenance.json','source_registry.csv','methods_and_limitations.md','final_qa.json']:
 p=V2/'reports'/name
 if p.exists():shutil.copy2(p,ref/'reports'/name)
for season in ['summer','winter']:
 for src,dst in [(V2/f'cache/source_discovery/s2_{season}_stac.json',ref/f'cache/source_discovery/s2_{season}_stac.json'),(V2/f'reports/sentinel_{season}_selection.json',ref/f'reports/sentinel_{season}_selection.json')]:shutil.copy2(src,dst)
shutil.copy2(V2/'outputs/qgis/planning_analysis.qgz',ref/'outputs/qgis/planning_analysis.qgz')
for id in ['02','04','06','08','11','15','16','18']:
 for p in (V2/'outputs/maps/A1').glob(id+'_*.png'):shutil.copy2(p,ref/'outputs/maps/A1'/p.name)
# Never persist token-bearing query strings in reproducibility files.
for folder in ['scripts','reports','styles']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.py','.md','.json','.csv','.qml']:
   if re.search(r'[?&](?:sig|signature|token|api_key)=[^&\s"<>]+',p.read_text(errors='replace'),re.I):raise RuntimeError('Credential-like query requires review: '+str(p))
files=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 rel=p.relative_to(ROOT)
 if rel.parts[0]=='downloads' or p.name=='manifest.json' or p.name=='packaging_execution.log' or p.name.endswith(('~','.pyc','.partial','.lock')):continue
 files.append(p)
qa=json.loads((ROOT/'reports/final_qa_v3.json').read_text())
manifest={'date':'2026-10-28','branch':'planning-v3-cartography-20261028','source_base_commit':subprocess.check_output(['git','rev-parse','origin/main'],cwd=REPO,text=True).strip(),'map_count':39,'source_protection_verified':qa['all_V2_and_old_model_files_unchanged'],'protected_count':qa['protected_files'],'qgis':'outputs/qgis/planning_analysis_v3.qgz','limitations':'Native10m imagery; sparse known functions/commercial observations; native1km population preserved; PR status in downloads separately','files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]}
dump(ROOT/'outputs/manifest.json',manifest);files.append(ROOT/'outputs/manifest.json')
groups={k:[] for k in ['01-core-gis-project','02-regional-maps-01-14','03-regional-maps-15-28','04-satellite-refined-comparisons']}
for p in files:
 rel=p.relative_to(ROOT);group='01-core-gis-project'
 if rel.parts[:2] in [('outputs','previews'),('outputs','comparisons')]:group='04-satellite-refined-comparisons'
 if rel.parts[:2]==('outputs','maps'):
  id=p.name.split('_')[0]
  if id.isdigit():group='02-regional-maps-01-14' if int(id)<=14 else '03-regional-maps-15-28'
  else:group='04-satellite-refined-comparisons'
 groups[group].append(p)
results=[]
for name,paths in groups.items():
 paths=sorted(set(paths+[ROOT/'README.md',ROOT/'outputs/manifest.json']));target=ROOT/f'downloads/shanghai-planning-v3-{name}.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in paths:z.write(p,'planning_v3/'+str(p.relative_to(ROOT)))
 assert target.stat().st_size<95*1024*1024,('Package exceeds safe GitHub file budget',target)
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 record={'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'members':len(paths),'CRC_verified':True};results.append(record);print(record,flush=True)
dump(ROOT/'downloads/package_verification.json',results)
(ROOT/'downloads/SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['file']+'\n' for r in results))
shutil.copy2(ROOT/'outputs/previews/INDEX_V3.png',ROOT/'downloads/INDEX_V3.png')
# Verify every manifest file as actually stored in ZIPs, not only in the source working directory.
expected={r['path']:r['sha256'] for r in manifest['files']};seen=set();fail=[]
for record in results:
 with zipfile.ZipFile(ROOT/'downloads'/record['file']) as z:
  for name in z.namelist():
   rel=name.removeprefix('planning_v3/')
   if rel not in expected:continue
   h=hashlib.sha256()
   with z.open(name) as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
   if h.hexdigest()!=expected[rel]:fail.append(rel)
   seen.add(rel)
assert not fail and seen==set(expected)
dump(ROOT/'downloads/archive_member_verification.json',{'manifest_files':len(expected),'verified_files':len(seen),'errors':fail,'all_verified':True})
print('ALL ARCHIVE MEMBERS VERIFIED',len(seen),flush=True)
