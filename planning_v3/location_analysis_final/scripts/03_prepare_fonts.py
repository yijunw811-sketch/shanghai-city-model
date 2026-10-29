from pathlib import Path
import io,string
from fontTools.ttLib import TTCollection,TTFont
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
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

P=Path(__file__).resolve().parents[1]
chars=set(string.printable)
for p in list((P/'scripts').glob('*.py'))+list((P/'reports').glob('*.json')):
 chars.update(p.read_text())
for weight in ['Regular','Bold']:
 f=TTCollection('/usr/share/fonts/opentype/noto/NotoSansCJK-'+weight+'.ttc').fonts[2]
 sub=subset.Subsetter();sub.populate(text=''.join(chars));sub.subset(f)
 for nid,value in [(1,'Shanghai Location Sans'),(2,weight),(4,'Shanghai Location Sans '+weight),(6,'ShanghaiLocationSans-'+weight)]:
  f['name'].setName(value,nid,3,1,0x409)
 converted=TTFont(io.BytesIO(true_type_bytes(f)))
 converted['OS/2'].usWeightClass=700 if weight=='Bold' else 400
 converted['OS/2'].fsSelection=32 if weight=='Bold' else 64
 converted['head'].macStyle=1 if weight=='Bold' else 0
 converted.save(P/'fonts'/('ShanghaiLocationSans-'+weight+'.ttf'))
print('Prepared portable TrueType fonts')
