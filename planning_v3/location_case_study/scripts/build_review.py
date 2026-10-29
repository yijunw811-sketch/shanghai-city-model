from pathlib import Path
import json,io,hashlib,zipfile
import requests
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
rows=[
('01','A','mandaworks',1,'Trenčín 城市与滨水结构','Mandaworks + Hosper｜2014 国际城市设计竞赛一等奖','浅底低饱和总平，弱化城市肌理。','一张大总平统领，河流成为构图骨架。','灰白建筑、蓝灰水面、黄绿空间。','河流和城市连接优先，建筑肌理其次。','适合片区层级；宏观上海定位需另配小图。','借鉴背景降权、道路跨越及开放空间连续性。','这是方案总平，不可将新增桥梁、绿地当成现状；不复制滨河条件。'),
('02','A','shanghai-midtown',3,'Shanghai Midtown Belt 北部框架','MLA+ Consortium｜2026 WLA Outstanding Award，概念总体规划与城市设计','浅底结构图，走廊、节点与板块清晰。','城市带展开，箭头表达跨区域联系，节点分级。','浅灰底、绿蓝骨架、橙色功能块。','区域通道—片区节点—功能板块。','很适合上海片区关系；原项目约600 km²，与66.10 ha场地尺度不同。','借鉴城市资源与走廊关系；本项目边界独立用朱红线。','图中包含规划意图，不能复制为现状；箭头不是流量或真实车行时间。'),
('03','B','thesis-diagrams',1,'Thesis 步行联系图','Alex Hogrefe｜2011 学位项目图解，非竞赛获奖案例','黑白体块配高亮路径，焦点集中。','俯视场地，路径横贯画面，角部图例。','炭黑、灰白、橙黄。','路径最强，体块其次，背景退后。','适合局部交通插图；不足以独立承担上海宏观区位。','借鉴路径分级与底图上的简洁图例。','线宽不代表实测人流；不能照搬其路线或把估计高度当成测绘。'),
('04','B','philly-diagram-study',19,'Philly Bridge 场地联系图','Alex Hogrefe｜2017 专业作品集／教程，非竞赛','深色模型上用暖色强化交通和地面空间。','斜俯视，以斜向交通结构带出场地焦点。','深紫灰、橙红、暖黄。','交通结构—场地空间—背景建筑。','局部识别性强，宏观定位能力较弱。','借鉴单一主题高对比和背景降权。','不借鉴景深模糊、雾化和夸张光效，以免影响真实边界、道路辨识。'),
('05','C','mla-felixx',3,'Bao’an G107 城市更新走廊','MLA+、Felixx、CAUPD及深圳市政设计研究院｜2016 城市设计竞赛一等奖','浅底城市拼贴，编号节点串联区域叙事。','斜俯视长走廊配节点编号和城市背景。','灰白底、黑色标题牌、彩色节点。','更新走廊—编号节点—背景城市。','适合解释地块与周边板块协同；须限制标签数量。','借鉴节点编号、短注释和跨尺度资源串联。','节点属于设计方案，不能复制为本项目现状设施；不移植新建体量。'),
('06','C','site-analysis-diagrams',12,'Long Wharf / Boston 多专题分析','Alex Hogrefe｜2014 专业作品集／教程，非竞赛','柔和纹理底叠加路径、绿地和空间层。','连续背景叠加专题线面，以留白缓冲。','灰色纹理、青色水面与红色场地层。','整体肌理—专题联系—场地位置。','适合资源综合；可用可靠矢量替代许可不明的影像纹理。','借鉴统一底图、可拆分专题、逐层显现信息。','港口船行逻辑不适用；不移植版权影像，不用低清底图制造高清假象。'),
('07','C','cranbrook-project',3,'Cranbrook 多尺度图解展板','Alex Hogrefe｜2013 校园建筑项目作品集，非竞赛','浅底拼贴，整体结构、分层图解和局部放大共同叙事。','横向跨页，从校园整体进入局部场地。','暖灰底、冷色线层、少量强调色。','总览—专题分解—局部定位。','很适合上海—城区—真实设计地块三级组织；校园事实不能迁移。','借鉴大小图阅读顺序、留白和短注释。','不把校园轴线当上海结构；不复制跨页缝、过小文字和装饰肌理。')]
fields=['风格特点','构图方式','色彩倾向','信息层级','是否适合本项目','可借鉴点','不建议照搬']
(ROOT/'case_images').mkdir(exist_ok=True);cases=[]
for row in rows:
 id,g,prefix,idx,name,credit,*notes=row
 page=next((ROOT/'cache/pages').glob(prefix+'*.json'),None)
 if page:
  src=json.loads(page.read_text());url=src['images'][idx]['src']
 else:
  existing=next(c for c in json.loads((ROOT/'cases.json').read_text()) if c['id']==id);src={'url':existing['source_url']};url=existing['image_url']
 target=ROOT/'case_images'/f'{id}.jpg'
 if not target.exists():
  r=requests.get(url,timeout=60);r.raise_for_status();im=Image.open(io.BytesIO(r.content)).convert('RGB');im.thumbnail((1500,1500));im.save(target,quality=90)
 cases.append(dict(id=id,group=g,name=name,credit=credit,source_url=src['url'],image_url=url,image=str(target.relative_to(ROOT)),thumbnail_size=Image.open(target).size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),review=dict(zip(fields,notes))))
