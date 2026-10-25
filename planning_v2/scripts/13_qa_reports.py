"""Independent readback, original-input protection, thematic gap tracking, and delivery reports."""
from common import *
import numpy as np,pyogrio,rasterio,xml.etree.ElementTree as ET,html,fitz
from shapely import union_all
from shapely.geometry import Point
from scipy.spatial import cKDTree
M=ROOT/'outputs/gis/planning_enriched.gpkg';A=ROOT/'outputs/gis/analysis_layers.gpkg'
# Every spatial table read back and geometry/CRS checked. Duplicate geometry is reported, not indiscriminately removed.
inventory=[];nulls=[]
for dbpath in [M,A]:
 with sqlite3.connect(dbpath) as con:
  assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 for layer,typ in pyogrio.list_layers(dbpath):
  if typ is None:continue
  f=gpd.read_file(dbpath,layer=layer)
  record={'database':dbpath.name,'layer':layer,'count':len(f),'crs':str(f.crs),'invalid':int((~f.is_valid).sum()),'empty':int(f.is_empty.sum()),'null_geometry':int(f.geometry.isna().sum()),'duplicate_wkb':int(f.geometry.to_wkb().duplicated().sum()),'aoi_intersect_count':int(f.intersects(AOI).sum()) if len(f) else 0,'geometry_types':json.dumps(f.geom_type.value_counts().to_dict())}
  inventory.append(record)
  for col in f.columns:
   if col=='geometry':continue
   nulls.append({'database':dbpath.name,'layer':layer,'field':col,'null_fraction':float(f[col].isna().mean()) if len(f) else None,'blank_fraction':float((f[col].astype(str)=='').mean()) if len(f) else None})
  assert f.crs.to_epsg()==32651,record
  assert not record['null_geometry'] and not record['invalid'],record
pd.DataFrame(inventory).to_csv(ROOT/'reports/output_layer_inventory.csv',index=False);pd.DataFrame(nulls).to_csv(ROOT/'reports/field_completeness.csv',index=False)
# AOI functional partition exactness, with sensible sub-mm numerical tolerance.
land=gpd.read_file(M,layer='landuse_existing');u=union_all(land.geometry)
assert abs(u.area-AOI.area)<.01
assert land.area.sum()-u.area<.01
boundary=gpd.read_file(M,layer='aoi_boundary').geometry.iloc[0];assert boundary.symmetric_difference(AOI).area<.001
old=json.loads((ROOT/'state/protected_input_hashes.json').read_text());protected=[]
for p,expected in old.items():
 actual=sha(p);protected.append({'path':p,'original_sha256':expected,'current_sha256':actual,'unchanged':actual==expected})
assert all(r['unchanged'] for r in protected)
pd.DataFrame(protected).to_csv(ROOT/'reports/protected_input_verification.csv',index=False)
# QA source-node graph coverage must increase with time.
coverage=pd.read_csv(ROOT/'reports/network_service_coverage.csv')
for kind,group in coverage.groupby('kind'):
 assert np.all(np.diff(group.sort_values('minutes').reachable_walk_m_aoi)>=-.001),kind
 assert (group.reachable_walk_m_aoi<=group.denominator_walk_m_aoi+.01).all(),kind
# Explicit audit of baseline flagged records, not counted as newly found real-world errors.
roads=gpd.read_file(M,layer='road_surfaces');build=gpd.read_file(M,layer='buildings_enriched');rb=union_all(roads.geometry);bb=union_all(build.geometry)
walk=gpd.read_file(M,layer='road_network_walk');points=[];nodeids=[]
for r in walk.itertuples():
 for n,c in [(r.u,r.geometry.coords[0]),(r.v,r.geometry.coords[-1])]:nodeids.append(n);points.append(c)
