"""Add editable vector captions outside existing map frames, preserving map graphics.
Exports existing36 topics; no new map, imagery, analysis geometry or recolouring.
"""
from pathlib import Path
import json,hashlib,re,os,unicodedata
os.environ.setdefault('OMP_NUM_THREADS','1')
import pymupdf as fitz
from fontTools.ttLib import TTCollection
from fontTools import subset
from font_compat import true_type_bytes,repair_source
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];V=P.parent
NOTES=json.loads((P/'reports/map_analysis_notes.json').read_text())
CACHE=Path('/workspace/.cache/fonts');CACHE.mkdir(parents=True,exist_ok=True)
all_text=json.dumps(NOTES,ensure_ascii=False)+'地块现状与问题区域协同关系改善方向周边研究区内米环带可达比例为步行路段长度非人口覆盖设计来源沿用原图说明区分现状证据与研究建议｜/©³²≥≤—–℃0123456789,.:;% OSM contributors Overture ESA Copernicus EC-JRC USGS WorldPop EPSG:32651 A1 A3'
font_key=hashlib.sha256(all_text.encode()).hexdigest()[:12]
FONT=CACHE/f'NotoSansCJKSC-notes-subset-{font_key}.ttf'
if not FONT.exists():
    collection=TTCollection('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    sub= subset.Subsetter();sub.populate(text=all_text);sub.subset(collection.fonts[2]);FONT.write_bytes(true_type_bytes(collection.fonts[2]))
font=fitz.Font(fontfile=str(FONT));MM=72/25.4
def rect(x,y,w,h):return fitz.Rect(x*MM,y*MM,(x+w)*MM,(y+h)*MM)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wrap(text,size,width):
    lines=[];line=''
    for char in text:
        if line and font.text_length(line+char,fontsize=size)>width:
            lines.append(line);line=char
        else:line+=char
    if line:lines.append(line)
    return '\n'.join(lines)
def normal(text):return re.sub(r'\s+','',unicodedata.normalize('NFKC',text))
def export(note,fmt):
    source=V/('outputs/maps/A1' if fmt=='A1' else 'outputs/maps/A3_review')/(note['stem']+'.pdf')
    out=P/f'outputs/{fmt}'/(note['stem']+'_分析说明.pdf');out.parent.mkdir(parents=True,exist_ok=True)
    signature=hashlib.sha256((sha(source)+json.dumps(note,ensure_ascii=False)+'caption-v2.1-ttf'+font_key).encode()).hexdigest()
    stamp=P/f'state/{note["id"]}_{fmt}.json';stamp.parent.mkdir(exist_ok=True)
    if stamp.exists() and json.loads(stamp.read_text()).get('signature')==signature and out.exists():
        print('CACHED',fmt,note['id'],flush=True);return json.loads(stamp.read_text())
    repaired=P/f'cache/font_repaired/{fmt}'/source.name
    font_repair=repair_source(source,repaired)
    src=fitz.open(repaired);old=src[0];doc=fitz.open();page=doc.new_page(width=old.rect.width,height=old.rect.height)
    page.show_pdf_page(page.rect,src,0)
    k=1 if fmt=='A1' else .5
    # Entire thematic map and scale bar lie above534mm in the original A1 layout.
    page.draw_rect(rect(0,534*k,841*k,60*k),fill=(248/255,247/255,242/255),color=None,overlay=True)
    page.draw_line(fitz.Point(30*k*MM,535*k*MM),fitz.Point(811*k*MM,535*k*MM),color=(.65,.71,.69),width=.6)
    size=11 if fmt=='A1' else 7.5;head=12 if fmt=='A1' else 9
    boxes=[]
    for i,(title,key) in enumerate([('地块现状与问题','site_problem'),('区域协同关系','regional_coordination'),('改善方向','improvement_direction')]):
        x=(30+264*i)*k;w=251*k
        head_spare=page.insert_textbox(rect(x,537*k,w,8 if fmt=='A1' else 7),title,fontsize=head,fontname='NotesCJK',fontfile=str(FONT),color=(.14,.27,.31))
        assert head_spare>=0,(note['id'],fmt,'heading',head_spare)
        box=rect(x,547*k,w,33*k);text=wrap(note[key],size,box.width-2)
        spare=page.insert_textbox(box,text,fontsize=size,fontname='NotesCJK',fontfile=str(FONT),lineheight=1.16,color=(.20,.28,.30))
        assert spare>=0,(note['id'],fmt,key,spare,len(note[key]))
        boxes.append({'section':key,'font_pt':size,'lines':len(text.splitlines()),'spare_pt':spare,'rect_pt':list(box)})
    scale=note['A1_scale'] if fmt=='A1' else note['A3_scale']
    foot=f'{fmt}｜1:{scale:,.2f}｜EPSG:32651｜设计66.0948ha｜周边=研究区内500米环带；可达比例为步行路段长度，非人口覆盖。'
    credits='来源沿用原图：© OpenStreetMap contributors / Overture；ESA、Copernicus、EC-JRC、USGS、WorldPop。三段说明区分现状证据与研究建议。'
    if fmt=='A1':
        for y,text in [(582,foot),(588,credits)]:
            spare=page.insert_textbox(rect(30,y,781,6),text,fontsize=8,fontname='NotesCJK',fontfile=str(FONT),color=(.34,.43,.44));assert spare>=0
    else:
        text=foot+'\n'+credits
        spare=page.insert_textbox(rect(15,290.4,390.5,6.5),text,fontsize=7,fontname='NotesCJK',fontfile=str(FONT),lineheight=1,color=(.34,.43,.44));assert spare>=0,(fmt,note['id'],'footer',spare)
    # Fonts are already subsetted and genuinely TrueType; do not re-subset CID fonts.
    doc.save(out,garbage=4,deflate=True);doc.close()
    # Verify legible/selectable Chinese and unchanged original map region.
    doc=fitz.open(out);txt=normal(doc[0].get_text())
    for key in ['site_problem','regional_coordination','improvement_direction']:
        assert normal(note[key]) in txt,(note['id'],fmt,'missing caption',key)
    for title in ['地块现状与问题','区域协同关系','改善方向']:assert title in txt,(note['id'],fmt,'missing heading')
    crop=rect(29.5*k,71.5*k,613*k,439*k)
    before=old.get_pixmap(matrix=fitz.Matrix(1,1),clip=crop,alpha=False).samples
    after=doc[0].get_pixmap(matrix=fitz.Matrix(1,1),clip=crop,alpha=False).samples
    assert before==after,(note['id'],fmt,'map graphics changed')
    exports={'pdf':str(out.relative_to(P))}
    if fmt=='A1':
        png=P/'outputs/PNG300'/(note['stem']+'_分析说明.png');png.parent.mkdir(parents=True,exist_ok=True)
        doc[0].get_pixmap(dpi=300,alpha=False).save(png);exports['png300']=str(png.relative_to(P))
        svg=P/'outputs/SVG'/(note['stem']+'_分析说明.svg');svg.parent.mkdir(exist_ok=True)
        svg.write_text(doc[0].get_svg_image(text_as_path=True));exports['svg']=str(svg.relative_to(P))
    rec={'id':note['id'],'format':fmt,'signature':signature,'files':exports,'captions':boxes,
        'page_mm':[doc[0].rect.width/MM,doc[0].rect.height/MM],'text_selectable_verified':True,
        'font_repaired_base_map_crop_pixels_identical':True,'font_repair':font_repair,
        'source_pdf_sha256':sha(source),'no_new_imagery':True}
    stamp.write_text(json.dumps(rec,ensure_ascii=False,indent=2));doc.close();src.close();print('EXPORTED',fmt,note['id'],flush=True)
    return rec
def main():
    records=[]
    for n in NOTES:
        for fmt in ['A1','A3']:records.append(export(n,fmt))
    (P/'reports/export_validation.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    tiles=[]
    for n in NOTES:
        im=Image.open(P/'outputs/PNG300'/(n['stem']+'_分析说明.png'));im.thumbnail((650,460))
        tile=Image.new('RGB',(670,485),'white');tile.paste(im,((670-im.width)//2,0));ImageDraw.Draw(tile).text((12,465),n['id'],fill='#24465b');tiles.append(tile)
    sheet=Image.new('RGB',(670*4,485*9),'white')
    for i,t in enumerate(tiles):sheet.paste(t,((i%4)*670,(i//4)*485))
    (P/'outputs/previews').mkdir(exist_ok=True);sheet.save(P/'outputs/previews/INDEX_36_ANALYSIS_NOTES.png')
    print('36 existing maps annotated;72 PDFs,36 PNG300,36SVG; unchanged map crops verified.')
if __name__=='__main__':main()
