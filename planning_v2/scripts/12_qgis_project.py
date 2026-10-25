"""Create and reopen a real QGIS project with themed layers and editable A1 layouts."""
import os,json,csv,textwrap
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_CACHE_HOME']='/workspace/.cache'
from qgis.core import *
from qgis.PyQt.QtGui import QColor,QFont
app=QgsApplication([],False);app.initQgis()
P=Path(__file__).resolve().parents[1];M=P/'outputs/gis/planning_enriched.gpkg';A=P/'outputs/gis/analysis_layers.gpkg';out=P/'outputs/qgis';out.mkdir(exist_ok=True)
project=QgsProject.instance();project.setCrs(QgsCoordinateReferenceSystem('EPSG:32651'));project.setFilePathStorage(Qgis.FilePathType.Relative)
root=project.layerTreeRoot();basegroup=root.addGroup('基础与已核实来源 / Baseline and observations');thematic=root.addGroup('规划分析专题 / Research analysis');qa=root.addGroup('证据与待复核 / Evidence and QA')
def vector(path,layer,name,group,color='#d8dad4'):
 v=QgsVectorLayer(str(path)+'|layername='+layer,name,'ogr')
 if not v.isValid():raise RuntimeError('Invalid QGIS layer '+layer)
 symbol=QgsSymbol.defaultSymbol(v.geometryType());symbol.setColor(QColor(color))
 if v.geometryType()==QgsWkbTypes.PolygonGeometry:symbol.symbolLayer(0).setStrokeStyle(__import__('qgis.PyQt.QtCore',fromlist=['Qt']).Qt.NoPen)
 v.renderer().setSymbol(symbol);project.addMapLayer(v,False);group.addLayer(v);return v
def graduated(v,field):
 i=v.fields().indexFromName(field);values=[float(f[field]) for f in v.getFeatures() if f[field]!=None and str(f[field]) not in ['NULL','nan']]
 if not values:return
 values=sorted(values);colors=['#ede9d7','#d8c59e','#bc9b74','#9b7156','#704e42'];ranges=[]
 for j,c in enumerate(colors):
  low=values[int((len(values)-1)*j/5)] if j else values[0];high=values[int((len(values)-1)*(j+1)/5)];sym=QgsSymbol.defaultSymbol(v.geometryType());sym.setColor(QColor(c));ranges.append(QgsRendererRange(low,high,sym,f'{low:.3g} – {high:.3g}'))
 v.setRenderer(QgsGraduatedSymbolRenderer(field,ranges))
b=vector(M,'buildings_enriched','建筑轮廓 / Buildings',basegroup)
aoi=vector(M,'aoi_boundary','研究边界 / AOI',basegroup,'#526a6f');sym=QgsFillSymbol.createSimple({'color':'transparent','outline_color':'#354d55','outline_width':'0.35'});aoi.renderer().setSymbol(sym)
for layer in ['road_network_vehicle','road_network_walk','road_network_cycle','transit_stations','transit_lines','poi_all','green_parks','green_spaces_all','blue_network','open_spaces','heritage_sites','admin_units','urban_blocks','wikidata_reference_points','historical_ndvi_coverage','physical_cover_clcd2019_30m','physical_cover_worldcover2021_10m','turn_restrictions','historical_water_occurrence_ge50']:
 try:vector(M,layer,layer,basegroup)
 except RuntimeError:pass
for layer in ['access_seed_audit','source_node_intersections']:
 vector(A,layer,layer,qa,'#9d6760')
