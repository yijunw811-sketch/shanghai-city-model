"""Read-only input inventory and baseline QA; hash all protected model/GIS inputs."""
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
import pyogrio
import shapely
from common import *

progress('inventory','baseline','running')
file_records=[];layers=[];protected={}
for path in sorted(REPO.rglob('*')):
    if not path.is_file() or ROOT in path.parents or '.git' in path.parts:continue
    ext=path.suffix.lower()
    if ext not in ('.gpkg','.geojson','.csv','.tif','.tiff','.shp','.dxf','.dwg','.gdb','.blend','.glb','.obj','.dae','.qgz','.qgs','.md','.txt','.zip','.pdf'):continue
    record={'record_type':'file','path':str(path.relative_to(REPO)),'bytes':path.stat().st_size,'sha256':sha(path),'format':ext,'role':'temporary_cache' if 'overture_ranges' in path.parts else 'existing_input'}
    file_records.append(record)
    if ext in ('.gpkg','.blend','.glb') or path.name.startswith('boundary.'):
        protected[str(path)]=record['sha256']
    if ext!='.gpkg':continue
    for layer,geometry_type in pyogrio.list_layers(path):
        frame=gpd.read_file(path,layer=layer)
        fields=[str(c) for c in frame.columns]
        nulls={str(c):float(frame[c].isna().mean()) for c in frame.columns if c!=frame.geometry.name}
        metric=frame.to_crs(32651) if frame.crs else frame
        geometry_valid=bool(frame.is_valid.all())
        source_columns=[c for c in fields if any(s in c.lower() for s in ['source','provider','license','date','release','confidence','inferred','height_source'])]
        source_values={c:frame[c].dropna().astype(str).value_counts().head(12).to_dict() for c in source_columns if c not in ('tags_json','properties_json','sources_json')}
        layers.append({'record_type':'layer','path':str(path.relative_to(REPO)),'layer':layer,'crs':str(frame.crs),'geometry_type':geometry_type,'feature_count':len(frame),'area_sum_m2':float(metric.area.sum()),'length_sum_m':float(metric.length.sum()),'valid_count':int(frame.is_valid.sum()),'invalid_count':int((~frame.is_valid).sum()),'empty_count':int(frame.is_empty.sum()),'fields':json.dumps(fields,ensure_ascii=False),'null_rates':json.dumps(nulls,ensure_ascii=False),'provenance_fields':json.dumps(source_values,ensure_ascii=False),'mapping_suitability':'geometry_valid_but_source_limits_apply' if geometry_valid else 'repair_or_review_required','sha256':record['sha256']})
pd.DataFrame(file_records+layers).to_csv(ROOT/'reports/input_inventory.csv',index=False)
dump(ROOT/'state/protected_input_hashes.json',protected)
buildings=gpd.read_file(CITY,layer='buildings')
unclassified=gpd.read_file(CITY,layer='unclassified_site')
conflict=gpd.read_file(CITY,layer='road_building_conflicts')
dangling=gpd.read_file(CITY,layer='road_dangling_review')
steep=gpd.read_file(CITY,layer='road_schematic_steep_review')
audit={'aoi_area_m2':AOI.area,'aoi_area_km2':AOI.area/1e6,'baseline_unclassified_km2':unclassified.area.sum()/1e6,'baseline_unclassified_percent':100*unclassified.area.sum()/AOI.area,'building_count':len(buildings),'height_source_counts':buildings.height_source.value_counts().to_dict(),'road_building_conflict_records':len(conflict),'road_building_conflict_area_m2':conflict.area.sum(),'dangling_review_count':len(dangling),'schematic_steep_segments':len(steep),'design_site_files':[r['path'] for r in file_records if '选定范围' in r['path'] or 'design_site' in r['path']],'protected_files':len(protected),'crs':'EPSG:32651','source_crs':'WGS84 confirmed by user in prior task','context_buffer_m':2000}
dump(ROOT/'reports/baseline_audit.json',audit)
(ROOT/'reports/baseline_audit.md').write_text('# 输入与基线实核\n\n'+f'原始边界 {AOI.area/1e6:.6f} km²；建筑 {len(buildings)}；未分类 {audit["baseline_unclassified_km2"]:.6f} km²。\n\n'+'道路建筑冲突记录表示已裁除的原缓冲冲突，不等于仍有建筑压路；单端节点不自动等于错误断路，可能是尽端道路/私有入口；纵坡为示意高程下的异常，不是实测。\n\n'+'19处冲突、267处单端点、9段示意坡度按真实输入记录清查，后续单独复核，不修改旧模型或源GPKG。\n\n'+json.dumps(audit,ensure_ascii=False,indent=2))
progress('inventory','baseline','verified',layers=len(layers),files=len(file_records),aoi_area_m2=AOI.area)
print(json.dumps(audit,ensure_ascii=False,indent=2))
