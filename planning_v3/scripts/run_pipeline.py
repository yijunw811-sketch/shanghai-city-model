"""Incremental V3 workflow. Protects V2; no model rebuild, no main merge."""
from pathlib import Path
import argparse,subprocess,sys,os
P=Path(__file__).resolve().parents[1]
stages=[('baseline','01_baseline.py','reports/protected_v2_baseline.csv'),('boundary','02_design_boundary.py','reports/design_boundary_validation.json'),('satellite','03_satellite.py','reports/satellite_provenance.json'),('multiscale','04_multiscale.py','reports/indicator_scale_selection.json'),('styles','05_styles.py','styles/COLOR_STYLE_SYSTEM.json'),('maps','06_maps.py','reports/map_catalog_v3.json'),('comparisons','07_checks_comparisons.py','reports/scale_stability_vs_v2.csv'),('qgis','08_qgis_project.py','reports/qgis_validation_v3.json'),('qa','09_qa.py','reports/final_qa_v3.json'),('reports','10_reports.py','reports/delivery_summary_v3.md')]
a=argparse.ArgumentParser();a.add_argument('--status',action='store_true');a.add_argument('--from-stage',choices=[r[0] for r in stages]);a.add_argument('--force',action='store_true');args=a.parse_args()
if args.status:
 for n,s,o in stages:print(n,'present' if (P/o).exists() else 'pending',o)
 sys.exit(0)
selected=not args.from_stage
for n,s,o in stages:
 if n==args.from_stage:selected=True
 if not selected:continue
 if (P/o).exists() and not args.force:print('skip existing',n,flush=True);continue
 cmd=['/usr/bin/python3' if n=='qgis' else sys.executable,str(P/'scripts'/s)]
 subprocess.run(cmd,cwd=P.parent,check=True,env={**os.environ,'QT_QPA_PLATFORM':'offscreen','XDG_CACHE_HOME':'/workspace/.cache','MPLCONFIGDIR':'/workspace/.cache/matplotlib'})
