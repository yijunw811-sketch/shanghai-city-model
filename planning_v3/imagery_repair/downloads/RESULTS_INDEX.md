# 卫星影像诊断补丁 · 2026-10-29

**真实高清替换尚未完成；当前工程仍为原生10 m。** 最新已核实Esri来源元数据：核心区候选0.34 m、2025-04-07，位置精度字段8.47 m；亚米级元数据足迹覆盖全研究区。尚未取得新图像、测量配准或完成三组真实新旧比较。

[下载Esri来源核查增量包（约0.93 MB，只有元数据与报告，无高清影像）](shanghai-gis-v3-esri-source-audit-20261029.zip) · [校验](esri_audit_package_verification.json) · [SHA256](ESRI_AUDIT_SHA256SUMS.txt)

需在原V3与下述诊断补丁之后叠加解压此增量包，更新报告和完整文件清单。旧诊断补丁是上一阶段快照，以最新增量包报告为准。

[下载可逆诊断/显示补丁（2.37MB）](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/planning-v3-imagery-repair-20261029/planning_v3/imagery_repair/downloads/shanghai-gis-v3-imagery-diagnostic-patch-20261029.zip) · [SHA256](SHA256SUMS.txt) · [验证](package_verification.json)

[完整影像质量报告](../../SATELLITE_IMAGE_QUALITY_REPORT.md) · [三个固定旧图窗口（不是已完成的新旧高清对比）](../outputs/three_fixed_baseline_windows_300dpi.png) · [应用与回滚说明](../README.md)

需先具备原V3基础数据，再将补丁解压到同一目录。补丁包含原工程备份、更新后的QGIS工程、481项更新清单、三个原生裁剪窗口及审计脚本。V2、源GIS/影像/设计边界不变。

已核实三个窗口共3600个RGB值与原TCI源完全相同，原生10m是主要细节瓶颈；没有发现额外JPEG压缩损失。纯影像和轻叠加主题实际重开108层验证通过。正式高清A1/A3/300DPI和三组新旧对比均待真实源取得后再做。

三个上海主机现已放行，实际返回网站防护403或上游TLS校验失败503。Esri来源REST/查询可用；专属许可链接需新增www.arcgis.com、goto.arcgisonline.com，两个域名已保存到环境草稿，需要在环境设置保存并发布后复测。不抓瓦片、不购买、不提取应用密钥、不用AI造细节。

分支planning-v3-imagery-repair-20261029，PR基线为planning-v3-cartography-20261028。实际PR状态见github_delivery_status.json，未自动合并任何分支。
