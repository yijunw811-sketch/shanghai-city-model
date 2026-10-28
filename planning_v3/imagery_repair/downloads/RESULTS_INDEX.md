# 卫星影像诊断补丁 · 2026-10-29

**真实高清替换尚未完成；当前仍为原生10m。** 指定官方服务请求在当前云代理处403，尚未到服务端，不能猜测其分辨率、日期或授权。

[下载可逆诊断/显示补丁（2.37MB）](https://github.com/yijunw811-sketch/shanghai-city-model/raw/refs/heads/planning-v3-imagery-repair-20261029/planning_v3/imagery_repair/downloads/shanghai-gis-v3-imagery-diagnostic-patch-20261029.zip) · [SHA256](SHA256SUMS.txt) · [验证](package_verification.json)

[完整影像质量报告](../../SATELLITE_IMAGE_QUALITY_REPORT.md) · [三个固定旧图窗口（不是已完成的新旧高清对比）](../outputs/three_fixed_baseline_windows_300dpi.png) · [应用与回滚说明](../README.md)

需先具备原V3基础数据，再将补丁解压到同一目录。补丁包含原工程备份、更新后的QGIS工程、481项更新清单、三个原生裁剪窗口及审计脚本。V2、源GIS/影像/设计边界不变。

已核实三个窗口共3600个RGB值与原TCI源完全相同，原生10m是主要细节瓶颈；没有发现额外JPEG压缩损失。纯影像和轻叠加主题实际重开108层验证通过。正式高清A1/A3/300DPI和三组新旧对比均待真实源取得后再做。

当前需在云环境设置应用已保存的域名增补：shanghai.tianditu.gov.cn、mape.shanghai-map.net、map4.shanghai-map.net；服务访问恢复后再运行02_probe_services.py核验元数据与许可。不抓瓦片、不购买、不提取应用密钥、不用AI造细节。

分支planning-v3-imagery-repair-20261029，PR基线为planning-v3-cartography-20261028。实际PR状态见github_delivery_status.json，未自动合并任何分支。
