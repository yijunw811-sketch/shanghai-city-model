"""Verified bounded seekable public HTTP reader, content-addressed byte cache."""
from common import *
import io
class PublicRange(io.RawIOBase):
 def __init__(self,url,size,budget=64*1024*1024):self.url=url;self.size=size;self.pos=0;self.total=0;self.budget=budget;self.name='public_range.tif';self.key=sha_text(url)
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.pos
 def seek(self,p,w=0):self.pos=p if w==0 else self.pos+p if w==1 else self.size+p;return self.pos
 def read(self,n=-1):
  n=min(n if n>=0 else self.size-self.pos,self.size-self.pos)
  if n<=0:return b''
  if n>8*1024*1024 or self.total+n>self.budget:raise RuntimeError('Bounded range budget exceeded')
  key=ROOT/f'cache/public_ranges/{self.key}_{self.pos}_{n}.bin';key.parent.mkdir(exist_ok=True)
  if key.exists():b=key.read_bytes()
  else:
   r=SESSION.get(self.url,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'},timeout=40,stream=True)
   if r.status_code!=206:r.close();raise RuntimeError('Exact HTTP206 required; no bulk fallback')
   b=r.raw.read(n+1);r.close()
   if len(b)!=n:raise RuntimeError('Range length mismatch')
   key.write_bytes(b)
  self.pos+=n;self.total+=n;return b
 def chunk_read(self,start,end):
  self.seek(start);chunks=[]
  while self.tell()<end:chunks.append(self.read(min(4*1024*1024,end-self.tell())))
  return b''.join(chunks)
def sha_text(t):return __import__('hashlib').sha256(t.encode()).hexdigest()[:16]
