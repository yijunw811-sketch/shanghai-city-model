"""Read public source metadata only; never acquires or caches basemap imagery."""
from pathlib import Path
import concurrent.futures, json, hashlib
import geopandas as gpd
import requests
from shapely.geometry import shape
from shapely.ops import unary_union

P = Path(__file__).resolve().parents[1]
V = P.parent
BASE = 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'

def get(url, params=None):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    j = r.json()
    if 'error' in j:
        raise RuntimeError(j['error'])
    return j

def main():
    windows = json.loads((P/'reports/fixed_comparison_windows.json').read_text())
    site = gpd.read_file(V/'outputs/gis/refined_analysis_v3.gpkg', layer='DESIGN_SITE').to_crs(32651).geometry.iloc[0]
    aoi = gpd.read_file(V/'outputs/gis/reference_v2.gpkg', layer='aoi_boundary').to_crs(32651).geometry.union_all()
    bbox = gpd.GeoSeries([aoi], crs=32651).to_crs(4326).total_bounds.tolist()
    metadata = get(BASE+'/0/query', {'f':'geojson','geometry':','.join(map(str,bbox)),
        'geometryType':'esriGeometryEnvelope','inSR':4326,'outSR':4326,
        'spatialRel':'esriSpatialRelIntersects','where':'1=1','outFields':'*',
        'returnGeometry':'true','resultRecordCount':100})
    assert not metadata.get('exceededTransferLimit'), 'Incomplete metadata response'
    (P/'data/esri_source_footprints.geojson').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
    footprints = gpd.GeoDataFrame.from_features(metadata['features'], crs=4326).to_crs(32651)
    footprints['aoi_intersection_m2'] = footprints.intersection(aoi).area
    footprints['design_intersection_m2'] = footprints.intersection(site).area
    rows=[]
    for _, row in footprints.iterrows():
        rows.append({k: row[k].item() if hasattr(row[k],'item') else row[k] for k in
            ['OBJECTID','SRC_DATE','SRC_RES','SRC_ACC','SRC_DESC','NICE_NAME','NICE_DESC','MinMapLevel','MaxMapLevel','aoi_intersection_m2','design_intersection_m2']})
    def identify(w):
        b=w['bounds_32651']
        j=get(BASE+'/identify',{'f':'json','geometry':f"{w['point_easting']},{w['point_northing']}",
            'geometryType':'esriGeometryPoint','sr':32651,'mapExtent':','.join(map(str,b)),
            'imageDisplay':'588,588,96','tolerance':0,'returnGeometry':'false','layers':'all:0'})
        return {'id':w['id'],'bounds_32651':b,'point_32651':[w['point_easting'],w['point_northing']],
            'source_results':j.get('results',[]),'actual_new_image_acquired':False}
    with concurrent.futures.ThreadPoolExecutor(3) as pool:
        point_rows=list(pool.map(identify,windows))
    good=footprints[(footprints.SRC_RES<=1)&(footprints.SRC_RES>0)]
    union=unary_union(good.geometry)
    protected=json.loads((P/'state/protected_inputs.json').read_text())
    checks={name:hashlib.sha256((V.parent/name).read_bytes()).hexdigest()==value for name,value in protected.items()}
    assert all(checks.values()),checks
    report={'source':'Esri World Imagery / public metadata','service':BASE,
        'source_footprints':rows,'fixed_location_identify':point_rows,
        'aoi_area_m2':aoi.area,'design_area_m2':site.area,
        'submeter_metadata_footprint_coverage_aoi_fraction':union.intersection(aoi).area/aoi.area,
        'submeter_metadata_footprint_coverage_design_fraction':union.intersection(site).area/site.area,
        'coverage_caveat':'Metadata footprint union only. Does not establish actual rendered pixel availability or which overlapping source wins at every scale.',
        'native_gsd_definition':'SRC_RES published by service; not independent sensor verification and not tile pixel spacing',
        'accuracy_caveat':'SRC_ACC=8.47m is publisher metadata, confidence convention unverified; not a measured RMSE. Clear imagery can still be geographically displaced.',
        'license_verified_for_this_workflow':False,'imagery_acquired':False,
        'registration_control_points_measured':0,'high_resolution_replacement_complete':False,
        'protected_source_SHA256_unchanged':checks}
    (P/'reports/esri_spatial_source_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
