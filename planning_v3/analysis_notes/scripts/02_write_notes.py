"""Map-specific planning interpretation from traceable read-only evidence.

Each note separates observations, regional coordination and conditional actions.
No zoning, service capacity, survey height or causal conclusion is invented.
"""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[1];V=P.parent
E=json.loads((P/'reports/spatial_evidence.json').read_text());S=E['zones']['site'];N=E['zones']['near500'];R=E['zones']['region']
def pct(x):return f'{100*x:.1f}%'
def ras(z,n,k='mean'):return z['raster'][n][k]
def acc(z,k,m=15):return pct(z['access'][k][str(m)])
notes={}
def add(i,site,region,action,keys):
    notes[i]={'site_problem':site,'regional_coordination':region,'improvement_direction':action,'evidence_keys':keys,
        'interpretation_status':'Observations are source-limited; actions are research proposals, not approved projects.'}

add('01',f"设计区只有{pct(S['known_function_fraction'])}面积有已映射功能依据，低于全域{pct(R['known_function_fraction'])}。当前主要问题是功能底数不完整，无法据图判断未知地块为空置、低效或可直接置换。",
    f"周边500米环带已映射商业、居住和公共服务用地，已知功能覆盖{pct(N['known_function_fraction'])}。设计地块应放在既有居住—就业—服务关系中理解，避免按红线构造自给封闭单元。",
    '先核对地块用途、经营状态和开放入口，再沿江场西路、万荣路评估可共享的首层服务与公共空间；以真实需求补短板，形成与周边既有功能的互补。',
    ['known_function_fraction','mapped_function_area_fraction','longest_mapped_roads'])
add('02',f"建筑轮廓并集覆盖设计区{pct(S['building_union_fraction'])}，高于全域{pct(R['building_union_fraction'])}；触及地块的100米图示单元中，≥40%高值部分约占地块{pct(S['grid100']['high_density_fraction'])}，内部疏密不均。",
    f"周边环带覆盖率为{pct(N['building_union_fraction'])}。地块需兼顾自身较密集的建筑基底与周边街区连续性，不能仅用全域平均值确定每一处的增减量。",
    '优先实查高覆盖单元的日照、消防、院落和通道，沿街道与开敞节点梳理可连通空间；通过局部退让、入口整合和共享院落改善环境，建设强度须另核法定条件。',
    ['building_union_fraction','grid100.high_density_fraction'])
add('03',f"设计区相交建筑记录{S['building_records_intersecting']}条，但全部高度来自默认或层数推算。图面高度同质或突变不能作为真实天际线、日照遮挡和高低建筑关系的可靠结论。",
    '区域高度图可帮助安排建筑复核次序，尚不足以确认地块与周边的高度协调问题。沿江场西路、万荣路和共和新路界面的实际建筑层数与街道断面应统一调查。',
    '补测高度、层数、用途和建筑间距后，再研究沿街尺度、重要开敞空间边缘的高度过渡与视线关系；当前保留空间协调议题，不提出具体控高数值。',
    ['building_records_intersecting','definition.height'])
add('04',f"设计区估高体量代理为{S['estimated_volume_proxy_m']:.2f}米³/米²，高于全域{R['estimated_volume_proxy_m']:.2f}；它反映轮廓与估高叠加，不能解释为实测建筑面积、容积率或确定的开发容量。",
    f"周边环带同口径约为{N['estimated_volume_proxy_m']:.2f}米³/米²。地块应结合较高的基底占用，协调内部开放空间与周边街道界面，而非按单一体量指标推导增建任务。",
    '先复核建筑真实高度、面积和使用效率，再联动交通承载、日照与公共空间需求比较存量优化方案；新体量应服务于街区关系改善，具体规模另行论证。',
    ['estimated_volume_proxy_m','building_union_fraction','definition.height'])
add('05',f"设计区建筑基底覆盖{pct(S['building_union_fraction'])}，其余图底白地包含道路、水面、院落及未分类空间，不能直接视为可建设用地。痛点在于需要辨明开敞空间是否真正连续、开放和可进入。",
    '江场西路、万荣路等通道穿联地块与周边街区。图底关系应同时检查沿街连续界面和跨边界步行联系，而不是只优化红线内部的形式构图。',
    '逐处核对围墙、门禁与通道，优先连接合法开放的院落和街角空间；在有权属及安全条件的界面补足步行联系，保留必要的生产、后勤与消防空间。',
    ['building_union_fraction','longest_mapped_roads','open_spaces_records_intersecting'])
