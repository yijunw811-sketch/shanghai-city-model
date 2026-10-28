"""Display-only fallback patch. Explicitly does not claim high-resolution imagery has been acquired."""
import os,json,hashlib,shutil
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_CACHE_HOME']='/workspace/.cache'
from qgis.core import *
from qgis.PyQt.QtGui import QColor
P=Path(__file__).resolve().parents[1];V3=P.parent;Q=V3/'outputs/qgis/planning_analysis_v3.qgz';out=V3/'outputs/qgis/planning_analysis_v3_imagery_diagnostic.qgz'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
backup=P/'state/planning_analysis_v3_before_imagery_repair.qgz'
if not backup.exists():shutil.copy2(Q,backup)
protected=json.loads((P/'state/protected_inputs.json').read_text());REPO=V3.parent
app=QgsApplication([],False);app.initQgis();project=QgsProject.instance();assert project.read(str(Q),QgsProject.ReadFlag.ForceReadOnlyLayers)
root=project.layerTreeRoot()
existing=root.findGroup('影像诊断｜当前仅10m备用，高清替换未完成')
if existing:
 project.removeMapLayers([n.layerId() for n in existing.findLayers()]);root.removeChildNode(existing)
group=root.addGroup('影像诊断｜当前仅10m备用，高清替换未完成')
def find(s):return next(v for v in project.mapLayers().values() if v.name()==s)
design=find('核心设计范围 / Design Site');aoi=find('AOI22.009km²')
# Real local native10m raster, no upsampled GeoTIFF and no false HD title.
raster=QgsRasterLayer(str(V3/'data/satellite/sentinel_truecolor_10m_context.tif'),'备用原生10m｜纯影像判读，无锐化','gdal');raster.setRenderer(QgsMultiBandColorRenderer(raster.dataProvider(),1,2,3));raster.setOpacity(1);raster.resampleFilter().setZoomedInResampler(None);raster.resampleFilter().setZoomedOutResampler(QgsBilinearRasterResampler());raster.resampleFilter().setMaxOversampling(1);project.addMapLayer(raster,False);group.addLayer(raster)
raster.setAbstract('Sentinel-2 TCI2026-10-14 native10m. Not a higher-resolution replacement; native pixel information unchanged. All core comparisons awaiting authorized higher-resolution source.')
opts=QgsVectorLayer.LayerOptions();opts.forceReadOnly=True
vectors=[]
for layername,name,color,width,opacity,polygon in [('buildings_enriched','轻叠加｜建筑细轮廓','#E7EEE6',.05,.25,True),('road_network_vehicle','轻叠加｜主要道路','#24465B',.06,.40,False),('green_spaces_all','轻叠加｜绿地边界','#8FAE85',.06,.30,True),('blue_network','轻叠加｜水面边界','#6E9FAF',.07,.40,True)]:
 v=QgsVectorLayer(str(V3/'outputs/gis/reference_v2.gpkg')+'|layername='+layername,name,'ogr',opts)
 if polygon:symbol=QgsFillSymbol.createSimple({'color':'0,0,0,0','outline_color':color,'outline_width':str(width),'outline_style':'solid'})
 else:
  symbol=QgsLineSymbol.createSimple({'line_color':color,'line_width':str(width)})
  v.setSubsetString('"highway" IN (\'motorway\',\'trunk\',\'primary\',\'secondary\',\'tertiary\',\'primary_link\',\'secondary_link\',\'tertiary_link\')')
 v.setRenderer(QgsSingleSymbolRenderer(symbol));v.setOpacity(opacity);project.addMapLayer(v,False);group.addLayer(v);vectors.append(v);v.saveNamedStyle(str(P/f'outputs/{layername}_light_overlay.qml'))
model=QgsLayerTreeModel(root)
def theme(name,visible):
 for n in root.findLayers():n.setItemVisibilityChecked(n.layerId() in visible)
 for g in root.findGroups():
  if any(n.layerId() in visible for n in g.findLayers()):g.setItemVisibilityChecked(True)
 project.mapThemeCollection().insert(name,QgsMapThemeCollection.createThemeFromCurrentState(root,model))
