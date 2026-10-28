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

## PR实际状态

四个ZIP均已上传本独立分支，远端下载返回206且ZIP文件头与长度核验通过；main仍为abea6f3，未合并。

实际PR创建返回：Post https://api.github.com/graphql: Forbidden。目前没有已经创建的PR编号或链接。允许api.github.com的环境配置草稿已保存，需在环境设置应用后才可重试自动创建；未索取或提取代理令牌。

[打开已预填的PR创建入口（这不是已经建立的PR）](https://github.com/yijunw811-sketch/shanghai-city-model/compare/main...planning-v3-cartography-20261028?expand=1&title=GIS+V3%EF%BC%9A%E7%9C%9F%E5%AE%9E%E5%8D%AB%E6%98%9F%E3%80%8166.0948%E5%85%AC%E9%A1%B7%E8%AE%BE%E8%AE%A1%E8%BE%B9%E7%95%8C%E4%B8%8E%E5%A4%9A%E5%B0%BA%E5%BA%A6%E5%88%B6%E5%9B%BE%E5%8D%87%E7%BA%A7&body=GIS+V3%EF%BC%9A39%E5%BC%A0%E5%9B%BE%E3%80%8166.0948ha%E7%9C%9F%E5%AE%9E%E8%AE%BE%E8%AE%A1%E7%BA%BF%E3%80%8110m%E5%8D%AB%E6%98%9F%E3%80%81%E5%A4%9A%E5%B0%BA%E5%BA%A6%E7%BB%9F%E8%AE%A1%E3%80%82%E6%AD%A3%E6%96%87%E8%A7%81planning_v3%2Freports%2FPR_BODY.md%EF%BC%9B%E4%B8%8B%E8%BD%BD%E8%A7%81planning_v3%2Fdownloads%2FRESULTS_INDEX.md%E3%80%82)。完整正文在PR_BODY.md，访问恢复后可运行python planning_v3/scripts/create_pull_request.py。
