"""Open V2 as a source, repoint to V3 copies, retain28 reference layouts and add39 real V3 layouts."""
import os,json,textwrap
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_CACHE_HOME']='/workspace/.cache'
from qgis.core import *
from qgis.PyQt.QtGui import QColor,QFont
from qgis.PyQt.QtCore import Qt
P=Path(__file__).resolve().parents[1];V2=P.parent/'planning_v2';M=P/'outputs/gis/reference_v2.gpkg';A=P/'outputs/gis/reference_analysis_v2.gpkg';D=P/'outputs/gis/refined_analysis_v3.gpkg';OUT=P/'outputs/qgis';OUT.mkdir(exist_ok=True)
if not V2.exists():V2=P/'data/v2_reference'
style=json.loads((P/'styles/COLOR_STYLE_SYSTEM.json').read_text());catalog=json.loads((P/'reports/map_catalog_v3.json').read_text())
# Recent per-map metadata additionally contains the exact raster display intervals.
catalog=[json.loads((P/f'reports/map_{m["id"]}.json').read_text()) for m in catalog]
app=QgsApplication([],False);app.initQgis();project=QgsProject.instance()
if not project.read(str(V2/'outputs/qgis/planning_analysis.qgz')):raise RuntimeError('Cannot read real V2 QGIS project')
root=project.layerTreeRoot()
for layout in project.layoutManager().layouts():layout.setName('V2_REFERENCE__'+layout.name())
for g in root.children():g.setName('V2参考 / '+g.name());g.setItemVisibilityChecked(False)
for layer in project.mapLayers().values():
 source=layer.source();s=QgsMapLayerStyle();s.readFromLayer(layer)
 if 'planning_enriched.gpkg' in source:new=str(M)+'|layername='+source.split('layername=')[-1].split('|')[0];provider='ogr'
 elif 'analysis_layers.gpkg' in source:new=str(A)+'|layername='+source.split('layername=')[-1].split('|')[0];provider='ogr'
 elif layer.type()==QgsMapLayerType.RasterLayer:new=str(P/'data/rasters_v2'/Path(source).name);provider='gdal'
 else:continue
 layer.setDataSource(new,'V2 / '+layer.name(),provider);s.writeToLayer(layer)
 if not layer.isValid():raise RuntimeError('Repointed V2 layer invalid '+layer.name())
project.setCrs(QgsCoordinateReferenceSystem('EPSG:32651'));project.setFilePathStorage(Qgis.FilePathType.Relative)
satgroup=root.addGroup('V3 S｜卫星影像 Satellite RGB');boundarygroup=root.addGroup('V3 D｜真实设计边界 Design Boundary');gridgroup=root.addGroup('V3 G｜多尺度网格与设计相交统计');themegroup=root.addGroup('V3 T｜统一色带专题');overlaygroup=root.addGroup('V3 C｜卫星综合叠加');evidencegroup=root.addGroup('V3 Q｜原位问题与拓扑证据')
def vector(path,layer,name,group,color='#A3B2AD',outline=False):
 v=QgsVectorLayer(str(path)+'|layername='+layer,name,'ogr')
 if not v.isValid():raise RuntimeError(name)
 sym=QgsSymbol.defaultSymbol(v.geometryType());sym.setColor(QColor(color))
 if v.geometryType()==QgsWkbTypes.PolygonGeometry:
  sym=QgsFillSymbol.createSimple({'color':'transparent' if outline else color,'outline_color':color,'outline_width':'0.12','outline_style':'solid' if outline else 'no'})
 v.setRenderer(QgsSingleSymbolRenderer(sym));project.addMapLayer(v,False);group.addLayer(v);return v