theme('IMAGE_A_纯影像_原生10m备用',[design.id(),aoi.id(),raster.id()]);theme('IMAGE_B_轻叠加_原生10m备用',[design.id(),aoi.id(),raster.id()]+[v.id() for v in vectors])
# Default to pure image, not dense outlines. The original pure-vector preset is retained unchanged.
theme('IMAGE_A_纯影像_原生10m备用',[design.id(),aoi.id(),raster.id()])
root.setHasCustomLayerOrder(True);original_order=list(root.customLayerOrder());front=[design,aoi]+vectors;root.setCustomLayerOrder(front+[v for v in original_order if v.id() not in [x.id() for x in front] and v.id()!=raster.id()]+[raster])
updated=[]
for layout in project.layoutManager().layouts():
 if not layout.name().startswith(('V3 S01 ','V3 S02 ','V3 S03 ')):continue
 layout.renderContext().setDpi(300)
 for item in layout.items():
  if isinstance(item,QgsLayoutItemMap):item.setLayers([design,aoi]+(vectors if layout.name().startswith('V3 S03 ') else [])+[raster]);item.setKeepLayerSet(True)
  if isinstance(item,QgsLayoutItemLabel) and item.text().startswith(('V3 S01 ','V3 S02 ','V3 S03 ')):item.setText(item.text().split('（原生10m备用')[0]+'（原生10m备用；高清待取得）')
 for item in layout.items():
  if isinstance(item,QgsLayoutItemLegend):
   item.setAutoUpdateModel(False);item.model().rootGroup().clear();item.model().rootGroup().addLayer(design)
   if layout.name().startswith('V3 S03 '):
    for v in vectors:item.model().rootGroup().addLayer(v)
 updated.append(layout.name())
project.setFilePathStorage(Qgis.FilePathType.Relative)
assert project.write(str(out));assert project.write(str(Q))
project.clear();assert project.read(str(out),QgsProject.ReadFlag.ForceReadOnlyLayers)
assert {'V3_A_纯矢量专题','IMAGE_A_纯影像_原生10m备用','IMAGE_B_轻叠加_原生10m备用'}<=set(project.mapThemeCollection().mapThemes())
invalid=[l.name() for l in project.mapLayers().values() if not l.isValid()];assert not invalid,invalid
layout=next(l for l in project.layoutManager().layouts() if l.name().startswith('V3 S02 '));settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=60;result=QgsLayoutExporter(layout).exportToImage(str(P/'outputs/QGIS_native10m_fallback_display_test.png'),settings);assert result==QgsLayoutExporter.Success
layer_count=len(project.mapLayers());project.clear()
check={p:sha(REPO/p)==value for p,value in protected.items()};assert all(check.values()),check
report={'high_resolution_replacement_complete':False,'actual_active_GSD_m':10,'source_capture_date':'2026-10-14','no_sharpen_or_AI':True,'source_data_changed':False,'native_local_raster_no_low_zoom_tiles':True,'pure_vector_theme_retained':True,'new_display_themes':['IMAGE_A_纯影像_原生10m备用','IMAGE_B_轻叠加_原生10m备用'],'original_project_backup':str(backup.relative_to(V3)),'updated_project':str(Q.relative_to(V3)),'diagnostic_project':str(out.relative_to(V3)),'valid_layers':layer_count,'invalid_sources':invalid,'satellite_layouts_export_DPI':300,'satellite_layouts_configured':updated,'formal_HD_maps_exported':False,'reason_formal_exports_deferred':'User requested real source replacement and comparisons before re-export; no verified authorized higher-resolution source yet','design_boundary_unchanged':True,'outside_mask':False,'inside_fill':False,'all_protected_source_file_SHA256_unchanged':check,'native_preview_export':'Success'}
(P/'reports/display_patch_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('DISPLAY PATCH VERIFIED; native10m only; no higher-resolution source claimed',flush=True);os._exit(0)
