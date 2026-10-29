# SHANGHAI PLANNING GIS V3

> 2026-10-29影像诊断：真实高清替换尚未完成。当前10m源不足以判读屋顶；官方候选主机被运行中出站策略阻挡。已加入可逆显示诊断补丁，详见SATELLITE_IMAGE_QUALITY_REPORT.md与imagery_repair/README.md。

2026-10-28，独立目录与分支 planning-v3-cartography-20261028。V2及原城市模型保持完整，992项源文件SHA256检查通过；不合并main。

## 下载与打开

下载本分支 planning_v3/downloads/RESULTS_INDEX.md 所列全部独立ZIP，解压到同一目录，形成 planning_v3 文件夹，无需拼接。

1. 首次打开QGIS前运行 python planning_v3/scripts/verify_delivery.py 校验文件。
2. 打开 planning_v3/outputs/qgis/planning_analysis_v3.qgz。
3. 切换地图主题 V3_A_纯矢量专题、V3_B_真实卫星、V3_C_卫星与GIS叠加，或独立开关图层。
4. 离线可筛选完整索引 outputs/RESULTS_INDEX.html；图纸总览 outputs/previews/INDEX_V3.png；正式A1在 outputs/maps/A1，A3在A3_review；卫星和精细图另有分类目录。

采用GeoPackage、GeoTIFF、相对路径和UTF-8文件名。QGIS3.40.6云端重开103个有效图层，保留28个V2参考布局并新增39个V3布局。Windows建议QGIS3.40+与Noto CJK/思源黑体或微软雅黑替代字体。PDF中文字体已嵌入。GIS软件打开后可能更新工作副本内部元数据，应先校验再打开。

## 影像与设计边界

- 真实Sentinel-2 L2A官方TCI自然色，拍摄2026-10-14 02:49:03 UTC，产品S2B_51RUQ_20261014_0_L2A，原生10m、EPSG:32651；已建2/4/8/16倍概览。
- 比较6个场景：选定场景核心区云影/无效SCL比例0%，全域约0.00363%；较新的10月26日全域云影约8.58%。
- Copernicus Sentinel开放数据许可与署名见reports/satellite_provenance.json。未取得可核实许可的0.5–2m正射数据，不把10m影像冒充建筑级测绘。
- 用户选定范围.csv原件完整保留。核验66.09476495ha / 0.660947649km²，全部在22.009120783km²背景区内。沿用项目WGS84确认，无猜测性GCJ/BD改正，无独立测绘精度声明。
- 原CSV闭合点约4cm处微自交，分析副本移除0.000714m²微碎片，修复过程存证，原CSV不改。
- 独立DESIGN_SITE_BOUNDARY为线图层：朱红#CB493E，A1线宽1.2mm、白色细衬线。无内部填充、外围灰化/蒙版或内外透明度差。

## 多尺度指标

50m覆盖设计区+500m必要周边；100/200m覆盖全AOI，并另存真实设计相交单元。原点统一(0,0)，EPSG:32651，分母为实际交集面积。核心区相交318/92/29个50/100/200m单元；V2原500m网格保留。

| 八类重点 | 正式表达 | 口径 |
|---|---|---|
| 建筑基底覆盖率 | 100m，50m对照 | 真建筑并集与真网格相交 |
| 估高体量代理 | 100m | m³/m²，全部非测绘高度，非容积率 |
| 已映射功能面积混合 | 200m，100m对照 | 面积Shannon/ln8，未知排除，已知覆盖低于50%留空；区别于V2 POI熵 |
| 车行密度/节点 | 200m，100m对照 | 真线长/交集面积，真实源节点；桥隧几何交叉不自动连接 |
| 商业观察密度 | 200m | 真实点数/真面积；KDE100/200/400m仅作敏感性 |
| 公共环境改善机会 | 100m | 沿用V2三项等权体系，非法定旧改/拆迁名单 |
| 数据问题与机会 | 100m+原位点线面 | 不将全部问题强行格网化 |
| 2025模型人口 | 原生约1km | 原48个裁切单元保留，未插值或降尺度成100m人口 |

核心证据限制：设计内已映射功能仅21.18%，约78.82%仍未知；商业观察点仅2条，完整率不明。200m设计相交统计仅4个单元符合功能混合度门槛。不能据此认定真实无商业或补成确定用途。三尺度设计区建筑占地覆盖率约26.5668%，体量代理约3.253964m³/m²，总量守恒不代表测绘精度。

区域与局部同指标共享固定分级。精细图是全域网格指标的局部视图，设计线不改变分母；design_grid_*另存设计相交面积口径。源建筑、道路、水、绿地几何完整保留。

## 图纸与工程

39张A1：28张区域优化图、R01–R08八张精细图、S01/S02/S03三张卫星图。各PDF/SVG/PNG，另39份适配A3 PDF；A3文字最小7pt，比例尺按物理图框计算并置于图框外。

15套色带与固定分界见styles/COLOR_STYLE_SYSTEM.json。顺序色带明度单调、邻级ΔE76大于7。同一指标共享分界，人口两年份也用同一分界，但不同模型不作真实变化结论。

QGIS实际导出02/R01/S02/S03布局，移除卫星后矢量02仍能导出。卫星合法离线打包，无在线服务依赖。配准检查是源坐标框架和实际叠加，无独立测绘控制点，不声称亚米精度。

## 复跑与验收

python scripts/run_pipeline.py --status 查看阶段，默认跳过已有产物；--from-stage multiscale --force 重跑该阶段及后续。禁止写V2。完整原文件保护复核与V2并排比较需原V2资料，本包自身可独立打开、编辑和校验。requirements-cloud.txt记录依赖，PyQGIS用系统Python。

- reports/delivery_summary_v3.md：完整结果与限制。
- reports/final_qa_v3.json、qgis_validation_v3.json：实际验收。
- reports/design_boundary_validation.json：边界、修复及面积。
- reports/design_scale_sensitivity.csv、scale_stability_vs_v2.csv、function_inference_sensitivity.csv、kde_bandwidth_sensitivity.csv：尺度与假设对照。
- reports/protected_v2_verification.csv：992项源文件SHA未变。
- outputs/comparisons：八张重点新旧并排与尺度对照。
- outputs/manifest.json、下载校验表：SHA256。

© OpenStreetMap contributors（ODbL-1.0），Overture及各源许可保留在来源字段；Contains modified Copernicus Sentinel data (2026)。ESA/Copernicus、USGS、EC-JRC、WorldPop原专题许可及年份保持。全部建筑高度估计/层数推算，人口为模型，非普查实测。

GitHub实际交付状态见downloads/github_delivery_status.json。API若仍返回Forbidden，不宣称PR已创建；正文和命令已准备，独立分支不自动合并main。