for layer in ['road_dangling_review','road_building_conflicts','road_schematic_steep_review','landuse_inference_review']:vector(M,layer,layer,qa,'#aa665c')
metas=sorted((P/'reports').glob('map_[0-9][0-9].json'));layouts=[]
for p in metas:
 m=json.loads(p.read_text());kind=m['kind'];id=m['id'];name=id+' '+m['title']
 if kind=='raster':
  v=QgsRasterLayer(str(P/f'outputs/gis/rasters/{m["layer"]}.tif'),name)
  if not v.isValid():raise RuntimeError(name)
  provider=v.dataProvider();stats=provider.bandStatistics(1,QgsRasterBandStats.All)
  ramp=QgsColorRampShader();ramp.setColorRampType(QgsColorRampShader.Interpolated);lo=stats.minimumValue;hi=stats.maximumValue;ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(lo,QColor('#e4e2b7'),str(lo)),QgsColorRampShader.ColorRampItem((lo+hi)/2,QColor('#82a38b'),'mid'),QgsColorRampShader.ColorRampItem(hi,QColor('#335e66'),str(hi))]);shader=QgsRasterShader();shader.setRasterShaderFunction(ramp);v.setRenderer(QgsSingleBandPseudoColorRenderer(provider,1,shader));project.addMapLayer(v,False);thematic.addLayer(v)
 elif kind in ['grid','issues']:v=vector(A,'planning_grid_500m',name,thematic);graduated(v,m.get('field') or 'research_amenity_priority')
 elif kind=='population':v=vector(A,m['layer'],name,thematic);graduated(v,m['field'])
 elif kind=='height':v=vector(M,'buildings_enriched',name,thematic);graduated(v,'height_m')
 elif kind=='land':
  v=vector(M,'landuse_existing',name,thematic);colors={'residential':'#d6b386','public_service':'#b07896','commercial':'#ca8a7c','industrial':'#a59bb5','transport':'#a8aaad','green_open':'#99b895','water':'#87b7c4','construction':'#d7cb9d','unknown':'#eeeae2'};cats=[]
  for cl,c in colors.items():sym=QgsSymbol.defaultSymbol(v.geometryType());sym.setColor(QColor(c));cats.append(QgsRendererCategory(cl,sym,cl))
  v.setRenderer(QgsCategorizedSymbolRenderer('class',cats))
 elif kind=='access':v=vector(A,'access_'+m['layer'],name,thematic,'#426f69');graduated(v,'minutes')
 elif kind=='road':v=vector(M,'road_network_vehicle',name,thematic,'#9e7760')
 elif kind=='bluegreen':v=vector(M,'green_spaces_all',name,thematic,'#91b094')
 else:v=vector(M,'buildings_enriched',name,thematic,'#3e4446')
 v.saveNamedStyle(str(out/f'{id}_theme.qml'))
 layout=QgsPrintLayout(project);layout.initializeDefaults();layout.setName(name);layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(841,594))
 def label(text,x,y,w,h,size):
  l=QgsLayoutItemLabel(layout);l.setText(text);l.setFont(QFont('Noto Sans CJK SC',size));layout.addLayoutItem(l);l.attemptMove(QgsLayoutPoint(x,y));l.attemptResize(QgsLayoutSize(w,h));return l
 label(name,29,19,790,27,25);label(m['en'],30,49,750,15,13)
 mapitem=QgsLayoutItemMap(layout);layout.addLayoutItem(mapitem);mapitem.attemptMove(QgsLayoutPoint(29.435,71.28));mapitem.attemptResize(QgsLayoutSize(613.93,439.56));mapitem.setCrs(project.crs());mapitem.setLayers([aoi,v,b] if kind not in ['raster','figure'] else [aoi,v]);mapitem.setKeepLayerSet(True);e=m['extent_32651'];mapitem.zoomToExtent(QgsRectangle(e[0],e[2],e[1],e[3]));mapitem.setScale(10000)
 legend=QgsLayoutItemLegend(layout);legend.setTitle('图例 / Legend');legend.setLinkedMap(mapitem);legend.setAutoUpdateModel(False);legend.model().rootGroup().clear();legend.model().rootGroup().addLayer(v);layout.addLayoutItem(legend);legend.attemptMove(QgsLayoutPoint(668,80));legend.attemptResize(QgsLayoutSize(150,135))
 label('主要发现\n'+'\n\n'.join(m.get('findings',[])),667,235,148,100,10);label('方法与适用性\n'+'\n'.join(textwrap.wrap(m['note'],36)),667,353,149,150,10)
 label('N ↑',614,83,25,20,15)
 scale=QgsLayoutItemScaleBar(layout);scale.setStyle('Single Box');scale.setLinkedMap(mapitem);scale.setUnits(Qgis.DistanceUnit.Meters);scale.setUnitsPerSegment(500);scale.setNumberOfSegments(2);scale.setNumberOfSegmentsLeft(0);scale.setUnitLabel('m');scale.applyDefaultSize();layout.addLayoutItem(scale);scale.attemptMove(QgsLayoutPoint(43,487))
 label('上海城市规划现状研究 | EPSG:32651 | A1 841×594mm | 1:10,000 | AOI 22.009km²',30,525,760,15,11)
 label('© OpenStreetMap contributors / Overture；遥感与人口来源及年份详见专题来源表。公开模型研究成果，非测绘、非法定规划。',30,548,775,20,9)
 project.layoutManager().addLayout(layout);layouts.append({'id':id,'scale':mapitem.scale(),'width_mm':mapitem.sizeWithUnits().width(),'height_mm':mapitem.sizeWithUnits().height(),'name':name})
project.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(aoi.extent(),project.crs()))
for node in root.findLayers():node.setItemVisibilityChecked(node.layerId() in [b.id(),aoi.id()] or node.name().startswith('01 '))
project.setTitle('Shanghai Planning GIS 2026 / Research observations and explicit gaps')
path=out/'planning_analysis.qgz'
if not project.write(str(path)):raise RuntimeError('QGIS write failed')
project.clear()
if not project.read(str(path)):raise RuntimeError('QGIS reopen failed')
layout=project.layoutManager().layouts()[0]
settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=70
result=QgsLayoutExporter(layout).exportToImage(str(out/'native_layout_01_preview.png'),settings)
if result!=QgsLayoutExporter.Success:raise RuntimeError('Native QGIS layout export failed '+str(result))
bad=[l.name() for l in project.mapLayers().values() if not l.isValid()]
if bad:raise RuntimeError(str(bad))
json.dump({'QGIS_version':Qgis.QGIS_VERSION,'project_reopened':True,'native_layout_export_verified':True,'valid_layers':len(project.mapLayers()),'layouts':layouts,'relative_paths':True},open(P/'reports/qgis_validation.json','w'),ensure_ascii=False,indent=2)
print('QGIS validated',len(project.mapLayers()),len(layouts),flush=True)
# Avoid Qt teardown SIGSEGV seen with some headless providers; all writes already closed.
os._exit(0)