add('06',f"设计区已知功能面积仅{pct(S['known_function_fraction'])}；触及地块的29个200米图示单元中，只有{S['grid200']['entropy_eligible_cells']}个有有效混合度值。低覆盖空值不能被解释为单一功能或缺乏活力。",
    f"全域功能证据覆盖{pct(R['known_function_fraction'])}，周边环带为{pct(N['known_function_fraction'])}。应核查地块与周边居住、商业及公共服务之间的使用联系，避免因数据详略不同误判功能差距。",
    '开展首层用途、经营时间与人群活动调查，先补齐混合功能证据；再选择合适街道节点引入互补服务及可分时共享空间，不以提高熵值本身作为设计目标。',
    ['known_function_fraction','grid200.entropy_eligible_cells','definition'])
add('07',f"设计区记录约{S['vehicle_length_m']/1000:.2f}公里车行源线，包含江场西路、万荣路及南北高架路等层级。线网存在不等于地面步行可穿越，高架与主路界面是需优先核对的衔接位置。",
    '全域共和新路、场中路等承担跨片区联系；地块需区分区域通行、片区集散和内部到达，避免将区域道路负担简单转入内部生活空间。',
    '核实车流、出入口、过街条件与高架下空间，组织清晰的到达层级、连续人行与后勤路线；改善方向以安全接入和街道协同为先，不凭模型新增道路。',
    ['vehicle_length_m','longest_mapped_roads'])
add('08',f"设计区车行源线密度{S['vehicle_density_km_km2']:.2f}公里/平方公里、真实源节点{S['mapped_vehicle_nodes']}处；密度高于全域{R['vehicle_density_km_km2']:.2f}，不能据此直接认定交通畅通或过街便捷。",
    f"邻近环带密度{N['vehicle_density_km_km2']:.2f}。区域与地块更需共同处理路口衔接、分层道路和边界通行，而非单纯追求更密集的中心线。",
    '围绕江场西路—万荣路等实际路口复核转向、行人等待与无障碍衔接，优先改善关键节点；新增连接需核实权属、交通影响及真实通行条件。',
    ['vehicle_density_km_km2','mapped_vehicle_nodes','longest_mapped_roads'])
add('09',f"按已映射步行网络，设计区{acc(S,'transit',5)}的路段长度可在5分钟内接入已记录公交节点，10分钟为{acc(S,'transit',10)}。总体接入基础较好，不能将其写成居民覆盖率或运力充足结论。",
    f"全域5分钟同口径为{acc(R,'transit',5)}。可结合源标注的江场西路原平路等公交节点，组织由周边公共交通进入地块的连续步行界面，而不重复建设封闭接驳体系。",
    '实查站台、道路两侧过街、入口开放时间与无障碍设施，把“最后一段”接入纳入地块和道路的联合设计；班次、客流和站点承载另以运营资料校核。',
    ['access.transit','named_resources_near500.transit_stations'])
add('10',f"已记录日常服务的15分钟可达路段占设计区步行网{acc(S,'daily_service')}，低于全域{acc(R,'daily_service')}。但全域该类观察点仅{R['poi_observations']['daily_service']}条，现图首先显示记录接入偏弱，不能证明真实服务缺失。",
    '应把地块与江场西路、万荣路及周边居住片区的服务网共同核对，区分“已有服务但入口难达”与“实际需求未被满足”，避免在红线内机械配齐全部功能。',
    '补查便利商业、餐饮及社区服务清单、开放时间和真实需求；若短板被证实，优先在公共路径交汇处配置可面向周边使用的小尺度服务，并同步改善步行接入。',
    ['access.daily_service','poi_observations.daily_service'])
add('11',f"设计区只有{S['poi_observations']['commercial']}条商业观察点，周边500米环带有{N['poi_observations']['commercial']}条。记录稀疏不能解释为无商业、低消费需求或确定的商业空白地段。",
    '商业组织应结合江场西路与万荣路的人行联系、周边既有商业和居住需求，研究地块首层服务的互补角色，而非按POI热度复制区域商业中心。',
    '实查店铺、空置、营业时段与实际客流，识别可接续的服务街段；优先利用适宜的沿街首层和共享节点试点经营，规模及业态待需求和运营验证后确定。',
    ['poi_observations.commercial','longest_mapped_roads'])
