"""Standard-library-only verification after extracting all three ZIPs together."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1];manifest=json.loads((root/'outputs/manifest.json').read_text());errors=[]
for row in manifest['files']:
 p=root/row['path']
 if not p.exists():errors.append((row['path'],'missing'));continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 if h.hexdigest()!=row['sha256']:errors.append((row['path'],'SHA256 mismatch'))
print(json.dumps({'manifest_files':len(manifest['files']),'errors':errors,'verified':not errors},ensure_ascii=False,indent=2));sys.exit(bool(errors))