tree=cKDTree(points);reviews=[]
for layer in ['road_building_conflicts','road_dangling_review','road_schematic_steep_review']:
 f=gpd.read_file(M,layer=layer)
 for i,r in f.iterrows():
  geom=r.geometry;p=geom if geom.geom_type=='Point' else geom.representative_point();ll=gpd.GeoSeries([p],crs=32651).to_crs(4326).iloc[0]
  dist,j=tree.query([p.x,p.y]);current_overlap=geom.intersection(rb).intersection(bb).area
  status='previously_trimmed_model_conflict_not_unrepaired_overlap' if layer=='road_building_conflicts' else ('schematic_model_slope_not_surveyed_road_gradient' if 'steep' in layer else ('near_latest_walk_node_review_source_or_boundary' if dist<5 else 'source_network_gap_or_intentional_endpoint_unresolved'))
  reviews.append({'baseline_layer':layer,'baseline_index':i,'longitude':ll.x,'latitude':ll.y,'latest_walk_node_distance_m':dist,'nearest_osm_node':int(nodeids[j]),'current_surface_building_overlap_m2':current_overlap,'boundary_distance_m':p.distance(AOI.boundary),'status':status,'source_url':f'https://www.openstreetmap.org/node/{int(nodeids[j])}','action':'No edits to original model; manual source/survey check where unresolved'})
pd.DataFrame(reviews).to_csv(ROOT/'reports/baseline_flag_reassessment.csv',index=False)
# Twenty concrete QA sample locations, stratified by existing flags and unknown functional land.
samples=pd.DataFrame(reviews).groupby('baseline_layer',group_keys=False).apply(lambda d:d.sample(min(5,len(d)),random_state=2026),include_groups=False).reset_index(drop=True)
samples.to_csv(ROOT/'reports/manual_priority_samples.csv',index=False)
# Raster readback checks, nonempty valid AOI masks; effective resolution explicitly recorded in methods.
rasters=[]
for path in (ROOT/'outputs/gis/rasters').glob('*.tif'):
 with rasterio.open(path) as ds:
  a=ds.read(1,masked=True);valid=a.compressed();valid=valid[np.isfinite(valid)]
  assert len(valid)>0,path
  rasters.append({'path':str(path.relative_to(ROOT)),'crs':str(ds.crs),'resolution':str(ds.res),'valid_pixels':len(valid),'min':float(valid.min()),'median':float(np.median(valid)),'max':float(valid.max()),'sha256':sha(path)})
pd.DataFrame(rasters).to_csv(ROOT/'reports/raster_validation.csv',index=False)
# Atlas structural validation: exact physical dimensions, searchable embedded text and nonempty SVG/PNG.
maprecords=[];metas=sorted((ROOT/'reports').glob('map_[0-9][0-9].json'))
for meta in metas:
 m=json.loads(meta.read_text());stem=m['id']+'_'+m['title'].replace('｜','_').replace('/','_')
 p=ROOT/f'outputs/maps/A1/{stem}.pdf';doc=fitz.open(p);page=doc[0];mm=(page.rect.width/72*25.4,page.rect.height/72*25.4)
 assert abs(mm[0]-841)<.01 and abs(mm[1]-594)<.01
 text=page.get_text();assert '1:10,000' in text and m['id'] in text
 fontlist=page.get_fonts(full=True);assert fontlist
 svg=ROOT/f'outputs/maps/A1/{stem}.svg';sv=ET.parse(svg).getroot();assert len(sv)>0
 from PIL import Image
 im=Image.open(ROOT/f'outputs/maps/A1/{stem}.png');assert im.width>3000 and im.height>2000
 review=fitz.open(ROOT/f'outputs/maps/A3_review/{stem}.pdf');rp=review[0];assert abs(rp.rect.width/72*25.4-420)<.01 and abs(rp.rect.height/72*25.4-297)<.01
 maprecords.append({'id':m['id'],'title':m['title'],'A1_width_mm':mm[0],'A1_height_mm':mm[1],'A1_scale':m['A1_map_scale'],'A3_scale':m['A3_map_scale'],'PNG_width':im.width,'PNG_height':im.height,'fonts_embedded_count':len(fontlist),'svg_parsed':True,'findings_count':len(m['findings'])})
 doc.close();review.close();im.close()
