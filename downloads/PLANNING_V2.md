# 上海城市规划 GIS · V2 完整成果下载

2026-10-26更新。原三维模型保持不变；本页是独立的规划现状数据库与分析成果。

**下载下面三个独立ZIP，并解压到同一文件夹**。它们共同组成 `planning_v2/`，无需分卷拼接。

| 文件 | 约大小 | 内容 |
|---|---:|---|
| [GIS数据库与栅格](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/main/downloads/shanghai-planning-v2-gis.zip) | 36 MB | 增强GeoPackage、分析GeoPackage、13个专题栅格 |
| [完整图册](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/main/downloads/shanghai-planning-v2-atlas.zip) | 84 MB | 28张A1 PDF/SVG/PNG、28份A3审阅PDF、统计图和总览 |
| [原始来源、QGIS、脚本与报告](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/main/downloads/shanghai-planning-v2-sources-repro.zip) | 63 MB | 可编辑QGIS工程、许可允许的原始资料、输入副本、复跑脚本、来源/缺口/QA |

先看[图纸总览](planning-v2-INDEX.png)、[完整交付说明](../planning_v2/reports/delivery_summary.md)和[项目说明](../planning_v2/README.md)。文件SHA256见[校验表](planning-v2-SHA256SUMS.txt)，每个ZIP均实际完成CRC检查，未截断数据库。

解压后打开 `planning_v2/outputs/qgis/planning_analysis.qgz`；离线数据证据仪表板是 `planning_v2/reports/data_completeness_dashboard.html`。运行 `python planning_v2/scripts/verify_delivery.py` 可逐文件验证manifest。不要只解压其中一个ZIP后就运行完整校验。

本轮138条来源/访问记录、194个需求子项；研究区标准化OSM相对旧库新增733个源ID，去重POI469条。用地功能待核实面积按同一规则从10.554降至10.492km²，仍有47.67%待补证，不能与旧模型14.087km²物理未分类直接比较。

**重要限制**：全部建筑高度非实测；人口为2020年100m与2025年约1km模型，不能由模型差异推出人口变化。土地功能解释不是法定用途，体量代理不是容积率，改善机会初筛不是旧改/拆迁名单。法定控制线、细尺度普查/年龄、容量、建设年代、真实交通流等仍列缺口，未虚构补齐。

实际验收：75个空间表读回、无效几何0；28套图纸尺寸/结构通过；QGIS3.40.6重开54个有效图层及28个布局并导出原生布局；原模型41个受保护文件SHA256未变。详见包内final_qa.json与qgis_validation.json。

© OpenStreetMap contributors（ODbL）；Overture及各遥感、人口、科研来源分别保留署名、年份与许可。再使用请检查包内source_registry.csv。
