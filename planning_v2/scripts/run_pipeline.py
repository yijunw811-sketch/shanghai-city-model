"""Resumable stage runner; no old-model writes. --status is read-only."""
import argparse,json,subprocess,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
stages=[('inventory','01_inventory.py','reports/input_inventory.csv'),('discovery','02_discovery.py','reports/round_1_source_discovery.md'),('overture','overture_reader.py','reports/overture_place_download.json'),('osm','03_osm_context.py','reports/osm_context_downloads.json'),('rasters','04_rasters.py','reports/sentinel_winter_selection.json'),('radiometry','04b_validate_radiometry.py','reports/sentinel_radiometry_control.json'),('research','05_external_round2.py','reports/round_2_source_discovery.md'),('population','06_population_research.py','reports/population_model_summary.csv'),('normalize','07_normalize.py','outputs/gis/planning_enriched.gpkg'),('round3','08_round3.py','reports/round3_acquisition.log'),('clcd','16_clcd_window.py','reports/clcd_window_download.json'),('remaining_sources','18_remaining_highvalue.py','reports/worldpop_age_download_links.json'),('transport_water_age','19_transport_water_age.py','reports/turn_restrictions_download.json'),('analysis','09_analysis.py','outputs/gis/analysis_layers.gpkg'),('additional','11_additional_evidence.py','reports/historical_ndvi_method.json'),('source_followups','11b_source_followups.py','reports/source_followups.log'),('cover_crosscheck','17_cover_crosscheck.py','reports/physical_cover_crosscheck.json'),('seasonality_water','20_seasonality_water.py','outputs/gis/rasters/ndvi_seasonal_difference2026_10m.tif'),('cartography','10_cartography.py','reports/map_catalog.csv'),('qgis','12_qgis_project.py','reports/qgis_validation.json'),('qa','13_qa_reports.py','reports/final_qa.json'),('figures','14_figures_docs.py','outputs/figures/network_coverage.pdf')]
ap=argparse.ArgumentParser();ap.add_argument('--status',action='store_true');ap.add_argument('--from-stage',choices=[s[0] for s in stages]);ap.add_argument('--force',action='store_true',help='Rerun selected stages; normalization rebuilds the NEW database only');args=ap.parse_args()
if args.status:
 for name,script,artifact in stages:print(name,'present' if (P/artifact).exists() else 'pending',artifact)
 sys.exit(0)
selected=False if args.from_stage else True
for name,script,artifact in stages:
 if name==args.from_stage:selected=True
 if not selected:continue
 if (P/artifact).exists() and not args.force:print('resume/skip',name,flush=True);continue
 if name=='overture':
  for typ in ['place','address','division_area','division','division_boundary','land_use','infrastructure','segment','connector','land_cover','water','building_part','building','land','bathymetry']:
   subprocess.run([sys.executable,str(P/'scripts'/script),typ],check=True,cwd=P.parent)
 else:
  python='/usr/bin/python3' if name=='qgis' else sys.executable
  subprocess.run([python,str(P/'scripts'/script)],check=True,cwd=P.parent,env={**os.environ,'QT_QPA_PLATFORM':'offscreen','XDG_CACHE_HOME':str(P.parent/'.cache')})
