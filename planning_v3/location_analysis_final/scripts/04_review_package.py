from pathlib import Path
import json,hashlib,zipfile,unicodedata,io
import pymupdf as fitz,geopandas as gpd,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];O=P/'outputs';meta=json.loads((P/'reports/layout_validation.json').read_text());site=gpd.read_file(P/'data/location_context.gpkg',layer='DESIGN_SITE').geometry.iloc[0];source=gpd.read_file(P.parent/'outputs/gis/refined_analysis_v3.gpkg',layer='DESIGN_SITE').geometry.iloc[0]
assert site.wkb==source.wkb;assert abs(site.area-660947.6494989631)<.01
b=gpd.read_file(P/'data/location_context.gpkg',layer='buildings_enriched').union_all();a=gpd.read_file(P/'data/location_context.gpkg',layer='study_area').union_all();density={'core_footprint_fraction':b.intersection(site).area/site.area,'study_footprint_fraction':b.intersection(a).area/a.area,'method':'union footprints, intersect exact polygons, divide by actual polygon areas; not floor area ratio'}
qa={'draft':True,'not_formal_final_delivery':True,'site_area_ha':site.area/1e4,'exact_site_wkb_matches_source':True,'same_three_extents':meta['same_extents_both_variants'],'building_coverage':density,'exports':[]}
for n in ['01','02']:
 d=fitz.open(O/f'location_{n}_draft_A1.pdf');assert len(d)==1;p=d[0];assert abs(p.rect.width*25.4/72-841)<.1;assert abs(p.rect.height*25.4/72-594)<.1
 text=unicodedata.normalize('NFKC',p.get_text()).replace(' ','').replace('\n','')
 for needle in ['66.0948','EPSG:32651','26.6%','22.6%','207m','356m','场地','区域','协同']:assert needle in text,(n,needle)
 fonts=p.get_fonts();assert len(fonts)==2
 for font in fonts:
  from fontTools.ttLib import TTFont
  tt=TTFont(io.BytesIO(d.extract_font(font[0])[3]));assert 'glyf' in tt and 'CFF ' not in tt
 dest=fitz.open();page=dest.new_page(width=420/25.4*72,height=297/25.4*72);page.show_pdf_page(page.rect,d,0);dest.save(O/f'location_{n}_draft_A3.pdf',garbage=4,deflate=True);dest.close()
 im=Image.open(O/f'location_{n}_draft_300dpi.png').convert('RGB');assert im.size==(9933,7015)
 arr=np.asarray(im);extent=meta['variants'][0]['map_extents']['region'];hits=[]
 for t in np.linspace(.005,.995,240):
  point=site.boundary.interpolate(float(t),normalized=True);x=(229+(point.x-extent[0])/(extent[2]-extent[0])*584)*300/25.4;y=(118+(extent[3]-point.y)/(extent[3]-extent[1])*328)*300/25.4
  tile=arr[max(0,int(y)-6):int(y)+7,max(0,int(x)-6):int(x)+7].astype(int);red=(tile[:,:,0]>150)&(tile[:,:,1]<140)&(tile[:,:,2]<120)&(tile[:,:,0]-tile[:,:,1]>45);hits.append(bool(red.any()))
 assert np.mean(hits)>.95,(n,np.mean(hits))
 preview=Image.open(O/f'previews/location_{n}_draft_preview.png').convert('RGB');preview.thumbnail((1800,1272));preview.save(O/f'previews/location_{n}_review.jpg',quality=94)
 qa['exports'].append({'variant':n,'A1_mm':[841,594],'A3_mm':[420,297],'png_px':list(im.size),'png_dpi':300,'pdf_true_type_fonts_embedded':len(fonts),'pdf_chinese_and_key_numeric_text_verified':True,'registered_redline_hit_fraction':float(np.mean(hits))})
board=Image.new('RGB',(3660,1430),'#f5f4ee');draw=ImageDraw.Draw(board);font=ImageFont.truetype(str(P/'fonts/ShanghaiLocationSans-Regular.ttf'),34)
draw.text((30,20),'01  水绿与城市肌理',font=font,fill='#637e71');draw.text((1860,20),'02  走廊与资源节点',font=font,fill='#a76d3b')
for i,n in enumerate(['01','02']):board.paste(Image.open(O/f'previews/location_{n}_review.jpg'),(30+i*1830,95))
board.save(O/'previews/location_two_variants_comparison.png')
(P/'reports/export_validation.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print(json.dumps(qa,ensure_ascii=False,indent=2))
