"""Resolve metadata/COG harmonization discrepancy with same-scene mirror controls."""
import runpy
import json
import numpy as np
import rasterio
import xml.etree.ElementTree as ET
from common import *

tools=runpy.run_path(str(ROOT/'scripts/04_rasters.py'),run_name='raster_tools')
control_output=ROOT/'reports/sentinel_radiometry_control.json'
controls=json.loads(control_output.read_text()) if control_output.exists() else {}
for season in ['summer','winter']:
    chosen=json.loads((ROOT/f'reports/sentinel_{season}_selection.json').read_text())
    if chosen['scene_id'] in controls:continue
    date=chosen['datetime'][:10]
    data=tools['stac_search']('s2_pc_'+season,'sentinel-2-l2a',date+'T00:00:00Z/'+date+'T23:59:59Z',None,provider='planetary')
    features=[f for f in data.get('features',[]) if f['properties'].get('s2:mgrs_tile')=='51RUQ']
    if not features:raise RuntimeError('No exact same-date/tile Sentinel control product')
    item=features[0];band_results={}
    for band,key in [('red','B04'),('nir','B08'),('green','B03'),('swir16','B11')]:
        asset=item['assets'][key]
        local=RAW/f'sentinel_control/{item["id"]}/{key}.tif'
        use_url=asset['href'] if local.exists() else tools['signed_pc'](asset['href'])
        raw,profile=tools['crop'](use_url,local,f'pc_s2_control_{season}_{key}',date,'Copernicus Sentinel open data terms','Same-scene mirror raw-DN calibration check; no SAS archived')
        with rasterio.open(RAW/f'sentinel2/{chosen["scene_id"]}/{band}.tif') as src:other=src.read(1);reference=src.profile.copy()
        mirror=tools['align'](raw,profile,reference)
        valid=(mirror>0)&(other>0)
        delta=mirror[valid]-other[valid]
        if not len(delta):raise RuntimeError('No common control pixels')
        values=np.quantile(delta,[.01,.5,.99])
        if not np.allclose(values,1000,atol=1):raise RuntimeError(f'Unresolved mirror calibration mismatch for {season}/{band}: {values}')
        band_results[band]={'common_pixels':len(delta),'pc_minus_aws_dn_p01_p50_p99':values.tolist(),'exact_1000_fraction':float(np.isclose(delta,1000,atol=1).mean()),'pc_asset_url':safe_url(asset['href'])}
    offsets=[];quantification=[]
    if 'product-metadata' in item['assets']:
        asset=item['assets']['product-metadata'];path=RAW/f'sentinel_control/{item["id"]}/product_metadata.xml'
        if not path.exists():
            r=SESSION.get(tools['signed_pc'](asset['href']),timeout=45)
            if not r.ok:raise RuntimeError(f'Control product XML HTTP {r.status_code}')
            path.write_bytes(r.content)
        root=ET.fromstring(path.read_bytes())
        offsets=sorted({v.text for v in root.iter() if v.tag.rsplit('}',1)[-1]=='BOA_ADD_OFFSET'})
        quantification=sorted({v.text for v in root.iter() if v.tag.rsplit('}',1)[-1]=='BOA_QUANTIFICATION_VALUE'})
    controls[chosen['scene_id']]={'season':season,'acquired':chosen['datetime'],'pc_product':item['id'],'bands':band_results,'xml_boa_offsets':offsets,'xml_quantification_values':quantification,'dn_shift_pc_minus_aws':1000,'effective_aws_reflectance_offset':0.,'interpretation':'PC unharmonized DN = AWS harmonized DN +1000 on same original scene. With product BOA correction -1000/10000, AWS pixels must not receive the offset a second time. Original STAC band offset is retained as conflicting metadata, never silently overwritten.','status':'verified_same_scene_mirror_representation','not_independent_ground_measurement':True}
    print('CALIBRATION_VERIFIED',season,chosen['scene_id'],flush=True)
    dump(control_output,controls)
dump(ROOT/'reports/sentinel_radiometry_control.json',controls)
progress('layer_validation','sentinel_radiometry','cross_mirror_verified',scenes=len(controls),all_bands_checked=True)
