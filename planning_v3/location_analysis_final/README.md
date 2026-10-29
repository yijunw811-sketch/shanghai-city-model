# 上海区位分析｜01与02两版草案

用户选择案例01、02后分别制作的两版真实场地草案，待审阅修改，尚未定为正式版。全新归档；既有V2/V3分析图、GIS和三维模型不变。没有复制案例图片，没有使用卫星影像或生成式地理细节。

| 草案 | 表达方向 | 对应参考 |
|---|---|---|
| 01 水绿与城市肌理 | 灰色建筑肌理、低饱和蓝绿、克制道路层级 | 案例01 Trencin 的背景降权与空间连续性 |
| 02 走廊与资源节点 | 暖色道路骨架、蓝绿结构、资源编号 | 案例02 Shanghai Midtown Belt 的走廊与节点层级 |

两版使用相同三个地图范围、原始几何、6个资源节点与分析文字，便于比较表达方式。表达参考不等于移植其方案事实。

## 查看顺序与文件

1. `outputs/previews/location_two_variants_comparison.png`：并排总览。
2. `outputs/previews/location_01_review.jpg`、`location_02_review.jpg`：单张轻量预览。
3. `outputs/location_01_draft_A1.pdf`、`location_02_draft_A1.pdf`：A1横版可检索文字、矢量地图PDF。
4. 对应 `*_draft_A3.pdf`：A3审阅版。
5. 对应 `*_draft_300dpi.png`：9933×7015像素，真实A1 300DPI排版；没有将DPI等同地理数据精度。
6. `outputs/qgis/location_two_variants_draft.qgz`：两个独立、可编辑原生布局；图层、地图、文字、图例、比例尺可以继续修改。
7. `data/location_context.gpkg`：脱离原仓库也可打开的制图数据副本。带有源网址、许可与高度估计字段等来源属性。

整个目录解压后保持原相对结构。编辑QGIS前，安装`fonts`内两个TrueType字体以复现版式（基于Noto CJK，OFL许可见LICENSE.txt；本包为已用字形子集，新增大量文字可改用完整Noto Sans CJK SC）。PDF字体已嵌入，浏览PDF不需安装。QGIS项目使用相对路径，可离线打开。

## 地理与分析依据

- 核心设计地块：66.09476495 ha，来自既有`refined_analysis_v3.gpkg / DESIGN_SITE`，WKB完全一致；朱红线加细白衬线，无填充、无外围蒙版。22.0091208 km²研究范围另以灰色虚线区分。
- 三个尺度：上海市域定位、片区结构、核心地块与直接周边。地块未移动、简化或改形。
- 图下分析按“场地—区域—协同”组织；建筑覆盖率由建筑轮廓去重合并后与真实多边形相交计算，不是容积率。约26.6%对22.6%只代表当前已记录轮廓，不宣称地面调查完整。
- 彭浦公园207.29 m、静安青年体育公园356.32 m是源公园几何至红线的平面最近距离，不是入口距离或步行距离。
- 资源节点代表源要素的内部代表点／原点位，不是已核实入口。站点代表站体位置；公园开放时段、过街条件、容量仍待核查。
- 道路沿真实线位显示，线宽用于制图分级，不声称实测路宽；轨道线路来自原有OSM关系几何，不虚构缺失连接。没有绘制未经建模的5/10分钟车行等时圈。
- 建筑数据主要覆盖22.009 km²原研究区；片区图外侧无建筑符号不等于真实空地。未知地面不涂成绿地。
- 向东接驳轨道、串联公园与就业资源是改善建议，不是已存在、已批准或已验证通行的工程。

## 来源与许可

- © OpenStreetMap contributors，ODbL-1.0：https://www.openstreetmap.org/copyright 。原V3道路、水绿、POI等源记录保存在GeoPackage中，主要快照为2026-10-25；快照不是逐个设施的实际调查日。
- Overture / East Asian Buildings 建筑：沿用原V3记录的ODbL-1.0集合许可；上游DOI `10.5281/zenodo.8174931`，Overture集合 `https://stac.overturemaps.org/2026-10-21.0/buildings/building/collection.json`。本次仅平面表达，高度估计字段保留而不作为真实测高。
- 上海宏观范围：OSM关系913067，标准公共API取得，2026-10-29快照、关系最近编辑2026-10-23。含海域的行政参考与Natural Earth 1:1000万陆域相交形成定位用陆域图，不是权属或岸线测量图。
- Natural Earth，公共领域：https://www.naturalearthdata.com/about/terms-of-use/ 。下载源、SHA256及验证见`reports/macro_source_validation.json`。
- 先测试的geoBoundaries 2019宏观轮廓仅35个顶点，已因过于粗略弃用；不在最终草案显示。Overpass请求返回HTTP 406，切换标准公开OSM API成功，没有绕过访问控制。
- 没有引用竞赛案例原图作为成图素材。所有版式与图面用本项目真实GIS重新制作。

## 复现

渲染现有制图数据库（无需原大型仓库、网络或旧模型）：

```bash
QT_QPA_PLATFORM=offscreen /usr/bin/python3 scripts/02_build_qgis.py --full
```

需要QGIS 3.40及PyQGIS。`03_prepare_fonts.py`可在有Noto CJK源字体和fontTools时重新生成便携字体；使用随包字体即可跳过。`00_macro_reference.py`重建宏观参考；`01_prepare.py`从原仓库只读数据重新筛选；`04_review_package.py`在原项目中执行边界对照、A3输出和导出核验。验证报告见`reports`。

先审阅两版预览，确认方向与修改点后再制作正式版。
