import os,json,sys
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_CACHE_HOME']='/workspace/.cache'
from qgis.core import *
from qgis.PyQt.QtGui import QColor,QFont,QFontDatabase
from qgis.PyQt.QtCore import Qt
P=Path(__file__).resolve().parents[1];G=P/'data/location_context.gpkg';app=QgsApplication([],False);app.initQgis();pr=QgsProject.instance();pr.setCrs(QgsCoordinateReferenceSystem('EPSG:32651'));pr.setFilePathStorage(Qgis.FilePathType.Relative);root=pr.layerTreeRoot()
FULL='--full' in sys.argv
for fp in (P/'fonts').glob('*.ttf'):assert QFontDatabase.addApplicationFont(str(fp))>=0
stats=json.loads((P/'reports/data_validation.json').read_text());qa=[]
def vect(layer,name,group):
 v=QgsVectorLayer(str(G)+'|layername='+layer,name,'ogr');assert v.isValid(),name;pr.addMapLayer(v,False);group.addLayer(v);return v
def fill(v,color,edge='transparent',width=.1):
 v.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({'color':color,'outline_color':edge,'outline_width':str(width),'outline_style':'no' if edge=='transparent' else 'solid'})))
def line(v,color,width=.2,dash=False):
 v.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({'line_color':color,'line_width':str(width),'line_style':'dash' if dash else 'solid','capstyle':'round','joinstyle':'round'})))
def labeling(v,field,size,color,placement='point'):
 pal=QgsPalLayerSettings();pal.fieldName=field;f=QgsTextFormat();f.setFont(QFont('Shanghai Location Sans',size));f.setSize(size);f.setColor(QColor(color));buf=QgsTextBufferSettings();buf.setEnabled(True);buf.setSize(.7);buf.setColor(QColor('#fffffb'));f.setBuffer(buf);pal.setFormat(f)
 if placement=='line':pal.placement=Qgis.LabelPlacement.Line;pal.mergeLines=True
 else:pal.placement=Qgis.LabelPlacement.OrderedPositionsAroundPoint;pal.dist=2
 v.setLabeling(QgsVectorLayerSimpleLabeling(pal));v.setLabelsEnabled(True)
def marker(v,color,size=2.6,stroke='white'):
 v.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({'name':'circle','color':color,'outline_color':stroke,'outline_width':'0.35','size':str(size)})))
def rect(layout,x,y,w,h,color):
 a=QgsLayoutItemShape(layout);a.setShapeType(QgsLayoutItemShape.Rectangle);a.setSymbol(QgsFillSymbol.createSimple({'color':color,'outline_style':'no'}));layout.addLayoutItem(a);a.attemptMove(QgsLayoutPoint(x,y));a.attemptResize(QgsLayoutSize(w,h));return a
def label(layout,text,x,y,w,h,size=12,color='#33413b',bold=False):
 a=QgsLayoutItemLabel(layout);a.setText(text);f=QFont('Shanghai Location Sans',size);f.setBold(bold);a.setFont(f);a.setFontColor(QColor(color));a.setMargin(0);a.setVAlign(Qt.AlignTop);layout.addLayoutItem(a);a.attemptMove(QgsLayoutPoint(x,y));a.attemptResize(QgsLayoutSize(w,h));return a
def wrap_cn(text,width=46):
 out=[]
 while len(text)>width:
  cut=width
  while cut<len(text) and text[cut] in '、，。；：？！）》】':cut+=1
  if text[cut-1] in '（《【':cut-=1
  out.append(text[:cut]);text=text[cut:]
 out.append(text);return '\n'.join(out)
def mapitem(layout,layers,x,y,w,h,extent,color):
 a=QgsLayoutItemMap(layout);layout.addLayoutItem(a);a.attemptMove(QgsLayoutPoint(x,y));a.attemptResize(QgsLayoutSize(w,h));a.setCrs(pr.crs());a.setLayers(layers);a.setKeepLayerSet(True);a.setKeepLayerStyles(True);a.setBackgroundEnabled(True);a.setBackgroundColor(QColor(color));a.zoomToExtent(extent);return a
