from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parents[1]
def eligible(f):
 rel=f.relative_to(P)
 return f.is_file() and 'ne_land_cache' not in rel.parts and '__pycache__' not in rel.parts and not f.name.endswith(('~','.aux.xml')) and f.name!='location_two_variants_drafts.zip' and f.name!='file_manifest.json'
files=sorted(f for f in P.rglob('*') if eligible(f))
manifest=[{'file':str(f.relative_to(P)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files]
(P/'reports/file_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(P/'location_two_variants_drafts.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files+[P/'reports/file_manifest.json']:z.write(f,str(f.relative_to(P)))
with zipfile.ZipFile(P/'location_two_variants_drafts.zip') as z:assert z.testzip() is None
print('ZIP CRC passed:',len(files)+1,'files,',round((P/'location_two_variants_drafts.zip').stat().st_size/1e6,2),'MB')
