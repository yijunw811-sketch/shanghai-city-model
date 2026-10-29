# 卫星影像诊断与可逆显示补丁 · 2026-10-29

**本补丁不是已完成的高清影像替换。当前仍是2026-10-14原生10m Sentinel-2备用图。**

已实际完成：源数据/导出/QGIS配置诊断；三组200×200m固定原生窗口；与原始TCI源的3600个RGB值一致性抽查；原工程备份；纯影像与轻叠加主题；108层重开和预览测试；源GIS/影像/设计CSV哈希不变。

已新增：Esri来源足迹与三个固定位置identify核查。核心区候选为0.34 m、2025-04-07；亚米级元数据足迹并集覆盖全部研究区，尚未验证实际渲染。发布者位置精度8.47 m，不是本项目RMSE。

未完成：合法新影像获取、三组实际新旧比较、配准残差和正式高清图。当前官方主机已放行：天地图主题页返回防护403，两个MapServer出现上游TLS证书验证失败503；没有绕过。Esri服务和通用条款可访问，但源专属条款指向的www.arcgis.com、goto.arcgisonline.com尚未放行。这两个域名已保存到草稿，需要在环境设置保存并发布，再核验许可。没有申请付费API或下载Esri图像。

## 应用补丁

先具备原V3四个成果包并解压，再将此诊断补丁解压到同一父目录，允许更新V3工程与V3清单。V2不会被改动。

- 打开 outputs/qgis/planning_analysis_v3.qgz，或同目录 planning_analysis_v3_imagery_diagnostic.qgz。
- 选择 IMAGE_A_纯影像_原生10m备用 或 IMAGE_B_轻叠加_原生10m备用；旧纯矢量主题保留。
- 原工程字节备份在 imagery_repair/state/planning_analysis_v3_before_imagery_repair.qgz。回滚时把该文件复制回 outputs/qgis/planning_analysis_v3.qgz；不要直接从备份目录打开，因为其内部路径以原工程目录为基准。
- 数据只读加载，防止样式调整意外写入源库；布局和显示样式可编辑。
- 根目录SATELLITE_IMAGE_QUALITY_REPORT.md为完整结论。outputs/three_fixed_baseline_windows_300dpi.png是旧10m基线诊断图，不是完成的新旧高清对比。
- 补丁更新后的完整文件清单在 outputs/manifest.json；先校验再打开QGIS。原版清单另保留为 imagery_repair/state/base_manifest_before_patch.json。

## 恢复源访问后

在环境设置保存并发布新增的www.arcgis.com、goto.arcgisonline.com，读取服务项目页专属使用条款。许可未核实前不启用候选为正式高清层，不打包下载影像。

元数据复核：python planning_v3/imagery_repair/scripts/06_esri_source_audit.py；报告更新：python planning_v3/imagery_repair/scripts/04_quality_report.py。06只调用公开来源query/identify，不下载影像；04检测到新审计后生成最新报告，避免恢复旧的网络阻断判断。02可按需重新测试服务元数据。

取得合法源后应沿用reports/fixed_comparison_windows.json中三组EPSG:32651范围作同范围、同显示比例对比；记录真实同名点而不是猜测配准误差，最后再出正式高清图。原生像元不能通过300DPI或上采样冒充更高分辨率。
