"""Refresh current status after metadata becomes accessible; no imagery download."""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[1]
V=P.parent
a=json.loads((P/'reports/esri_spatial_source_audit.json').read_text())
report='''# SATELLITE_IMAGE_QUALITY_REPORT

上海 GIS V3 · 2026-10-29（上海时间）

**当前结果：已锁定覆盖核心区的真正亚米级影像候选，但尚未取得并验证新影像，不能宣称高清替换完成。Esri 服务对核心设计区标注的源分辨率为 0.34 m，拍摄日期为 2025-04-07。影像位置精度字段为 8.47 m，不能将清晰度等同于测量精度。**

## 1. 原影像诊断

原底图为 Copernicus Sentinel-2 L2A 官方 TCI 真彩色，S2B_51RUQ_20261014_0_L2A，拍摄时间 2026-10-14T02:49:03.229Z；本地 GeoTIFF 为 EPSG:32651、原生 10×10 m、3通道 uint8、DEFLATE 无损压缩。它是本地栅格源，不是低缩放等级在线瓦片；没有变成虚假的0.5 m产品。

核心图比例1:4000，每个10 m源像元占纸面2.5 mm，地图宽度仅约245.6个独立源像元。原PNG约120 DPI；300 DPI只会将每个源像元画成约29.53个打印像素，不能恢复屋顶和小尺度地物。三个旧图窗口与远程原始TCI对应的3600个RGB值全部相同，平均DN差为0，未发现此裁剪流程造成附加损失。

TIFF/PNG无损，检查的PDF嵌入图像为FlateDecode，未发现连续JPEG重压缩。原QGIS亮度0、对比度0、gamma1、无锐化；S02本来没有密集建筑轮廓，因此纯影像模糊主因是原生10 m不足。S03叠加线条可能增加视觉杂乱，已做可逆的轻叠加样式。

## 2. 已测试来源及实际结果

当前运行环境策略为 revision13、enforced。三个上海官方主机、Esri服务、Esri法律文件和OpenAerialMap已放行，不再沿用早前revision8的代理隧道403判断。

| 来源 | 当前实测 | 判断 |
|---|---|---|
| 天地图·上海主题页 | HTTP403，页面称访问被网站防护拦截 | 未绕过；影像GSD、日期、CRS、授权未知 |
| 上海SHMAP_IMAGE | 网关HTTP503，上游TLS证书校验失败 | 未关闭TLS校验；未取得服务元数据 |
| 上海shyx2024 | 网关HTTP503，上游TLS证书校验失败 | 服务名年份不能当拍摄日期 |
| Esri World Imagery | REST元数据、来源足迹query和三个位置identify均HTTP200 | 核心区0.34 m候选；尚未取得图像和专属条款 |
| OpenAerialMap | AOI目录HTTP200，3个相交产品 | 2个1000 m、1个1180.715 m，虽标注WorldView传感器仍不符合高清要求，全部排除 |
| Earth Search/Planetary Computer NAIP | 前阶段上海bbox查询0条 | 美国航空集合不能作为上海影像 |
| qucity公开旧入口 | IIS默认页 | HTTP200不是影像服务可用证明 |

官方地址与全部服务探测记录保留在 `imagery_repair/reports/`。没有付费API、批量瓦片抓取、共享密钥提取、登录绕过或AI补画。

## 3. 双尺度候选与真实分辨率

Esri World Imagery REST：
https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer

从其公开来源图层 `/0/query` 取得3个相交影像元数据足迹，转换到EPSG:32651与真实边界求交：

| 对象ID | 发布者标注GSD | 拍摄日期 | 源 | 与核心区相交 |
|---|---|---|---|---|
| 3144165 | 0.34 m | 2025-04-07 | Vantor / Vivid Advanced / LG03 | 覆盖整个660947.6495 m²核心区 |
| 3144175 | 0.31 m | 2025-04-18 | Vantor / Vivid Advanced / WV03 | 无 |
| 2807139 | 0.50 m | 2025-04-25 | Vantor / Vivid Advanced / WV02 | 无 |

3个亚米级元数据足迹的并集覆盖整个22.0091208 km²研究区。**这只是来源元数据足迹覆盖，不是实际渲染无缺口验收。** 背景区涉及多个日期，不能标成全域单一拍摄日。核心区三个固定点identify均返回对象3144165、0.34 m、2025-04-07。

源GSD来自SRC_RES字段，不是根据最深瓦片LOD推断。服务EPSG:3857可通过标准投影转换到EPSG:32651，但转换公式准确不证明源影像定位准确。服务位置精度SRC_ACC=8.47 m，置信统计定义尚未核实；它不是本项目实测RMSE。

## 4. 使用许可与数据交付边界

已读取Esri公开Master Agreement和Website Properties Terms（相关条款、URL、文件SHA256见 `esri_license_evidence.json`）。网站通用条款2.2描述内部/非商业用途的有限许可；同时有专属条款、第三方内容和用途限制。Master Agreement 3.2区分署名静态地图输出与底图数据离线保存，不能把通用条款或公开匿名接口视为任意GeoTIFF下载/再分发许可。

服务元数据 `licenseInfo` 为空，其“更多信息及使用条款”指向 `https://goto.arcgisonline.com/maps/World_Imagery`。当前环境尚未放行该域名及ArcGIS项目页 `www.arcgis.com`，专属条款未能读取。两个精确域名已加入环境配置草稿，工具确认saved、requires_publish=true。**草稿保存不等于生效：需在环境设置保存并发布后复测。** 这是读取真实条款的网络前提，不是购买影像或索取令牌。

当前未申请账户、未调用收费接口，也未以“用户同意使用”代替数据提供方许可。未下载或打包Esri原始/渲染影像。许可核实后优先提供合法在线图层；仅在明确允许时保存GeoTIFF/COG。若需要已有机构授权或服务限制外部客户端，将如实报告，不能默认QGIS适用。

## 5. 三组同尺度比较与配准状态

三个比较窗口已冻结，不因候选源改变而重选：

| ID | 类型 | EPSG:32651窗口xmin,ymin,xmax,ymax | 旧源 |
|---|---|---|---|
| P01 | 建筑密集区 | 350650,3463850,350850,3464050 | 200×200 m，20×20原生像元 |
| P02 | 道路交叉口 | 351840,3463830,352040,3464030 | 同上 |
| P03 | 已映射绿地 | 350230,3463800,350430,3464000 | 同上 |

[旧图三个固定窗口预览](imagery_repair/outputs/three_fixed_baseline_windows_300dpi.png)。本次新增每个固定点的Esri来源identify原始结果；**仍不是新旧图像比较**。新图像未取得，实际新旧比较0组，同名地面点实测0个，未计算配准残差/RMSE，也未靠目测宣称准确。

后续须在合法影像上对可辨识的稳定地面路口/角点进行分布式检查，记录图像像素和地图坐标，与既有GIS的相对残差区分于绝对测量精度。建筑屋顶受楼高和侧视影响，不能将屋顶角点无条件当作地面控制点。不得凭SRC_ACC或投影操作的0 m数学精度宣称亚米配准。

## 6. QGIS显示与正式输出

上一阶段已实际更新主V3工程并另存诊断工程，重开108个有效图层，原工程有回滚备份。保留纯矢量主题，提供明确标注原生10 m备用的纯影像/轻叠加主题。建筑轮廓不透明度25%、主要道路40%，未改原始专题数据。

真实设计范围保留朱红线与细白衬线，无内部填色、外围灰色蒙版或区外压暗。此次仅新增来源核查，不启用许可未经证实的高清层，不改变真实边界或既有分析裁剪范围。7项受保护输入SHA256再次全部一致。

卫星布局已配置300 DPI并有原生10 m显示测试。根据用户要求，真正影像替换、三个同范围对比和配准检查完成前，不重新输出并冠以“高清”的A1/A3/300 DPI正式图。当前正式高清图输出数0。

## 7. 下一阶段及审计材料

优先完成专属条款访问；确认合法在线/有限静态输出路径后，在现有固定窗口检验真实像素与地物细节，再检查配准。通过后更新纯高清/高清叠加主题，导出核心、城市背景、叠加、比较四类A1/A3/300 DPI图。

- `imagery_repair/reports/esri_spatial_source_audit.json`：足迹覆盖、源字段、三个固定点identify、7项SHA校验。
- `imagery_repair/data/esri_source_footprints.geojson`：公开来源元数据足迹，非影像文件。
- `imagery_repair/data/esri_aoi_source_footprints.json`：REST原始响应。
- `imagery_repair/data/openaerialmap_aoi_metadata.json`：排除的低分辨率产品证据。
- `imagery_repair/reports/esri_license_evidence.json`：通用条款核查证据及未完成事项。
- `imagery_repair/reports/network_release_verification_20261029.json`：官方主机放行后的错误类型。
- `imagery_repair/reports/fixed_comparison_windows.json`：冻结窗口，不包含新图。
- 原生像素、QGIS渲染、DPI与旧文件完整性诊断仍保留。

**交付状态：候选源的亚米GSD及元数据覆盖已证实；图像取得、专属用途许可、三组真实比较、配准实测和正式高清图尚未完成。**
'''
(V/'SATELLITE_IMAGE_QUALITY_REPORT.md').write_text(report)
status=json.loads((P/'reports/work_status.json').read_text())
status.update(runtime_revision='13',candidate_metadata_GSD_m=0.34,candidate_capture_date='2025-04-07',
    candidate_metadata_coverage_core_fraction=1.0,candidate_metadata_coverage_context_fraction=1.0,
    candidate_spatial_accuracy_metadata_m=8.47,blocker='Source-specific Esri terms linked to www.arcgis.com and goto.arcgisonline.com not accessible under current egress policy; draft saved, not applied',
    high_resolution_acquired=False,high_resolution_replacement_complete=False)
(P/'reports/work_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
connection={'provider_candidate':'arcgismapserver (ams)','url':a['service'],
    'enabled':False,'reason':'Source-specific use rights not verified; metadata only',
    'service_CRS':'EPSG:3857','project_CRS':'EPSG:32651',
    'core_source_GSD_m':0.34,'core_capture_date':'2025-04-07',
    'position_accuracy_metadata_m':8.47,'no_offline_redistribution_permission_established':True}
(P/'data/esri_pending_connection.json').write_text(json.dumps(connection,ensure_ascii=False,indent=2))
print('Current report refreshed; metadata candidate verified, actual imagery pending')