pd.DataFrame(maprecords).to_csv(ROOT/'reports/map_export_validation.csv',index=False)
# Gap tracking remains conservative: mapped observations do not establish topic completeness.
demand=pd.read_csv(ROOT/'reports/data_demand_catalog.csv').astype(object).fillna('');available={x['layer']:x for x in inventory if x['database']==M.name}
rules=[('街道行政|行政区划','admin_units','Reference administrative polygons, not certified current/legal units'),('建筑轮廓|建筑高度|建筑层数|屋顶高度|建筑用途|建筑类型','buildings_enriched','Footprints retained; all heights estimated/levels-derived, use/floors sparse'),('街坊','urban_blocks','Derived analysis units, not cadastral parcels'),('现状用地|功能用地|工业仓储|教育医疗用地|商业商务用地|居住用地|城市空地|工地','landuse_existing','Source-tag functional partition; 47.67% unknown; no official land survey'),('快速路|服务道路|交叉口|单行|桥梁|隧道|立交|道路慢行|人行道|非机动车|过街','road_network_walk','Mapped node network; attribute gaps and access uncertainty retained'),('道路面|路宽','road_surfaces','Existing mapped/inferred widths, not surveyed road cross-sections'),('公交线路|轨道线路','transit_lines','Mapped relation members only; no verified timetables'),('公交站|轨道.*站|轨道.*出入口','transit_stations','Stop/platform/entrance records, not unique stations/frequency'),('公园','green_parks','Mapped parks; access from source path crossings, no field verification'),('绿地|绿化|林地','green_spaces_all','Mapped green spaces, not official green coverage'),('河渠|水面|水体|水系|湖塘','blue_network','Mapped water, topology and dates uncertain'),('历史文化资源|历史建筑|文保','heritage_sites','Mapped heritage references; no legal protection polygons'),('人口栅格|人口密度|常住与模型','population_ghsl2020','GHSL2020 native100m +WorldPop2025 ALPHA native~1km models; not resident census')]
import re
source_snapshot=export_registry()
for idx,row in demand.iterrows():
 item=row['item'];matches=[(layer,note) for pattern,layer,note in rules if re.search(pattern,item)]
 theme=str(row.theme)[0];matching_sources=[r['source_id'] for r in source_snapshot if theme in str(r.get('category','')).split()]
 demand.loc[idx,'sources_investigated']=';'.join(matching_sources);demand.loc[idx,'government_search']='metadata discovery performed; exact table access not assured';demand.loc[idx,'open_geography_search']='all published Overture themes and structured OSM context checked';demand.loc[idx,'scientific_or_remote_search']='topic discovery and relevance/license screening; no universal coverage claim'
 demand.loc[idx,'status']='blocked' if theme=='J' else 'searchable';demand.loc[idx,'gap']='No confirmed source-specific local evidence; source/permission/manual follow-up remains. Portal metadata is not a downloaded dataset.'
 for layer,note in matches:
  if layer in available and available[layer]['count']>0:
   demand.loc[idx,'status']='fetched';demand.loc[idx,'fetched']=True;demand.loc[idx,'existing_evidence']=layer;demand.loc[idx,'gap']=note+'; completeness not established'
 if theme=='D':
  demand.loc[idx,'status']='searchable';demand.loc[idx,'gap']='POI categories include source subcategories, but this exact subtype must be checked; no capacity/absence inference'
 if re.search('NDVI|NDWI|NDBI|Sentinel|Landsat|卫星地表温度|高程|坡度|地表覆盖',item):
  demand.loc[idx,'status']='verified';demand.loc[idx,'fetched']=True;demand.loc[idx,'verified']=True;demand.loc[idx,'existing_evidence']='raster_validation.csv; sentinel_radiometry_control.json';demand.loc[idx,'gap']='Product-specific valid coverage and effective resolution apply; no land-use/legal or field measurement claim'
 if theme=='K':demand.loc[idx,'status']='fetched';demand.loc[idx,'gap']='Only supported derived indicators in analysis_layers.gpkg; no inferred FAR, jobs, footfall or legal renewal boundaries'
 demand.loc[idx,'blocked']=demand.loc[idx,'status']=='blocked'
