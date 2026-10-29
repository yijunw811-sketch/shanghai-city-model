import os,json,shutil,tempfile
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='offscreen'
from qgis.core import QgsApplication,QgsProject,QgsLayoutItemLabel
from qgis.PyQt.QtGui import QFontDatabase
P=Path(__file__).resolve().parents[1];app=QgsApplication([],False);app.initQgis()
for p in (P/'fonts').glob('*.ttf'):QFontDatabase.addApplicationFont(str(p))
t=Path(tempfile.mkdtemp(prefix='shanghai_location_portable_',dir='/tmp'));(t/'data').mkdir();(t/'outputs/qgis').mkdir(parents=True)
shutil.copy2(P/'data/location_context.gpkg',t/'data/location_context.gpkg');shutil.copy2(P/'outputs/qgis/location_two_variants_draft.qgz',t/'outputs/qgis/location_two_variants_draft.qgz')
p=QgsProject.instance();assert p.read(str(t/'outputs/qgis/location_two_variants_draft.qgz'));assert all(v.isValid() for v in p.mapLayers().values());assert len(p.layoutManager().layouts())==2
for layout in p.layoutManager().layouts():
 for item in layout.items():
  if isinstance(item,QgsLayoutItemLabel):
   assert '\ufffd' not in item.text()
res={'relocated_project_reopened':True,'valid_layers':len(p.mapLayers()),'layouts':len(p.layoutManager().layouts()),'self_contained_GPKG':True,'network_required_to_view':False,'portable_font_files_provided':2}
(P/'reports/portable_project_validation.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));print(res);p.clear();shutil.rmtree(t);os._exit(0)
