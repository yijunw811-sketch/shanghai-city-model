"""Save a separate editable QGIS project; change captions only, never source GIS."""
import os,json,hashlib,textwrap
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen';os.environ['XDG_CACHE_HOME']='/workspace/.cache'
from qgis.core import *
from qgis.PyQt.QtGui import QColor,QFont
P=Path(__file__).resolve().parents[1];V=P.parent
notes={n['id']:n for n in json.loads((P/'reports/map_analysis_notes.json').read_text())}
app=QgsApplication([],False);app.initQgis();project=QgsProject.instance()
source=V/'outputs/qgis/planning_analysis_v3.qgz'
source_project_sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert project.read(str(source),QgsProject.ReadFlag.ForceReadOnlyLayers)
protected=json.loads((P/'reports/input_baseline.json').read_text())
def hashes():return {k:hashlib.sha256((V.parent/k).read_bytes()).hexdigest()==h for k,h in protected.items()}
assert all(hashes().values())
def label(layout,text,x,y,w,h,size,bold=False,id=None):
    item=QgsLayoutItemLabel(layout);item.setText(text);f=QFont('Noto Sans CJK SC',size);f.setBold(bold);item.setFont(f);item.setFontColor(QColor('#24465B'))
    item.setMargin(0);layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(x,y));item.attemptResize(QgsLayoutSize(w,h))
    if id:item.setId(id)
    return item
updated=[]
for layout in project.layoutManager().layouts():
    parts=layout.name().split(' ')
    if len(parts)<3 or parts[0]!='V3' or parts[1] not in notes:continue
    n=notes[parts[1]]
    maps=[i for i in layout.items() if isinstance(i,QgsLayoutItemMap)]
    before=[(m.pos().x(),m.pos().y(),m.sizeWithUnits().width(),m.sizeWithUnits().height(),m.scale(),m.extent().toString()) for m in maps]
    for i in list(layout.items()):
        if isinstance(i,QgsLayoutItemLabel) and i.pos().y()>=527:layout.removeLayoutItem(i)
    for j,(heading,key) in enumerate([('地块现状与问题','site_problem'),('区域协同关系','regional_coordination'),('改善方向','improvement_direction')]):
        x=30+264*j
        label(layout,heading,x,537,251,8,12,True,'ANALYSIS_HEADING_'+key)
        label(layout,textwrap.fill(n[key],width=52,break_long_words=True,break_on_hyphens=False),x,547,251,33,11,False,'ANALYSIS_BODY_'+key)
    label(layout,f'A1｜1:{n["A1_scale"]:,}｜EPSG:32651｜设计66.0948ha｜周边=研究区内500米环带；可达比例为步行路段长度，非人口覆盖。',30,582,781,5,8)
    label(layout,'来源沿用原图：© OpenStreetMap contributors / Overture；ESA、Copernicus、EC-JRC、USGS、WorldPop。说明区分现状证据与研究建议。',30,588,781,5,8)
    after=[(m.pos().x(),m.pos().y(),m.sizeWithUnits().width(),m.sizeWithUnits().height(),m.scale(),m.extent().toString()) for m in maps]
    assert before==after,(n['id'],'map geometry changed')
    updated.append(n['id'])
assert len(updated)==36
root=project.layerTreeRoot()
project.mapThemeCollection().applyTheme('V3_A_纯矢量专题',root,QgsLayerTreeModel(root))
out=P/'outputs/qgis/planning_analysis_v3_with_notes.qgz';out.parent.mkdir(parents=True,exist_ok=True)
project.setFilePathStorage(Qgis.FilePathType.Relative);assert project.write(str(out));project.clear()
assert project.read(str(out),QgsProject.ReadFlag.ForceReadOnlyLayers)
bad=[l.name() for l in project.mapLayers().values() if not l.isValid()];assert not bad,bad
body_count=sum(1 for l in project.layoutManager().layouts() for i in l.items() if isinstance(i,QgsLayoutItemLabel) and i.id().startswith('ANALYSIS_BODY_'))
assert body_count==108
exports=[]
for ident in ['02','10','22','R01']:
    layout=next(l for l in project.layoutManager().layouts() if l.name().startswith('V3 '+ident+' '))
    settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=100
    target=P/f'outputs/previews/QGIS_notes_{ident}.png';target.parent.mkdir(exist_ok=True)
    result=QgsLayoutExporter(layout).exportToImage(str(target),settings);assert result==QgsLayoutExporter.Success
    exports.append(str(target.relative_to(P)))
layer_count=len(project.mapLayers());layout_count=len(project.layoutManager().layouts());project.clear()
assert all(hashes().values())
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_project_sha
report={'updated_existing_layouts':36,'editable_analysis_paragraphs':108,'valid_layers':layer_count,'layouts':layout_count,
    'invalid_layers':bad,'map_extent_size_scale_positions_unchanged':True,'source_project_untouched':True,
    'relative_paths':True,'default_display':'existing pure-vector theme','source_project_sha256':source_project_sha,'no_added_basemap_or_topic':True,'protected_source_SHA256_unchanged':hashes(),
    'native_preview_exports':exports,'project':str(out.relative_to(P))}
(P/'reports/qgis_caption_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('QGIS caption project verified',report,flush=True);os._exit(0)