(ROOT/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2))
md='''# 区位分析案例评审｜阶段1

本包仅供风格选择，未制作上海最终区位图。核对日期：2026-10-29。7个案例：2个城市设计竞赛获奖项目、1个专业奖项框架、4个专业作品集／教学图解。后者用于表达借鉴，不冒称竞赛获奖作品。

应用对象为已核验约66.0948 ha核心设计边界；22.009 km²研究区仅作背景，不能替代红线。案例内方案、节点与箭头不是本项目事实。

## 检索与筛选

检索 WLA 的 urban design competition、Visualizing Architecture 的 site analysis / diagrams 等专题，核对文章与真实图片并检查图面。ASLA旧档案入口失效、ArchDaily动态结果未形成可核验案例，未计入。前海候选以模型为主，Chouteau与Derbent候选以效果图为主，未入选。保留能表达城市结构、区域联系、路径或多尺度展板组织的图面。

部分图是规划方案图，并非现状区位图；逐例指出迁移边界。预览保留完整画幅，版权归原作者。公开访问不等于开放授权；缩略图仅用于本次评论与选择，不作为本项目成图素材，不据此分发商业素材包。最终制图使用本项目真实GIS与自行绘制符号。

'''
for c in cases:
 md+=f"## {c['id']}｜{c['name']}（{c['group']}）\n\n{c['credit']}\n\n![案例{c['id']}]({c['image']})\n\n- 发布页：{c['source_url']}\n- 原图：{c['image_url']}\n"
 for k,v in c['review'].items():md+=f'- **{k}**：{v}\n'
 md+='\n'
(ROOT/'LOCATION_CASE_REVIEW.md').write_text(md)
(ROOT/'STYLE_OPTIONS_SUMMARY.md').write_text('''# 三组候选风格｜推荐排序

仅阶段1。请选择A、B、C或指定案例组合，确认后才进入阶段2。

| 排序 | 方向 | 案例 | 视觉与适用内容 | 优点 | 风险与场地适配 |
|---|---|---|---|---|---|
| 1 | A 浅底理性结构风 | 01、02 | 克制清晰；宏观定位、片区道路水绿骨架与节点 | 地理关系易读，A1/A3均适用，现有GIS可支撑 | 避免普通GIS打印感，以版式、字体、留白和注释提升竞赛气质。最适合本项目 |
| 2 | C 浅底拼贴信息风 | 05、06、07 | 多尺度叙事；城市—城区—场地与资源协同 | 主次图同时讲清场地问题和区域机会 | 易拥挤，限制主题，不依赖未授权高清影像，不把方案当现状。适合本项目 |
| 3 | B 深底高对比风 | 03、04 | 强焦点；交通骨架与局部联系 | 远观识别强，适合主题插图 | 小字密线易糊，打印偏暗；避免发光、景深与伪精确三维。非首选 |

## 推荐组合

**A为主，借鉴07的多尺度版式与05的节点编号短注释。** 宏观图交代上海位置，片区主图表达真实道路、水绿及城市资源，局部图突出66.0948 ha真实边界。

设计红线继续朱红色及细白衬线；不加灰蒙版、不填充内部。图下说明组织为“场地问题—区域联系—改善方向”，区分观测、推断与建议。没有可靠交通模型时不画5/10分钟车行等时圈。

阶段2先出草案预览供审阅，修改后再导出A1、A3、PNG、PDF与可编辑源文件。本包不含最终区位图。
''')
def font(n):return ImageFont.truetype(F,n,index=2)
def txt(im,xy,s,n=25,w=900,color='#33414b'):
 d=ImageDraw.Draw(im);x,y=xy;f=font(n);line=''
 for ch in s:
  if d.textlength(line+ch,font=f)>w:
   d.text((x,y),line,font=f,fill=color);y+=int(n*1.5);line=ch
  else:line+=ch
 if line:d.text((x,y),line,font=f,fill=color);y+=int(n*1.5)
 return y
