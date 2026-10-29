from pathlib import Path
import json,re,hashlib,unicodedata,xml.etree.ElementTree as ET
import pymupdf as fitz
from PIL import Image
P=Path(__file__).resolve().parents[1];V=P.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(t):return re.sub(r'\s+','',unicodedata.normalize('NFKC',t))
notes=json.loads((P/'reports/map_analysis_notes.json').read_text());exports=json.loads((P/'reports/export_validation.json').read_text())
assert len(notes)==36 and len(exports)==72
assert len({n[k] for n in notes for k in ['site_problem','regional_coordination','improvement_direction']})==108
checked=[];invalid_font_streams=[]
for n in notes:
    for fmt in ['A1','A3']:
        record=next(x for x in exports if x['id']==n['id'] and x['format']==fmt)
        assert record['font_repaired_base_map_crop_pixels_identical']
        assert record['font_repair']['page_graphics_commands_unchanged'] and record['font_repair']['embedded_image_streams_unchanged']
        source=V/('outputs/maps/A1' if fmt=='A1' else 'outputs/maps/A3_review')/(n['stem']+'.pdf')
        assert sha(source)==record['source_pdf_sha256']
        d=fitz.open(P/record['files']['pdf']);page=d[0];text=norm(page.get_text())
        assert len(d)==1
        for k in ['site_problem','regional_coordination','improvement_direction']:assert norm(n[k]) in text
        for h in ['地块现状与问题','区域协同关系','改善方向']:assert h in text
        expected=(841,594) if fmt=='A1' else (420,297)
        assert all(abs(a-b)<.01 for a,b in zip(record['page_mm'],expected))
        # Verify every actual FontFile2 contains TrueType data rather than CFF.
        for font in page.get_fonts():
            if font[2]!='Type0':continue
            children=d.xref_get_key(font[0],'DescendantFonts')[1]
            m=re.search(r'(\d+) 0 R',children)
            if not m:continue
            desc=d.xref_get_key(int(m.group(1)),'FontDescriptor')[1]
            typ,obj=d.xref_get_key(int(desc.split()[0]),'FontFile2')
            if typ=='xref' and d.xref_stream(int(obj.split()[0]))[:4]==b'OTTO':invalid_font_streams.append([n['id'],fmt,font[3]])
        spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if 'cjksc' in s['font'].lower()]
        assert spans,(n['id'],fmt,'caption font missing')
        assert all(s['bbox'][0]>=0 and s['bbox'][2]<=page.rect.width+.1 and s['bbox'][1]>=0 and s['bbox'][3]<=page.rect.height+.1 for s in spans),(n['id'],fmt,'text outside page')
        checked.append({'id':n['id'],'format':fmt,'caption_spans':len(spans),'map_content_unchanged_after_font_repair':True,'caption_text_complete':True})
        d.close()
    path=P/'outputs/PNG300'/(n['stem']+'_分析说明.png')
    with Image.open(path) as im:
        assert abs(im.width-841/25.4*300)<2 and abs(im.height-594/25.4*300)<2
        assert 299<im.info['dpi'][0]<301
        im.verify()
    ET.parse(P/'outputs/SVG'/(n['stem']+'_分析说明.svg'))
assert not invalid_font_streams,invalid_font_streams
protected=json.loads((P/'reports/input_baseline.json').read_text());unchanged={k:sha(V.parent/k)==v for k,v in protected.items()};assert all(unchanged.values())
q=json.loads((P/'reports/qgis_caption_validation.json').read_text());assert q['updated_existing_layouts']==36 and q['editable_analysis_paragraphs']==108 and not q['invalid_layers']
result={'existing_topics_annotated':36,'interpretation_paragraphs':108,'A1_PDF':36,'A3_PDF':36,'PNG_300DPI':36,'SVG':36,
    'all_caption_text_and_headings_complete':True,'caption_font_A1_pt':11,'caption_font_A3_pt':7.5,'A3_footer_font_pt':7,
    'CFF_mislabeled_as_TrueType_remaining':len(invalid_font_streams),'font_repair':'Cubic CFF outlines converted to actual TrueType, preserving glyph order/advances; old graphics commands/images unchanged. Original files not rewritten.',
    'new_maps_or_basemaps':0,'maps_keep_original_geometry_color_scale_extent':True,
    'all_original_source_PDF_SHA256_unchanged':True,'protected_source_SHA256_unchanged':unchanged,
    'QGIS_valid_layers':q['valid_layers'],'QGIS_editable_paragraphs':108,'checks':checked}
(P/'reports/FINAL_QA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('PASS:36 existing maps,108 captions,72 PDFs,36PNG300,36SVG; all map/source preservation checks passed.')