def metric(v,field):
 st=style['metric_styles'][field];bounds=st['breaks'];colors=style['palettes'][st['palette']];rootrule=QgsRuleBasedRenderer.Rule(None)
 for i,c in enumerate(colors):
  symbol=QgsSymbol.defaultSymbol(v.geometryType());symbol.setColor(QColor(c))
  if v.geometryType()==QgsWkbTypes.PolygonGeometry:symbol=QgsFillSymbol.createSimple({'color':c,'outline_style':'no'})
  condition=f'"{field}" >= {bounds[i]} AND "{field}" '+('<=' if i==len(colors)-1 else '<')+f' {bounds[i+1]}'
  rule=QgsRuleBasedRenderer.Rule(symbol,0,0,condition,f'{bounds[i]:,.3g} – {bounds[i+1]:,.3g}');rootrule.appendChild(rule)
 symbol=QgsFillSymbol.createSimple({'color':'#D5D5CB','outline_style':'no'});rootrule.appendChild(QgsRuleBasedRenderer.Rule(symbol,0,0,f'"{field}" IS NULL','资料/有效覆盖不足，未计算'))
 v.setRenderer(QgsRuleBasedRenderer(rootrule));v.setAbstract(st['unit']+'; fixed thresholds shared between regional and refined atlas')
 return v
def categorical(v,field,pairs):
 cats=[]
 for value,label,c in pairs:
  s=QgsFillSymbol.createSimple({'color':c,'outline_style':'no'});cats.append(QgsRendererCategory(value,s,label))
 v.setRenderer(QgsCategorizedSymbolRenderer(field,cats))
def rgb(name,opacity):
 v=QgsRasterLayer(str(P/'data/satellite/sentinel_truecolor_10m_context.tif'),name,'gdal');v.setRenderer(QgsMultiBandColorRenderer(v.dataProvider(),1,2,3));v.setOpacity(opacity);project.addMapLayer(v,False);satgroup.addLayer(v);return v
rgb_b=rgb('B｜Sentinel-2 true RGB 2026-10-14 native10m',1);rgb_c=rgb('C｜Same RGB, uniform display weight72%',.72)
design=vector(D,'DESIGN_SITE_BOUNDARY','核心设计范围 / Design Site',boundarygroup,'#CB493E');symbol=QgsLineSymbol.createSimple({'line_color':'255,255,255,255','line_width':'1.65','line_width_unit':'MM'});symbol.appendSymbolLayer(QgsSimpleLineSymbolLayer.create({'line_color':'203,73,62,255','line_width':'1.2','line_width_unit':'MM'}));design.setRenderer(QgsSingleSymbolRenderer(symbol));design.setAbstract('66.09476495ha from uploaded选定范围.csv; line only, no fill/outside mask; tiny closure repair audited')
aoi=vector(M,'aoi_boundary','AOI22.009km²',boundarygroup,'#526A70',True)
b=vector(M,'buildings_enriched','A｜原建筑轮廓参考',overlaygroup,'#CED2CD');b_outline=vector(M,'buildings_enriched','C｜建筑轮廓线（无填充）',overlaygroup,'#E8E9E2',True);b_outline.setOpacity(.75)
road=vector(M,'road_network_vehicle','C｜道路源网络',overlaygroup,'#355F69');road.renderer().symbol().setWidth(.16)
green=vector(M,'green_spaces_all','C｜绿色空间（统一35%）',overlaygroup,'#7C9F78');green.setOpacity(.35)
water=vector(M,'blue_network','C｜水面（统一65%）',overlaygroup,'#6B9DAD');water.setOpacity(.65)
rail=vector(M,'transit_lines','C｜轨道线路',overlaygroup,'#745E79');rail.setSubsetString('"route_mode" IN (\'subway\',\'train\',\'tram\')');rail.renderer().symbol().setWidth(.3)
for size in [50,100,200]:
 v=vector(D,f'grid_{size}m',f'{size}m完整源统计网格',gridgroup);metric(v,'building_density')
 vector(D,f'design_grid_{size}m',f'{size}m真实设计相交单元（单独统计口径）',gridgroup,'#8A9B91',True)
