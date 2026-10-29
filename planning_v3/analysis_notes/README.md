# 上海GIS V3｜既有分析图加注版

已对01–28及R01–R08共36张既有非卫星专题图逐图分析，在地图下方加入“地块现状与问题／区域协同关系／改善方向”三栏，共108段。没有增加专题或底图，没有继续卫星影像搜集。旧图与V2、原三维模型、原始GIS和设计范围均保留。

快速阅读下载目录中的36页A3合订PDF；正式打印可用A1合订PDF，或分图包内的单张A1/A3。每张另有300 DPI PNG与SVG。MAP_ANALYSIS_NOTES.md为逐图文字全文；DESIGN_COORDINATION_SUMMARY.md为跨图协调方向。

## 说明依据

设计区与环带统计仅用于文字依据，不改变图中原网格数值、分母或原分析范围。所有数值来自只读空间复核，比较真实设计区66.0948ha、周边500米欧氏环带（排除设计区并裁至研究区）和原22.009km²全域。周边环带不是步行服务圈。可达百分比是可达的已映射步行路段并集长度比例，不是居民或用地覆盖率。

建筑高度均估算；体量代理不是容积率。商业及服务POI不完整，空白不能确定为缺乏设施。2020和2025人口产品不得作为真实人口变化；各期遥感产品不能直接替代现况地面调查。改善方向均为有条件的研究建议，不是批准的项目、用地控制或建设规模。

## 字体与原图保护

原PDF的部分CFF字形被嵌入为TrueType字体，导致当前渲染器错显。本版将其转为真实TrueType字形，保留字形顺序与字宽；原PDF文件没有重写。修复前后原绘图指令、栅格流保持一致；在修复字体后的基图上，加注前后地图区域像素完全相同。图面比例、色带、空间范围和朱红设计线不变；无新增填色或外围蒙版。

A1说明正文11pt，A3为7.5pt（页脚7pt）；PNG为300 DPI，未改变专题数据的原生分辨率。PDF字体嵌入，SVG使用字形路径。最终核查见reports/FINAL_QA.json。

## QGIS编辑

将四个加注包解压到原项目同一父目录，形成planning_v3/analysis_notes。打开outputs/qgis/planning_analysis_v3_with_notes.qgz。在对应V3布局底部编辑ANALYSIS_BODY_*文本项即可；108段文字均是独立可编辑文本，原图层仍可单独显示。

QGIS工程沿用原V3数据的相对路径，需已有V3核心GIS数据包。仅阅读PDF/PNG/SVG不需要GIS。工程实际重开108个有效图层、67个布局，36个既有V3布局完成加注，未新增主题。建议QGIS3.40+与Noto CJK／思源黑体，替换字体后须复核换行。

## 复跑与校验

使用既有项目Python环境。完整重算需原始受保护输入与原V3图纸：依次运行scripts/01_evidence.py、02_write_notes.py、03_export_annotated.py；QGIS步骤用系统Python运行04_qgis_notes.py；最后运行05_qa.py、06_package.py。原始输入缺失时不伪造复核通过。

四包完整解压后可运行python scripts/verify_package.py检查本加注包文件SHA256；包本身校验见downloads/SHA256SUMS.txt。输出与缓存分离，支持按源文件/说明内容哈希断点续跑。QGIS打开前先校验，后续编辑会改变工作副本。

© OpenStreetMap contributors，ODbL-1.0：https://www.openstreetmap.org/copyright 。Overture、ESA/Copernicus、EC-JRC、USGS、WorldPop等专题许可与日期沿用原项目。Contains modified Copernicus Sentinel data (2026)仅涉及原R08已有背景；本次没有取得或添加新影像。
