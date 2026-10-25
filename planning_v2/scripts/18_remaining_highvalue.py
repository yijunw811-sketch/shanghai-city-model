from common import *
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import zipfile,io
# Actual age-sex category139 link found in public WorldPop page, no guessed authentication API.
url='https://hub.worldpop.org/ajax/geolisting/category?id=139';sid='worldpop_agesex2025_1km'
register(sid,category='F',provider='WorldPop',dataset_name='Global2 R2025A country age-sex ~1km',url=url,family='population_model',license='CC-BY-4.0 subject to official release terms',round=3)
p=request_public(sid,url,ROOT/'cache/source_discovery/worldpop_age139.json',3)
if p:
 try:
  records=json.loads(p.read_text());china=[r for r in records if r.get('country')=='China' and r.get('popyear')=='2025'];dump(ROOT/'reports/worldpop_age_candidates.json',china)
  if china:
   summary='https://hub.worldpop.org/geodata/summary?id='+str(china[0]['id']);p=request_public(sid+'_summary',summary,ROOT/'cache/source_discovery/worldpop_age2025_summary.html',3)
   if p:
    soup=BeautifulSoup(p.read_bytes(),'html.parser');links=[{'text':a.get_text(' ',strip=True),'url':urljoin(summary,a['href'])} for a in soup.select('a[href]') if any(t in a['href'].lower() for t in ['.tif','.zip','.csv','data.worldpop'])];dump(ROOT/'reports/worldpop_age_download_links.json',links);print('AGE links',links[:6],flush=True)
 except Exception as e:attempt(sid,3,'metadata_parse_failed',str(e))
# Download the official tiny downloader as TEXT ONLY, inspect published URL layout, never execute it.
url='https://storage.googleapis.com/water-world/downloads_ancillary/Download_WaterData_Python3.zip';sid='jrc_water_downloader_metadata'
register(sid,category='G H',provider='EC JRC Global Surface Water',dataset_name='Official public water data download instructions',url=url,family='remote_sensing',round=3)
p=request_public(sid,url,ROOT/'cache/source_discovery/JRC_Water_Downloader.zip',3,'metadata')
if p:
 try:
  with zipfile.ZipFile(p) as z:
   scripts={n:z.read(n).decode('utf-8',errors='replace') for n in z.namelist() if n.endswith('.py') and z.getinfo(n).file_size<100000}
  dump(ROOT/'reports/jrc_water_published_download_instructions.json',scripts)
  for n,s in scripts.items():print(n,s[:7000],flush=True)
 except Exception as e:attempt(sid,3,'archive_inspection_failed',str(e))
export_registry()
