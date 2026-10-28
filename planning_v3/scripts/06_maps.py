from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager
from matplotlib.colors import ListedColormap,BoundaryNorm,LinearSegmentedColormap
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import rasterio,textwrap,pymupdf
from PIL import Image,ImageDraw
fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','pdf.fonttype':42,'svg.fonttype':'path','axes.unicode_minus':False,'font.size':11})
STYLE=json.loads((ROOT/'styles/COLOR_STYLE_SYSTEM.json').read_text());SAT=json.loads((ROOT/'reports/satellite_provenance.json').read_text());SITE=read('DESIGN_SITE',D).geometry.iloc[0]
b=read('buildings_enriched');roads=read('road_network_vehicle');land=read('landuse_existing');green=read('green_spaces_all');water=read('blue_network');poi=read('poi_all');junctions=read('source_node_intersections',A);junctions=junctions[junctions['mode']=='vehicle'];rail=read('transit_lines');rail=rail[rail.route_mode.isin(['subway','tram','train'])]
G100=read('grid_100m',D);G200=read('grid_200m',D);GRIDS={100:G100,200:G200};maps=[]
for p in sorted((V2/'reports').glob('map_[0-9][0-9].json')):
 item=json.loads(p.read_text());item['series']='regional';item['scope']='whole AOI';item['scale']=10000;item['base_mode']='A';item.pop('data_signature',None);maps.append(item)
changes={'02':(100,'building_density'),'04':(100,'volume_proxy_m'),'06':(200,'land_function_entropy'),'08':(200,'vehicle_density_km_km2'),'11':(200,'commercial_density_km2'),'15':(100,'research_amenity_priority'),'16':(100,'research_amenity_priority')}
for m in maps:
 if m['id'] in changes:m['grid_size'],m['field']=changes[m['id']];m['kind']='grid' if m['id']!='16' else 'issues'
 if m['id']=='06':m['title']='已映射土地功能面积混合度';m['en']='Mapped land-function area diversity';m['note']='200m；按已映射功能面面积计算H/ln(8)，未知不入确定用途；已知功能面积比例不足50%不计算。与V2的POI熵是不同指标。'
 if m['id']=='11':m['title']='商业POI观察密度';m['note']='200m网格；真实观测点数/裁切单元面积（POI/km²），零值不表示无商业。KDE100/200/400m仅作敏感性对照，不代表客流。'
 if m['id']=='08':m['note']='200m；源线km/实际单元km²，双幅分计。叠加真实源节点度≥3的车行路口，桥隧几何交叉不增节点。'
 if m['id'] in ['02','04','15','16']:m['note']+=' V3改为100m真实相交重算；设计线仅标注，不改变全域统计口径。'
 if m['id']=='18':m['note']='保持WorldPop2025 ALPHA原生约1km的48个裁切单元；不插值到100m。与2020不同模型不可解释为人口真实变化。'
for id,title,en,mode,scale in [('S01','研究区卫星影像总览','Satellite Context Map','B',10000),('S02','核心设计区卫星现状','Design Site Satellite Map','B',4000),('S03','卫星影像与城市综合空间','Urban Spatial Structure on Satellite Imagery','C',10000)]:
 maps.append({'id':id,'title':title,'en':en,'kind':'satellite','series':'satellite','scope':'design-context view' if id=='S02' else 'whole AOI','scale':scale,'base_mode':mode,'note':f'真实Sentinel-2 TCI，自然色，拍摄{SAT["acquisition_datetime"][:10]}，原生10m；许可Copernicus Sentinel开放数据。未取得可离线再分发的0.5–2m正射影像，不虚构建筑级细节。设计内外采用相同影像权重。'})
