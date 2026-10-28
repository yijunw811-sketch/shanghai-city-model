from pathlib import Path
import json,hashlib,datetime,shutil,sqlite3,os
os.environ.setdefault("MPLCONFIGDIR","/workspace/.cache/matplotlib")
os.environ.setdefault("XDG_CACHE_HOME","/workspace/.cache")
import geopandas as gpd,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parent;V2=REPO/'planning_v2'
if not V2.exists():V2=ROOT/'data/v2_reference'
M=ROOT/'outputs/gis/reference_v2.gpkg';A=ROOT/'outputs/gis/reference_analysis_v2.gpkg';D=ROOT/'outputs/gis/refined_analysis_v3.gpkg'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def dump(p,o):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2,default=str))
def read(layer,path=M):return gpd.read_file(path,layer=layer)
def put(frame,layer,path=D):
 if V2 in Path(path).resolve().parents:raise RuntimeError('V2 is read-only')
 frame.to_file(path,layer=layer,driver='GPKG')
def checkpoint(key,**fields):dump(ROOT/f'state/{key}.json',{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),**fields})
AOI=gpd.read_file(M if M.exists() else V2/'outputs/gis/planning_enriched.gpkg',layer='aoi_boundary').geometry.iloc[0]
CONTEXT=AOI.buffer(2000)
