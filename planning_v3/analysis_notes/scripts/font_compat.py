"""Repair CFF data incorrectly embedded as PDF FontFile2 without moving graphics.

Convert cubic outlines to TrueType with <=0.5 font-unit error, preserving glyph
order, advances, Unicode mappings and vertical metrics. Existing CIDToGIDMap
then works with the actual TrueType font required by FontFile2.
"""
import io,re,hashlib,json
from pathlib import Path
import pymupdf as fitz
from fontTools.ttLib import TTFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
_cache={}
def true_type_bytes(font):
    if 'CFF ' not in font:
        out=io.BytesIO();font.save(out);return out.getvalue()
    order=font.getGlyphOrder();gs=font.getGlyphSet();glyphs={}
    for name in order:
        pen=TTGlyphPen(gs);gs[name].draw(Cu2QuPen(pen,max_err=.5,reverse_direction=True));glyphs[name]=pen.glyph()
    fb=FontBuilder(font['head'].unitsPerEm,isTTF=True)
    fb.setupGlyphOrder(order);fb.setupCharacterMap(font.getBestCmap() or {})
    fb.setupGlyf(glyphs);fb.setupHorizontalMetrics(font['hmtx'].metrics)
    fb.setupHorizontalHeader(ascent=font['hhea'].ascent,descent=font['hhea'].descent)
    family=font['name'].getDebugName(1) or 'NotoNotes';style=font['name'].getDebugName(2) or 'Regular'
    fb.setupNameTable({'familyName':family,'styleName':style,'uniqueFontIdentifier':family+style,
        'fullName':font['name'].getDebugName(4) or family,'psName':font['name'].getDebugName(6) or 'NotoNotes'})
    fb.setupOS2(sTypoAscender=font['OS/2'].sTypoAscender,sTypoDescender=font['OS/2'].sTypoDescender,
        usWinAscent=font['OS/2'].usWinAscent,usWinDescent=font['OS/2'].usWinDescent)
    fb.setupPost();out=io.BytesIO();fb.save(out);return out.getvalue()
def repair_source(source,target):
    stamp=target.with_suffix('.json');signature=hashlib.sha256(source.read_bytes()).hexdigest()
    if target.exists() and stamp.exists():
        j=json.loads(stamp.read_text())
        if j.get('source_sha256')==signature:return j
    doc=fitz.open(source);page=doc[0];contents=hashlib.sha256(page.read_contents()).hexdigest()
    images={x[0]:hashlib.sha256(doc.xref_stream(x[0])).hexdigest() for x in page.get_images()}
    fixed=[]
    for item in page.get_fonts():
        _,_,_,data=doc.extract_font(item[0])
        font=TTFont(io.BytesIO(data))
        if 'CFF ' not in font:continue
        child=int(re.search(r'(\d+) 0 R',doc.xref_get_key(item[0],'DescendantFonts')[1]).group(1))
        desc=int(doc.xref_get_key(child,'FontDescriptor')[1].split()[0])
        kind,value=doc.xref_get_key(desc,'FontFile2')
        if kind!='xref':continue
        stream=int(value.split()[0]);key=hashlib.sha256(data).hexdigest()
        if key not in _cache:_cache[key]=true_type_bytes(font)
        new=_cache[key];doc.update_stream(stream,new,compress=True);doc.xref_set_key(stream,'Length1',str(len(new)))
        fixed.append({'font':item[3],'glyphs':len(font.getGlyphOrder()),'glyph_order_and_advances_preserved':True})
    assert hashlib.sha256(page.read_contents()).hexdigest()==contents
    assert images=={x:hashlib.sha256(doc.xref_stream(x)).hexdigest() for x in images}
    target.parent.mkdir(parents=True,exist_ok=True);doc.save(target,garbage=4,deflate=True);doc.close()
    j={'source_sha256':signature,'fonts_repaired':fixed,'page_graphics_commands_unchanged':True,
        'embedded_image_streams_unchanged':True,'outline_max_conversion_error_font_units':.5}
    stamp.write_text(json.dumps(j,ensure_ascii=False,indent=2));return j
