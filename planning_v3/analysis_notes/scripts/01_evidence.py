"""Read-only, exact spatial evidence for captions. No new source data or basemap."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,geopandas as gpd,shapely,rasterio
from rasterio.windows import from_bounds,Window
P=Path(__file__).resolve().parents[1];V=P.parent
M=V/'outputs/gis/reference_v2.gpkg';A=V/'outputs/gis/reference_analysis_v2.gpkg';D=V/'outputs/gis/refined_analysis_v3.gpkg'
(P/'reports').mkdir(parents=True,exist_ok=True)
def read(name,path=M):return gpd.read_file(path,layer=name)
def clip(frame,zone):
    f=frame.iloc[frame.sindex.query(zone,predicate='intersects')].copy()
    f['geometry']=f.geometry.intersection(zone)
    return f[~f.geometry.is_empty]
def union(frame):return shapely.union_all(frame.geometry) if len(frame) else shapely.GeometryCollection()
def weighted(values,weights):
    ok=np.isfinite(values)&(weights>0);v=np.asarray(values)[ok];w=np.asarray(weights)[ok]
    if not len(v):return {'mean':None,'median':None,'p10':None,'p90':None,'valid_weight':0}
    order=np.argsort(v);s=v[order];c=np.cumsum(w[order]);
    return {'mean':float(np.average(v,weights=w)),'median':float(s[np.searchsorted(c,.5*c[-1])]),
        'p10':float(s[np.searchsorted(c,.1*c[-1])]),'p90':float(s[np.searchsorted(c,.9*c[-1])]),'valid_weight':float(w.sum())}
def raster_stats(path,zone):
    with rasterio.open(path) as ds:
        assert ds.crs.to_epsg()==32651
        win=from_bounds(*zone.bounds,ds.transform).round_offsets().round_lengths()
        win=Window(max(0,win.col_off-1),max(0,win.row_off-1),win.width+2,win.height+2).intersection(Window(0,0,ds.width,ds.height))
        arr=ds.read(1,window=win,masked=True);tr=ds.window_transform(win)
        rr,cc=np.indices(arr.shape);x=tr.c+cc*tr.a;y=tr.f+rr*tr.e
        pixels=shapely.box(x.ravel(),(y+tr.e).ravel(),(x+tr.a).ravel(),y.ravel())
        area=shapely.area(shapely.intersection(pixels,zone));v=arr.data.ravel().astype(float)
        good=(~np.ma.getmaskarray(arr).ravel())&np.isfinite(v)&(area>0)
        if any(t in path.stem for t in ['ndvi','ndwi','ndbi']):good &= (v>=(-2 if 'difference' in path.stem else -1))&(v<=(2 if 'difference' in path.stem else 1))
        if 'occurrence' in path.stem:good &= (v>=0)&(v<=100)
        result=weighted(v[good],area[good]);result.update(valid_area_fraction=float(area[good].sum()/zone.area),pixel_size_m=list(ds.res),native_grid_preserved=True)
        if path.stem.startswith(('worldcover','clcd')):
            result['class_fraction_of_valid']={str(int(c)):float(area[good&(v==c)].sum()/area[good].sum()) for c in np.unique(v[good])}
            for key in ['mean','median','p10','p90']:result[key]=None
        return result
def main():
    baseline=json.loads((P/'reports/input_baseline.json').read_text())
    assert all(hashlib.sha256((V.parent/k).read_bytes()).hexdigest()==h for k,h in baseline.items())
    aoi=read('aoi_boundary').geometry.iloc[0];site=read('DESIGN_SITE',D).geometry.iloc[0]
    zones={'site':site,'near500':site.buffer(500).difference(site).intersection(aoi),'region':aoi}
    buildings=read('buildings_enriched');roads=read('road_network_vehicle');walk=read('road_network_walk');land=read('landuse_existing')
    green=read('green_spaces_all');water=read('blue_network');poi=read('poi_all');nodes=read('source_node_intersections',A);nodes=nodes[nodes['mode']=='vehicle']
    access={k:read('access_'+k,A) for k in ['transit','daily_service','education','parks']}
    result={'definition':{'site':'Exact user design polygon;66.09476495ha','near500':'500m Euclidean surrounding ring excluding site, clipped to22.009km2 AOI; not walking catchment','region':'Full unchanged22.009km2 research boundary','ratios':'Exact geometry clipping, union for polygon coverage; no implicit population allocation','access':'Share of mapped walk-edge union length reachable from mapped seeds, not land/population/actual service coverage','height':'All estimated; overlap volume uses max height, not measured FAR','raster':'Exact pixel-footprint intersection area weights, native pixels unchanged'},'zones':{}}
    for key,z in zones.items():
        b=clip(buildings,z);road=clip(roads,z);w=clip(walk,z);lu=clip(land,z);g=union(clip(green,z));blue=union(clip(water,z));bw=union(b)
        volume=0;last=0
        for h in sorted(b.height_m.dropna().unique()):
            volume+=(float(h)-last)*union(b[b.height_m>=h]).area;last=float(h)
        known=union(lu[lu['class']!='unknown']).area
        classes={c:union(group).area/z.area for c,group in lu.groupby('class')}
        roadnames=road[road.name.notna()&(road.name!='')].copy();roadnames['clipped_length_m']=roadnames.length
        r={'area_m2':z.area,'building_records_intersecting':len(b),'building_union_fraction':bw.area/z.area,'estimated_volume_proxy_m':volume/z.area,
            'known_function_fraction':known/z.area,'mapped_function_area_fraction':classes,'mapped_green_fraction':g.area/z.area,'mapped_water_fraction':blue.area/z.area,
            'vehicle_length_m':road.length.sum(),'vehicle_density_km_km2':road.length.sum()/z.area*1000,
            'walk_union_length_m':union(w).length,'mapped_vehicle_nodes':len(clip(nodes,z)),
            'longest_mapped_roads':roadnames.groupby('name').clipped_length_m.sum().sort_values(ascending=False).head(6).to_dict(),
            'poi_observations':poi[poi.geometry.intersects(z)].groupby('category').size().to_dict(),
            'access':{}}
        for k,f in access.items():
            r['access'][k]={str(minutes):float(union(clip(f[f.minutes==minutes],z)).length/max(union(w).length,1e-9)) for minutes in [5,10,15]}
        for layer in ['road_dangling_review','road_building_conflicts','road_schematic_steep_review','open_spaces']:
            r[layer+'_records_intersecting']=len(clip(read(layer),z))
        for layer in ['population_ghsl2020','population_worldpop2025']:
            pop=clip(read(layer,A),z);r[layer]=weighted(pop.population_density_km2.to_numpy(),pop.area.to_numpy());r[layer]['intersecting_native_cells']=len(pop)
        r['raster']={p.stem:raster_stats(p,z) for p in sorted((V/'data/rasters_v2').glob('*.tif')) if 'winter' not in p.stem or 'ndvi' in p.stem}
        for size in [100,200]:
            cells=read(f'grid_{size}m',D);part=clip(cells,z);valid=part.land_function_entropy.notna()
            threshold=json.loads((V/'styles/COLOR_STYLE_SYSTEM.json').read_text())['metric_styles']['building_density']['breaks'][-3]
            r[f'grid{size}']={'intersecting_cells':len(part),'entropy_eligible_cells':int(valid.sum()),
                'entropy_eligible_area_fraction':float(part.loc[valid].area.sum()/z.area),
                'priority_score':weighted(part.research_amenity_priority.to_numpy(),part.area.to_numpy()),
                'high_density_threshold':threshold,'high_density_fraction':float(part.loc[part.building_density>=threshold].area.sum()/z.area)}
        result['zones'][key]=r
        print('EVIDENCE',key,'area',z.area,'coverage',r['building_union_fraction'],flush=True)
    result['named_resources_near500']={}
    for layer in ['green_parks','transit_stations','poi_education']:
        features=read(layer);near=features[features.geometry.intersects(site.buffer(500))&features.name.notna()&(features.name!='')]
        result['named_resources_near500'][layer]=[{'name':r['name'],'source_url':r.get('source_url'),
            'distance_to_site_m':r.geometry.distance(site),'intersects_site':r.geometry.intersects(site),
            'public_access_status':r.get('public_access_status','unverified')} for _,r in near.iterrows()]
    result['protected_SHA256_unchanged']={k:hashlib.sha256((V.parent/k).read_bytes()).hexdigest()==h for k,h in baseline.items()}
    assert all(result['protected_SHA256_unchanged'].values())
    (P/'reports/spatial_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=lambda x:int(x) if isinstance(x,np.integer) else float(x)))
if __name__=='__main__':main()