refined=[('R01','建筑基底覆盖率｜100米','Building footprint coverage',100,'building_density'),('R02','估高建筑体量代理｜100米','Estimated volume proxy',100,'volume_proxy_m'),('R03','已映射土地功能混合｜200米','Mapped land-function area diversity',200,'land_function_entropy'),('R04','车行路网与真实节点｜200米','Vehicle density and source-node junctions',200,'vehicle_density_km_km2'),('R05','商业观察密度｜200米','Observed commercial POI density',200,'commercial_density_km2'),('R06','公共环境改善机会｜100米','Research amenity-improvement screening',100,'research_amenity_priority'),('R07','数据问题与改善机会｜100米','Evidence issues and improvement screening',100,'research_amenity_priority'),('R08','2025模型人口｜原生约1公里','Native WorldPop population model 2025',None,'population_density_km2')]
for id,title,en,size,field in refined:
 maps.append({'id':id,'title':title,'en':en,'kind':'population' if id=='R08' else ('issues' if id=='R07' else 'grid'),'series':'refined_analysis','scope':'design-context view; metrics still whole-AOI source units','scale':5000,'base_mode':'C' if id=='R08' else 'A','grid_size':size,'field':field,'layer':'population_worldpop2025' if id=='R08' else None,'note':('原生人口单元保持不变；卫星与建筑只增加空间参照，不制造人口局部差异。' if id=='R08' else '采用与全域相同固定分级；只是局部放大视图，不将设计线变成强制统计裁切。')+' '+({'R01':'50m真实相交结果另存，100m为正式表达。','R02':'m³/m²；所有高度均非测绘，非容积率。','R03':'未知用地不当已知类别；已知比例<50%留空，另有剔除在建类敏感性。','R04':'只保留真实源拓扑；不把高架上下交点当路口。','R05':'观察点密度，不是客流/就业；带宽100/200/400m对照见报告。','R06':'V2三项等权体系沿用；不是政府更新、拆迁或建设名单。','R07':'点线面问题保留原位置，不是所有问题格网化。','R08':'2025 ALPHA模型，非普查实测人口。'}[id])})
with rasterio.open(ROOT/'data/satellite/sentinel_truecolor_10m_context.tif') as ds:rgb=np.moveaxis(ds.read(),0,-1)/255.;sat_bounds=ds.bounds
snap=sha(ROOT/'styles/COLOR_STYLE_SYSTEM.json')+sha(D)+sha(ROOT/'data/satellite/sentinel_truecolor_10m_context.tif')+'maps-v3.4'
def sym(layer,data,field,alpha=1):
 style=STYLE['metric_styles'][field];colors=STYLE['palettes'][style['palette']];bounds=style['breaks'];cmap=ListedColormap(colors);norm=BoundaryNorm(bounds,len(colors),clip=True)
 data.plot(ax=layer,column=field,cmap=cmap,norm=norm,edgecolor='none',zorder=3,missing_kwds={'color':'#D5D5CB'},alpha=alpha)
 handles=[Patch(color=c,label=f'{bounds[i]:,.3g} – {bounds[i+1]:,.3g}') for i,c in enumerate(colors)]
 if data[field].isna().any():handles.append(Patch(color='#D5D5CB',label='资料/有效覆盖不足，未计算'))
 return handles,style['unit']
def satellite(ax,mode):
 image=rgb if mode=='B' else rgb*.72+np.array([248,247,242])/255*.28
 ax.imshow(image,extent=[sat_bounds.left,sat_bounds.right,sat_bounds.bottom,sat_bounds.top],interpolation='nearest',zorder=0)
def extent_for(item):
 center=SITE.centroid if item['scope'].startswith('design') else AOI.centroid;w=.73*.841*item['scale'];h=.74*.594*item['scale'];return [center.x-w/2,center.x+w/2,center.y-h/2,center.y+h/2]