add('12',f"设计区没有教育POI记录，但已有教育节点的15分钟步行可达路段占比为{acc(S,'education')}。这表明不能以红线内点位为空就认定缺校，图中也不包含学位容量和入学资格。",
    f"周边环带有{N['poi_observations']['education']}条教育设施记录，包括源标注的田家炳小学、永和小学等。地块可协调周边学校的接入环境，是否共享场地须由学校与管理条件确认。",
    '联合核查校门位置、接送流线、交通冲突、通学安全及设施容量，优先改善地块至周边教育资源的连续步行路线；不凭可达线网判断学位是否满足。',
    ['access.education','poi_observations','named_resources_near500.poi_education'])
add('13',f"设计区已映射绿地约{pct(S['mapped_green_fraction'])}、水面约{pct(S['mapped_water_fraction'])}；全域同口径分别为{pct(R['mapped_green_fraction'])}和{pct(R['mapped_water_fraction'])}。资源相对集中，但图面不能证明岸线开放、生态质量或公共可用性。",
    '可把地块水绿界面与周边半里绿廊、彭浦公园及静安青年体育公园等资源作为协同研究对象，重点核查连续路径、入口和道路阻隔，而非把各绿块孤立布置。',
    '优先保护已有水绿资源，补查河道管理、岸线安全、绿地权属和开放时段；在条件允许处接续遮荫步道、街角绿地与滨水节点，形成对周边居民可用的空间网络。',
    ['mapped_green_fraction','mapped_water_fraction','named_resources_near500.green_parks'])
add('14',f"已映射公园节点5分钟可达路段占设计区步行网{acc(S,'parks',5)}，10分钟为{acc(S,'parks',10)}。接近绿地的优势较明显，但图中不反映入口真实性、场地容量、开放时段与活动设施质量。",
    f"全域5分钟同口径为{acc(R,'parks',5)}，邻近环带为{acc(N,'parks',5)}。地块可作为衔接周边公园与街区的节点，发挥资源协同作用，而非只增加内部绿化面积。",
    '核实彭浦公园、青年体育公园及近邻绿廊的真实接入口，接续可公开通行的步道；根据实际人群需求补充休憩、健身和无障碍设施，避免重复设置同质空间。',
    ['access.parks','named_resources_near500.green_parks'])
add('15',f"设计区有效部分的公共环境初筛均值{S['grid100']['priority_score']['mean']:.3f}，与全域{R['grid100']['priority_score']['mean']:.3f}接近；地块约{pct(S['grid100']['priority_score']['valid_weight']/S['area_m2'])}面积有有效值，不能据此把整块定为全域最紧迫对象。",
    '应将局部高值与周边街道、绿地及服务接入共同核对。密度、已映射绿地不足和服务接入三项等权指标，只支持调研排序，不代表真实需求、公共投资收益或既定项目清单。',
    '优先实查高值单元的通行、遮荫、休憩和服务接入口，选择能同时改善地块与相邻街区的小尺度工程；补充权属、使用人群及实施成本后再确定项目顺序。',
    ['grid100.priority_score','definition.access'])
add('16',f"设计区有{S['road_dangling_review_records_intersecting']}处源网络端点复核位置、{S['road_building_conflicts_records_intersecting']}处道路面与建筑叠置记录。这些可能来自数据缺口、估算路宽或真实边界条件，不能直接认定断头路或实体冲突。",
    '问题核查应沿设计边界向周边道路延伸，关注江场西路、万荣路和高架界面的入口与分层关系；仅在红线内修图，可能掩盖跨边界的真实衔接条件。',
    '建立现场复核清单，逐项记录能否通行、道路实宽、建筑边界和门禁；证实后再完善慢行接续或路口组织。示意坡度记录不作为地形、排水或工程整改依据。',
    ['road_dangling_review_records_intersecting','road_building_conflicts_records_intersecting','road_schematic_steep_review_records_intersecting'])
