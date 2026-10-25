"""A1/A3 vector planning atlas with true physical map scales; supports checkpoints."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,fontManager
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np,rasterio
from PIL import Image,ImageOps,ImageDraw
from shapely import union_all
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';fontManager.addfont(font)
plt.rcParams.update({'font.family':'Noto Sans CJK JP','pdf.fonttype':42,'svg.fonttype':'path','axes.unicode_minus':False,'font.size':11})
M=ROOT/'outputs/gis/planning_enriched.gpkg';A=ROOT/'outputs/gis/analysis_layers.gpkg'
def r(l,p=M):return gpd.read_file(p,layer=l)
b=r('buildings_enriched');roads=r('road_network_vehicle');grid=r('planning_grid_500m',A);land=r('landuse_existing');poi=r('poi_all');blue=r('blue_network');green=r('green_spaces_all')
# Research score uses transparent equal-weight ranks; not age, vacancy or official renewal.
access=r('access_daily_service',A);accessible=union_all(access[access.minutes==15].geometry)
walk=r('road_network_walk');ratios=[]
for g in grid.geometry:
 denom=walk.intersection(g).length.sum();numer=accessible.intersection(g).length
 ratios.append(min(1,numer/denom) if denom>0 else np.nan)
grid['daily_service_reachable_walk_fraction']=ratios
grid['research_amenity_priority']=(grid.building_density.rank(pct=True)+(1-grid.mapped_green_fraction).rank(pct=True)+(1-grid.daily_service_reachable_walk_fraction).rank(pct=True))/3
write_layer(grid,A,'planning_grid_500m');write_layer(grid,M,'planning_grid_500m')
data_signature=sha(ROOT/'reports/network_topology.json')+sha(ROOT/'reports/landuse_partition_qa.json')+sha(ROOT/'reports/network_service_coverage.csv')+'atlas-v2c'
items=[]
def add(id,title,en,kind,layer=None,field=None,cmap='YlOrRd',note='',findings=None):items.append(dict(id=id,title=title,en=en,kind=kind,layer=layer,field=field,cmap=cmap,note=note,findings=findings or []))
add('01','现状土地功能分类','Existing mapped land functions','land',note='现状功能研究分类；非法定用途。仅映射有证据的面，不用单个POI填满未知地。2023指南参考代码的最新修订未核实。')
add('02','建筑密度分析','Building footprint density','grid',field='building_density',cmap='YlOrBr',note='建筑占地并集面积 / 裁切后500米网格面积；边界网格修正，重叠占地不重复计入。')
add('03','建筑高度分布｜全部含估算','Building height: source estimates','height',note='11,856体块均非实测高度：11,833默认/上下文估高，23由层数×3米推算。用于形态研究。')
add('04','建筑体量强度代理','Estimated volume intensity proxy','grid',field='volume_proxy_m',cmap='YlOrBr',note='各高度占地互斥面×估算高度之和 / 网格面积（m³/m²）。重叠取较高值；不是容积率。')
add('05','城市肌理与图底关系','Urban figure-ground','figure',note='现有建筑真实来源轮廓的图底表达；不表示产权、竣工状态或完整测绘。')
add('06','已映射城市功能混合度','Mapped POI category diversity','grid',field='poi_entropy',cmap='YlGnBu',note='9类POI归一化Shannon熵 H/ln(9)；少于5点网格不报告。反映已映射样本，不代表完整真实功能。')
add('07','道路等级与交通结构','Road hierarchy and grade separation','road',note='保留源等级、桥隧、层级和单行属性；几何相交不自动连通。不是官方道路行政等级。')
add('08','车行路网密度与节点连通','Mapped vehicle network density','grid',field='vehicle_density_km_km2',cmap='YlOrRd',note='源线长度(km) / 裁切网格面积(km²)；双幅路分别计入，非道路走廊去重长度。节点只按真实OSM ID连接。')
add('09','公共交通接入与步行网络覆盖','Transit access on mapped walk network','access',layer='transit',note='5/10/15分钟，4.5km/h最短路径。站台/出入口/停靠点记录不是独立车站或班次；仅合格接入点进入计算。')
add('10','日常服务慢行可达性','Daily-service walking reach','access',layer='daily_service',note='基于OSM步行节点和已映射设施，5/10/15分钟；结果为可达路段，不是欧氏圈或服务人口比例。')
add('11','商业POI观察密度','Mapped commercial POI observations','grid',field='commercial_poi',cmap='OrRd',note='每个裁切500米网格内商业POI计数；边缘网格面积不同。数据稀疏，不等同客流、就业或真实经济活力。')
add('12','已映射教育设施步行覆盖','Mapped education walking access','access',layer='education',note='公共服务分项之一：教育。只计算能接入真实路网的设施；无床位、等级或容量推断。其它分项见数据库和覆盖表。')
add('13','蓝绿空间现状网络','Mapped blue and green spaces','bluegreen',note='绿地与水面为开放地图观察；不等同官方绿化覆盖率，不自动认定全部开放。')
add('14','公园绿地网络可达性','Park access on mapped walking network','access',layer='parks',note='源步道真实穿越公园边界处的近似接入（端点≤20m），排除明确私有/禁入；开放时间和门禁未实地核实。')
add('15','公共环境改善机会研究初筛','Research screening for amenity improvement','grid',field='research_amenity_priority',cmap='YlOrRd',note='等权：建筑密度百分位、已映射绿地不足百分位、日常服务可达路段不足百分位。仅研究初筛，不是旧改/拆迁名单。')
add('16','现状数据问题与改善机会','Evidence gaps and amenity priorities','issues',note='底色为透明初筛分数；叠加旧模型267端点复核位置，端点不自动视为错误。未分类地功能仍需补证。')
add('17','模型人口密度｜2020年100米','GHSL model population 2020','population',layer='population_ghsl2020',field='population_density_km2',cmap='YlOrRd',note='GHSL R2023A 2020原生100m格网，边界按像元面积比例裁切。模型不是普查街坊实测人口。')
add('18','模型人口密度｜2025年约1公里','WorldPop ALPHA model population 2025','population',layer='population_worldpop2025',field='population_density_km2',cmap='YlOrRd',note='WorldPop R2025A ALPHA原生约1km。保留粗网格，未降尺度到楼栋；与2020产品差异不能直接解释为人口增长。')
for id,title,key,cmap,note in [
 ('19','物理地表覆盖｜2021年','worldcover2021_10m','tab10','ESA WorldCover v200 10m物理覆盖，非功能/法定用地。'),
 ('20','夏季植被指数｜2026年9月14日','ndvi_summer2026_10m','YlGn','Sentinel-2 10m NDVI；排除SCL云阴影。已逐波段同景镜像交叉核验1000DN差并避免重复扣offset。'),
 ('21','冬季植被指数｜2026年2月21日','ndvi_winter2026_10m','YlGn','Sentinel-2 10m NDVI；冬夏植被差异含季节、太阳高度和物候影响，非绿化退化结论。'),
 ('22','夏季卫星地表温度｜2026年8月1日','lst_summer2026_effective100m','inferno','Landsat L2 ST温度°C；原始30m产品聚合到热红外有效100m。云掩膜后单景地表温度，不是实测气温。'),
 ('23','表面高程｜2021年约30米','dsm_copernicus2021_30m','terrain','Copernicus GLO30 DSM，含建筑和树冠；不是裸地DTM、道路实测高程或洪水淹没面。'),
 ('24','夏季水体光谱指数','ndwi_summer2026_10m','BrBG','Sentinel-2 NDWI=(绿光−近红外)/(绿光+近红外)，10m；不能直接等同真实水边界。'),
 ('25','夏季建成光谱指数','ndbi_summer2026_20m','RdYlBu_r','Sentinel-2 NDBI=(SWIR−NIR)/(SWIR+NIR)，20m；裸地等可混淆，不是法定建设用地。')]:add(id,title,key,'raster',layer=key,cmap=cmap,note=note)
if (ROOT/'outputs/gis/rasters/clcd2019_30m.tif').exists():add('26','历史物理地表覆盖｜2019年','CLCD historical physical land cover 2019','raster',layer='clcd2019_30m',cmap='tab10',note='CLCD2019原生约30米；仅选取压缩扫描行局部解码。与WorldCover2021年份/方法不同，不能直接把差异当真实变化。')
if (ROOT/'outputs/gis/rasters/jrc_water_occurrence1984_2021_30m.tif').exists():add('27','历史水面观测频率｜1984—2021','Historical water observation occurrence','raster',layer='jrc_water_occurrence1984_2021_30m',cmap='Blues',note='EC JRC GSW v1.4历史水面观测频率%；仅局部六瓦片压缩约20KB。不是2026水边界、洪水概率或法定蓝线。')
if (ROOT/'outputs/gis/rasters/ndvi_seasonal_difference2026_10m.tif').exists():add('28','冬夏植被指数季节差｜2026年','Summer minus winter NDVI on joint valid pixels','raster',layer='ndvi_seasonal_difference2026_10m',cmap='RdYlGn',note='9月14日NDVI减2月21日NDVI；只用双方有效像元10m。含物候、太阳角度与季节影响，不是永久绿化变化。')
colors={'residential':'#d6b386','public_service':'#b07896','commercial':'#ca8a7c','industrial':'#a59bb5','transport':'#a8aaad','green_open':'#99b895','water':'#87b7c4','construction':'#d7cb9d','unknown':'#eeeae2'}
landlabels=dict(zip(land['class'],land.class_name));catalog=[]
for item in items:
 id=item['id'];stem=id+'_'+item['title'].replace('｜','_').replace('/','_');paths={ext:ROOT/f'outputs/maps/A1/{stem}.{ext}' for ext in ['pdf','svg','png']}
 if all(p.exists() for p in paths.values()) and (ROOT/f'outputs/maps/A3_review/{stem}.pdf').exists() and (ROOT/f'reports/map_{id}.json').exists() and json.loads((ROOT/f'reports/map_{id}.json').read_text()).get('data_signature')==data_signature:
  print('cached',id,flush=True);saved=json.loads((ROOT/f'reports/map_{id}.json').read_text());catalog.append({**saved,'status':'generated','stem':stem});continue
 fig=plt.figure(figsize=(841/25.4,594/25.4),facecolor='#faf9f5');ax=fig.add_axes([.035,.14,.73,.74]);ax.set_facecolor('#f4f2ec')
 cx,cy=AOI.centroid.coords[0];scale=10000;extent=[cx-841/1000*.73*scale/2,cx+841/1000*.73*scale/2,cy-594/1000*.74*scale/2,cy+594/1000*.74*scale/2]
 ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
 if item['kind'] not in ['figure','raster']:b.plot(ax=ax,color='#dfdfda',edgecolor='none',zorder=1)
 handles=[];mappable=None;kind=item['kind'];findings=[]
 if kind=='land':
  for cl,group in land.groupby('class'):group.plot(ax=ax,color=colors[cl],edgecolor='none',zorder=2);handles.append(Patch(color=colors[cl],label=landlabels[cl]))
  unk=land.loc[land['class']=='unknown'].area.sum()/AOI.area*100;findings=[f'待核实功能面积占 {unk:.1f}%',f'分类面总覆盖研究边界 {AOI.area/1e6:.3f} km²（含待核实）']
 elif kind in ['grid','issues','population']:
  data=r(item['layer'],A) if kind=='population' else grid
  field=item['field'] if kind!='issues' else 'research_amenity_priority';finite=data[field].replace([np.inf,-np.inf],np.nan).dropna()
  vmax=float(finite.quantile(.98)) if len(finite) else 1;vmin=float(finite.min()) if len(finite) else 0
  data.plot(ax=ax,column=field,cmap=item['cmap'],edgecolor='#ffffff',linewidth=.12,zorder=2,vmin=vmin,vmax=max(vmin+1e-9,vmax),missing_kwds={'color':'#e8e5de','hatch':'///'})
  mappable=plt.cm.ScalarMappable(norm=plt.Normalize(vmin,max(vmin+1e-9,vmax)),cmap=item['cmap']);findings=[f'有效分析单元 {len(finite)} / {len(data)}',f'有效单元中位值 {finite.median():.3g}；显示上限P98 {vmax:.3g}']
  if kind=='issues':
   d=r('road_dangling_review');d.plot(ax=ax,color='#8b3939',markersize=7,zorder=5);handles=[Line2D([],[],marker='o',ls='',color='#8b3939',label='旧模型端点待复核（非确认错误）')]
 elif kind=='height':
  b.plot(ax=ax,column='height_m',cmap='YlOrBr',vmin=0,vmax=100,edgecolor='none',zorder=2);mappable=plt.cm.ScalarMappable(norm=plt.Normalize(0,100),cmap='YlOrBr');findings=[f'建筑体块 {len(b):,}',f'估高体块占100%；中位高度 {b.height_m.median():.1f} m']
 elif kind=='figure':b.plot(ax=ax,color='#3e4446',edgecolor='none',zorder=2);findings=[f'建筑轮廓并集占地 {union_all(b.geometry).area/1e6:.3f} km²','白地不等同可开发空地']
 elif kind=='road':
  major=['motorway','trunk','primary','secondary','tertiary'];palette=['#a66350','#ba8060','#c49c77','#9c9f99','#b9bbb5']
  for cl,c in zip(major,palette):
   d=roads[roads.highway.str.replace('_link','',regex=False)==cl];d.plot(ax=ax,color=c,linewidth=2.3-major.index(cl)*.3,zorder=3);handles.append(Line2D([],[],color=c,lw=2,label=cl))
  roads[~roads.highway.str.replace('_link','',regex=False).isin(major)].plot(ax=ax,color='#b4b7b1',linewidth=.6,zorder=2);findings=[f'研究区车行源线 {roads.intersection(AOI).length.sum()/1000:.1f} km','双幅分计；等级是OSM标签']
 elif kind=='bluegreen':
  green.plot(ax=ax,color='#91b094',edgecolor='none',zorder=2);blue.plot(ax=ax,color='#86b4c2',edgecolor='none',zorder=3);handles=[Patch(color='#91b094',label='已映射绿色空间'),Patch(color='#86b4c2',label='已映射水面')];findings=[f'绿地并集 {union_all(green.geometry).intersection(AOI).area/1e6:.3f} km²','面积不表示公共开放性或官方绿化率']
 elif kind=='access':
  d=r('access_'+item['layer'],A);palette={15:'#d3d8bb',10:'#93b49d',5:'#426f69'}
  for mins in [15,10,5]:d[d.minutes==mins].plot(ax=ax,color=palette[mins],linewidth=2.2,zorder=2+(15-mins)/5);handles.append(Line2D([],[],color=palette[mins],lw=3,label=f'{mins}分钟可达已映射路段'))
  seeds=r('access_seed_audit',A);seeds=seeds[seeds.kind==item['layer']];seeds.plot(ax=ax,color='#614b42',markersize=9,zorder=7)
  cv=pd.read_csv(ROOT/'reports/network_service_coverage.csv');cv=cv[(cv.kind==item['layer'])&(cv.minutes==15)].iloc[0];findings=[f'上下文合格接入节点 {int(cv.seed_nodes_context)}',f'15分钟可达已映射步行长度占 {cv.reachable_walk_m_aoi/cv.denominator_walk_m_aoi*100:.1f}%（非人口）']
 elif kind=='raster':
  with rasterio.open(ROOT/f'outputs/gis/rasters/{item["layer"]}.tif') as ds:
   a=ds.read(1,masked=True);bounds=ds.bounds;v=a.compressed();v=v[np.isfinite(v)];lo,hi=np.percentile(v,[2,98]);lo,hi=(float(v.min()),float(v.max())) if hi<=lo else (lo,hi);cmap=item['cmap']
   if id=='26':
    cs=['#dbc589','#438158','#a2a75d','#b6c783','#80afc3','#e7edf2','#d6d0c5','#b3a29b','#7aa99b'];names=['耕地','林地','灌丛','草地','水体','冰雪','裸地','不透水','湿地'];cmap=ListedColormap(cs);norm=BoundaryNorm(np.arange(.5,10,1),9);ax.imshow(a,extent=[bounds.left,bounds.right,bounds.bottom,bounds.top],cmap=cmap,norm=norm,zorder=2);handles=[Patch(color=c,label=n) for cl,n,c in zip(range(1,10),names,cs) if cl in np.unique(v)];mappable=None
   elif id=='19':
    wc=[10,20,30,40,50,60,70,80,90,95,100];names=['树木','灌丛','草地','耕地','建成覆盖','裸地','冰雪','水体','湿地','红树林','苔藓'];cs=['#438158','#a2a75d','#b6c783','#dbc589','#b3a29b','#d6d0c5','#e7edf2','#80afc3','#7aa99b','#5e9088','#bbc2a6'];cmap=ListedColormap(cs);norm=BoundaryNorm([5,15,25,35,45,55,65,75,85,92,97,105],11);mappable=ax.imshow(a,extent=[bounds.left,bounds.right,bounds.bottom,bounds.top],cmap=cmap,norm=norm,zorder=2);handles=[Patch(color=c,label=n) for cl,n,c in zip(wc,names,cs) if cl in np.unique(v)];mappable=None
   else:mappable=ax.imshow(a,extent=[bounds.left,bounds.right,bounds.bottom,bounds.top],cmap=cmap,vmin=lo,vmax=hi,zorder=2)
   findings=[f'有效像元统计中位值 {np.median(v):.3g}',f'色阶P2—P98，无跨度用全值域；有效像元 {len(v):,}']
 if id=='27':findings.append('历史频率最高48%；不能否定窄河渠的存在')
 # Boundary, labels and true metric scale bar.
 gpd.GeoSeries([AOI],crs=32651).boundary.plot(ax=ax,color='#354d55',linewidth=1.2,zorder=12)
 labelroads=roads[(roads.name!='')&roads.intersects(AOI)].sort_values('length_m',ascending=False).drop_duplicates('name').head(9)
 for rr in labelroads.itertuples():
  p=rr.geometry.interpolate(.5,normalized=True)
  if AOI.covers(p):ax.text(p.x,p.y,rr.name,fontsize=7,color='#485354',ha='center',bbox={'facecolor':'#faf9f5','alpha':.72,'edgecolor':'none','pad':1},zorder=15)
 x=extent[0]+180;y=extent[2]+180;ax.plot([x,x+1000],[y,y],color='#33454a',lw=2,zorder=20)
 for d in [0,500,1000]:ax.plot([x+d,x+d],[y-20,y+20],color='#33454a',lw=1,zorder=20);ax.text(x+d,y-45,str(d),ha='center',va='top',fontsize=9,zorder=20)
 ax.text(x+1140,y,'m',va='center');ax.annotate('N',xy=(extent[1]-150,extent[3]-450),xytext=(extent[1]-150,extent[3]-150),ha='center',arrowprops={'arrowstyle':'<-','lw':1.5},fontsize=13)
 fig.text(.035,.945,f'{id}  {item["title"]}',fontsize=28,color='#253e44',weight='bold');fig.text(.037,.911,item['en'],fontsize=15,color='#6d7a7b')
 panel=fig.add_axes([.79,.18,.185,.67]);panel.axis('off');panel.text(0,1,'图例 / LEGEND',fontsize=16,va='top',color='#365357')
 if handles:panel.legend(handles=handles,loc='upper left',bbox_to_anchor=(-.05,.95),frameon=False,fontsize=11)
 if mappable is not None:
  cax=fig.add_axes([.80,.67,.15,.017]);fig.colorbar(mappable,cax=cax,orientation='horizontal');cax.tick_params(labelsize=10)
 import textwrap
 def wrap(t,n=22):return '\n'.join(textwrap.wrap(t,n,break_long_words=True))
 panel.text(0,.50,'主要发现 / FINDINGS',fontsize=14,color='#365357',va='top')
 panel.text(0,.44,'\n\n'.join(wrap('• '+f) for f in findings[:3]),fontsize=11,va='top',linespacing=1.5)
 panel.text(0,.18,'方法与适用性 / METHOD',fontsize=14,color='#365357',va='top');panel.text(0,.12,wrap(item['note']),fontsize=10,va='top',linespacing=1.5)
 fig.text(.035,.08,'上海城市规划现状研究  |  AOI 22.009 km²  |  EPSG:32651  |  A1 841×594mm  |  1:10,000',fontsize=12,color='#42575c')
 fig.text(.035,.05,'来源：© OpenStreetMap contributors（ODbL） / Overture 2026-10-21；ESA/Copernicus、USGS、GHSL或WorldPop（各专题详见来源表）。',fontsize=10,color='#737d7e')
 fig.text(.035,.028,'公开数据与模型研究成果；非测绘、非法定规划。数据年份与采集时间分开记录；设施未映射不等于真实缺失。生成日期：2026-10-26。',fontsize=10,color='#737d7e')
 for ext,path in paths.items():fig.savefig(path,dpi=120,facecolor=fig.get_facecolor())
 # A3 physical page via verified PDF scaling; exact resulting map ratio disclosed.
 import fitz
 source=fitz.open(paths['pdf']);review=fitz.open();page=review.new_page(width=420/25.4*72,height=297/25.4*72)
 target=page.rect;page.show_pdf_page(target,source,0,keep_proportion=True)
 ratio=10000*841/420
 # Replace the A1 scale/page line in the reduced sheet; fixed 1km graphical scale stays valid.
 cover=fitz.Rect(12, target.height*.905, target.width*.79,target.height*.932);page.draw_rect(cover,color=None,fill=(.9804,.9765,.9608),overlay=True)
 page.insert_text((16,target.height*.922),f'A3 REVIEW 420 x 297 mm | EPSG:32651 | Scale 1:{ratio:,.2f} | AOI 22.009 km2',fontsize=6,color=(.26,.34,.36))
 review.save(ROOT/f'outputs/maps/A3_review/{stem}.pdf');review.close();source.close()
 plt.close(fig)
 item['findings']=findings;catalog.append({**item,'status':'generated','stem':stem});dump(ROOT/f'reports/map_{id}.json',{**item,'data_signature':data_signature,'extent_32651':extent,'A1_map_scale':10000,'A1_mm':[841,594],'A3_mm':[420,297],'A3_map_scale':10000*841/420,'source_registry':'reports/source_registry.csv'})
 progress('cartography',id,'complete',stem=stem);print('generated',id,flush=True)
pd.DataFrame(catalog).to_csv(ROOT/'reports/map_catalog.csv',index=False)
thumbs=[]
for row in catalog:
 with Image.open(ROOT/f'outputs/maps/A1/{row["stem"]}.png') as im:
  im.thumbnail((520,380));tile=Image.new('RGB',(540,405),'#faf9f5');tile.paste(im,((540-im.width)//2,0));ImageDraw.Draw(tile).text((10,385),row['id'],fill='#263d42');thumbs.append(tile)
index=Image.new('RGB',(540*5,405*((len(thumbs)+4)//5)),'white')
for i,t in enumerate(thumbs):index.paste(t,((i%5)*540,(i//5)*405))
index.save(ROOT/'outputs/maps/INDEX.png');progress('cartography','atlas','complete',count=len(catalog))
