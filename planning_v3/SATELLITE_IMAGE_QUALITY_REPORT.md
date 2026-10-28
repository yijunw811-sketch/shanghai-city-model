# SATELLITE IMAGE QUALITY REPORT

上海GIS V3 · 2026-10-29（上海时间）

**结论：已确认原影像屋顶不清晰的主要原因是原生10m采样不足。尚未完成0.3–1m/1–2m真实影像替换。指定官方服务的请求被云端代理在建立HTTPS隧道时403拒绝，尚未到达服务端，不能把这个错误说成官方服务失效、需要令牌或许可禁止。**

## 1. 原影像与模糊诊断

- 源：Copernicus Sentinel-2 L2A官方TCI真彩色；S2B_51RUQ_20261014_0_L2A；实际拍摄2026-10-14 02:49:03 UTC（上海10:49），不是下载日。
- 实际GeoTIFF：3通道uint8、EPSG:32651、[10.0, 10.0]m/pixel、[787, 986]像素，DEFLATE无损压缩，概览[2, 4, 8, 16]。
- 当前实际源是本地10m GeoTIFF，不是低缩放级别在线XYZ瓦片；也不是NDVI/LST/DSM伪装真彩色。源文件未上采样成虚假的0.5m。
- S02 A1比例1:4000，每个10m源像元在纸面为2.50mm。地图宽约2455.7m，仅约245.6个独立原生像元。20m屋顶宽度只有约2像元，屋顶边缘和小空地无法从数据中恢复。
- 原A1 PNG为[3973, 2806]、约120DPI。即使改300DPI，每个原生10m像元也只是变成约29.53个打印像素，不增加真实地物信息。因此原输出DPI不足不是当前主要成因。
- 三个固定窗口各抽查1200个RGB值，与原始公开TCI源对应原生窗口完全相同，DN平均绝对差0；没有发现该裁剪流程造成附加重采样或有损压缩。这个结论只覆盖抽查窗口，不是任意历史处理的绝对证明。
- 本地TIFF为DEFLATE，PNG无损，检查的S01–S03 PDF嵌入图像为FlateDecode，不存在已发现的连续JPEG重压缩证据。
- 原QGIS RGB=1/2/3、亮度0、对比度0、gamma1；原放大方式为最近邻、无锐化。S02本来就是纯RGB+必要边界，无密集建筑轮廓，说明线条不是纯影像模糊主因；S03叠加可能增加视觉杂乱。

## 2. 官方与替代源实际测试

| 候选 | 实际访问结果 | 真采集GSD/日期/CRS | 账号与使用许可 |
|---|---|---|
| tianditu_shanghai | HTTPS代理隧道403，未到服务端 | 未取得，不能猜测 | 未知，不把公开URL等同授权 |
| shanghai_airphoto | HTTPS代理隧道403，未到服务端 | 未取得，不能猜测 | 未知，不把公开URL等同授权 |
| shanghai_2024 | HTTPS代理隧道403，未到服务端 | 未取得，不能猜测 | 未知，不把公开URL等同授权 |

候选原始地址：

- https://shanghai.tianditu.gov.cn/map/views/theme.html
- https://mape.shanghai-map.net/arcgis/rest/services/SHMAP_IMAGE/MapServer
- https://map4.shanghai-map.net/arcgis/rest/services/shyx2024/MapServer

Esri World Imagery公开元数据及官方条款、OpenAerialMap目录也实际测试，同样被当前出站策略拒绝；没有使用付费API、未提取应用密钥、未下载瓦片。可访问的qucity旧入口只返回IIS默认页，HTTP200不代表可用影像。Earth Search和Planetary Computer元数据可访问；两处NAIP亚米航空集合对上海设计区bbox实际查询均返回0，不能将美国航空产品当上海数据。

深层LOD或服务导出像元间距不等于原始拍摄分辨率；shyx2024服务名不等于已核实的2024拍摄日期。只有在元数据和源许可足够时才能作这些判断。

## 3. 当前选择与双尺度方案

- 城市背景：继续保留2026-10-14原生10m真彩色，作为明确标注的备用背景。
- 核心区：没有取得可合法验证的0.3–1m或1–2m源，不宣称已有高清替换。
- 合法在线层或离线影像两条路径都保留；在源CRS、原生GSD、真实日期、访问身份与学术输出/缓存/下载/再分发许可确认前，不启用未知服务为高清层。
- 未验证连接信息在imagery_repair/data/pending_service_connections.json，仅是候选清单，不是已可用图层。

## 4. 配准与三组固定位置

