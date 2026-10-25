"""Bounded range-based TIFF layout check and selected-tile decoding, no national raster download."""
from common import *
import io,tifffile,numpy as np,rasterio,runpy
from pyproj import CRS,Transformer
class BoundedRange(io.RawIOBase):
 def __init__(self,url,size):self.url=url;self.size=size;self.pos=0;self.total=0;self.name='remote_clcd.tif'
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.pos
 def seek(self,p,w=0):self.pos=p if w==0 else self.pos+p if w==1 else self.size+p;return self.pos
 def read(self,n=-1):
  n=min(n if n>=0 else self.size-self.pos,self.size-self.pos)
  if n<=0:return b''
  if n>8*1024*1024 or self.total+n>64*1024*1024:raise RuntimeError('64MiB total/8MiB request budget; national bulk read forbidden')
  start=self.pos;key=ROOT/f'cache/clcd_ranges/{start}_{n}.bin';key.parent.mkdir(exist_ok=True)
  if key.exists():b=key.read_bytes()
  else:
   r=SESSION.get(self.url,headers={'Range':f'bytes={start}-{start+n-1}'},timeout=40,stream=True)
   if r.status_code!=206:r.close();raise RuntimeError('Server did not honor range')
   b=r.raw.read(n+1);r.close()
   if len(b)!=n:raise RuntimeError('Incomplete/oversized range')
   key.write_bytes(b)
  self.total+=n;self.pos+=n;return b
