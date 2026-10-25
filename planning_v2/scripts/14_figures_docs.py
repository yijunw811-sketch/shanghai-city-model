from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','pdf.fonttype':42,'svg.fonttype':'path'})
for name,file,x,y,title in [('landuse_area','landuse_statistics.csv','class_name','area_m2','现状功能面积｜有来源解释，非官方调查'),('population_models','population_model_summary.csv','source','model_estimate_aoi_area_weighted','模型人口｜两年份两模型，不是增长比较')]:
 d=pd.read_csv(ROOT/'reports'/file);fig,ax=plt.subplots(figsize=(10,5));ax.bar(d[x],d[y],color='#87aaa1');ax.set_title(title);ax.tick_params(axis='x',rotation=25);ax.set_ylabel('m²' if name=='landuse_area' else '模型人数（边界像元按面积比例）');fig.tight_layout()
 for ext in ['png','pdf','svg']:fig.savefig(ROOT/f'outputs/figures/{name}.{ext}',dpi=150)
 plt.close(fig)
d=pd.read_csv(ROOT/'reports/network_service_coverage.csv');fig,ax=plt.subplots(figsize=(10,5))
for kind,g in d.groupby('kind'):ax.plot(g.minutes,g.reachable_walk_m_aoi/g.denominator_walk_m_aoi*100,marker='o',label=kind)
ax.set(xlabel='步行分钟（4.5km/h）',ylabel='已映射步行网络可达长度占比 %',title='设施接入网络覆盖｜非人口覆盖率',xticks=[5,10,15]);ax.legend(ncols=2);fig.tight_layout()
for ext in ['png','pdf','svg']:fig.savefig(ROOT/f'outputs/figures/network_coverage.{ext}',dpi=150)
plt.close(fig)
(ROOT/'reports/methods_and_limitations.md').write_text('''# 分析口径与重要限制\n\n## 坐标与边界\n用户确认WGS84；米制分析为EPSG:32651。使用真实边界，不从近似范围重画。AOI面积22.009120783km²；数据检索常规外扩2km，统计严格裁切AOI。未发现重点设计地块，不伪造design_site。\n\n## 功能分类与面积\n只对有来源的OSM/Overture真实功能面映射；道路/水/公共服务/绿地/商工住等按确定优先级裁去重叠。小面优先，水/公共服务等优先；未知面保留。全部功能解释均标is_inferred，因为源标签映射也非土地调查。参考2023分类指南，但官方原文和最新修订验证受限，不宣称现行正式法定分类。已识别物理覆盖不自动变成功能。旧物理未分类14.087km²与功能未知不同比较口径。\n\n## 建筑与形态\n保留原11856体块，不用最新Overture候选直接替换原模型。估高11833，层数推算23，实测0。密度为占地并集/裁切网格面积。体量强度按从高到低互斥占地×估高/网格面积，单位m³/m²，不冒充FAR。500m网格103个；街坊是源地面路网与水边界围合分析面，不是宗地，细小面≤100m²不列街坊。\n\n## 网络\n原始way相邻node形成线段，按真实node ID共享拓扑；几何桥隧交叉不增加节点。分块递归skeleton不得覆盖完整tags。保留层级、桥隧、宽度、车道、单向、步行骑行和无障碍属性及空值。图描述不声称道路名称级完整或路口渠化测绘；车行转向关系保留在raw中，未执行驾驶时间路径。步行排除明确private/no及墙/围栏节点；未知街道默认可步行的假设记录。步行图移除明确限制的31节点，剩余56分量，最大分量95.94%节点。\n\n设施接入仅映射节点2m内，或12m内经水/线障碍/建筑穿越筛查的短连接；短连接不是已核实入口，审查表逐点记录。公园以映射步道真实穿越边界处端点≤20m为近似入口，排除明确禁入，开放时间未核。4.5km/h最短路径，5/10/15min对应375/750/1125m。先合并线性里程区间再生成部分边，防浮点重复计长；随时间单调且不得超过网络总长。显示为可达路段，非欧氏圈、实际服务土地或服务人口比例。上下文2km有截断影响；未映射/未接入的设施不等于真实缺失。\n\n## 人口与遥感\nGHSL2020 100m与WorldPop2025 ALPHA约1km原生计数格网保留。边缘像元按交叠面积分摊是透明假设，不是住宅人口空间定位。两套模型/年份差异不得作为人口变化。\nSentinel2026夏冬逐景同镜像控制发现AWS DN较PC低1000：原始XML−1000量化偏移已在AWS影像体现，不能再次套STAC非零offset。保存8波段像元差分与XML证据。原始文件不修改，指数使用经验证有效校准。NDVI有效覆盖夏95.06%冬近100%。季节/太阳角度不同，不直接解读为退化。WorldCover2021仅物理覆盖。\nLandsat2026-08-01 L2 ST产品30m网格来自约100m热红外；聚合到有效100m显示，单位°C，单景地表温度非气温。CopernicusDSM2021约30m含树冠屋顶，不是裸地DTM，更非道路坡度/精确洪水模拟。\n历史NDVI2012–2024来自科研MODIS派生，约250m，仅48.48% AOI；CRS由明确lat/lon坐标推断。observed掩膜排除补插值；不与Sentinel跨传感器直接做趋势。ERA5(-Land)为9/25km再分析单点背景，不作城市微气候实测面。ERA5-Land降水返回全空值，绝不能求和成0；温度与降水使用独立来源/有效日计数。\n\n## 机会研究与管理约束\n等权平均三个百分位：建筑密度、已映射绿色空间不足、日常服务可达已映射步行长度不足。它只用于公共环境改善研究，缺少建设年代/空置/产权/官方更新依据，不能声称拆迁、低效用地或法定旧改潜力。官方红蓝绿线、容量、年龄、交通流和噪声均不编造。\n\n## 制图与许可\nA1 841×594mm，地图框613.93×439.56mm，真实1:10000。A3整张等比缩小至420×297mm，真实比例约1:20023.81并改注；图形比例尺仍准确。PDF嵌入中文字体、SVG文字转路径，PNG120dpi。主要GIS是ODbL衍生研究库，保留OpenStreetMap与各Overture源许可/归属；遥感/人口/科研许可逐源独立列明。不将商业地图显示或检索权限当批量持久化许可。\n''')
progress('figures','statistics','complete')
