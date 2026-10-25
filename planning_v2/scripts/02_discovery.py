"""Whole-topic demand catalogue and real, recorded public-source discovery rounds."""
import concurrent.futures
import json
from urllib.parse import quote
from common import *

TOPICS={
'A_空间底图与形态':'街道行政边界|社区居委边界|街坊与地块|宗地公开资料|门牌地址|地名|建筑轮廓|建筑高度|建筑层数|建筑用途|建筑体量|建设年代|住宅小区|楼宇园区名称|建筑入口|地下与高架线索|历史航空遥感|地形高程',
'B_土地利用与覆盖':'现状用地图斑|法定规划用途|建筑园区功能|工业仓储|教育医疗用地|商业商务用地|居住用地|绿地林地|公共开敞空间|空地|停车场|硬质地面|湿地|裸地|农用地|水域水利|交通用地|工地|地表覆盖',
'C_交通与活动':'快速路主干次干支路|园区内部与服务道路|道路面与路宽|真实同层交叉口|转向限制|单行方向|桥隧及上下层|过街通道|人行道|骑行设施|无障碍通道|公交线路|公交站点|轨道线路|轨道车站|轨道出入口|慢行阻隔|公共停车设施|停车入口|公交场站|出租共享单车|公开交通流量|通勤节点',
'D_公共服务':'幼儿园|小学|中学|高校|职业教育|教育培训|综合医院|专科医院|社区卫生|药店|养老机构|日间照料|托育|儿童友好设施|文化馆|图书馆|博物馆|影剧院|社区活动中心|体育馆|室外球场|政务服务|公共厕所|垃圾分类站|快递柜驿站|菜市场|超市|生鲜|便利店|餐饮|银行|消防站|避难场所',
'E_功能产业与活力':'办公企业机构|研发创新|科技园区|工业仓储机构|商业综合体|商场零售|酒店旅宿|餐饮金融|夜间消费|生活服务|文化休闲|公共空间节点|POI业态|职住代理',
'F_人口与住房':'统计年鉴|普查单元统计|人口栅格|常住与模型人口区分|人口密度|年龄结构|老龄化|儿童人口|居住空间|住房类型|住房年代|社区服务人群',
'G_蓝绿生态':'公园边界|公园出入口|城市绿地|居住区绿地|道路绿化|树冠覆盖|街道树|河渠湖塘|河岸护岸|湿地|岸线|生态廊道|NDVI|NDWI|NDBI|植被季节变化|绿地破碎度|不透水地表|滨水公共空间|生态敏感区',
'H_环境与韧性':'Sentinel光学影像|Landsat热红外|卫星地表温度|热岛代理|高程与坡度|公开排水资料|易涝公共信息|洪涝灾害暴露|通风廊道代理|遮阴绿荫代理|空气监测站|噪声监测站|道路影响|气象再分析',
'I_历史文化与更新':'历史街区|文保单位|优秀历史建筑|旧工业厂房|官方老旧小区|存量更新项目|城市更新政策|建设项目公示|历史用地变化|历史影像|街区演变|空置低效利用线索',
'J_规划管理约束':'国土空间规划|控制性详细规划|法定规划用途|公共绿地控制|蓝线|道路红线|历史风貌保护范围|城市开发边界|建设项目公示|交通绿地海绵防灾专项|强制控制指标|最新版用地用海分类',
'K_分析辅助':'分析街坊|500米网格|土地利用结构|建筑密度|体量强度代理|车行路网密度|步行骑行网络|真实同层交叉口密度|公交可达路段|15分钟服务网络|公园入口可达性|功能混合熵|POI点密度|人口与服务缺口|蓝绿连通|更新机会研究指标|重点设计区对比'
}
SOURCES=[
('sh_open','A B C D E F G H I J','上海公共数据开放平台','上海市','https://data.sh.gov.cn/view/','government'),
('sh_gov','A B D E F G H I J','上海市人民政府公开信息','上海市人民政府','https://www.shanghai.gov.cn/','government'),
('sh_planning','A B I J','上海规划自然资源公开规划','上海市规划和自然资源局','https://ghzyj.sh.gov.cn/','government'),
('sh_stats','F E','上海统计局统计与年鉴','上海市统计局','https://tjj.sh.gov.cn/','government'),
('sh_transport','C','上海交通设施公开信息','上海市交通委','https://jtw.sh.gov.cn/','government'),
('sh_health','D F','上海卫生机构公开名录','上海市卫健委','https://wsjkw.sh.gov.cn/','government'),
('sh_education','D','上海教育机构名录','上海市教委','https://edu.sh.gov.cn/','government'),
('sh_green','G H','上海绿化公园信息','上海市绿化市容局','https://lhsr.sh.gov.cn/','government'),
('sh_housing','A F I','上海建设住房与更新信息','上海市住建委','https://zjw.sh.gov.cn/','government'),
('sh_environment','G H','上海生态环境监测信息','上海市生态环境局','https://sthj.sh.gov.cn/','government'),
('sh_culture','D I','上海文化旅游历史资源','上海市文旅局','https://whlyj.sh.gov.cn/','government'),
('jingan','A D F I J','静安区公开数据','静安区人民政府','https://www.jingan.gov.cn/','government'),
('baoshan','A D F I J','宝山区公开数据','宝山区人民政府','https://www.shbsq.gov.cn/','government'),
('hongkou','A D F I J','虹口区公开数据','虹口区人民政府','https://www.shhk.gov.cn/','government'),
('sh_tdt','A C J','天地图上海公开服务与使用条件','天地图上海','https://qucity.shanghai-map.net/','government_service'),
('mnr','A B J','用地用海分类与自然资源公开资料','自然资源部','https://www.mnr.gov.cn/','government'),
('nbs','F E','国家统计局人口与普查','国家统计局','https://www.stats.gov.cn/','government'),
('mee','G H','生态环境公开监测目录','生态环境部','https://www.mee.gov.cn/','government'),
('mwr','G H','水利公开资料','水利部','https://www.mwr.gov.cn/','government'),
('worldpop','F','WorldPop人口栅格目录','WorldPop','https://hub.worldpop.org/','scientific_raster'),
('worldpop_data','F','WorldPop公开栅格数据','WorldPop','https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/CHN/chn_ppp_2020_UNadj.tif','scientific_raster'),
('ghsl','A F','GHSL人口建成区体量年代','European Commission JRC','https://human-settlement.emergency.copernicus.eu/datasets.php','scientific_raster'),
('ghsl_data','A F','GHSL官方开放数据目录','European Commission JRC','https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/','scientific_raster'),
('worldcover','B G','ESA WorldCover 10m 2020/2021','ESA','https://esa-worldcover.org/en/data-access','scientific_raster'),
('worldcover_cog','B G','WorldCover2021研究区所在COG','ESA','https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N30E120_Map.tif','scientific_raster'),
('earthsearch','B G H','Earth Search STAC Sentinel/Landsat','Element84 / USGS / Copernicus','https://earth-search.aws.element84.com/v1/collections','remote_sensing'),
('planetary','A B F G H','Planetary Computer STAC公开产品','Microsoft / data providers','https://planetarycomputer.microsoft.com/api/stac/v1/collections','remote_sensing'),
('copernicus','G H','Copernicus Data Space访问方式','Copernicus','https://dataspace.copernicus.eu/','remote_sensing'),
('cdse_stac','G H','Copernicus官方STAC目录','Copernicus','https://stac.dataspace.copernicus.eu/v1/collections','remote_sensing'),
('dynamicworld','B G','Dynamic World10m概率土地覆盖','Google / WRI','https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1','remote_sensing'),
('surfacewater','G H','JRC Global Surface Water历史水域','European Commission JRC','https://global-surface-water.appspot.com/download','scientific_raster'),
('earthdata','G H','NASA CMR遥感专题目录','NASA','https://cmr.earthdata.nasa.gov/search/collections.json?keyword=land%20surface%20temperature&page_size=5','scientific_catalog'),
('geoboundaries','A F','geoBoundaries中国行政区边界元数据','geoBoundaries','https://www.geoboundaries.org/api/current/gbOpen/CHN/ADM2/','open_geography'),
('wikidata','D I','Wikidata公共地理资源','Wikimedia','https://query.wikidata.org/','open_knowledge'),
('geofabrik','A C D','Geofabrik中国OSM开放数据目录','Geofabrik','https://download.geofabrik.de/asia/china.html','open_geography'),
('overture_root','A B C D E F G I','Overture全主题目录','Overture Maps Foundation','https://stac.overturemaps.org/catalog.json','open_geography'),
('overture_docs','A B C D E G','Overture官方说明与许可','Overture Maps Foundation','https://docs.overturemaps.org/getting-data/','open_geography'),
('zenodo','A B C D F G H I','Zenodo公开研究数据目录','CERN / research providers','https://zenodo.org/api/records?q=Shanghai%20geospatial&size=5','scientific_catalog'),
('openmeteo','H','ERA5-Land再分析访问说明','Open-Meteo / Copernicus','https://open-meteo.com/en/docs/historical-weather-api','scientific_raster'),
('copdem_registry','A H','Copernicus DEM公开数据许可及访问','AWS Open Data Registry','https://raw.githubusercontent.com/awslabs/open-data-registry/main/datasets/copernicus-dem.yaml','scientific_catalog'),
]
def initialize():
    existing={'建筑轮廓':'buildings','建筑高度':'buildings (all heights estimated)','建筑层数':'23 OSM floor-tag based buildings only','建筑体量':'estimated height proxy only','道路面与路宽':'road_surfaces; widths partly inferred','城市绿地':'greens','河渠湖塘':'water','街道树':'mapped_trees','高程与坡度':'only schematic road heights, not DEM','地表覆盖':'two generalized urban polygons, not detailed land cover'}
    rows=[]
    for theme,items in TOPICS.items():
        for item in items.split('|'):
            sources=[s[0] for s in SOURCES if theme[0] in s[1].split()]
            rows.append({'theme':theme,'item':item,'status':'existing' if item in existing else 'searchable','needed':True,'existing_evidence':existing.get(item,''),'candidate_sources':';'.join(sources),'government_search':False,'open_geography_search':False,'scientific_or_remote_search':False,'fetched':False,'verified':False,'blocked':False,'no_source':False,'not_applicable':False,'gap':'No verified completeness claim; inspect raw attributes and additional sources','planning_value':'Supports factual inventory, context or transparently inferred planning analysis'})
    pd.DataFrame(rows).to_csv(ROOT/'reports/data_demand_catalog.csv',index=False)
    pd.DataFrame(rows).to_csv(ROOT/'reports/gap_matrix.csv',index=False)
    for source_id,cats,title,provider,url,family in SOURCES:
        register(source_id,category=cats,dataset_name=title,provider=provider,url=url,family=family,access_status='discovered_not_yet_probed',reuse_allowed='unknown_until_terms_checked',license='not_yet_verified',api_registration_needed='to_check',notes='A discovered public endpoint is not proof of data availability or reuse rights',round=1)
    export_registry();progress('source_search','demand_catalog','generated',subtopics=len(rows),providers=len(SOURCES))

