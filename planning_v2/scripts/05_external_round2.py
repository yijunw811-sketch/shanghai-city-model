"""Second-round source expansion: official documents, research catalogue, open knowledge."""
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import re
from common import *

keywords={
'A':'Shanghai building footprint urban morphology cadastral',
'B':'Shanghai land use land cover urban',
'C':'Shanghai road transport metro mobility',
'D':'Shanghai hospital school public service facility',
'E':'Shanghai urban industry vitality POI',
'F':'Shanghai population demography census',
'G':'Shanghai vegetation green water wetland',
'H':'Shanghai heat temperature flooding environment',
'I':'Shanghai heritage historical urban renewal',
'J':'Shanghai spatial planning regulation land use',
'K':'Shanghai accessibility urban planning analysis'}
research=[]
for topic,query in keywords.items():
    sid='zenodo_'+topic
    url='https://zenodo.org/api/records'
    # Query title explicitly; an affiliation in Shanghai is not study-area evidence.
    tokens=' OR '.join('"'+w+'"' for w in query.split()[1:])
    params={'q':'metadata.title:"Shanghai" AND ('+tokens+')','size':10,'sort':'mostrecent'}
    register(sid,category=topic,dataset_name='Zenodo topic search: '+query,provider='Zenodo',url=url,family='scientific_catalog',reuse_allowed='metadata_only; each record license separately inspected',round=2)
    result=request_public(sid,url,ROOT/f'cache/research/zenodo_{topic}.json',round_number=2,params=params)
    if not result:continue
    try:data=json.loads(result.read_text())
    except Exception:continue
    for hit in data.get('hits',{}).get('hits',[]):
        metadata=hit.get('metadata',{});title=metadata.get('title','');description=BeautifulSoup(metadata.get('description',''),'html.parser').get_text(' ',strip=True)
        license=metadata.get('license',{});license=license.get('id') if isinstance(license,dict) else license
        files=hit.get('files',[])
        geographic='shanghai' in (title+' '+description).lower()
        commercial=any(t in (title+' '+description).lower() for t in ['amap','gaode','baidu','高德','百度'])
        research.append({'topic':topic,'record_id':hit.get('id'),'title':title,'doi':metadata.get('doi'),'url':hit.get('links',{}).get('html') or hit.get('links',{}).get('self_html') or f'https://zenodo.org/records/{hit.get("id")}','published_at':metadata.get('publication_date'),'license':license,'resource_type':json.dumps(metadata.get('resource_type',{})),'geographic_evidence':geographic,'commercial_map_permission_review':commercial,'files_json':json.dumps([{'key':f.get('key'),'bytes':f.get('size'),'download':f.get('links',{}).get('self'),'checksum':f.get('checksum')} for f in files]),'abstract':description[:3500],'status':'requires_upstream_permission_review' if commercial else 'candidate_needs_AOI_format_review' if geographic else 'irrelevant_geography_rejected'})
    export_registry()
pd.DataFrame(research).to_csv(ROOT/'reports/research_dataset_candidates.csv',index=False)

# Use actual official-page hyperlinks, not guessed article IDs or commercial-map scraping.
seeds=[
('stats2025','F','https://tjj.sh.gov.cn/tjgb/20260330/e0772941e8e041eaaad2df850b44ef98.html','上海市统计局'),
('pop2025','F','https://tjj.sh.gov.cn/tjgb/20260630/b74619258aee4912a55a1da928b5be30.html','上海市统计局'),
('parks_official','G','https://lhsr.sh.gov.cn/gyldml/','上海绿化市容局')]
pages=[]
for name,categories in [('sh_education','D'),('sh_transport','C'),('sh_planning','A B I J'),('sh_housing','A F I'),('sh_environment','G H'),('sh_culture','D I'),('jingan','A D F I J'),('baoshan','A D F I J'),('hongkou','A D F I J')]:
    path=ROOT/f'cache/source_discovery/{name}.txt'
    if not path.exists():continue
    soup=BeautifulSoup(path.read_bytes(),'html.parser')
    with db() as con:row=con.execute('SELECT record_json FROM sources WHERE source_id=?',(name,)).fetchone()
    parent=json.loads(row[0]);base_url=parent['url']
    for a in soup.find_all('a',href=True):
        title=a.get_text(' ',strip=True);url=urljoin(base_url,a['href'])
        if not url.startswith('http'):continue
        priority=re.search('名录|名单|通讯录|地址|学校概况|医疗机构|统计公报|统计年鉴|人口普查|保护单位|历史建筑|公园名录|开放公园|分类指南|用地用海|规划成果|规划公示|控制性详细规划|行政区划',title)
        if not priority:continue
        pages.append({'parent':name,'category':categories,'title':title,'url':url,'provider':parent['provider']})
        seeds.append(('gov_'+hashlib.sha256(url.encode()).hexdigest()[:12],categories,url,parent['provider']))