add('17',f"2020年模型人口密度在设计区的面积加权均值约{S['population_ghsl2020']['mean']/10000:.2f}万人/平方公里；周边环带约{N['population_ghsl2020']['mean']/10000:.2f}万。周边模型密度更高，提示公共空间可能承接跨边界需求，而非仅服务地块内。",
    f"全域同口径约{R['population_ghsl2020']['mean']/10000:.2f}万人/平方公里。应结合较密集的近邻居住区组织服务与步行联系，但历史模型不能确定当前常住、就业、昼夜或流动人口。",
    '补充现况人口与实际活动调查，按人群和时段校核休憩、通学及日常服务容量；研究对周边开放的空间和设施，避免把模型数值直接换算成确定的建设规模。',
    ['population_ghsl2020'])
add('18',f"2025年人口模型在设计区的面积加权均值约{S['population_worldpop2025']['mean']/10000:.2f}万人/平方公里，触及{S['population_worldpop2025']['intersecting_native_cells']}个原生约1公里单元。像元大于多数设计细部，不能据图定位具体楼栋或街角需求。",
    f"全域同口径约{R['population_worldpop2025']['mean']/10000:.2f}万人/平方公里，与地块总体接近。宜用于片区服务协同的背景判断；与2020年产品来源和尺度不同，不作人口增减结论。",
    '按现况居民、就业者和到访者补查活动分布，再协调周边服务、通行与公共空间容量；保留原生模型单元，不把公里级数值拆细成看似精确的设计指标。',
    ['population_worldpop2025'])
add('19',f"2021年10米地表覆盖产品中，建成类占设计区有效面积{pct(ras(S,'worldcover2021_10m','class_fraction_of_valid').get('50',0))}，高于全域{pct(ras(R,'worldcover2021_10m','class_fraction_of_valid').get('50',0))}。它说明建成背景突出，不能区分具体屋顶、道路与透水铺装。",
    '地块与周边均处于连续建成环境，蓝绿改善应跨街区接续。分类中的水面、植被与现状矢量存在尺度差异，不能仅据10米类别决定岸线和小绿地边界。',
    '结合现场铺装、树冠和水面核查，优先在可实施的硬化界面增设遮荫、透水及雨水调蓄设施；把地块改造与周边道路绿化衔接，具体工程参数另行勘察。',
    ['raster.worldcover2021_10m','mapped_green_fraction','mapped_water_fraction'])
add('20',f"2026年9月14日夏季NDVI面积加权均值：设计区{ras(S,'ndvi_summer2026_10m'):.3f}、全域{ras(R,'ndvi_summer2026_10m'):.3f}；地块有效像元覆盖{pct(ras(S,'ndvi_summer2026_10m','valid_area_fraction'))}。地块植被光谱信号偏弱，空值不能当作裸地。",
    f"周边环带同景均值{ras(N,'ndvi_summer2026_10m'):.3f}。宜将地块绿化与周边街道树冠和绿廊连续研究，避免只在局部集中植绿而沿步行路径仍缺少遮荫。",
    '现场核查树冠、种植条件和缺绿界面，优先接续江场西路—万荣路等公共路径的遮荫；保护既有植被并选择适地补植，不以单景NDVI直接认定绿化率或植物健康。',
    ['raster.ndvi_summer2026_10m'])
add('21',f"2026年2月21日冬季NDVI均值为设计区{ras(S,'ndvi_winter2026_10m'):.3f}、周边环带{ras(N,'ndvi_winter2026_10m'):.3f}、全域{ras(R,'ndvi_winter2026_10m'):.3f}。地块冬季光谱绿量相对较弱，但不能从指数直接识别树种或确定养护问题。",
    '冬季环境品质应沿公共路径与邻近绿廊共同考虑。地块内部种植与周边街道绿化宜在季相、视线、采光和步行舒适性上协调，而非只追求夏季效果。',
    '调查现有常绿和落叶树种、树冠及冬季日照，因地制宜配置混合植被与挡风休憩点；保留冬季采光通道，避免在需要日照的界面机械加密常绿植物。',
    ['raster.ndvi_winter2026_10m'])
