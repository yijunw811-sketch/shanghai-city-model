"""Additional independent source checks, bounded downloads, and evidence dispositions."""
from common import *
from bs4 import BeautifulSoup
import concurrent.futures
sources=[('euluc_tsinghua','B','Tsinghua EULUC functional urban land-use portal','https://data.ess.tsinghua.edu.cn/'),('resdc','B F','CAS Resource and Environment Science Data Center','https://www.resdc.cn/'),('geodata','G H','National Earth System Science Data Center','https://www.geodata.cn/'),('tpdc','G H','National Tibetan Plateau scientific data center','https://data.tpdc.ac.cn/'),('gov_landcode','B J','Official national classification search','https://sousuo.www.gov.cn/sousuo/search.shtml?code=17da70961a7&dataTypeId=107&searchWord=国土空间调查规划用途管制用地用海分类指南'),('worldpop_api','F','WorldPop public statistics API documentation','https://www.worldpop.org/sdi/introapi/')]
def probe(v):
 sid,cat,title,url=v;register(sid,category=cat,dataset_name=title,provider=title,url=url,family='official_or_scientific_portal',round=3)
 p=request_public(sid,url,ROOT/f'cache/source_discovery/{sid}_round3.html',3)
 if p:
  soup=BeautifulSoup(p.read_bytes(),'html.parser');links=[{'text':a.get_text(' ',strip=True)[:130],'url':a.get('href')} for a in soup.select('a[href]') if any(k in a.get_text(' ',strip=True).lower() for k in ['euluc','land','下载','数据','分类','2023','api','234'])]
  dump(ROOT/f'reports/{sid}_links.json',links[:100]);return sid,len(links)
 return sid,'blocked'
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 for r in pool.map(probe,sources):print(r,flush=True)
# Explicitly inspect China annual land-cover metadata; fetch only if efficient range access exists.
p=ROOT/'cache/source_discovery/clcd_zenodo.txt'
if p.exists():
 j=json.loads(p.read_text());fs=[f for f in j.get('files',[]) if '.tif' in f['key']];f=sorted(fs,key=lambda v:v['key'])[-1]
 url=f['links']['self'];sid='clcd_china';register(sid,category='B G',dataset_name=j['metadata']['title'],provider='Yang and Huang / Zenodo',url='https://zenodo.org/records/4417810',license=j['metadata'].get('license',{}).get('id'),spatial_resolution='30m',round=3,format='GeoTIFF')
 try:
  r=SESSION.get(url,headers={'Range':'bytes=0-16383'},stream=True,timeout=45)
  detail={'file':f['key'],'size':f['size'],'status':r.status_code,'content_range':r.headers.get('Content-Range')};r.close()
  dump(ROOT/'reports/clcd_range_probe.json',detail)
  register(sid,access_status='metadata_verified_bulk_download_deferred',reason='National ~0.8GB raster; no validated efficient spatial window reader yet; not downloaded as a global base',notes=str(detail))
  attempt(sid,3,'range_probe',str(detail))
 except Exception as e:attempt(sid,3,'probe_failed',str(e))
# Nonspatial research datasets must not be spatially fabricated.
notes=[{'record':'21217171','decision':'retained_nonspatial_reference','reason':'500m grid IDs have no coordinates or fishnet origin. No reconstruction from FID. Sentiment is not footfall; raw user text absent.'},{'record':'18673350','decision':'unverified_citywide_reference_only','reason':'No authenticated station/measurement lineage. No AOI air-pollution surface generated.'},{'record':'21345765','decision':'partial_historical_reference','reason':'2012–2024 MODIS-derived cube covers only southern AOI; coordinates and observed mask retained, temporal interpolation not an observation.'}]
dump(ROOT/'reports/research_quality_dispositions.json',notes)
export_registry();progress('discovery','round3','source_checks_saved')