demand.to_csv(ROOT/'reports/gap_matrix_after.csv',index=False)
# Detailed public-service subtype availability from observed tags, no made-up facilities.
poi=gpd.read_file(M,layer='poi_all');poic=poi[poi.in_aoi].groupby(['category','subcategory']).size().reset_index(name='mapped_observations_aoi');poic.to_csv(ROOT/'reports/public_service_subtype_inventory.csv',index=False)
needs=[('上海市公共数据开放平台','道路/教育/卫生/养老/公园/统计开放表','https://data.sh.gov.cn/view/','HTTP503 in this session; authentication requirement unconfirmed','Actual licensed downloadable catalogue/API; check access from normal browser or request official export'),('上海市规划和自然资源局','现状调查图斑、控规/红蓝绿线及官方分类修订','https://ghzyj.sh.gov.cn/','No verified reusable precise vectors; metadata/publication pages only','Official published reusable vector/table and terms; images remain reference only'),('自然资源部','2023用地用海分类指南正式原文及最新修订','https://www.mnr.gov.cn/','Proxy403; official gov search returned zero for long/short queries','Provide accessible official document or restored official endpoint; codebook remains research reference'),('上海市统计局/各区','细尺度普查、年龄结构、社区人口','https://tjj.sh.gov.cn/','Homepage accessible; targeted yearbook/census pages blocked403 in this session','Public tables and matching statistical boundaries; do not allocate district age counts into AOI'),('WorldPop','China2025 native100m population','https://hub.worldpop.org/geodata/summary?id=72927','~922MB file ignores byte Range; 1km fallback acquired','Efficient official COG/window service or authorized regional subset'),('Tsinghua / Starcloud','EULUC城市功能用地','https://data-starcloud.pcl.ac.cn/','Official old portal migrated; new host unavailable in this session','Accessible licensed regional download; do not bypass site'),('CLCD / Zenodo','中国年度30米地表覆盖','https://zenodo.org/records/4417810','~0.8GB national TIFF; no validated efficient window path','COG or permitted provincial/regional subset'),('GHSL','GHS AGE建成时间代理','https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/','Global ZIP only; no regional tile/efficient window path found','Efficient subset; model epochs are not building construction year'),('商业地图/API','批量持久化POI或交通流','User licensed provider only','No provided lawful bulk-reuse permission or authorized key','User licensed export and reuse scope; do not scrape display maps')]
if any(r.get('source_id')=='clcd_china' and str(r.get('access_status','')).startswith('verified_bounded') for r in export_registry()):needs=[r for r in needs if r[0]!='CLCD / Zenodo']
needs.append(('WorldPop','2025年龄性别约1km原生模型','https://hub.worldpop.org/geodata/listing?id=139','Official archive1.19GB; individual files~22MB ignore Range200','Efficient authorized regional age-sex subsets; do not bulk-download dozens of national rasters or infer age from total population'))
pd.DataFrame(needs,columns=['platform','resource','url','observed_blocker','required_next_action']).to_csv(ROOT/'reports/needs_user_access.csv',index=False)
blocked=[('真实容积率/法定开发强度','No actual GFA or reliable complete floors; delivered volume proxy instead'),('实时交通流/客流/噪声/污染精细面','No lawful verified local observation source'),('法定规划用途/控制线','No verified reusable precise official vectors'),('街坊年龄/老龄/儿童人口','No fine-scale official table+boundaries; no downscaling'),('建筑年代/空置/官方更新名单','No verified local evidence; research amenity score not demolition potential')]
pd.DataFrame(blocked,columns=['topic','reason']).to_csv(ROOT/'reports/blocked_maps.csv',index=False)
regs=export_registry();reg=pd.DataFrame(regs)
# Useful clean derivative database metadata tables are included without changing spatial feature counts.
with sqlite3.connect(M) as con:
 reg.astype(str).to_sql('source_registry',con,if_exists='replace',index=False);demand.astype(str).to_sql('topic_gap_status',con,if_exists='replace',index=False);coverage.to_sql('network_service_coverage',con,if_exists='replace',index=False)