vector(A,'planning_grid_500m','V2原始500m网格（未改）',gridgroup,'#8A9B91',True)
junctions=vector(A,'source_node_intersections','真实源节点交叉口（保留分层）',evidencegroup,'#37525A');junctions.setSubsetString('"mode"=\'vehicle\'');junctions.renderer().symbol().setSize(1.1)
dangling=vector(M,'road_dangling_review','原模型端点待核实（非确认错误）',evidencegroup,'#876843');dangling.renderer().symbol().setSize(1.2)
vector(M,'road_building_conflicts','原模型已处理冲突记录',evidencegroup,'#876843');vector(M,'road_schematic_steep_review','原模型示意坡度待复核',evidencegroup,'#876843')
cache={};layoutresults=[]
for m in catalog:
 id=m['id'];kind=m['kind'];name='V3 '+id+' '+m['title'];key=(kind,m.get('grid_size'),m.get('field'),m.get('layer'),id=='R08')
 v=None;layers=[]
 if kind in ['grid','issues']:
  if key not in cache:cache[key]=metric(vector(D,f'grid_{m["grid_size"]}m',name,themegroup),m['field'])
  v=cache[key];layers=[v,b]
  if id in ['08','R04']:layers.insert(0,junctions)
  if kind=='issues':layers.insert(0,dangling)
 elif kind=='population':
  v=metric(vector(A,m['layer'],name,themegroup),m['field']);layers=[v,b]
  if id=='R08':v.setOpacity(.65);layers=[b_outline,v,rgb_c]
 elif kind=='height':v=metric(vector(M,'buildings_enriched',name,themegroup),'height_m');layers=[v]
 elif kind=='land':
  v=vector(M,'landuse_existing',name,themegroup);categorical(v,'class',[(cl,cl,c) for cl,c in style['landuse'].items()]);layers=[v]
 elif kind=='figure':v=vector(M,'buildings_enriched',name,themegroup,'#3D5054');layers=[v]
 elif kind=='road':
  v=vector(M,'road_network_vehicle',name,themegroup,'#8E9899');cats=[]
  for h,c in [('motorway','#4D676B'),('trunk','#5F7A7C'),('primary','#799393'),('secondary','#96AAA7'),('tertiary','#B4C3BA')]:
   symbol=QgsLineSymbol.createSimple({'line_color':c,'line_width':'.5'});cats.append(QgsRendererCategory(h,symbol,h))
  cats.append(QgsRendererCategory(None,QgsLineSymbol.createSimple({'line_color':'#8E9899','line_width':'.15'}),'其它道路'));v.setRenderer(QgsCategorizedSymbolRenderer('regexp_replace("highway",\'_link$\',\'\')',cats));layers=[v,b]
 elif kind=='bluegreen':v=green;layers=[water,green,b]
 elif kind=='access':
  v=vector(A,'access_'+m['layer'],name,themegroup,'#326C69');cats=[]
  for mins,c in [(15,'#A4BFB1'),(10,'#6B9C91'),(5,'#326C69')]:cats.append(QgsRendererCategory(mins,QgsLineSymbol.createSimple({'line_color':c,'line_width':'.5'}),str(mins)+'min'))
  v.setRenderer(QgsCategorizedSymbolRenderer('minutes',cats));layers=[v,b]
 elif kind=='raster':
  v=QgsRasterLayer(str(P/f'data/rasters_v2/{m["layer"]}.tif'),name,'gdal');rs=m['raster_style'];provider=v.dataProvider()
  if rs['categorical']:
   classes=[QgsPalettedRasterRenderer.Class(code,QColor(color),label) for code,color,label in zip(rs['codes'],rs['colors'],rs['labels'])];v.setRenderer(QgsPalettedRasterRenderer(provider,1,classes))
  else:
   ramp=QgsColorRampShader();ramp.setColorRampType(QgsColorRampShader.Interpolated);lo,hi=rs['vmin'],rs['vmax'];colors=style['palettes'][rs['palette']];ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(lo+(hi-lo)*i/(len(colors)-1),QColor(c),f'{lo+(hi-lo)*i/(len(colors)-1):.3g}') for i,c in enumerate(colors)]);shader=QgsRasterShader();shader.setRasterShaderFunction(ramp);v.setRenderer(QgsSingleBandPseudoColorRenderer(provider,1,shader))
  project.addMapLayer(v,False);themegroup.addLayer(v);layers=[v]
 elif kind=='satellite':v=rgb_b if m['base_mode']=='B' else rgb_c;layers=[rgb_b] if m['base_mode']=='B' else [rail,road,b_outline,water,green,rgb_c]
 if v is None or not v.isValid():raise RuntimeError('No valid theme for '+id)
 v.saveNamedStyle(str(P/f'styles/{id}_v3.qml'))
 layout=QgsPrintLayout(project);layout.initializeDefaults();layout.setName(name);layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(841,594))
 def label(text,x,y,w,h,size):
  l=QgsLayoutItemLabel(layout);l.setText(text);l.setFont(QFont('Noto Sans CJK SC',size));l.setFontColor(QColor('#24465B'));layout.addLayoutItem(l);l.attemptMove(QgsLayoutPoint(x,y));l.attemptResize(QgsLayoutSize(w,h));return l
 label(name,29,17,790,26,25);label(m['en'],30,47,760,15,13)
 mp=QgsLayoutItemMap(layout);layout.addLayoutItem(mp);mp.attemptMove(QgsLayoutPoint(29.435,71.28));mp.attemptResize(QgsLayoutSize(613.93,439.56));mp.setBackgroundEnabled(True);mp.setBackgroundColor(QColor('#F8F7F2'));mp.setCrs(project.crs());mp.setLayers([design,aoi]+layers);mp.setKeepLayerSet(True);e=m['extent'];mp.zoomToExtent(QgsRectangle(e[0],e[2],e[1],e[3]));mp.setScale(m['A1_scale'])
 legend=QgsLayoutItemLegend(layout);legend.setTitle('图例 / Legend');legend.setLinkedMap(mp);legend.setAutoUpdateModel(False);legend.model().rootGroup().clear();legend.model().rootGroup().addLayer(design)
 if kind!='satellite':legend.model().rootGroup().addLayer(v)
 elif m['base_mode']=='C':
  for contextlayer in [road,b_outline,green,water,rail]:legend.model().rootGroup().addLayer(contextlayer)
 layout.addLayoutItem(legend);legend.attemptMove(QgsLayoutPoint(666,80));legend.attemptResize(QgsLayoutSize(153,145))
 label('主要发现 / Findings\n'+'\n\n'.join('\n'.join(textwrap.wrap(t,32)) for t in m['findings']),667,250,150,92,10)
 label('指标与方法\n'+'\n'.join(textwrap.wrap(m['note'],35)),667,370,151,128,10)
 label('N ↑',617,82,22,20,14)
 scale=QgsLayoutItemScaleBar(layout);scale.setStyle('Single Box');scale.setLinkedMap(mp);scale.setUnits(Qgis.DistanceUnit.Meters);scale.setNumberOfSegments(2);scale.setNumberOfSegmentsLeft(0);scale.setUnitsPerSegment(500 if m['A1_scale']==10000 else 250);scale.setUnitLabel('m');layout.addLayoutItem(scale);scale.attemptMove(QgsLayoutPoint(42,514))
 label(f'GIS V3 | EPSG:32651 | A1 841×594mm | 1:{m["A1_scale"]:,} | 真实设计范围66.0948ha',30,527,775,15,11)
 label('© OpenStreetMap contributors / Overture / 各专题开放源；可选B/C底图：Contains modified Copernicus Sentinel data (2026), acquired2026-10-14, native10m.',30,548,781,18,9)
 label('独立边界线，无填充、无外围蒙版；估高不是测绘，体量不是容积率，人口模型不是普查，研究初筛不是法定更新范围。',30,569,780,15,9)
 project.layoutManager().addLayout(layout);layoutresults.append({'id':id,'name':name,'scale':mp.scale(),'map_mm':[mp.sizeWithUnits().width(),mp.sizeWithUnits().height()],'design_boundary_layer_id':design.id(),'new_layout':True})