catalog=[]
for item in maps:
 id=item['id'];stem=id+'_'+item['title'].replace('｜','_').replace('/','_');paths={ext:ROOT/f'outputs/maps/A1/{stem}.{ext}' for ext in ['pdf','svg','png']};meta=ROOT/f'reports/map_{id}.json';a3=ROOT/f'outputs/maps/A3_review/{stem}.pdf'
 if meta.exists() and json.loads(meta.read_text()).get('signature')==snap and all(p.exists() for p in paths.values()) and a3.exists():catalog.append(json.loads(meta.read_text()));print('CACHED',id,flush=True);continue
 fig=plt.figure(figsize=(841/25.4,594/25.4),facecolor=STYLE['base']['paper']);ax=fig.add_axes([.035,.14,.73,.74]);ax.set_facecolor('#EFEEE7');extent=extent_for(item);ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
 mode=item['base_mode'];kind=item['kind'];handles=[];units='';findings=[]
 if mode in ['B','C']:satellite(ax,mode)
 elif kind not in ['figure','raster']:b.plot(ax=ax,color=STYLE['base']['buildings'],edgecolor='none',zorder=1)
 if kind in ['grid','issues']:
  data=GRIDS[item['grid_size']];field=item['field'];handles,units=sym(ax,data,field)
  view=box(*[extent[0],extent[2],extent[1],extent[3]]) if False else __import__('shapely').geometry.box(extent[0],extent[2],extent[1],extent[3]);v=data.loc[data.intersects(view),field];findings=[f'{item["grid_size"]}m真实几何统计；视图内{len(v)}个单元',f'有效{v.notna().sum()}；中位值{v.median():.3g}']
  if field=='land_function_entropy':findings.append(f'全域已知功能占比仍约52.33%；低覆盖单元不计算')
  if id in ['08','R04']:
   j=junctions[junctions.intersects(view)];j.plot(ax=ax,color='#37525A',markersize=6,zorder=8);handles.append(Line2D([],[],color='#37525A',marker='o',ls='',label='真实源节点车行度≥3'))
  if id=='R05':
   pp=poi[(poi.category=='commercial')&poi.intersects(view)];pp.plot(ax=ax,color='#503A23',markersize=13,zorder=8);handles.append(Line2D([],[],color='#503A23',marker='o',ls='',label='已映射商业观察点'));findings.append(f'局部观察点{len(pp)}；零格不能证明无商业')
  if kind=='issues':
   dangling=read('road_dangling_review');dangling.plot(ax=ax,color='#876843',markersize=8,zorder=9);handles.append(Line2D([],[],color='#876843',marker='o',ls='',label='原端点复核位置（非确认错误）'))
 elif kind=='population':
  data=read(item['layer'],A);handles,units=sym(ax,data,item['field'],.65 if id=='R08' else 1);findings=[f'原生模型：{len(data)}个AOI裁切格网','2025约1km / 2020约100m；不重新细分']
  if id=='R08':
   data.boundary.plot(ax=ax,color='#47606E',linewidth=.7,zorder=7);b.boundary.plot(ax=ax,color='#F0F1E8',linewidth=.23,alpha=.75,zorder=8)
 elif kind=='land':
  for cl,group in land.groupby('class'):group.plot(ax=ax,color=STYLE['landuse'][cl],edgecolor='none',zorder=3);handles.append(Patch(color=STYLE['landuse'][cl],label=group.class_name.iloc[0]))
  findings=['未知功能保留，非法定用途调查','设计线仅标注，不改变22.009km²统计范围']
 elif kind=='height':handles,units=sym(ax,b,'height_m');findings=['11,856个体块；实测高度0','11,833默认/上下文估高，23由层数推算']
 elif kind=='figure':b.plot(ax=ax,color='#3D5054',edgecolor='none',zorder=2);findings=['保留原始建筑几何','白地不自动认定为空地或可开发空间']
 elif kind=='road':
  major=['motorway','trunk','primary','secondary','tertiary'];colors=['#4D676B','#5F7A7C','#799393','#96AAA7','#B4C3BA']
  for j,(cl,c) in enumerate(zip(major,colors)):
   rr=roads[roads.highway.str.replace('_link','',regex=False)==cl];rr.plot(ax=ax,color=c,linewidth=2.2-j*.25,zorder=5);handles.append(Line2D([],[],color=c,lw=2,label=cl))
  roads[~roads.highway.str.replace('_link','',regex=False).isin(major)].plot(ax=ax,color='#8E9899',linewidth=.5,zorder=3);findings=['道路几何与等级标签沿用V2','层级、桥隧和真实节点拓扑保留']
 elif kind=='bluegreen':green.plot(ax=ax,color='#7C9F78',edgecolor='none',zorder=3);water.plot(ax=ax,color='#6B9DAD',edgecolor='none',zorder=4);handles=[Patch(color='#7C9F78',label='已映射绿色空间'),Patch(color='#6B9DAD',label='已映射水面')];findings=['开放性不等于绿量','不将已映射面积称为官方绿化率']
 elif kind=='access':
  d=read('access_'+item['layer'],A)
  for mins,c in [(15,'#A4BFB1'),(10,'#6B9C91'),(5,'#326C69')]:d[d.minutes==mins].plot(ax=ax,color=c,linewidth=2,zorder=4+(15-mins)/5);handles.append(Line2D([],[],color=c,lw=3,label=f'{mins}分钟已映射可达路段'))
  seeds=read('access_seed_audit',A);seeds[seeds.kind==item['layer']].plot(ax=ax,color='#5F5542',markersize=8,zorder=9);findings=['复用V2真实源节点步行分析，4.5km/h','设施接入和门禁不确定性保留；非人口覆盖率']
 elif kind=='raster':
  with rasterio.open(ROOT/f'data/rasters_v2/{item["layer"]}.tif') as ds:
   array=ds.read(1,masked=True);v=array.compressed();lo,hi=np.percentile(v,[2,98]);lo,hi=(v.min(),v.max()) if hi<=lo else (lo,hi);bounds=ds.bounds;name=item['layer'];palette='ndvi' if 'ndvi_' in name else 'water' if 'occurrence' in name else 'ndwi' if 'ndwi' in name else 'ndbi' if 'ndbi' in name else 'temperature' if 'lst_' in name else 'dsm';palette='seasonal' if 'difference' in name else palette
   if id in ['19','26']:
    codes=[10,20,30,40,50,60,70,80,90,95,100] if id=='19' else list(range(1,10));labels=['树木','灌丛','草地','耕地','建成覆盖','裸地','冰雪','水体','湿地','红树林','苔藓'] if id=='19' else ['耕地','林地','灌丛','草地','水体','冰雪','裸地','不透水','湿地'];colors=['#628568','#A5A56D','#92AE78','#C7B579','#A18C80','#B8AE97','#CBD6D8','#6595A7','#76A28E','#497C72','#A8B29C'] if id=='19' else ['#C7B579','#628568','#A5A56D','#92AE78','#6595A7','#CBD6D8','#B8AE97','#A18C80','#76A28E'];rgba=np.ones(array.shape+(4,));rgba[:,:,:3]=np.array([248,247,242])/255
    for code,color,label in zip(codes,colors,labels):
     from matplotlib.colors import to_rgb
     rgba[array.data==code,:3]=to_rgb(color)
     if code in v:handles.append(Patch(color=color,label=label))
    rgba[:,:,3]=~np.ma.getmaskarray(array);ax.imshow(rgba,extent=[bounds.left,bounds.right,bounds.bottom,bounds.top],interpolation='nearest',zorder=3)
   else:
    if palette=='ndvi':lo,hi=-.2,.8
    if palette in ['ndwi','ndbi']:lo,hi=-.8,.8
    if palette=='seasonal':lo,hi=-.5,.5
    cmap=LinearSegmentedColormap.from_list(palette,STYLE['palettes'][palette]);im=ax.imshow(array,extent=[bounds.left,bounds.right,bounds.bottom,bounds.top],cmap=cmap,vmin=lo,vmax=hi,interpolation='nearest',zorder=3);cax=fig.add_axes([.80,.68,.15,.017]);fig.colorbar(im,cax=cax,orientation='horizontal',extend='both');units='原始分辨率与单位见方法'
   findings=[f'有效像元{len(v):,}；中位数{np.median(v):.3g}','源栅格复用，不改分辨率或数据值']
 elif kind=='satellite':
  if mode=='C':
   b.boundary.plot(ax=ax,color='#E8E9E2',linewidth=.22,alpha=.75,zorder=3);roads.plot(ax=ax,color='#355F69',linewidth=.5,alpha=.8,zorder=4);green.plot(ax=ax,color='#7C9F78',edgecolor='none',alpha=.35,zorder=4);water.plot(ax=ax,color='#6B9DAD',edgecolor='none',alpha=.65,zorder=5);rail.plot(ax=ax,color='#745E79',linewidth=1.0,zorder=6);handles=[Line2D([],[],color='#E8E9E2',lw=1,label='建筑轮廓'),Line2D([],[],color='#355F69',lw=1,label='道路源网络'),Patch(color='#7C9F78',label='绿色空间'),Patch(color='#6B9DAD',label='水面'),Line2D([],[],color='#745E79',lw=1,label='轨道交通')]
  findings=[f'拍摄：{SAT["acquisition_datetime"][:10]}；原生10m',f'真实设计范围：{SITE.area/10000:.4f}公顷','真彩色影像，不是NDVI/LST或合成细节']
 if kind=='raster':item['raster_style']={'palette':palette,'vmin':float(lo),'vmax':float(hi),'categorical_codes':codes if id in ['19','26'] else None,'categorical_colors':colors if id in ['19','26'] else None,'categorical_labels':labels if id in ['19','26'] else None}
 # AOI boundary and design ring. No filled design polygon, outside dimming mask or differential alpha.
 gpd.GeoSeries([AOI],crs=32651).boundary.plot(ax=ax,color='#526A70',linewidth=.8,zorder=15)
 line=gpd.GeoSeries([SITE.boundary],crs=32651);line.plot(ax=ax,color='white',linewidth=1.65*72/25.4,zorder=29);line.plot(ax=ax,color='#CB493E',linewidth=1.2*72/25.4,zorder=30);handles.append(Line2D([],[],color='#CB493E',lw=1.2*72/25.4,label='核心设计范围 / Design Site'))
 view=__import__('shapely').geometry.box(extent[0],extent[2],extent[1],extent[3]);labels=roads[(roads.name!='')&roads.intersects(view)].sort_values('length_m',ascending=False).drop_duplicates('name').head(6)
 for rr in labels.itertuples():
  p=rr.geometry.intersection(view).interpolate(.5,normalized=True)
  if not p.is_empty:ax.text(p.x,p.y,rr.name,fontsize=8,color='#24465B',ha='center',bbox={'facecolor':'#F8F7F2','alpha':.8,'edgecolor':'none','pad':1},zorder=20)
 scale=item['scale'];bar=1000 if scale==10000 else 500
 sax=fig.add_axes([.040,.105,.20,.025]);sax.set_xlim(0,.20*.841*scale);sax.set_ylim(0,1);sax.axis('off');sax.plot([0,bar],[.6,.6],color='#24465B',lw=2)
 for dd in [0,bar/2,bar]:sax.plot([dd,dd],[.45,.75],color='#24465B',lw=1);sax.text(dd,.30,str(int(dd)),ha='center',va='top',fontsize=9)
 sax.text(bar*1.1,.6,'m',va='center',fontsize=10)
 ax.set_xlabel('');ax.set_ylabel('');ax.annotate('N',xy=(extent[1]-.035*(extent[1]-extent[0]),extent[3]-.12*(extent[3]-extent[2])),xytext=(extent[1]-.035*(extent[1]-extent[0]),extent[3]-.04*(extent[3]-extent[2])),ha='center',arrowprops={'arrowstyle':'<-','lw':1.5},fontsize=13)
 fig.text(.035,.946,f'{id}  {item["title"]}',fontsize=27,color='#24465B',weight='bold');fig.text(.037,.913,item['en'],fontsize=14,color='#587474')
 panel=fig.add_axes([.79,.17,.19,.68]);panel.axis('off');panel.text(0,1,'图例 / LEGEND',va='top',fontsize=15,color='#24465B')
 if handles:panel.legend(handles=handles,loc='upper left',bbox_to_anchor=(-.05,.96),frameon=False,fontsize=10,handlelength=2)
 def wrap(t,n=25):return '\n'.join(textwrap.wrap(t,n,break_long_words=True))
 panel.text(0,.49,'主要发现 / FINDINGS',fontsize=14,color='#24465B',va='top');panel.text(0,.43,'\n\n'.join(wrap('• '+f) for f in findings[:3]),fontsize=10.5,va='top',linespacing=1.4)
 panel.text(0,.20,'指标与方法 / METHOD',fontsize=14,color='#24465B',va='top');panel.text(0,.14,wrap((units+'。' if units else '')+item['note']),fontsize=9.5,va='top',linespacing=1.35)
 fig.text(.035,.083,f'SHANGHAI PLANNING GIS V3  |  EPSG:32651  |  A1 841×594mm  |  1:{scale:,}  |  设计范围66.0948ha',fontsize=11,color='#24465B')
 fig.text(.035,.053,'来源：© OpenStreetMap contributors（ODbL）/ Overture；ESA、Copernicus、EC-JRC、USGS、WorldPop。年份与指标定义详见图注及来源表。',fontsize=9.5,color='#657575')
 fig.text(.035,.032,f'可选B/C底图：Contains modified Copernicus Sentinel data (2026), acquired {SAT["acquisition_datetime"][:10]}, native10m。专题日期见图注；无设计填充/外围灰化。',fontsize=9.5,color='#657575')
 for ext,path in paths.items():fig.savefig(path,dpi=120,facecolor=fig.get_facecolor())
 # Adapt A3 physically: minimum7pt text rather than unreadable4.75pt shrink-only review.
 fig.set_size_inches(420/25.4,297/25.4)
 for text in fig.findobj(match=matplotlib.text.Text):text.set_fontsize(max(7,text.get_fontsize()*.55))
 for line in fig.findobj(match=matplotlib.lines.Line2D):line.set_linewidth(max(.2,line.get_linewidth()*.5))
 for axes in fig.axes:
  for collection in axes.collections:
   if hasattr(collection,'get_linewidths'):collection.set_linewidths(np.array(collection.get_linewidths())*.5)
   if hasattr(collection,'get_sizes'):collection.set_sizes(np.array(collection.get_sizes())*.25)
 ratio=scale*841/420
 # Replace the physical A1 label; retained graphical scale stays geographically correct.
 for text in fig.texts:
  if text.get_position()==(.035,.083):text.set_text(f'GIS V3 | EPSG:32651 | A3 420×297mm | 1:{ratio:,.2f} | 设计范围66.0948ha')
 fig.savefig(a3,dpi=120,facecolor=fig.get_facecolor());plt.close(fig)
 record={**item,'signature':snap,'stem':stem,'extent':extent,'fixed_style':STYLE['metric_styles'].get(item.get('field',''),{}),'findings':findings,'A1_mm':[841,594],'A1_scale':scale,'A3_mm':[420,297],'A3_scale':ratio,'A3_min_font_pt':7,'design_line_mm':1.2,'design_fill':'none','outside_mask':False};dump(meta,record);catalog.append(record);print('MAP',id,flush=True)
 # Separate series output paths are actual files via hard links where supported, no path placeholders.
 if item['series']!='regional':
  for ext,p in paths.items():
   dst=ROOT/f'outputs/maps/{item["series"]}/{stem}.{ext}'
   if dst.exists():dst.unlink()
   try:dst.hardlink_to(p)
   except OSError:shutil.copy2(p,dst)
pd.DataFrame(catalog).to_csv(ROOT/'reports/map_catalog_v3.csv',index=False)
thumbs=[]
for record in catalog:
 with Image.open(ROOT/f'outputs/maps/A1/{record["stem"]}.png') as im:
  im.thumbnail((490,345));tile=Image.new('RGB',(510,370),'#F8F7F2');tile.paste(im,((510-im.width)//2,0));ImageDraw.Draw(tile).text((12,350),record['id'],fill='#24465B');thumbs.append(tile)
index=Image.new('RGB',(510*5,370*((len(thumbs)+4)//5)),'white')
for i,t in enumerate(thumbs):index.paste(t,((i%5)*510,(i//5)*370))
index.save(ROOT/'outputs/previews/INDEX_V3.png');dump(ROOT/'reports/map_catalog_v3.json',catalog);checkpoint('maps',count=len(catalog),A1_complete=True,A3_complete=True)
