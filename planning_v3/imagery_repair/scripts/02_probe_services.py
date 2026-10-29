"""Metadata only. Does not export imagery, request tokens, scrape tiles, or infer reuse permission."""
from pathlib import Path
import json,math,requests,concurrent.futures
from pyproj import CRS
P=Path(__file__).resolve().parents[1]
SOURCES=[('shanghai_airphoto','https://mape.shanghai-map.net/arcgis/rest/services/SHMAP_IMAGE/MapServer'),('shanghai_2024','https://map4.shanghai-map.net/arcgis/rest/services/shyx2024/MapServer'),('esri_world_imagery','https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer')]
def probe(source):
 id,url=source;record={'id':id,'url':url,'access':'not_tested','source_native_GSD_m':None,'actual_capture_date':None,'academic_map_use_allowed':None,'offline_cache_allowed':None,'download_allowed':None,'redistribution_allowed':None,'auth_requirement':'unverified','qgis_provider_candidate':'arcgismapserver (ams)','qgis_layer_enabled':False}
 try:
  r=requests.get(url,params={'f':'pjson'},timeout=30);record['http_status']=r.status_code
  if not r.ok:record['access']='http_'+str(r.status_code);return record
  j=r.json();(P/f'data/{id}_metadata.json').write_text(json.dumps(j,ensure_ascii=False,indent=2))
  if 'error' in j:
   record['access']='arcgis_error';record['error']=j['error'];record['auth_requirement']='token_required' if j['error'].get('code')==499 else 'must_check_error';return record
  record.update(access='metadata_accessible',copyright=j.get('copyrightText'),service_description=j.get('serviceDescription'),description=j.get('description'),supported_image_formats=j.get('supportedImageFormatTypes'),supported_extensions=j.get('supportedExtensions'),capabilities=j.get('capabilities'),tile_cache=j.get('singleFusedMapCache'),max_export_size=[j.get('maxImageWidth'),j.get('maxImageHeight')],authInfo=j.get('authInfo'),document_info=j.get('documentInfo'))
  sr=j.get('spatialReference') or j.get('fullExtent',{}).get('spatialReference') or {};record['spatial_reference']=sr;wkid=sr.get('latestWkid',sr.get('wkid'));tile=j.get('tileInfo',{});lods=tile.get('lods',[])
  if lods:
   deepest=min(lods,key=lambda l:l.get('resolution',float('inf')));record['deepest_advertised_LOD']=deepest
   if wkid in [3857,102100,102113]:record['nominal_display_ground_spacing_at31_3N_m']=deepest['resolution']*math.cos(math.radians(31.3))
   elif wkid in [4326,4490]:record['nominal_display_ground_spacing_at31_3N_m_xy']=[deepest['resolution']*111320*math.cos(math.radians(31.3)),deepest['resolution']*110870]
   else:record['nominal_display_resolution_map_units']=deepest.get('resolution')
  record['critical_warning']='Deepest tile pixel spacing is NOT proof of native acquisition GSD; service name2024/copyright year is NOT a verified capture date; public metadata is NOT a redistribution license'
  if wkid:
   try:
    from pyproj.transformer import TransformerGroup
    group=TransformerGroup(CRS.from_epsg(wkid),CRS.from_epsg(32651),always_xy=True);record['projection_operations']=[{'description':t.description,'declared_accuracy_m':t.accuracy} for t in group.transformers[:4]];record['best_transform_available']=group.best_available
   except Exception as exc:record['projection_check_error']=type(exc).__name__
  return record
 except Exception as exc:record.update(access='proxy_denied' if 'Tunnel connection failed: 403' in str(exc) else 'request_failed',error=str(exc)[:700]);return record
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(probe,SOURCES))
 (P/'reports/service_capability_rights_matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False,indent=2))