def scale(layout,mp,x,y,units=500):
 s=QgsLayoutItemScaleBar(layout);s.setStyle('Line Ticks Middle');s.setLinkedMap(mp);s.setUnits(Qgis.DistanceUnit.Meters);s.setUnitsPerSegment(units);s.setNumberOfSegments(2);s.setNumberOfSegmentsLeft(0);s.setUnitLabel('m');s.setFont(QFont('Shanghai Location Sans',9));s.setLineWidth(.2);layout.addLayoutItem(s);s.attemptMove(QgsLayoutPoint(x,y));return s
for id in ['01','02']:
 g=root.addGroup(id+'｜'+('水绿与城市肌理' if id=='01' else '走廊与资源节点'))
 accent='#637e71' if id=='01' else '#a76d3b';bg='#f5f4ee';green='#b8c7a5' if id=='01' else '#9cba89';water='#8eafb7' if id=='01' else '#79aab5'
 b=vect('buildings_enriched','建筑轮廓',g);fill(b,'#d8d9d3' if id=='01' else '#e3e3d9')
 gr=vect('green_spaces_all','已记录绿地',g);fill(gr,green)
 wa=vect('blue_network','已记录水面',g);fill(wa,water)
 wc=vect('waterway_centerlines','已记录河道',g);line(wc,water,.45 if id=='01' else .65)
 ro=vect('road_network_vehicle','道路网络（线宽仅作制图分级）',g)
 rr=QgsRuleBasedRenderer(QgsLineSymbol.createSimple({'line_color':'#cecec4','line_width':'.14'}));rt=rr.rootRule();rt.removeChildAt(0)
 for cls,color,width in [("'motorway','motorway_link','trunk','trunk_link'",'#aeb4af' if id=='01' else '#d59a50',.62 if id=='01' else 1.05),("'primary','primary_link'",'#b7bdb7' if id=='01' else '#dcb77b',.45 if id=='01' else .72),("'secondary','secondary_link','tertiary','tertiary_link'",'#c7ccc5' if id=='01' else '#c5bd9b',.28 if id=='01' else .42)]:
  rule=QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({'line_color':color,'line_width':str(width),'capstyle':'round','joinstyle':'round'}));rule.setFilterExpression('"highway" IN ('+cls+')');rt.appendChild(rule)
 rule=QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({'line_color':'#deded3','line_width':'.12'}));rule.setIsElse(True);rt.appendChild(rule);ro.setRenderer(rr)
 tr=vect('transit_lines','轨道交通线路',g);line(tr,'#8f7782' if id=='01' else '#b17f83',.38,True)
 st=vect('transit_stations','轨道站点（非出入口）',g);marker(st,'#8f7782',2.0)
 nd=vect('resource_nodes','重点资源节点（点为代表位置）',g);marker(nd,accent,2.8);labeling(nd,'label',12,accent)
 rdlabel=vect('road_labels','主要道路名称',g);line(rdlabel,'transparent',.01);labeling(rdlabel,'name',11,'#6d736d','line')
 wl=vect('water_labels','河流名称',g);line(wl,'transparent',.01);labeling(wl,'name',10,'#497f91','line')
 mainloc=vect('site_locator','核心设计地块注记',g);marker(mainloc,'transparent',.01,'transparent');labeling(mainloc,'name',13,'#b34432')
 ds=vect('DESIGN_SITE_BOUNDARY','真实设计红线 66.0948 ha',g);sym=QgsLineSymbol.createSimple({'line_color':'white','line_width':'1.25','joinstyle':'round'});sym.appendSymbolLayer(QgsSimpleLineSymbolLayer.create({'line_color':'#c24d36','line_width':'.58','joinstyle':'round'}));ds.setRenderer(QgsSingleSymbolRenderer(sym))
 area=vect('study_area','研究范围 22.0091 km²（非设计边界）',g);fill(area,'transparent','#a9aaa0',.16);a=area.renderer().symbol().symbolLayer(0);a.setStrokeStyle(Qt.DashLine)
 loc=vect('site_locator','宏观定位点（不代表边界）',g);marker(loc,'#c24d36',3.4);labeling(loc,'name',10,'#b34432')
 sh=vect('shanghai_land_reference','上海陆域制图参考 OSM × Natural Earth',g);fill(sh,'#d2ddcf','#829688',.23)
 land=vect('regional_land_reference','Natural Earth 陆域制图参考',g);fill(land,'#efeee6','#c4c8c0',.1)
 layout=QgsPrintLayout(pr);layout.initializeDefaults();layout.setName(id+'_DRAFT_A1_区位分析');layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(841,594));layout.pageCollection().pages()[0].setPageStyleSymbol(QgsFillSymbol.createSimple({'color':bg,'outline_style':'no'}));layout.renderContext().setDpi(300)
 rect(layout,28,22,18,2.4,accent);label(layout,'SHANGHAI / SITE LOCATION ANALYSIS',28,29,680,12,12,accent,True)
 label(layout,'区位分析｜'+('水绿与城市肌理' if id=='01' else '走廊与资源节点'),27,43,725,28,29,'#2d3c35',True)
 label(layout,'上海 · 静安北部 / 江场西路沿线     核心设计范围 66.0948 ha',29,74,700,10,12,'#657368')
 label(layout,id,756,23,60,35,42,accent,True);label(layout,'草案 / DRAFT',756,64,65,10,10,accent)
 # Three real, matched spatial extents in both variants.
 label(layout,'01 / 上海市域定位',28,99,190,12,14,accent,True)
 ex=QgsRectangle(sh.extent());ex.grow(6500);macro=mapitem(layout,[loc,ds,area,sh,land],28,118,180,163,ex,'#e6eeed')
 label(layout,'上海市',140,238,55,10,11,'#657b70');scale(layout,macro,34,267,20000)
 label(layout,'轮廓：OSM × Natural Earth（非权属界线）\n定位点仅提示位置；真实地块见下方红线。',28,285,181,19,9,'#7f887f')
 label(layout,'02 / 核心地块与直接周边',28,317,190,12,14,accent,True)
 ex=QgsRectangle(ds.extent());ex.grow(260);detail=mapitem(layout,[ds,wl,gr,wa,wc,ro,b],28,337,180,109,ex,bg);scale(layout,detail,33,448,250)
 label(layout,'无填充红线 / 不裁改既有分析数据',28,467,185,10,9,'#7f887f')
 label(layout,'03 / 片区'+('空间结构与水绿资源' if id=='01' else '交通走廊与城市资源'),229,99,500,12,14,accent,True)
 ex=QgsRectangle(area.extent());ex.grow(160);region=mapitem(layout,[ds,mainloc,nd,rdlabel,wl,st,tr,gr,wa,wc,ro,b,area],229,118,584,328,ex,bg)
 label(layout,'N ↑\n网格北',788,123,24,20,10,accent,True);scale(layout,region,235,449,1000)
 label(layout,'建筑轮廓仅覆盖原研究区；外侧空白不代表无建筑。道路线宽为制图分级。',413,452,400,10,9,'#7a8379')
 # Manual editable legend, not a default GIS legend block.
 entries=[('设计红线','#c24d36'),('道路骨架', '#aeb4af' if id=='01' else '#d59a50'),('轨道交通','#8f7782'),('已记录绿地',green),('已记录水系',water),('建筑轮廓','#d8d9d3'),('研究范围（虚线）','#a9aaa0')]
 for j,(name,color) in enumerate(entries):
  x=230+j*83
  if j==6:
   for dx in [0,2.7,5.4]:rect(layout,x+dx,470,1.6,1.2,color)
  else:rect(layout,x,470,7,1.6,color)
  label(layout,name,x+10,466,73,10,11,'#627066')
 rect(layout,28,486,785,.35,'#d3d7ce')
 notes=[('场地｜线性展开的设计范围','地块沿江场西路一带东西向展开，已记录建筑覆盖率26.6%，高于研究区22.6%。道路与河道交织，内部步行连续性及跨越条件需核查；空间优化应兼顾街坊与沿河联系。'),('区域｜轨道与水绿资源邻近','彭浦公园、静安青年体育公园距红线最近约207m、356m（直线距离）。周边有1号线站点、半里绿廊及市北高新商务中心；资源邻近不等于入口可达或服务充分。'),('协同｜从内部优化走向片区连接','建议以江场西路—万荣路组织片区联系，向东衔接轨道，串联周边公园及就业资源。先核实出入口、过街与跨河条件，再落实慢行路径、沿街界面和公共空间的协同改善。')]
 for j,(head,body) in enumerate(notes):
  x=28+j*267;label(layout,head,x,495,249,12,15,accent,True);label(layout,wrap_cn(body),x,512,249,40,14,'#556259')
 label(layout,'数据：© OpenStreetMap contributors；Overture / East Asian Buildings（ODbL）；Natural Earth（公共领域）。来源时间不一，并非同一时点普查。',28,561,785,10,9,'#858c82')
 label(layout,'EPSG:32651  /  2026-10-29  /  草案供风格与内容审阅；建议不代表已存在或已获批工程。站点为站体位置，公园出入口和开放条件尚待核实。',28,575,785,9,9,'#858c82')
 pr.layoutManager().addLayout(layout)
 meta={'variant':id,'layout':layout.name(),'site_layer':ds.id(),'site_area_ha':stats['site_area_ha'],'map_extents':{},'draft':True}
 for n,mp in [('macro',macro),('region',region),('detail',detail)]:
  e=mp.extent();meta['map_extents'][n]=[e.xMinimum(),e.yMinimum(),e.xMaximum(),e.yMaximum()]
 png=QgsLayoutExporter.ImageExportSettings();png.dpi=100
 assert QgsLayoutExporter(layout).exportToImage(str(P/f'outputs/previews/location_{id}_draft_preview.png'),png)==QgsLayoutExporter.Success
 settings=QgsLayoutExporter.PdfExportSettings();settings.dpi=300;settings.forceVectorOutput=True;settings.textRenderFormat=Qgis.TextRenderFormat.AlwaysText
 assert QgsLayoutExporter(layout).exportToPdf(str(P/f'outputs/location_{id}_draft_A1.pdf'),settings)==QgsLayoutExporter.Success
 if FULL:
  png.dpi=300;assert QgsLayoutExporter(layout).exportToImage(str(P/f'outputs/location_{id}_draft_300dpi.png'),png)==QgsLayoutExporter.Success
 qa.append(meta);print('Rendered',id,flush=True)
assert qa[0]['map_extents']==qa[1]['map_extents']
pr.setTitle('上海区位分析｜01与02两版草案');pr.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(region.extent(),pr.crs()))
# Keep only the second variant visible on opening; layouts keep separate, explicit layer sets.
for group in root.children():group.setItemVisibilityChecked(group.name().startswith('02'))
assert pr.write(str(P/'outputs/qgis/location_two_variants_draft.qgz'))
(P/'reports/layout_validation.json').write_text(json.dumps({'QGIS':Qgis.QGIS_VERSION,'same_extents_both_variants':True,'variants':qa,'full_300dpi_png':FULL},ensure_ascii=False,indent=2))
# Verify project reopening and all portable sources.
pr.clear();assert pr.read(str(P/'outputs/qgis/location_two_variants_draft.qgz'));assert all(v.isValid() for v in pr.mapLayers().values());print('Project reopened:',len(pr.mapLayers()),'valid layers, two layouts',flush=True)
os._exit(0)
