# Project instructions: Shanghai 22 km² city massing model (Codex Cloud)

## Inputs
- `data/boundary.csv` is the original user-provided closed polygon with fields Longitude, Latitude, Elevation.
- `data/boundary.geojson` is derived from the same vertices. WGS84/EPSG:4326 is assumed ONLY; verify source coordinate system, including potential GCJ-02 or BD-09 offsets, using reliable control features before geospatial joins.
- The approximate extent is 121.4048638239..121.4658442408 longitude, 31.2829837492..31.3171844724 latitude, about 22.01 km².
- Source elevation samples (~5.19-5.57 m) are NOT a usable DEM. Do not invent terrain from them.
- Additional user GIS layers, if provided, take priority over online substitutes once alignment, currency and licensing have been verified.

## Goal
Create an **actual, georeferenced, editable LOD1 model** for the entire study boundary: buildings, continuous road surface, road centerline network, green space, water features, hardscape, and optional real terrain. Do not confuse a preview render with the deliverable 3D mesh files.

## Cloud workflow
- This task runs inside an isolated Codex Cloud environment, NOT the user's Windows workstation. Never try to access the user's C: or D: paths, local MCP, Blender GUI, SketchUp GUI, or ArcGIS GUI from cloud.
- Prefer Python geospatial pipeline (geopandas, shapely, pyproj, osmnx, pyogrio, rasterio when necessary, trimesh) and headless Blender only if verified available. Install and test dependencies in the environment.
- Confirm outbound internet connectivity/allowed hostnames to the chosen data endpoints. If blocked, report exact needed domains and use any preloaded source data; do not invent successful network calls.
- Chunk Overpass/OSM downloads to be API-respectful, retry with caching, or use licensed regional extracts. Retain date, URL, source, and licensing metadata.

## Modeling rules
1. Transform source geometry to a meter-based CRS (candidate EPSG:32651), create a reversible local XY origin near the center of the extent, set Z in meters, and store transformation metadata.
2. Validate and clip to the exact study polygon; query a 100-200 m buffer to preserve boundary roads and junctions before final clipping.
3. Buildings: preserve footprint, height from source where available; else building:height or levels (document level height), else explicit modeled estimates with `height_source` and confidence. No fake real-height claims. Fix invalid polygons and duplicate footprints, preserving audit logs.
4. Roads: keep line network and generate true planar road surfaces using verified pavement polygons where possible; otherwise use widths/lanes or classification-specific configurable estimates. Cover motor roads, residential/service/access roads, pedestrian lanes, walkways where mapped, ramps and grade-separated infrastructure. Build junction geometries; connect true at-grade intersections; do not falsely connect bridges/tunnels. Do not fabricate nonexistent links merely to improve connectivity stats.
5. Landscape: polygon surfaces for parks, grass, forest, planted areas, medians, public squares and other open space; add lightweight tree proxies only where tree locations are grounded or clearly identified as schematic. Keep water separate. Do not label unknown areas as verified greenspace.
6. Fix geometry overlaps and invalidity, avoid z-fighting by stable height offsets; model bridges/tunnels according to evidence. All layers must be separately toggleable and exported.
7. Use tiles (roughly 500 m to 1 km) and level-of-detail/performance controls. Provide both combined visualization and separately importable per-layer/per-tile GLBs. Never let grouping destroy editability.
8. Deliver source GIS GeoPackage with provenance columns, model `.blend` if Blender works, `.glb`, and optionally `.obj`. `.skp` or `.dae` only if a verified converter is available; do not rename file extensions. glTF/GLB is an accepted native import format for current SketchUp versions, but test export with a parser and a small sample.
9. Design visuals: buildings off-white/light gray; roads charcoal/neutral gray; green spaces greens; water muted blue; hardscape warm/light gray; terrain neutral, low saturation. No flashy fictional facades.
10. Source and inferred attributes can share visual styling, but provenance/confidence/source_date must remain in machine-readable GIS and reports.

## Quality assurance: test, don't promise
- Save geometry counts, actual extent, GIS CRS, total modeled area and source coverage by layer.
- Verify building meshes have positive, plausible heights and correct footprints; report height missingness, estimation rates and abnormal outliers.
- Verify at-grade road graph connectivity, dangling endpoints inside area, road polygons, major intersections, grade-separated distinctions and where source data is incomplete.
- Report green/water feature coverage, overlaps, number of empty tiles, missing source records and unresolved issues.
- Validate every exported GLB is loadable and measure output size, triangles, object counts and bounds, including a test of one tile.
- Save preview images (top-down, axonometric, road-only, greens-only), automated QA report, sources table, run instructions and rerunnable scripts.
- Never claim 100% real-world completeness if source datasets lack evidence. Highlight unresolved gaps with clear documentation for manual verification.