seen=set();official_evidence=[]
for sid,categories,url,provider in seeds:
    if url in seen:continue
    seen.add(url)
    register(sid,category=categories,dataset_name='Official public document/catalogue',provider=provider,url=url,family='government',license='public disclosure; specific reuse terms need inspection',reuse_allowed='metadata_and_public_facts_only_until_terms_verified',round=2)
    path=request_public(sid,url,ROOT/f'cache/official/{sid}.html',round_number=2,timeout=25)
    if not path:
        official_evidence.append({'source_id':sid,'url':url,'status':'access_failed','category':categories});continue
    soup=BeautifulSoup(path.read_bytes(),'html.parser');text=soup.get_text(' ',strip=True)
    title=soup.title.get_text(' ',strip=True) if soup.title else ''
    attachments=[urljoin(url,a['href']) for a in soup.find_all('a',href=True) if re.search(r'\.(?:pdf|xlsx?|csv|geojson|zip|docx?)(?:\?|$)',a['href'],re.I)]
    official_evidence.append({'source_id':sid,'url':url,'status':'page_fetched_not_assumed_vector_data','category':categories,'title':title,'attachments_json':json.dumps(attachments,ensure_ascii=False),'excerpt':text[:2500]})
    (ROOT/f'cache/official/{sid}.txt').write_text(text)
pd.DataFrame(pages).to_csv(ROOT/'reports/official_resource_links.csv',index=False)
pd.DataFrame(official_evidence).to_csv(ROOT/'reports/official_document_evidence.csv',index=False)

# Wikidata is a separate CC0 source; designation points are not legal protection boundaries.
sid='wikidata_context';url='https://query.wikidata.org/sparql'
bounds=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).iloc[0].bounds
w,s,e,n=bounds
query=f'''SELECT ?item ?itemLabel ?coord ?type ?typeLabel ?heritage ?heritageLabel ?inception WHERE {{
 SERVICE wikibase:box {{ ?item wdt:P625 ?coord . bd:serviceParam wikibase:cornerWest "Point({w} {s})"^^geo:wktLiteral ; wikibase:cornerEast "Point({e} {n})"^^geo:wktLiteral . }}
 OPTIONAL {{ ?item wdt:P31 ?type . }} OPTIONAL {{ ?item wdt:P1435 ?heritage . }} OPTIONAL {{ ?item wdt:P571 ?inception . }}
 SERVICE wikibase:label {{ bd:serviceParam wikibase:language "zh,en" . }}
}} LIMIT 1000'''
register(sid,category='A D I',dataset_name='Wikidata AOI+2km georeferenced resources',provider='Wikidata',url=url,family='open_knowledge',license='CC0-1.0',reuse_allowed=True,api_registration_needed=False,round=2)
SESSION.headers['User-Agent']='ShanghaiPlanningGISResearch/2.0 (https://github.com/yijunw811-sketch/shanghai-city-model)'
path=request_public(sid,url,RAW/'wikidata/context.json',round_number=2,params={'query':query,'format':'json'},timeout=70,kind='data')
if path:
    try:
        rows=json.loads(path.read_text()).get('results',{}).get('bindings',[])
        register(sid,access_status='fetched_context_pending_exact_clip',notes=f'{len(rows)} bindings, may contain multiple types per entity; deduplicate IDs before statistics')
    except Exception as exc:register(sid,access_status='invalid_json_response',reason=str(exc))

# Deliberately record failed/irrelevant general searches instead of accepting bad results as evidence.
search_failures=[{'engine':'Bing HTML','query':'site:gov.cn 国土空间调查 规划 用地用海 分类指南 2023 234 修订2025 2026','outcome':'irrelevant_results_rejected','evidence':'Returned Minecraft pages despite government/topic query; not used as evidence'}, {'engine':'Bing RSS','query':'自然资发2023 234 分类指南','outcome':'irrelevant_and_reuse_restricted_rejected','evidence':'Returned unrelated church pages; RSS explicitly restricts reuse beyond personal aggregator'}, {'engine':'Bing China','query':'自然资发2023 234 分类指南','outcome':'no_visible_results','evidence':'HTML contained only search shell'}, {'engine':'Google','query':'上海 国土空间 用地用海分类 指南2023 234号','outcome':'javascript_required','evidence':'No visible results in accessible HTML'}, {'engine':'DuckDuckGo','query':'Shanghai land use GIS data open population','outcome':'human_challenge','evidence':'HTTP202 human challenge; no bypass attempted'}]
pd.DataFrame(search_failures).to_csv(ROOT/'reports/general_search_limitations.csv',index=False)
export_registry();progress('source_search','round_2','catalogue_and_official_expansion_complete',research_candidates=len(research),official_pages=len(official_evidence))
(ROOT/'reports/round_2_source_discovery.md').write_text('# 第二轮：针对缺口扩展来源\n\n'+f'按A–K主题执行独立科研目录查询，保留{len(research)}条实际候选；按真实官方页面链接调查{len(official_evidence)}个文件/目录。另查Wikidata CC0坐标资源。\n\n'+'一般搜索引擎返回无关结果、JS壳或人机验证，已排除且未绕过。官方深层页面与首页访问状态分开记录，503不被误写成需要密钥。高德/百度来源的科研POI即使上传者标注开放许可，仍列上游许可复核，不自动导入。\n\n'+'继续处理实际可得的遥感COG、人口替代产品与开放矢量，不因这些访问限制停止其他主题。')
print('ROUND2 research',len(research),'official',len(official_evidence),flush=True)
