# 上海城市规划 GIS · 全领域现状数据与分析 V2

生成日期：2026-10-26（上海时间）。研究区 **22.009120783 km²**，EPSG:32651，用户确认边界源坐标为WGS84。本成果独立于原三维模型，不覆盖旧成果。

## 先打开这些文件

- `outputs/qgis/planning_analysis.qgz`：实际生成并重开的QGIS工程，54个有效图层、28个可编辑A1布局；数据路径相对存储。
- `outputs/maps/INDEX.png`：28图总览；`A1/`每图PDF/SVG/PNG，`A3_review/`审阅PDF。
- `outputs/gis/planning_enriched.gpkg`：标准化增强数据库；`analysis_layers.gpkg`：网格、街坊、路网指标、网络可达路段及人口格网。
- `reports/data_completeness_dashboard.html`：离线可检索来源、许可、年份与受限原因；`gap_matrix_after.csv`逐项追踪194个需求。
- `reports/final_qa.json`、`qgis_validation.json`、`methods_and_limitations.md`：实测验收结果与分析口径。

## 已完成的增益

三轮检索与复核，138条数据源/访问记录（不是132个独立提供方，更不是132份全覆盖数据）。全主题OSM与Overture范围查询，加入ESA、Copernicus、Sentinel、USGS/Landsat、GHSL、WorldPop、CLCD、JRC Global Surface Water、Wikidata、geoBoundaries、公开科研和再分析数据。政府平台/法规/年鉴、国内专题平台同样实际检索；页面能访问不等同矢量已取得，受限与许可不明资源没有冒充下载成功。

研究区内标准化OSM要素3,500条，其中733个源ID相对旧库新增；这是**新取得的观察记录**，不是新建建筑/新建设施。去重POI研究区469条、上下文1,930条；不得用未映射推断真实缺失。已补入2019年CLCD约30m物理覆盖（仅2.34MB压缩扫描行）与JRC1984–2021历史水面频率（六瓦片约20KB），以及38个转向限制关系。原11,856建筑体块保留不改。最新Overture建筑候选单独存放，不自动修改旧模型。

按相同功能分类规则比较：未知功能面积从 **10.5541降至10.4918 km²**，约47.67%仍待核实。旧模型14.0867km²是物理场地未分类面积，与功能未知不能直接比较。功能面互斥完整分割AOI，但未知并未涂成居住/绿地。分类为研究功能解释，**非法定用途**；2023指南正式原文及最新修订未能通过可访问官方源核实，参考代码不冒充现行法定分类。

GHSL2020原生100米模型面积分摊约521,289人；WorldPop2025 ALPHA约1公里模型约456,084人。两套模型年份/方法不同，不能作为人口增长或减少结论，更不是街坊普查人口。

步行图保留源节点拓扑；56个分量、最大分量约95.94%节点。5/10/15分钟覆盖来自实际路段最短路径，非圆缓冲；设施入口未核实、地图遗漏和2km上下文截断仍限制结果。公园入口为实际步道穿界近似，不是全部经过实地核查的大门。具体接入点和短连接审查见`access_seed_audit`。

## 不能误读

全部建筑高度非测绘实测：11,833默认/上下文估计，23由层数换算。体量强度是m³/m²代理，不是容积率。机会初筛是透明赋权的公共环境研究，不是旧改或拆迁名单。Landsat为单景卫星地表温度（有效100m），不是气温；DSM含树冠/屋顶，不是裸地DTM。历史MODIS派生NDVI仅覆盖48.48% AOI且仅使用observed掩膜，补插值不当作观测。

官方细尺度土地调查、规划控制线、年龄结构、设施容量、建设年代、真实客流/交通流、污染/噪声等仍有明确缺口。见`needs_user_access.csv`和`blocked_maps.csv`；未绕过登录、验证码或商业地图权限。

## 运行与断点续跑

需要Python3.12、`requirements-cloud.txt`中的已验证依赖、Noto CJK字体。QGIS阶段使用系统`/usr/bin/python3`与PyQGIS；本次3.40.6验证成功。

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-cloud.txt
python -m pip check
python scripts/run_pipeline.py --status
python scripts/run_pipeline.py
```

已有产物默认跳过，下载脚本有缓存/校验和/局部读取。指定`--from-stage analysis --force`会重跑该阶段及后续；`normalize --force`仅重建**新的规划数据库**，会删除其后派生层，故应继续后续阶段。不要将任何脚本输出指向旧模型。原始输入副本在`inputs/`，用于离线分析；旧三维模型文件不重复打包。原始网络响应/裁剪栅格/研究ZIP见`planning_raw_sources/`；大字节缓存和不可确认再分发的搜索网页不打包，源URL和失败记录保留。

远程COG必须保留TLS校验，环境CA参数为`GDAL_CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt`。Sentinel双镜像1000DN校准控制为必要证据，不能直接重复扣STAC offset，详见radiometry报告。允许独立主题失败后继续，但必须读报告确认是成功、无记录还是访问受限。

## 署名与许可

© OpenStreetMap contributors，ODbL-1.0；Overture各源许可保留于source_properties_json和来源表，整合衍生库按相关ODbL义务提供。ESA/Copernicus、USGS、EC-JRC/GHSL、WorldPop、CLCD、JRC Global Surface Water、Wikidata、geoBoundaries、科研记录许可独立列明；不将一种许可套给所有来源。公开数据不代表不受再使用条件限制。源要素重复/差异和时间差保留审计，不宣称现实世界100%完整。
