from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parents[1];manifest=json.loads((P/'outputs/manifest.json').read_text());errors=[]
for r in manifest['files']:
 p=P/r['path']
 if not p.is_file():errors.append([r['path'],'missing']);continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 if h.hexdigest()!=r['sha256']:errors.append([r['path'],'SHA256 mismatch'])
print(json.dumps({'files':len(manifest['files']),'errors':errors,'verified':not errors},ensure_ascii=False,indent=2));sys.exit(bool(errors))