j=json.loads((ROOT/'cache/source_discovery/clcd_zenodo.txt').read_text());entry=next(v for v in j['files'] if v['key']=='CLCD_v01_2019.tif');url=entry['links']['self'];stream=BoundedRange(url,entry['size'])
with tifffile.TiffFile(stream) as tif:
 p=tif.pages[0];tags={k:str(p.tags[k].value)[:2000] for k in ['ImageWidth','ImageLength','TileWidth','TileLength','RowsPerStrip','Compression','ModelPixelScaleTag','ModelTiepointTag','GeoKeyDirectoryTag'] if k in p.tags}
 dump(ROOT/'reports/clcd_tiff_layout.json',{'tags':tags,'geotiff_metadata':tif.geotiff_metadata,'tiled':p.is_tiled,'segments':len(p.dataoffsets),'bytes_metadata_read':stream.total})
 print(tags,flush=True)
 if not p.is_tiled:
  from rasterio.transform import from_origin
  from rasterio.windows import from_bounds
  scale=p.tags['ModelPixelScaleTag'].value;tie=p.tags['ModelTiepointTag'].value
  transform=from_origin(tie[3],tie[4],scale[0],scale[1]);bounds=gpd.GeoSeries([CONTEXT],crs=32651).to_crs(4326).total_bounds
  window=from_bounds(*bounds,transform=transform).round_offsets().round_lengths()
  x0,y0=int(window.col_off),int(window.row_off);x1=x0+int(window.width);y1=y0+int(window.height)
  rps=p.rowsperstrip;indices=list(range(y0//rps,(y1-1)//rps+1));bytecost=sum(p.databytecounts[i] for i in indices)
  dump(ROOT/'reports/clcd_strip_cost.json',{'selected_strips':len(indices),'compressed_bytes':bytecost,'row_width_pixels':p.imagewidth,'total_strips':len(p.dataoffsets)})
  if bytecost>48*1024*1024:raise RuntimeError('Selected strips exceed48MiB; refuse national bulk download')
  # Contiguous selected strips are fetched as one bounded compressed span; only AOI columns retained.
  begin=min(p.dataoffsets[i] for i in indices);end=max(p.dataoffsets[i]+p.databytecounts[i] for i in indices)
  if end-begin>48*1024*1024:raise RuntimeError('Selected strip byte span exceeds48MiB')
  stream.seek(begin);payload=b''.join(stream.read(min(4*1024*1024,end-stream.tell())) for _ in range((end-begin+4*1024*1024-1)//(4*1024*1024)))
  array=np.zeros((y1-y0,x1-x0),dtype=p.dtype)
  for i in indices:
   offset=p.dataoffsets[i]-begin;raw=payload[offset:offset+p.databytecounts[i]];tile,pos,shape=p.decode(raw,i);tile=np.squeeze(tile)
   if tile.ndim==1:tile=tile[None,:]
   row=i*rps;top=max(row,y0);bottom=min(row+tile.shape[0],y1)
   array[top-y0:bottom-y0,:]=tile[top-row:bottom-row,x0:x1]
  profile={'driver':'GTiff','width':array.shape[1],'height':array.shape[0],'count':1,'dtype':str(array.dtype),'crs':'EPSG:4326','transform':rasterio.windows.transform(window,transform),'nodata':0,'compress':'deflate'}
  out=RAW/'clcd/clcd2019_context_30m.tif';out.parent.mkdir(exist_ok=True)
  with rasterio.open(out,'w',**profile) as dst:dst.write(array,1)
  tools=runpy.run_path(str(ROOT/'scripts/04_rasters.py'),run_name='raster_tools');ref=tools['metric_reference'](profile,30);aligned=tools['align'](array,profile,ref)
  tools['save_product']('clcd2019_30m',aligned,ref,{'source_url':'https://zenodo.org/records/4417810','license':j['metadata'].get('license',{}).get('id'),'year':2019,'method':'Selected compressed native TIFF strips via bounded206 ranges; physical cover not functional land use'})
  dump(ROOT/'reports/clcd_window_download.json',{'selected_strips':len(indices),'selected_compressed_bytes':bytecost,'total_range_bytes':stream.total,'national_file_bytes':entry['size'],'native_crop_sha256':sha(out),'classes':np.unique(array).tolist()})
  register('clcd_china',access_status='verified_bounded_native_strips',local_path=str(out.relative_to(ROOT)),checksum=sha(out),valid_year=2019,notes='Historical physical land cover; selected compressed strips only; national file NOT downloaded',reason=None)
  export_registry();print('CLCD bounded strip crop complete',flush=True)
  raise SystemExit(0)
 # TIFF metadata projected/geographic source CRS is interpreted independently with GDAL header/range open.
 tools=runpy.run_path(str(ROOT/'scripts/04_rasters.py'),run_name='raster_tools')
 with rasterio.Env(**tools['ENV']):
  with rasterio.open(url) as ds:
   from rasterio.warp import transform_bounds
   from rasterio.windows import from_bounds
   bounds=transform_bounds(32651,ds.crs,*CONTEXT.bounds,densify_pts=21);window=from_bounds(*bounds,ds.transform).round_offsets().round_lengths();profile=ds.profile.copy();sourcecrs=ds.crs;transform=ds.window_transform(window)
 tw=p.tilewidth;th=p.tilelength;tilesx=(p.imagewidth+tw-1)//tw
 x0,y0=int(window.col_off),int(window.row_off);x1=x0+int(window.width);y1=y0+int(window.height);indices=[ty*tilesx+tx for ty in range(y0//th,(y1-1)//th+1) for tx in range(x0//tw,(x1-1)//tw+1)]
 size=sum(p.databytecounts[i] for i in indices)
 if size>48*1024*1024:raise RuntimeError('AOI tile byte cost exceeds48MiB; stop before data reads')
 array=np.zeros((y1-y0,x1-x0),dtype=p.dtype)
 for i in indices:
  stream.seek(p.dataoffsets[i]);raw=stream.read(p.databytecounts[i]);tile,pos,shape=p.decode(raw,i)
  tile=np.squeeze(tile);ty=i//tilesx*th;tx=i%tilesx*tw;left=max(tx,x0);right=min(tx+tw,x1);top=max(ty,y0);bottom=min(ty+th,y1)
  array[top-y0:bottom-y0,left-x0:right-x0]=tile[top-ty:bottom-ty,left-tx:right-tx]
 profile.update(width=array.shape[1],height=array.shape[0],transform=transform,driver='GTiff',count=1,compress='deflate',nodata=0)
 out=RAW/'clcd/clcd2019_context_30m.tif';out.parent.mkdir(exist_ok=True)
 with rasterio.open(out,'w',**profile) as ds:ds.write(array,1)
 ref=tools['metric_reference'](profile,30);aligned=tools['align'](array,profile,ref);tools['save_product']('clcd2019_30m',aligned,ref,{'source_url':'https://zenodo.org/records/4417810','license':j['metadata'].get('license',{}).get('id'),'year':2019,'method':'Selected native TIFF tiles via verified206 byte ranges; physical cover not statutory functions'})
 dump(ROOT/'reports/clcd_window_download.json',{'selected_tiles':len(indices),'selected_compressed_bytes':size,'total_range_bytes':stream.total,'national_file_bytes':entry['size'],'native_crop_sha256':sha(out),'classes':np.unique(array).tolist()})
 register('clcd_china',access_status='verified_bounded_native_tiles',local_path=str(out.relative_to(ROOT)),checksum=sha(out),valid_year=2019,notes='Physical historical land cover; native30m; national giant file NOT downloaded',reason=None)
 export_registry();print('CLCD bounded crop complete',flush=True)
