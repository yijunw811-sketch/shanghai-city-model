"""Shared IO, provenance and restart checkpoints for the separate planning task."""
from pathlib import Path
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import sqlite3
import time
from urllib.parse import urlsplit,urlunsplit
import geopandas as gpd
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
BASE=REPO/'上海城市模型_Codex云端起步包'
CITY=BASE/'outputs/gis/city.gpkg'
if not CITY.exists():CITY=ROOT/'inputs/city.gpkg'
AUDIT=BASE/'outputs/gis/overture_audit.gpkg'
if not AUDIT.exists():AUDIT=ROOT/'inputs/overture_audit.gpkg'
RAW=ROOT/'outputs/gis/planning_raw_sources'
for name in ['reports','state','cache','standards','scripts','outputs/gis/planning_raw_sources','outputs/maps/A1','outputs/maps/A3_review','outputs/qgis','outputs/figures']:(ROOT/name).mkdir(parents=True,exist_ok=True)
boundary_path=BASE/'data/boundary.geojson'
if not boundary_path.exists():boundary_path=ROOT/'inputs/boundary.geojson'
AOI=gpd.read_file(boundary_path).to_crs(32651).geometry.iloc[0]
CONTEXT=AOI.buffer(2000)
SESSION=requests.Session()
SESSION.headers['User-Agent']='ShanghaiPlanningGISResearch/2.0 (public-data research; cached small-area requests)'
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as file:
        for chunk in iter(lambda:file.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def safe_url(url):
    p=urlsplit(url)
    if any(key in p.query.lower() for key in ['signature=','sig=','token=','api_key=','key=']):return urlunsplit((p.scheme,p.netloc,p.path,'',''))
    return url
def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str));tmp.replace(path)
def progress(stage,key,status,**details):
    path=ROOT/'state/progress.json'
    with (ROOT/'state/progress.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=json.loads(path.read_text()) if path.exists() else {'started_at':now(),'stages':{}}
        state['updated_at']=now();state['stages'].setdefault(stage,{})[key]={'status':status,'updated_at':now(),**details}
        dump(path,state)
        fcntl.flock(lock,fcntl.LOCK_UN)
def db():
    con=sqlite3.connect(ROOT/'state/catalog.sqlite',timeout=30)
    con.execute('CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY, record_json TEXT NOT NULL)')
    con.execute('CREATE TABLE IF NOT EXISTS attempts(attempt_id INTEGER PRIMARY KEY, source_id TEXT, attempted_at TEXT, round INTEGER, outcome TEXT, detail TEXT)')
    return con
FIELDS=['source_id','category','dataset_name','provider','url','discovered_at','published_at','valid_year','updated_at','format','feature_count_aoi','spatial_resolution','coverage_percent','license','access_status','api_registration_needed','reuse_allowed','local_path','checksum','notes','reason','alternative_sources','family','round']
def register(source_id,**record):
    with db() as con:
        row=con.execute('SELECT record_json FROM sources WHERE source_id=?',(source_id,)).fetchone()
        current=json.loads(row[0]) if row else {k:None for k in FIELDS}
        current.update({'source_id':source_id,'discovered_at':current.get('discovered_at') or now(),**record})
        if current.get('url'):current['url']=safe_url(current['url'])
        con.execute('INSERT OR REPLACE INTO sources VALUES(?,?)',(source_id,json.dumps(current,ensure_ascii=False,default=str)))
def attempt(source_id,round_number,outcome,detail):
    with db() as con:con.execute('INSERT INTO attempts(source_id,attempted_at,round,outcome,detail) VALUES(?,?,?,?,?)',(source_id,now(),round_number,outcome,str(detail)[:2500]))
def export_registry():
    with db() as con:records=[json.loads(r[0]) for r in con.execute('SELECT record_json FROM sources ORDER BY source_id')]
    pd.DataFrame(records).reindex(columns=FIELDS).to_csv(ROOT/'reports/source_registry.csv',index=False)
    return records
def request_public(source_id,url,path=None,round_number=1,kind='metadata',timeout=35,params=None,method='GET',data=None,archive=True):
    path=Path(path) if path else RAW/source_id/'metadata.bin'
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size:
        progress('downloads',source_id,'cached',path=str(path.relative_to(ROOT)),checksum=sha(path))
        return path
    try:
        response=SESSION.request(method,url,params=params,data=data,timeout=timeout)
        status=response.status_code
        if not response.ok:
            result='blocked_http_'+str(status) if status in (401,403,429) else 'http_'+str(status)
            register(source_id,access_status=result,reason=f'HTTP {status}; remote access/authorization and platform policy need distinguishing; no bypass attempted',round=round_number)
            attempt(source_id,round_number,result,safe_url(response.url));progress('source_search',source_id,result)
            return None
        payload=response.content
        if len(payload)>32*1024*1024 and kind=='metadata':raise RuntimeError('Unexpectedly large metadata response; refusing bulk archive')
        if archive:
            tmp=path.with_suffix(path.suffix+'.partial');tmp.write_bytes(payload);tmp.replace(path)
            register(source_id,access_status='metadata_fetched' if kind=='metadata' else 'fetched',local_path=str(path.relative_to(ROOT)),checksum=sha(path),round=round_number)
            progress('downloads',source_id,'fetched',bytes=len(payload),path=str(path.relative_to(ROOT)))
        attempt(source_id,round_number,'success',f'{safe_url(response.url)}; {len(payload)} bytes; {response.headers.get("Content-Type","")}')
        return path if archive else response
    except Exception as exc:
        message=str(exc)
        result='blocked_proxy' if '403' in message and ('Proxy' in type(exc).__name__ or 'tunnel' in message.lower()) else 'request_failed'
        register(source_id,access_status=result,reason=message[:1000],round=round_number)
        attempt(source_id,round_number,result,message[:1500]);progress('source_search',source_id,result)
        return None
def provenance(provider,dataset,url,license,**extra):
    return {'provider':provider,'dataset':dataset,'source_url':safe_url(url),'retrieved_at':now(),'release_date':None,'license':license,'crs_original':'EPSG:4326','processing_steps':'Project to EPSG:32651; preserve context and AOI distinctions','is_inferred':False,'evidence':'source feature geometry and attributes','confidence':'source_not_independently_surveyed','spatial_accuracy_m':None,**extra}
def write_layer(frame,path,layer):
    path=Path(path)
    if path.resolve() in (CITY.resolve(),AUDIT.resolve()):raise RuntimeError('Protected original GIS path')
    frame.to_file(path,layer=layer,driver='GPKG')
def source_context(frame):
    if frame.crs is None:raise ValueError('Source CRS must be known')
    if frame.crs.to_epsg()==4326:
        context4326=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).iloc[0]
        frame=frame[frame.intersects(context4326)].copy()
        frame['geometry']=frame.geometry.make_valid().intersection(context4326)
    frame=frame.to_crs(32651)
    frame=frame[frame.intersects(CONTEXT)].copy()
    frame['geometry']=frame.geometry.make_valid().intersection(CONTEXT)
    frame=frame[~frame.is_empty]
    frame['in_aoi']=frame.intersects(AOI)
    return frame