以下位置均实际落在66.0948公顷用户设计范围内，旧图窗口严格固定为EPSG:32651的200×200m，原生20×20像元，裁剪不重采样。后续新图必须沿用相同空间范围和显示比例。

| ID | 类型 | 参考坐标E,N | 窗口 | 新旧对比状态 |
|---|---|---|---|
| P01 | 建筑密集区 | 350750.000, 3463950.000 | 200×200m | 旧图已冻结，新图未取得 |
| P02 | 道路交叉口 | 351941.578, 3463928.690 | 200×200m | 旧图已冻结，新图未取得 |
| P03 | 已映射绿地 | 350338.768, 3463890.924 | 200×200m | 旧图已冻结，新图未取得 |

[三个固定基线窗口300DPI预览](imagery_repair/outputs/three_fixed_baseline_windows_300dpi.png)；[PDF](imagery_repair/outputs/three_fixed_baseline_windows.pdf)。这不是已经完成的新旧高清对比。三个原生裁剪TIFF、窗口范围JSON、位置GeoPackage已实际生成。

当前参考节点来自既有GIS而非独立测量控制。尚不能计算新影像相对GIS的残差/RMSE，不能仅凭视觉宣称准确。服务恢复后须先核实真实CRS和转换操作的精度，使用可辨识稳定地面道路节点/角点记录新图像素坐标，计算同名点残差；不可将CGCS2000、WGS84、GCJ等默认为一致，更不能手工猜偏移。

## 5. QGIS显示修正及输出测试

- 原工程已备份；更新现有planning_analysis_v3.qgz，并另存planning_analysis_v3_imagery_diagnostic.qgz。
- 保留原纯矢量主题，新增IMAGE_A_纯影像_原生10m备用、IMAGE_B_轻叠加_原生10m备用。全部明确是10m备用，未命名为已替换高清。
- 纯图层保持完整自然RGB，最近邻放大，不锐化；缩小使用适当浏览重采样/现有概览。轻叠加建筑轮廓0.05mm/25%不透明度，主要道路0.06mm/40%不透明度，绿地水面仅轻边界，降低遮挡。这里的显示权重在设计范围内外一致。
- 设计朱红线、白衬线和源几何保持；无外围蒙版，无场地内填色，没有重裁已有分析数据。
- 实际重开修改工程108有效图层、无缺失源；原生布局诊断预览实际导出。原始GIS库、真实边界CSV和原影像等7项关键文件SHA256全未变。
- S01–S03布局配置300DPI，以备合法高分源取得后输出；本轮没有用300DPI重出旧图冒充正式高清图。已生成的300DPI图仅是清晰标识的诊断窗口。

## 6. 许可与再分发

- 旧Sentinel影像延续Copernicus开放数据条款及署名；本轮原生小窗口为同源基线，不产生新的高分影像许可。
- 三个官方候选、Esri与OpenAerialMap的具体服务学术图纸使用/本地缓存/下载/再分发条件仍未核实，访问被代理拦截不代表源自身禁止或允许。不得因为匿名可读就批量抓瓦片。
- 源许可不允许离线时只配置合法在线方式，不将服务图像打包再分发；任何凭证需合法授权并通过安全环境配置，不从页面提取共享密钥。

## 7. 当前阻断与续跑

运行中的云环境出站策略仍为revision8；三个指定主机不在该策略中。已经通过配置工具保存完整保留式域名增补，返回requires_publish=true；保存草稿没有自动应用到当前实例。需在云环境设置应用后重新验证，不是索取个人地图账号或付款。

必要主机：shanghai.tianditu.gov.cn、mape.shanghai-map.net、map4.shanghai-map.net；替代与PR还包括services.arcgisonline.com、www.esri.com、api.openaerialmap.org、api.github.com。

恢复访问后先运行imagery_repair/scripts/02_probe_services.py，取得元数据及可证明的使用条款；再决定合法服务配置或有限离线获取，完成真实同名点配准和三组同范围对比。最后才输出核心高清、城市背景高清、GIS叠加及新旧比较的A1/A3与300DPI PNG。当前这些正式高清交付仍未完成。

## 8. 审计材料

- imagery_repair/reports/native_raster_diagnosis.json
- imagery_repair/reports/native_source_pixel_control.json
- imagery_repair/reports/export_resolution_diagnosis.json
- imagery_repair/reports/qgis_source_render_audit.json
- imagery_repair/reports/initial_service_access.json
- imagery_repair/reports/service_capability_rights_matrix.json
- imagery_repair/reports/accessible_alternative_catalogue_checks.json
- imagery_repair/reports/fixed_comparison_windows.json
- imagery_repair/reports/display_patch_validation.json
