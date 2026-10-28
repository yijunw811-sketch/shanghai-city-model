# 卫星影像诊断与可逆显示补丁 · 2026-10-29

**本补丁不是已完成的高清影像替换。当前仍是2026-10-14原生10m Sentinel-2备用图。**

已实际完成：源数据/导出/QGIS配置诊断；三组200×200m固定原生窗口；与原始TCI源的3600个RGB值一致性抽查；原工程备份；纯影像与轻叠加主题；108层重开和预览测试；源GIS/影像/设计CSV哈希不变。

未完成：0.3–1m或1–2m合法影像获取、实际新旧三组对比、配准残差和正式高清A1/A3/300DPI图纸。指定三个主机被云端代理HTTPS隧道403拒绝，尚未到达服务端。域名放行草稿已保存，但当前运行策略revision8尚未应用。

## 应用补丁

先具备原V3四个成果包并解压，再将此诊断补丁解压到同一父目录，允许更新V3工程与V3清单。V2不会被改动。

- 打开 outputs/qgis/planning_analysis_v3.qgz，或同目录 planning_analysis_v3_imagery_diagnostic.qgz。
- 选择 IMAGE_A_纯影像_原生10m备用 或 IMAGE_B_轻叠加_原生10m备用；旧纯矢量主题保留。
- 原工程字节备份在 imagery_repair/state/planning_analysis_v3_before_imagery_repair.qgz。回滚时把该文件复制回 outputs/qgis/planning_analysis_v3.qgz；不要直接从备份目录打开，因为其内部路径以原工程目录为基准。
- 数据只读加载，防止样式调整意外写入源库；布局和显示样式可编辑。
- 根目录SATELLITE_IMAGE_QUALITY_REPORT.md为完整结论。outputs/three_fixed_baseline_windows_300dpi.png是旧10m基线诊断图，不是完成的新旧高清对比。
- 补丁更新后的完整文件清单在 outputs/manifest.json；先校验再打开QGIS。原版清单另保留为 imagery_repair/state/base_manifest_before_patch.json。

## 恢复源访问后

先在云环境设置应用已经保存的域名增补：shanghai.tianditu.gov.cn、mape.shanghai-map.net、map4.shanghai-map.net。替代及PR所需还包括services.arcgisonline.com、www.esri.com、api.openaerialmap.org、api.github.com。

运行 python planning_v3/imagery_repair/scripts/02_probe_services.py。脚本只取公开元数据，不抓瓦片、不登录、不申请/提取令牌，不调用付费API。先核实真实GSD、拍摄日期、CRS与条款；tile LOD不是拍摄GSD，服务名2024不是拍摄日期，匿名可读不是下载/再分发授权。

取得合法源后应沿用reports/fixed_comparison_windows.json中三组EPSG:32651范围作同范围、同显示比例对比；记录真实同名点而不是猜测配准误差，最后再出正式高清图。原生像元不能通过300DPI或上采样冒充更高分辨率。
