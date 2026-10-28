from common import *
from matplotlib.colors import to_rgb
palettes={
'density':['#B8D0D0','#8CB3B3','#609392','#397A7C','#24465B'],
'volume':['#B4CADB','#8FAAC5','#6784AA','#465E85','#293D63'],
'road':['#BCD3CB','#91B8AA','#65A08F','#3D8579','#255F61'],
'mix':['#C1D3AF','#99BE8C','#6BA77D','#3C8B72','#226859'],
'commercial':['#D8C58F','#C7A562','#AF8444','#8A622F','#644823'],
'opportunity':['#D2C39A','#A0B79B','#759D93','#4A7C82','#24465B'],
'population':['#BDD2D8','#92B3BE','#648F9F','#426D82','#24465B'],
'height':['#D4C89B','#B9B27F','#949B70','#6A805F','#445F52'],
'ndvi':['#C9B996','#A7BD83','#759A6A','#427659','#275147'],
'temperature':['#D5C98F','#C8AD6C','#B68C55','#9F6850','#754738'],
'dsm':['#CFCCB5','#B6B199','#9A967F','#7A7F6A','#566452'],
'water':['#C0D0CF','#9ABCC1','#76A5B4','#4D8298','#2F5E7B'],
'ndwi':['#9E744F','#C7AD7D','#C5CCC1','#78A5AF','#335F77'],
'ndbi':['#305F69','#75A5A7','#C5C5AC','#BE9D6A','#89613F'],
'seasonal':['#8E7251','#BEAB78','#C0C9AF','#78A087','#356B5C']}
land={'residential':'#C3A876','public_service':'#A6819B','commercial':'#B97766','industrial':'#918AA8','transport':'#8C9B9E','green_open':'#7C9F78','water':'#6B9DAD','construction':'#C6B574','unknown':'#DCD9D0'}
metric={
'building_density':{'palette':'density','breaks':[0,.15,.3,.45,.6,1],'unit':'建筑占地并集 / 实际单元面积'},
'volume_proxy_m':{'palette':'volume','breaks':[0,3,6,12,24,max(48,float(read('grid_100m',D).volume_proxy_m.max()))],'unit':'m³/m²，估高体量代理，非容积率'},
'land_function_entropy':{'palette':'mix','breaks':[0,.2,.4,.6,.8,1],'unit':'H(已映射功能面积)/ln(8)；已知功能比例≥50%'},
'vehicle_density_km_km2':{'palette':'road','breaks':[0,5,10,20,35,max(60,float(read('grid_200m',D).vehicle_density_km_km2.max()))],'unit':'km / km²，双幅源道路分计'},
'commercial_density_km2':{'palette':'commercial','breaks':[0,10,25,50,100,max(250,float(read('grid_200m',D).commercial_density_km2.max()))],'unit':'已映射商业POI / km²；零值不表示无商业'},
'research_amenity_priority':{'palette':'opportunity','breaks':[0,.2,.4,.6,.8,1],'unit':'三项等权百分位均值，非法定更新风险'},
'commercial_kde_h200_km2':{'palette':'commercial','breaks':[0,5,10,25,50,max(100,float(read('grid_100m',D).commercial_kde_h200_km2.max()))],'unit':'核观测强度 / km²；h=200m，不是客流'},
'height_m':{'palette':'height','breaks':[0,12,24,54,100,max(150,float(read('buildings_enriched').height_m.max()))],'unit':'m，全部估计/层数推算'},
'population_density_km2':{'palette':'population','breaks':[0,10000,20000,40000,80000,max(160000,float(read('population_ghsl2020',A).population_density_km2.max()),float(read('population_worldpop2025',A).population_density_km2.max()))],'unit':'模型人 / km²；两年份产品不可直接作人口变化'}}
def lab(hex):
 rgb=np.array(to_rgb(hex));v=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
 xyz=np.array([[.4124564,.3575761,.1804375],[.2126729,.7151522,.0721750],[.0193339,.1191920,.9503041]])@v/np.array([.95047,1,1.08883]);f=np.where(xyz>(6/29)**3,np.cbrt(xyz),xyz/(3*(6/29)**2)+4/29)
 return np.array([116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])])
qa=[]
for name,colors in palettes.items():
 v=np.array([lab(c) for c in colors]);sequential=name not in ['ndwi','ndbi','seasonal'];d=np.linalg.norm(np.diff(v,axis=0),axis=1)
 qa.append({'palette':name,'type':'sequential' if sequential else 'diverging','lightness':v[:,0].tolist(),'adjacent_deltaE76':d.tolist(),'monotonic_L_if_sequential':bool(np.all(np.diff(v[:,0])<0)) if sequential else None,'min_deltaE76':float(d.min()),'lightest_is_not_white':max(v[:,0])<88})
 if sequential:assert np.all(np.diff(v[:,0])<0),name
 assert d.min()>7,name
 assert max(v[:,0])<88,name
style={'version':'V3 2026-10-28','palettes':palettes,'metric_styles':metric,'landuse':land,'design_boundary':{'color':'#CB493E','line_mm':1.2,'white_understroke_mm':1.65,'fill':'none','z_order':'top','outside_mask':False},'base':{'paper':'#F8F7F2','text':'#24465B','buildings':'#CED2CD','road':'#8E9899','water':'#6B9DAD','green':'#7C9F78'},'satellite':{'whole_image_overlay_mode_opacity':.72,'inside_outside_same':True,'natural_rgb_preserved':True},'classification':'Fixed metric boundaries shared across global/refined/scale comparisons; no quantile recalibration per sheet','missing':'Grey neutral; missing functional coverage remains missing, not zero','qgis_line_units':'mm; Matplotlib converts to points by72/25.4'}
dump(ROOT/'styles/COLOR_STYLE_SYSTEM.json',style);dump(ROOT/'reports/color_quality_checks.json',qa)
(ROOT/'styles/COLOR_STYLE_SYSTEM.md').write_text('# V3统一制图色彩\n\n专题颜色、固定分界、单位与边界线宽见同名JSON。顺序色带按CIELAB明度单调变暗，邻级ΔE76>7；发散色带分别用于有零基准的光谱指数。人口2020/2025使用同一分级，但不能由模型差异推出真实增长。全域与局部同一指标保持同一分界，不将未知值当零。\n\n设计线#CB493E，1.2mm，白色衬线1.65mm，不填充，无外围蒙版。卫星背景只作整张图统一权重处理，不改变设计内外差异。\n')
checkpoint('styles',palettes=len(palettes),checks_passed=True);print('STYLES',len(palettes),flush=True)
