from common import *
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import runpy,zipfile
helper=runpy.run_path(str(ROOT/'scripts/06_population_research.py'),run_name='source_tools');limited=helper['limited_download']
# Follow real directory links, not guessed dataset endpoints.
url='https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_AGE_GLOBE_R2025A/V1-0/'
sid='ghsl_built_age';register(sid,category='A I',provider='European Commission JRC',dataset_name='GHS AGE R2025A',url=url,family='scientific_raster',license='verify official copyright',round=3)
for depth in range(4):
 p=request_public(sid+'_directory_'+str(depth),url,ROOT/f'cache/source_discovery/ghs_age_depth{depth}.html',3)
 if not p:break
 soup=BeautifulSoup(p.read_bytes(),'html.parser');links=[urljoin(url,a['href']) for a in soup.select('a[href]') if not a['href'].startswith(('?','/'))];print('AGE',url,links[:15],flush=True)
 zips=[u for u in links if 'R6_C30' in u and u.endswith('.zip')]
 if zips:
  z=limited(sid,zips[0],RAW/'ghsl_age'/Path(zips[0]).name,64*1024*1024)
  with zipfile.ZipFile(z) as archive:
   assert archive.testzip() is None
   names=archive.namelist();dump(ROOT/'reports/ghs_age_archive.json',{'url':zips[0],'members':names,'sha256':sha(z)})
   for member in names:
    if member.lower().endswith('.tif'):
     # Extract only regional tile into cache then clip with trusted same reader.
     target=ROOT/'cache/ghsl_age'/Path(member).name;target.parent.mkdir(exist_ok=True)
     if not target.exists():
      with archive.open(member) as src,target.open('wb') as dst:__import__('shutil').copyfileobj(src,dst)
     import rasterio
     from rasterio.windows import from_bounds
     with rasterio.open(target) as ds:
      extent=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(ds.crs).total_bounds
      window=from_bounds(*extent,transform=ds.transform).round_offsets().round_lengths();arr=ds.read(window=window);profile=ds.profile.copy();profile.update(height=arr.shape[1],width=arr.shape[2],transform=ds.window_transform(window),compress='deflate')
      crop=RAW/'ghsl_age/ghs_age_context_native.tif'
      with rasterio.open(crop,'w',**profile) as dst:dst.write(arr)
      dump(ROOT/'reports/ghs_age_source.json',{'archive':zips[0],'native_crs':str(ds.crs),'resolution':ds.res,'interpretation':'Model of built-up development epochs; NOT individual building construction date','crop_sha256':sha(crop)})
  register(sid,access_status='regional_tile_verified_cropped',local_path=str(z.relative_to(ROOT)),checksum=sha(z));break
 candidates=[u for u in links if u.endswith('/') and ('tile' in u.lower() or '54009' in u or '100' in u)]
 if not candidates:register(sid,access_status='metadata_only',reason='No efficient selected regional tile link identified');break
 url=candidates[0]
# Independent historical admin boundaries, public PDDL; explicit outdated year.
meta=json.loads((ROOT/'cache/source_discovery/geoboundaries.txt').read_text());url=meta.get('simplifiedGeometryGeoJSON')
if url:
 sid='geoboundaries_adm2_2017';register(sid,category='A',dataset_name='geoBoundaries CHN ADM2 2017 simplified',provider='geoBoundaries',url=url,license=meta.get('boundaryLicense'),valid_year=2017,family='independent_geography',round=3)
 p=request_public(sid,url,RAW/'geoboundaries/CHN_ADM2_2017_simplified.geojson',3,'data')
 if p:
  g=source_context(gpd.read_file(p));g['year']=2017;g['confidence']='historical_simplified_not_current_legal_boundary';g['source_url']=url;g['license']=meta['boundaryLicense'];write_layer(g,ROOT/'outputs/gis/planning_enriched.gpkg','admin_reference_2017');register(sid,access_status='verified_historical_reference',feature_count_aoi=int(g.in_aoi.sum()))
export_registry()
