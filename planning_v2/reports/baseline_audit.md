# 输入与基线实核

原始边界 22.009121 km²；建筑 11856；未分类 14.086698 km²。

道路建筑冲突记录表示已裁除的原缓冲冲突，不等于仍有建筑压路；单端节点不自动等于错误断路，可能是尽端道路/私有入口；纵坡为示意高程下的异常，不是实测。

19处冲突、267处单端点、9段示意坡度按真实输入记录清查，后续单独复核，不修改旧模型或源GPKG。

{
  "aoi_area_m2": 22009120.78313864,
  "aoi_area_km2": 22.00912078313864,
  "baseline_unclassified_km2": 14.086697685008867,
  "baseline_unclassified_percent": 64.0039092147688,
  "building_count": 11856,
  "height_source_counts": {
    "landuse_context_default_estimate": 10125,
    "type_default_estimate": 1708,
    "osm_levels_times_3m": 23
  },
  "road_building_conflict_records": 19,
  "road_building_conflict_area_m2": 2276.410939939537,
  "dangling_review_count": 267,
  "schematic_steep_segments": 9,
  "design_site_files": [],
  "protected_files": 41,
  "crs": "EPSG:32651",
  "source_crs": "WGS84 confirmed by user in prior task",
  "context_buffer_m": 2000
}