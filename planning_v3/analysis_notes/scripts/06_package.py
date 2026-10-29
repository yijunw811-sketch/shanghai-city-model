from pathlib import Path
import json,hashlib,zipfile,re,unicodedata
import pymupdf as fitz
P=Path(__file__).resolve().parents[1];D=P/'downloads';D.mkdir(exist_ok=True)
notes=json.loads((P/'reports/map_analysis_notes.json').read_text());qa=json.loads((P/'reports/FINAL_QA.json').read_text());assert qa['existing_topics_annotated']==36
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t):return re.sub(r'\s+','',unicodedata.normalize('NFKC',t))
records=[]
for fmt in ['A1','A3']:
    target=D/f'Shanghai_GIS_V3_Analysis_{fmt}_36maps.pdf';doc=fitz.open()
    for n in notes:
        src=fitz.open(P/f'outputs/{fmt}'/(n['stem']+'_分析说明.pdf'));doc.insert_pdf(src);src.close()
    doc.set_toc([[1,n['id']+' '+n['title'],i+1] for i,n in enumerate(notes)])
    doc.set_metadata({'title':'上海GIS V3｜36张既有专题图分析说明｜'+fmt,'author':'Shanghai city-model GIS project','subject':'地块问题、区域协同与改善方向；无新底图'})
    doc.save(target,garbage=4,deflate=True);doc.close()
    with fitz.open(target) as d:
        assert len(d)==36
        for i,n in enumerate(notes):
            text=norm(d[i].get_text())
            assert all(norm(n[k]) in text for k in ['site_problem','regional_coordination','improvement_direction'])
    records.append({'file':target.name,'bytes':target.stat().st_size,'sha256':sha(target),'pages':36,'text_verified_all_pages':True})
    print('BOOK',fmt,target.stat().st_size,flush=True)
files=sorted([p for p in P.rglob('*') if p.is_file() and p.parts[len(P.parts)] not in ['downloads','cache','state']
    and '__pycache__' not in p.parts and p.name!='DELIVERY_MANIFEST.json' and not p.name.endswith('~')])
manifest={'existing_maps_annotated':36,'paragraphs':108,'new_basemaps':0,'qgis':'outputs/qgis/planning_analysis_v3_with_notes.qgz',
    'files':[{'path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
(P/'reports/DELIVERY_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));files.append(P/'reports/DELIVERY_MANIFEST.json')
core=[p for p in files if 'outputs' not in p.relative_to(P).parts or p.relative_to(P).parts[1] in ['qgis','previews']]
groups=[('shanghai-v3-analysis-notes-00-core.zip',core)]
for name,ids in [('01-maps-01-12',[f'{i:02}' for i in range(1,13)]),('02-maps-13-24',[f'{i:02}' for i in range(13,25)]),('03-maps-25-28-R01-R08',[f'{i:02}' for i in range(25,29)]+[f'R{i:02}' for i in range(1,9)])]:
    group=[]
    for n in notes:
        if n['id'] not in ids:continue
        for folder,ext in [('A1','pdf'),('A3','pdf'),('PNG300','png'),('SVG','svg')]:group.append(P/f'outputs/{folder}'/(n['stem']+'_分析说明.'+ext))
    groups.append(('shanghai-v3-analysis-notes-'+name+'.zip',group))
packaged=set()
for name,group in groups:
    target=D/name
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in group:z.write(p,'planning_v3/analysis_notes/'+str(p.relative_to(P)));packaged.add(p)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for p in group:assert hashlib.sha256(z.read('planning_v3/analysis_notes/'+str(p.relative_to(P)))).hexdigest()==sha(p)
    assert target.stat().st_size<95*1024*1024,'GitHub file too large'
    records.append({'file':name,'bytes':target.stat().st_size,'sha256':sha(target),'members':len(group),'CRC_and_member_SHA256_verified':True})
    print('PACKAGE',name,target.stat().st_size,flush=True)
assert packaged==set(files),[str(x) for x in set(files)-packaged]
(D/'package_verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
(D/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['file']+'\n' for r in records))
index=['# 上海GIS V3｜36张既有分析图加注成果','','已完成108段逐图说明：地块现状与问题、区域协同关系、改善方向。没有新增地图主题或底图。','',
    '## 先看合订图册','','- [A3审阅图册｜36页](Shanghai_GIS_V3_Analysis_A3_36maps.pdf)','- [A1正式图册｜36页](Shanghai_GIS_V3_Analysis_A1_36maps.pdf)',
    '- [逐图说明全文](../MAP_ANALYSIS_NOTES.md) · [跨图协调方向](../DESIGN_COORDINATION_SUMMARY.md) · [36图预览索引](../outputs/previews/INDEX_36_ANALYSIS_NOTES.png)','',
    '## 完整文件包','','四包解压到同一目录，可得到单张A1/A3 PDF、300DPI PNG、SVG、说明全文、证据和可编辑QGIS工程。','','| 文件 | 大小 | 内容 |','|---|---:|---|']
for r in records:
    if not r['file'].endswith('.zip'):continue
    detail='QGIS工程、逐图说明、证据、脚本和QA' if '00-core' in r['file'] else '对应专题的A1/A3 PDF、PNG300及SVG'
    index.append(f"| [{r['file']}]({r['file']}) | {r['bytes']/1e6:.2f} MB | {detail} |")
index += ['', '静态图纸可独立阅读。QGIS沿用原V3数据相对路径，需要已有[原V3核心GIS包](https://github.com/yijunw811-sketch/shanghai-city-model/blob/planning-v3-cartography-20261028/planning_v3/downloads/RESULTS_INDEX.md)。',
    '', '说明位于地图下方，地图几何、色带、比例与设计红线保留；原PDF字体兼容性已修复。地块与周边500米环带、全域对照；数据不足处明确保留不确定性，改善方向为研究建议。',
    '', '[SHA256](SHA256SUMS.txt) · [压缩包验证](package_verification.json) · [最终QA](../reports/FINAL_QA.json) · [使用说明](../README.md)',
    '', '分支planning-v3-analysis-notes-20261029；本包与未完成的影像搜集分开交付，原GIS、V2和三维模型不变。']
(D/'RESULTS_INDEX.md').write_text('\n'.join(index)+'\n')
print('COMPLETE:2 searchable36-page books+4verified archives; all delivery members covered.')