add('22',f"2026年8月1日单景地表温度均值：设计区{ras(S,'lst_summer2026_effective100m'):.1f}℃、周边{ras(N,'lst_summer2026_effective100m'):.1f}℃、全域{ras(R,'lst_summer2026_effective100m'):.1f}℃。地块并非整体更热；该值是100米尺度地表温度，不是人体感受的气温。",
    '地块的水绿资源可作为与周边建成街区协同改善热环境的研究基础，但单次观测不能证明降温因果、热岛强度或每个街角的舒适度。',
    '优先实测重要步行路径的遮荫、辐射、风和使用时段，再安排树荫休憩、适宜铺装与可安全使用的水绿界面；把降温路径向周边连续衔接，避免用单景温度规定工程指标。',
    ['raster.lst_summer2026_effective100m','mapped_green_fraction','mapped_water_fraction'])
add('23',f"30米表面高程产品在设计区的均值约{ras(S,'dsm_copernicus2021_30m'):.2f}米，与周边{ras(N,'dsm_copernicus2021_30m'):.2f}米接近。它含屋顶和植被影响，不能把图中微小起伏直接当作裸地地形或积水洼地。",
    '地块排水、滨水高程和道路衔接必须与周边管网、河道及控制标高统筹。当前DSM只能作为区域表面形态参照，不能判定跨边界汇流方向或防洪安全。',
    '补充地形测量、入口与道路高程、河道水位及排水资料后，再设计竖向、无障碍和雨水系统；保留现有基准，不依据粗DSM编造微地形或工程坡度。',
    ['raster.dsm_copernicus2021_30m'])
add('24',f"夏季NDWI均值为设计区{ras(S,'ndwi_summer2026_10m'):.3f}、全域{ras(R,'ndwi_summer2026_10m'):.3f}；设计区有效覆盖{pct(ras(S,'ndwi_summer2026_10m','valid_area_fraction'))}。负均值不表示无水，窄河道、阴影和混合像元均影响表达。",
    '图示光谱与矢量水面应交叉核对，关注地块水系与区域蓝绿通道的连续关系。不能用单一指数确定岸线开放程度、水质或水生态状况。',
    '先核查真实岸线、水面与桥下空间，结合管理和安全条件接续滨水步行及生态缓冲；水质、流量和水位另行监测，不按指数颜色直接安排水系改造。',
    ['raster.ndwi_summer2026_10m','mapped_water_fraction'])
add('25',f"夏季NDBI均值为设计区{ras(S,'ndbi_summer2026_20m'):.3f}、周边{ras(N,'ndbi_summer2026_20m'):.3f}、全域{ras(R,'ndbi_summer2026_20m'):.3f}。设计区相对偏高，但负值不能解释为非建成区，指数也不是建筑密度或透水率。",
    '应把地块与周边连续建成街区一并检查，结合建筑轮廓、植被和温度判断具体硬化界面；不同指标的分辨率与含义不同，不作直接一一对应。',
    '核实道路、屋顶与场地铺装后，优先改善公共路径的遮荫和可透水空间，并向相邻街段接续；不以NDBI高低直接划定拆改或新增建设范围。',
    ['raster.ndbi_summer2026_20m','building_union_fraction'])
add('26',f"2019年30米CLCD将设计区有效面积{pct(ras(S,'clcd2019_30m','class_fraction_of_valid').get('8',0))}标为不透水类，全域为{pct(ras(R,'clcd2019_30m','class_fraction_of_valid').get('8',0))}。粗分类说明历史建成背景，不能替代现状小尺度铺装调查。",
    '该图与2021年WorldCover的分类体系及精度不同，不能把差异解释为两年间绿地或水面变化。地块应在区域存量建成格局中研究修补，而非套用历史像元边界。',
    '对照现况资料确认仍然存在的硬化界面，联动周边道路与公共空间开展适度透水、植绿和连通优化；土地用途、工程透水率与实施范围均需另行核定。',
    ['raster.clcd2019_30m','raster.worldcover2021_10m'])
add('27',f"历史30米水面观测频率在设计区的面积加权均值接近0，而现状矢量水面占{pct(S['mapped_water_fraction'])}。这种明显不一致提示窄水道、时间范围或分类识别差异，不能判断水面消失、填埋或新增。",
    '地块水系必须放入周边真实河网、桥梁及管网关系中核查。历史水面频率不反映当前水位、河道连通、岸线可达性或内涝风险。',
    '以现况岸线和水务资料为主核对水系，保留可确认的蓝绿联系；在权属、防洪和水生态条件明确后研究连续岸线及步行节点，不依据低频像元削减水系空间。',
    ['raster.jrc_water_occurrence1984_2021_30m','mapped_water_fraction'])
