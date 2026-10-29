from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parents[1]
m=json.loads((P/'reports/DELIVERY_MANIFEST.json').read_text());errors=[]
for f in m['files']:
 p=P/f['path']
 if not p.exists():errors.append([f['path'],'missing'])
 elif hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:errors.append([f['path'],'SHA256 mismatch'])
print(json.dumps({'files':len(m['files']),'verified':not errors,'errors':errors},ensure_ascii=False,indent=2));sys.exit(bool(errors))