# Three real map themes with independent raster/vector toggles; no internet dependency.
model=QgsLayerTreeModel(root)
def theme(name,visible):
 for node in root.findLayers():node.setItemVisibilityChecked(node.layerId() in visible)
 for group in [satgroup,boundarygroup,gridgroup,themegroup,overlaygroup,evidencegroup]:group.setItemVisibilityChecked(True)
 project.mapThemeCollection().insert(name,QgsMapThemeCollection.createThemeFromCurrentState(root,model))
landlayer=next(v for v in project.mapLayers().values() if v.name().startswith('V3 01 '))
theme('V3_A_纯矢量专题',[design.id(),aoi.id(),landlayer.id()]);theme('V3_B_真实卫星',[design.id(),aoi.id(),rgb_b.id()]);theme('V3_C_卫星与GIS叠加',[design.id(),aoi.id(),rgb_c.id(),rail.id(),road.id(),b_outline.id(),water.id(),green.id()])
# Put the boundary group first in layer-tree rendering order for interactive use as well as layouts.
clone=boundarygroup.clone();root.insertChildNode(0,clone);root.removeChildNode(boundarygroup)
root.setHasCustomLayerOrder(True);root.setCustomLayerOrder([design,aoi]+[v for v in project.mapLayers().values() if v.id() not in [design.id(),aoi.id(),rgb_b.id(),rgb_c.id()]]+[rgb_b,rgb_c])
project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(aoi.extent(),project.crs()));project.setTitle('Shanghai Planning GIS V3 / True RGB, real design boundary, multiscale evidence')
path=OUT/'planning_analysis_v3.qgz'
if not project.write(str(path)):raise RuntimeError('V3 QGZ write failed')
project.clear()
if not project.read(str(path)):raise RuntimeError('V3 QGZ reopen failed')
bad=[v.name() for v in project.mapLayers().values() if not v.isValid()]
if bad:raise RuntimeError(str(bad))
exports=[]
for id in ['02','R01','S02','S03']:
 layout=next(l for l in project.layoutManager().layouts() if l.name().startswith('V3 '+id+' '));settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=70;target=P/f'outputs/previews/QGIS_native_{id}.png';result=QgsLayoutExporter(layout).exportToImage(str(target),settings)
 if result!=QgsLayoutExporter.Success:raise RuntimeError('Native layout export failed '+id)
 exports.append({'id':id,'file':str(target.relative_to(P)),'result':'Success'})