def pic(im,c,b):
 a=Image.open(ROOT/c['image']);a.thumbnail((b[2]-b[0],b[3]-b[1]));im.paste(a,(b[0]+(b[2]-b[0]-a.width)//2,b[1]+(b[3]-b[1]-a.height)//2))
board=Image.new('RGB',(3600,3000),'#f5f3ee');d=ImageDraw.Draw(board)
txt(board,(90,55),'区位分析｜7个真实案例 · 3组风格候选',58,3300)
txt(board,(92,150),'阶段1：仅供风格挑选 / NOT THE SHANGHAI FINAL DIAGRAM',28,3300)
labels={'A':'A｜浅底理性结构风  推荐1','B':'B｜深底高对比风  推荐3','C':'C｜浅底拼贴信息风  推荐2'}
for col,g in enumerate('ABC'):
 x=75+col*1180;txt(board,(x,240),labels[g],35,1120)
 for j,c in enumerate([c for c in cases if c['group']==g]):
  y=335+j*820;d.rounded_rectangle((x,y,x+1120,y+785),radius=15,fill='white');txt(board,(x+25,y+15),c['id']+'  '+c['name'],30,1070)
  pic(board,c,(x+25,y+85,x+1095,y+595));yy=txt(board,(x+25,y+605),c['review']['风格特点'],24,1070);txt(board,(x+25,yy+8),c['credit'],20,1070)
  txt(board,(x+25,y+738),'来源链接与完整评审见 LOCATION_CASE_REVIEW.md',18,1070)
txt(board,(90,2860),'建议：A为主 + 07多尺度版式 + 05节点注释。选择后再制作真实场地区位图。',30,3400)
board.save(ROOT/'location_case_contact_sheet.png');pages=[board]
for c in cases:
 im=Image.new('RGB',(2480,1754),'#f5f3ee');txt(im,(70,45),f"{c['id']} / {c['group']}  {c['name']}",46,2330);txt(im,(70,120),c['credit'],25,2330);pic(im,c,(65,205,1550,1440));y=210
 for k,v in c['review'].items():
  y=txt(im,(1610,y),k,25,790,color='#bd4937');y=txt(im,(1610,y+5),v,24,790)+20
 assert y<1460,(c['id'],y)
 y=txt(im,(70,1480),'发布页：'+c['source_url'],22,2330);txt(im,(70,y+10),'原图URL、SHA256及评审数据见 cases.json。原作者版权保留；仅供案例评论。',24,2330);pages.append(im)
pages[0].save(ROOT/'location_case_contact_sheet.pdf',save_all=True,append_images=pages[1:],resolution=150,quality=92)
import pymupdf as fitz
pdf=fitz.open(ROOT/'location_case_contact_sheet.pdf');assert len(pdf)==8
for i,c in enumerate(cases,1):
 page=pdf[i];page.insert_link({'kind':fitz.LINK_URI,'from':fitz.Rect(20,page.rect.height-100,page.rect.width-20,page.rect.height-10),'uri':c['source_url']})
pdf.saveIncr()
report={'phase':1,'cases':len(cases),'groups':{g:[c['id'] for c in cases if c['group']==g] for g in 'ABC'},'pdf_pages':len(pdf),'all_images_decode':True,'all_source_pages_cached':all(next((ROOT/'cache/pages').glob(r[2]+'*.json'),None) for r in rows),'pdf_source_links':sum(len(p.get_links()) for p in pdf),'phase2_not_started':True,'notes':'PDF为高质量图像排版；文字、来源与重建脚本另附。未修改GIS或模型。'}
(ROOT/'QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(ROOT/'README.md').write_text('# 第一阶段成果\n\n先看PNG总览或8页PDF，再读两份Markdown。cases.json保留来源、分析与缩略图校验；scripts/build_review.py可重新排版。依赖Pillow、requests、pymupdf与Noto CJK字体。cache不纳入交付。\n\n阶段2未开始，等待选择风格。\n')
with zipfile.ZipFile(ROOT/'location_case_study_review.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in ROOT.rglob('*'):
  if f.is_file() and 'cache' not in f.relative_to(ROOT).parts and f.suffix!='.zip':z.write(f,str(f.relative_to(ROOT)))
print(json.dumps(report,ensure_ascii=False))