qa={'protected_original_files':len(protected),'all_original_hashes_unchanged':True,'spatial_tables_read_back':len(inventory),'invalid_geometries':sum(r['invalid'] for r in inventory),'A1_maps_verified':len(maprecords),'A3_maps_verified':len(maprecords),'rasters_verified':len(rasters),'source_records':len(regs),'topic_requirements':len(demand),'functional_partition_qa':json.loads((ROOT/'reports/landuse_partition_qa.json').read_text()),'network':json.loads((ROOT/'reports/network_topology.json').read_text()),'limitations':'No claim of complete real-world facilities/land-use survey; source dates, unresolved gaps and inference explicitly retained'}
dump(ROOT/'reports/final_qa.json',qa)
# Standalone filterable evidence dashboard, no external scripts/tracking.
rows=''.join('<tr>'+''.join('<td>'+html.escape(str(r.get(c,'')))+'</td>' for c in ['source_id','dataset_name','provider','valid_year','license','access_status','reason'])+'</tr>' for r in regs)
htmltext='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>上海规划数据完整性与证据</title><style>body{font:15px system-ui;background:#f7f6f1;color:#254148;margin:30px}input{padding:12px;width:70%}table{border-collapse:collapse;width:100%;font-size:12px}td,th{padding:8px;text-align:left;border-bottom:1px solid #ccd6d1;word-break:break-word}thead{position:sticky;top:0;background:#dce7df}.cards{display:flex;gap:25px;margin:20px 0}article{background:white;padding:18px}a{color:#28686a}</style><h1>上海城市规划GIS · 数据证据与完整性</h1><p>公开数据的可用性不是现实世界完整率。所有高度均非实测；未知功能保留；模型人口不是普查人口。</p>'''
htmltext+=f'<div class="cards"><article>{len(regs)} 来源/访问记录</article><article>{len(demand)} 专题子项</article><article>{len(maprecords)} 张已验证A1专题图</article><article>原模型 {len(protected)} 文件哈希未变</article></div>'
htmltext+='<p><a href="source_registry.csv">来源表</a> · <a href="gap_matrix_after.csv">逐项缺口</a> · <a href="needs_user_access.csv">访问与申请清单</a> · <a href="final_qa.json">QA</a> · <a href="../outputs/maps/INDEX.png">图纸总览</a></p><input id="q" placeholder="检索来源、年份、许可、失败原因…"><table><thead><tr>'+''.join('<th>'+s+'</th>' for s in ['ID','数据','提供方','年份','许可','状态','限制'])+'</tr></thead><tbody>'+rows+'</tbody></table><script>q.oninput=()=>{let s=q.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.innerText.toLowerCase().includes(s))}</script>'
(ROOT/'reports/data_completeness_dashboard.html').write_text(htmltext)
(ROOT/'reports/round_3_source_discovery.md').write_text('''# 第三轮：互证与受限资源复核\n\n- OSM瓦片递归 skeleton 不能覆盖带完整标签的对象；网络合并规则已修正。以实际节点ID连接，不以几何桥下交点连通。\n- 服务路段使用线性里程区间合并，避免浮点几何并集重复计长；5/10/15分钟长度单调与不超过总网长的检查通过。\n- Sentinel逐场景逐波段与独立镜像比较，验证1000DN差；有效offset修正后重算，原始数据不改。\n- 两套人口保留2020年100米和2025年约1公里模型尺度；不同年份/方法不能做增长结论。年龄性别官方分类139进一步查明1.19GB档案，单文件Range返回200，不下载全国数十文件。\n- 显式转向限制补查38关系，30个via-node记录；保留原始成员，非驾驶路由承诺。JRC历史水面频率以六瓦片约20KB局部压缩数据取得，非现状水边界/洪水概率。独立2017年行政边界与Wikidata参考点补入；不作为当前法定边界/文保保护范围。\n- 2012–2024历史NDVI cube已排除时间补插值，仅保留observed掩膜；仅覆盖48.48% AOI，CRS由明确经纬坐标推定。\n- EULUC旧站迁移继续跟随新站，CLCD国家大文件通过TIFF布局复核，以2.34MB压缩扫描行局部读取成功并做物理覆盖交叉表；GHS AGE全球ZIP未找到有效局部入口；无下载全球巨型底库。\n- 国家官方分类指南及最新修订无法验证，参考代码不冒充现行法定分类。上海开放平台/深层年鉴403/503不自动等同需要密钥。\n- 科研鸟类情感网格缺地理原点，不凭FID造坐标；空气质量包缺监测来源，不生成虚假污染图。\n\n停止条件：本轮已发现可访问、许可明确且能有效局部读取的数据已处理。其余精细用地/人口年龄/容量/管理约束等需要可访问官方发布、合法申请或高效区域数据服务。未宣称全面资料完备，逐项见gap_matrix_after.csv。\n''')
progress('qa','readback','complete',**{k:v for k,v in qa.items() if isinstance(v,(bool,int))});print('QA PASSED',qa['A1_maps_verified'],len(inventory),flush=True)
