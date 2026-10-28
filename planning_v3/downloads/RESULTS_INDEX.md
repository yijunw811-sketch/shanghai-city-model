# 上海规划 GIS V3 · 完整成果下载

请下载以下四个独立ZIP，全部解压到同一目录，形成planning_v3文件夹；无需拼接。原V2及三维模型保持不变，本分支不合并main。

| 文件 | 大小 | 内容 |
|---|---:|---|
| [shanghai-planning-v3-01-core-gis-project.zip](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/planning-v3-cartography-20261028/planning_v3/downloads/shanghai-planning-v3-01-core-gis-project.zip) | 43.6 MB | GIS数据库、真实设计边界、10m真彩色、QGIS工程、样式、脚本与报告 |
| [shanghai-planning-v3-02-regional-maps-01-14.zip](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/planning-v3-cartography-20261028/planning_v3/downloads/shanghai-planning-v3-02-regional-maps-01-14.zip) | 53.6 MB | 区域优化图01–14的A1 PDF/SVG/PNG及A3审阅版 |
| [shanghai-planning-v3-03-regional-maps-15-28.zip](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/planning-v3-cartography-20261028/planning_v3/downloads/shanghai-planning-v3-03-regional-maps-15-28.zip) | 23.9 MB | 区域优化图15–28的A1 PDF/SVG/PNG及A3审阅版 |
| [shanghai-planning-v3-04-satellite-refined-comparisons.zip](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/planning-v3-cartography-20261028/planning_v3/downloads/shanghai-planning-v3-04-satellite-refined-comparisons.zip) | 73.8 MB | 三张卫星图、八张精细图、分类副本、原生预览与新旧/尺度对照 |

[39图总览](INDEX_V3.png) · [完整交付说明](../reports/delivery_summary_v3.md) · [QA](../reports/final_qa_v3.json) · [SHA256](SHA256SUMS.txt) · [归档逐文件验证](archive_member_verification.json) · [异目录独立加载验证](relocation_verification.json)

解压后先运行 python planning_v3/scripts/verify_delivery.py，再打开 planning_v3/outputs/qgis/planning_analysis_v3.qgz。离线可筛选的完整索引：planning_v3/outputs/RESULTS_INDEX.html。

实际验收：39套A1/A3，83个空间表、无效几何0；QGIS103个有效图层、28个保留V2布局及39个新布局。核心ZIP已实际解压到另一目录，103个数据源均从新目录解析，S02重新导出成功，无原工作区数据源依赖。

真实设计边界66.09476495ha，源CSV保留，闭合微自交修复记录见报告。真实Sentinel-2 TCI拍摄2026-10-14，原生10m；没有取得可离线再分发的0.5–2m正射影像。

核心区50/100/200m相交318/92/29单元，建筑基底覆盖率26.5668%、估高体量代理3.253964m³/m²；体量不是容积率，全部高度非实测。设计内已映射功能仅21.18%、商业观察仅2条，不能据此推断真实无商业。2025人口保留原生约1km。

独立分支：planning-v3-cartography-20261028。实际PR创建状态见 [github_delivery_status.json](github_delivery_status.json)；若API仍Forbidden，不宣称PR已经建立。PR正文已准备在 [PR_BODY.md](../reports/PR_BODY.md)，不自动合并main。

© OpenStreetMap contributors（ODbL）/ Overture及各源许可保留；Contains modified Copernicus Sentinel data (2026)。
