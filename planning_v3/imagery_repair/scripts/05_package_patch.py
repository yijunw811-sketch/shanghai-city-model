from pathlib import Path
import json,hashlib,shutil,zipfile
P=Path(__file__).resolve().parents[1];V3=P.parent
D=P/'downloads';D.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
backup=P/'state/base_manifest_before_patch.json'
if not backup.exists():shutil.copy2(V3/'outputs/manifest.json',backup)
base=json.loads(backup.read_text());entries={r['path']:r for r in base['files']}
files=[V3/'README.md',V3/'SATELLITE_IMAGE_QUALITY_REPORT.md',V3/'outputs/qgis/planning_analysis_v3.qgz',V3/'outputs/qgis/planning_analysis_v3_imagery_diagnostic.qgz']
for p in P.rglob('*'):
 if not p.is_file() or 'downloads' in p.relative_to(P).parts or '__pycache__' in p.parts or p.suffix=='.log' or p.name.endswith(('~','.pyc','.partial')):continue
 files.append(p)
files=sorted(set(files))
for p in files:entries[str(p.relative_to(V3))]={'path':str(p.relative_to(V3)),'bytes':p.stat().st_size,'sha256':sha(p)}
base['files']=sorted(entries.values(),key=lambda r:r['path']);base['imagery_repair']={'date':'2026-10-29','branch':'planning-v3-imagery-repair-20261029','source_resolution_m':10,'high_resolution_replacement_complete':False,'baseline_windows_prepared':3,'new_old_comparisons_completed':0,'formal_HD_maps_exported':0,'display_patch_verified':True,'blocker':'Current runtime proxy403 before contact to official services; rights and native GSD unknown'}
(V3/'outputs/manifest.json').write_text(json.dumps(base,ensure_ascii=False,indent=2));files.append(V3/'outputs/manifest.json')
target=D/'shanghai-gis-v3-imagery-diagnostic-patch-20261029.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,'planning_v3/'+str(p.relative_to(V3)))
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for p in files:assert hashlib.sha256(z.read('planning_v3/'+str(p.relative_to(V3)))).hexdigest()==sha(p)
record={'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'files':len(files),'CRC_verified':True,'archive_member_SHA256_verified':True,'requires_base_V3_core_data':True,'high_resolution_replacement_complete':False}
(D/'package_verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));(D/'SHA256SUMS.txt').write_text(record['sha256']+'  '+target.name+'\n');print(record,flush=True)