# Simulate satellite being unavailable on a temporary probe project only; all vector sources must still load.
probe=QgsProject();assert probe.read(str(path));
for layer in list(probe.mapLayers().values()):
 if layer.type()==QgsMapLayerType.RasterLayer and 'sentinel_truecolor' in layer.source():probe.removeMapLayer(layer.id())
vectorvalid=[v.isValid() for v in probe.mapLayers().values() if v.type()==QgsMapLayerType.VectorLayer];assert all(vectorvalid)
vectorlayout=next(l for l in probe.layoutManager().layouts() if l.name().startswith('V3 02 '));settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=60
assert QgsLayoutExporter(vectorlayout).exportToImage(str(P/'outputs/previews/QGIS_vector_satellite_removed.png'),settings)==QgsLayoutExporter.Success
result={'QGIS_version':Qgis.QGIS_VERSION,'project_reopened':True,'valid_layers':len(project.mapLayers()),'missing_layers':bad,'V2_reference_layouts':len([l for l in project.layoutManager().layouts() if l.name().startswith('V2_REFERENCE__')]),'new_V3_layouts':len(layoutresults),'layouts':layoutresults,'map_themes':project.mapThemeCollection().mapThemes(),'native_exports':exports,'all_paths_relative':True,'online_dependency':False,'vector_layers_valid_independent_of_satellite':all(vectorvalid),'design_layer':'DESIGN_SITE_BOUNDARY','design_fill':'none','outside_mask':False}
(P/'reports/qgis_validation_v3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('QGIS V3',result['valid_layers'],'layers',result['V2_reference_layouts'],'old+',result['new_V3_layouts'],'new layouts',flush=True);os._exit(0)