add('28',f"2026年冬夏共同有效像元内，设计区NDVI季节差均值{ras(S,'ndvi_seasonal_difference2026_10m'):.3f}，周边{ras(N,'ndvi_seasonal_difference2026_10m'):.3f}。地块可见一定季相差异，但两景差值不代表年度增绿或植被退化。",
    '区域绿化协调应同时考虑地块与周边街道在不同季节的遮荫、采光和景观连续性。天气、物候、阴影和有效像元缺失均会影响图示差异。',
    '调查树种与季节使用需求，沿公共路径优化常绿—落叶搭配、林下休憩及冬季采光；用多时相观测和养护记录检验效果，不把单次差值直接转为种植数量目标。',
    ['raster.ndvi_seasonal_difference2026_10m','raster.ndvi_winter2026_10m','raster.ndvi_summer2026_10m'])

add('R01',f"设计区基底覆盖{pct(S['building_union_fraction'])}；图示100米单元中≥40%高值与低值空间并存，重点不是全区一律疏解，而是辨明密集建筑边缘的通行、日照和院落是否受限。",
    f"邻近环带覆盖{pct(N['building_union_fraction'])}。局部改善宜沿江场西路和万荣路衔接相邻街区，避免只在内部形成可见但不可进入的开敞空间。",
    '对高覆盖单元逐处调查入口、后勤和消防，争取合法开放的连通院落、街角退让与连续人行；细部以建筑和权属实测为准，100米格网不作为项目边界。',
    ['building_union_fraction','grid100.high_density_fraction','longest_mapped_roads'])
add('R02',f"设计区估高体量代理{S['estimated_volume_proxy_m']:.2f}米³/米²，周边{N['estimated_volume_proxy_m']:.2f}。局部高值可能主要由建筑基底占用造成，现有估高不足以支持真实高度梯度或容积率判断。",
    '应把地块建筑边缘、主街界面和近邻开敞空间一起研究，避免将粗略体量图直接转化为单侧增高或压低的设计要求。',
    '补测层数、面积、结构及现状用途，比较存量利用、界面修补与公共空间释放方案；以日照、通行和周边承载校核体量安排，不沿模型高值线直接划分建设任务。',
    ['estimated_volume_proxy_m','definition.height'])
add('R03',f"触及地块的29个200米图示单元仅{S['grid200']['entropy_eligible_cells']}个具有有效混合度；地块内功能证据覆盖{pct(S['known_function_fraction'])}。局部空值首先是证据不足，不能确定为单功能片区。",
    '周边可见居住、商业和公共服务功能，地块的改善应关注这些功能能否经公共路径相互服务，而不是以红线为界重复配置全部业态。',
    '逐建筑和首层补查用途、开放时间、经营与人群活动，沿实际可达节点评估互补服务及分时共享；先验证需求，再确定功能组合，不为提高指数而混合配置。',
    ['grid200.entropy_eligible_cells','known_function_fraction','mapped_function_area_fraction'])
add('R04',f"地块车行源线密度{S['vehicle_density_km_km2']:.2f}公里/平方公里，并有{S['mapped_vehicle_nodes']}处真实源节点。局部图强调节点位置，仍不能说明主路、高架上下空间和内部道路具有同等通行条件。",
    '江场西路、万荣路与共和新路等界面连接内部与区域道路，应将边界路口和跨街联系作为共同研究对象，区分区域车流和地块日常到达。',
    '逐个复核关键路口、过街与入口，协调人车分流、后勤及无障碍路线；只有在真实通行和交通安全条件得到证明后，才进一步设计新的连接。',
    ['vehicle_density_km_km2','mapped_vehicle_nodes','longest_mapped_roads'])
