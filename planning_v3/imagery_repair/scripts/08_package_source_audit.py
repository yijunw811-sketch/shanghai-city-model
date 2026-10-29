"""Package source metadata and current reports; no third-party imagery included."""
from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parents[1];V=P.parent;D=P/'downloads'
names=['SATELLITE_IMAGE_QUALITY_REPORT.md','imagery_repair/README.md',
 'imagery_repair/scripts/04_quality_report.py','imagery_repair/scripts/06_esri_source_audit.py',
 'imagery_repair/scripts/07_refresh_source_report.py','imagery_repair/scripts/08_package_source_audit.py',
 'imagery_repair/reports/work_status.json','imagery_repair/reports/PR_BODY.md',
 'imagery_repair/reports/service_capability_rights_matrix.json',
 'imagery_repair/reports/network_release_verification_20261029.json',
 'imagery_repair/reports/esri_license_evidence.json','imagery_repair/reports/esri_spatial_source_audit.json',
 'imagery_repair/data/esri_aoi_source_footprints.json','imagery_repair/data/esri_pending_connection.json',
 'imagery_repair/data/esri_source_footprints.geojson','imagery_repair/data/esri_world_imagery_metadata.json',
 'imagery_repair/data/openaerialmap_aoi_metadata.json']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=V/'outputs/manifest.json';manifest=json.loads(m.read_text());entries={e['path']:e for e in manifest['files']}
for name in names:
 p=V/name;entries[name]={'path':name,'bytes':p.stat().st_size,'sha256':sha(p)}
manifest['files']=sorted(entries.values(),key=lambda e:e['path'])
manifest['imagery_repair'].update(blocker='Source-specific Esri license verification pending access to www.arcgis.com and goto.arcgisonline.com; no actual imagery acquired',candidate_core_GSD_metadata_m=0.34,candidate_core_capture_date='2025-04-07',candidate_metadata_footprint_coverage_fraction=1.0,position_accuracy_metadata_m=8.47,runtime_revision='13')
m.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));names.append('outputs/manifest.json')
target=D/'shanghai-gis-v3-esri-source-audit-20261029.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name in names:z.write(V/name,'planning_v3/'+name)
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for name in names:assert hashlib.sha256(z.read('planning_v3/'+name)).hexdigest()==sha(V/name)
record={'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'members':len(names),
 'CRC_and_member_SHA256_verified':True,'contains_high_resolution_imagery':False,
 'metadata_only':True,'requires_original_V3_and_diagnostic_patch_for_full_project':True}
(D/'esri_audit_package_verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
(D/'ESRI_AUDIT_SHA256SUMS.txt').write_text(record['sha256']+'  '+target.name+'\n')
print(json.dumps(record,ensure_ascii=False))