def probe_one(record,round_number):
    source_id,cats,title,provider,url,family=record
    if source_id in ('worldpop_data','worldcover_cog'):  # range metadata, never GET whole global raster
        try:
            response=SESSION.get(url,headers={'Range':'bytes=0-16383','Accept-Encoding':'identity'},timeout=25,stream=True)
            if response.status_code==206:
                data=response.raw.read(16384)
                path=ROOT/'cache/source_discovery'/f'{source_id}_header.bin';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                register(source_id,access_status='range_metadata_fetched',local_path=str(path.relative_to(ROOT)),checksum=sha(path),format='GeoTIFF',round=round_number)
                attempt(source_id,round_number,'range_success',response.headers.get('Content-Range'))
            else:
                status='range_not_supported' if response.ok else 'blocked_http_'+str(response.status_code)
                register(source_id,access_status=status,reason=f'Range probe HTTP {response.status_code}; full raster download not attempted',round=round_number)
                attempt(source_id,round_number,status,safe_url(url))
            response.close()
        except Exception as exc:register(source_id,access_status='request_failed',reason=str(exc)[:700],round=round_number);attempt(source_id,round_number,'request_failed',str(exc)[:700])
    else:request_public(source_id,url,ROOT/'cache/source_discovery'/f'{source_id}.txt',round_number=round_number,timeout=22)
    return source_id
def probe(round_number):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for source_id in pool.map(lambda s:probe_one(s,round_number),SOURCES):print('PROBED',source_id,flush=True)
    records=export_registry()
    lines=[f'# 第{round_number}轮：全主题元数据与可访问性探测','', '本轮仅把真实返回结果作为证据；网站首页成功不等于专题已下载，网络阻断不等于数据不存在。','']
    for row in records:lines.append(f'- {row["source_id"]}：{row.get("access_status")}；{row.get("reason") or "需继续核查专题内容、许可与AOI贡献"}；{row.get("url")}')
    (ROOT/f'reports/round_{round_number}_source_discovery.md').write_text('\n'.join(lines))
    progress('source_search',f'round_{round_number}','metadata_probed',sources=len(records))
if __name__=='__main__':
    import sys
    if not (ROOT/'reports/data_demand_catalog.csv').exists():initialize()
    probe(int(sys.argv[1]) if len(sys.argv)>1 else 1)