add('R05',f"地块内商业观察点仅{S['poi_observations']['commercial']}条，密度图对数据遗漏十分敏感。空格和低值不等于没有门店，也不支持把某个空白街角认定为商业开发机会。",
    f"周边环带记录{N['poi_observations']['commercial']}条商业观察点。地块可沿江场西路—万荣路衔接现有服务，重点研究互补、共享与便捷进入，不在内部复制封闭商业中心。",
    '补查沿街店铺、空置和客流，分清经营弱与记录少；有实际需求时先利用既有首层进行小规模、可调整的业态试点，再依据运营和居民反馈完善。',
    ['poi_observations.commercial','longest_mapped_roads'])
add('R06',f"地块有效初筛均值{S['grid100']['priority_score']['mean']:.3f}，并非全域突出高值；约{pct(S['grid100']['priority_score']['valid_weight']/S['area_m2'])}面积有分数。局部高值可帮助安排走访，但缺值和源数据稀疏限制了排序解释。",
    '设计地块与周边的改造应共享问题清单，优先选择能同时改善街道通行、绿化和日常服务接入的接口，避免以红线分割连续的公共环境问题。',
    '实查高值单元后，把可实施的入口、遮荫、休憩和服务补点组合成分期行动；用权属、成本、需求与运营反馈校核顺序，不以初筛分数直接替代项目决策。',
    ['grid100.priority_score','definition.access'])
add('R07',f"地块局部需复核{S['road_dangling_review_records_intersecting']}处源端点和{S['road_building_conflicts_records_intersecting']}处路建叠置。图中标记指向数据或空间问题的核查位置，不是已经确认的实体缺陷。",
    '复核路线应跨越设计边界，与江场西路、万荣路及高架界面一起检查；需要区分真实门禁、分层道路、数据断点和估宽偏差，避免只追求图面线网闭合。',
    '按位置建立照片、通行条件、实宽与责任主体台账；确认后再处理入口、过街和连续人行等可实施问题，先修正误判记录，不依据示意坡度安排工程。',
    ['road_dangling_review_records_intersecting','road_building_conflicts_records_intersecting','longest_mapped_roads'])
add('R08',f"设计区触及{S['population_worldpop2025']['intersecting_native_cells']}个原生约1公里人口单元，内部色差不是楼栋级人口差异。细部公共空间和服务容量不能直接由这幅局部放大图确定。",
    f"地块模型密度约{S['population_worldpop2025']['mean']/10000:.2f}万人/平方公里，全域约{R['population_worldpop2025']['mean']/10000:.2f}万；宜作为片区协同背景，不能推断地块应独立承担多少新增设施。",
    '联合调查地块与邻近街区的现况居住、就业和到访人群，按实际时段配置共享空间与接入路线；模型保持原生尺度，不向100米网格分摊人口来制造精细结论。',
    ['population_worldpop2025'])

catalog=[m for m in json.loads((V/'reports/map_catalog_v3.json').read_text()) if m['kind']!='satellite']
assert len(catalog)==36 and set(notes)=={m['id'] for m in catalog}
for m in catalog:
    n=notes[m['id']]
    for key in ['site_problem','regional_coordination','improvement_direction']:n[key]=n[key].replace('≥40%','≥45%')
    n.update(id=m['id'],title=m['title'],stem=m['stem'],A1_scale=m['A1_scale'],A3_scale=m['A3_scale'])
    for k in ['site_problem','regional_coordination','improvement_direction']:
        assert 40<=len(n[k])<=195,(m['id'],k,len(n[k]))
(P/'reports/map_analysis_notes.json').write_text(json.dumps([notes[m['id']] for m in catalog],ensure_ascii=False,indent=2))
md=['# 上海GIS V3逐图分析说明','', '范围：36张既有非卫星专题图；不增加新底图或新专题。周边指设计范围之外500米欧氏环带与研究区的交集；可达比例均为已映射步行路段长度，非居民/用地覆盖率。事实与研究建议分开，数据不支持的短板不作确定判断。','']
for m in catalog:
    n=notes[m['id']];md += [f"## {m['id']} {m['title']}",'','**地块现状与问题**：'+n['site_problem'],'','**区域协同关系**：'+n['regional_coordination'],'','**改善方向**：'+n['improvement_direction'],'','证据字段：'+', '.join(n['evidence_keys']),'']
(P/'MAP_ANALYSIS_NOTES.md').write_text('\n'.join(md)+'\n')
print('36 maps / 108 distinct interpretation paragraphs written; all tied to spatial evidence.')
