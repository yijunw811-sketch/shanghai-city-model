"""Self-contained thematic ZIPs, each under GitHub's 100MB limit, verified CRC and SHA."""
from common import *
import zipfile,re,shutil
# Preserve useful licensed metadata/research extraction without huge byte-range caches or search HTML.
metadata=RAW/'metadata_snapshots';metadata.mkdir(exist_ok=True)
for name in ['geoboundaries.txt','clcd_zenodo.txt']:
 p=ROOT/'cache/source_discovery'/name
 if p.exists():shutil.copy2(p,metadata/(p.stem+'.json'))
for p in (ROOT/'cache/source_discovery').glob('*.json'):
 if p.stat().st_size<8*1024*1024:shutil.copy2(p,metadata/p.name)
# Source code, reports and allowed raw data are checked for accidentally persisted credential queries.
for folder in ['scripts','reports','standards','outputs/gis/planning_raw_sources/metadata_snapshots']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and p.suffix in ['.py','.md','.json','.csv','.html','.txt']:
   text=p.read_text(errors='replace')
   if re.search(r'[?&](?:sig|signature|token|api_key)=[^&\s"<>]+',text,re.I):raise RuntimeError('Credential-like URL parameter requires review: '+str(p.relative_to(ROOT)))
progress('delivery','packages','packaging_verified_inputs')
files=[]
for p in ROOT.rglob('*'):
 if not p.is_file() or any(x in p.parts for x in ['__pycache__']):continue
 rel=p.relative_to(ROOT)
 if rel.parts[0]=='cache' and rel.parts[:2]!=('cache','research'):continue
 if p.suffix in ['.lock','.partial','.pyc'] or p.name=='manifest.json' or p.name=='packaging_execution.log' or p.name.endswith('~'):continue
 files.append(p)
manifest={'created_at':now(),'project':'Shanghai planning GIS V2','aoi_km2':AOI.area/1e6,'original_model_unchanged_verified':'reports/protected_input_verification.csv','commands':'scripts/run_pipeline.py; reports/resume_status.txt','versions':'requirements-cloud.txt; reports/qgis_validation.json','completion':str(json.loads((ROOT/'reports/final_qa.json').read_text())['A1_maps_verified'])+' maps verified; source completeness limited and explicit','files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]}
dump(ROOT/'outputs/manifest.json',manifest);files.append(ROOT/'outputs/manifest.json')
dest=REPO/'downloads';dest.mkdir(exist_ok=True)
groups={'gis':[],'atlas':[],'sources-repro':[]}
for p in files:
 rel=p.relative_to(ROOT)
 if rel.parts[:2]==('outputs','maps') or rel.parts[:2]==('outputs','figures'):group='atlas'
 elif rel.parts[:2]==('outputs','gis') and 'planning_raw_sources' not in rel.parts:group='gis'
 else:group='sources-repro'
 groups[group].append(p)
# Copy the small readme/manifest into each ZIP; all paths use the same root so extraction composes safely.
results=[]
for name,paths in groups.items():
 paths=sorted(set(paths+[ROOT/'README.md',ROOT/'outputs/manifest.json']))
 target=dest/f'shanghai-planning-v2-{name}.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in paths:z.write(p,arcname='planning_v2/'+str(p.relative_to(ROOT)))
 if target.stat().st_size>=95*1024*1024:raise RuntimeError('Thematic ZIP too large; split further before GitHub upload')
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 results.append({'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'members':len(paths),'CRC_verified':True});print(results[-1],flush=True)
dump(dest/'planning-v2-package-verification.json',results)
(dest/'planning-v2-SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['file']+'\n' for r in results))
shutil.copy2(ROOT/'outputs/maps/INDEX.png',dest/'planning-v2-INDEX.png')
# Verification JSON in downloads is authoritative; avoid mutating manifest-listed state after hashing.
