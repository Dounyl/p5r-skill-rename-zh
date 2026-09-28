import struct,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=Path(r'C:\XboxGames\Persona 5 Royal\Content\CPK')
def utf(b):
 if b[:4]!=b'@UTF':
  x=0x655f; z=bytearray(b)
  for i in range(len(z)): z[i]^=x&255; x=x*0x4115&0xffffffff
  b=bytes(z)
 assert b[:4]==b'@UTF',b[:16]
 rows,strings,data= [struct.unpack_from('>I',b,p)[0]+8 for p in (8,12,16)]
 nc,rs,nr=struct.unpack_from('>HHI',b,24)
 def s(o): return b[strings+o:b.index(0,strings+o)].decode('utf-8')
 def val(p,t):
  fmt={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'Q',7:'q',8:'f',10:'I',11:'II'}[t]
  v=struct.unpack_from('>'+fmt,b,p); v=v[0] if len(v)==1 else v
  return (s(v) if t==10 else v),p+struct.calcsize('>'+fmt)
 cols=[];p=32
 for _ in range(nc):
  f=b[p];name=s(struct.unpack_from('>I',b,p+1)[0]);p+=5;c=None
  if f&0xf0==0x30:c,p=val(p,f&15)
  cols.append((name,f,c))
 result=[]
 for r in range(nr):
  p=rows+r*rs;row={}
  for name,f,c in cols:
   if f&0xf0==0x50:c,p=val(p,f&15)
   row[name]=c
  result.append(row)
 return result
def packet(f,off):
 f.seek(off);h=f.read(16);size=struct.unpack_from('<Q',h,8)[0];return utf(f.read(size))
def extract(lang):
 with (GAME/(lang+'.CPK')).open('rb') as f:
  h=packet(f,0)[0];toc=packet(f,h['TocOffset']);matches=[r for r in toc if r.get('FileName','').upper()=='NAME.TBL']
  print(lang,'matches',matches)
  assert len(matches)==1
  r=matches[0];f.seek(min(h['TocOffset'],h['ContentOffset'])+r['FileOffset']);b=f.read(r['FileSize'])
  assert r['FileSize']==r['ExtractSize'],'compressed file needs decompression'
  (ROOT/'input'/(lang+'-NAME.TBL')).write_bytes(b)

chars=(ROOT/'vendor/source/P5NameTBLEditor-main/P5NameTBLEditor/Charsets/P5R_CHS.tsv').read_text(encoding='utf-8-sig').splitlines()
chars=[c for line in chars for c in line.split('\t')]
enc={};dec={}
for i,c in enumerate(chars):
 if i<128:code=bytes([i])
 else:
  g=i+0x60;t=g//128-1;code=bytes([0x80|t,g-t*128])
 enc.setdefault(c,code);dec[code]=c
for i in range(32,len(chars)):
 g=i+0x60;t=g//128-1;dec[bytes([0x80|t,g-t*128])]=chars[i]
def decode(b):
 out='';p=0
 while p<len(b):
  n=2 if b[p]&128 else 1;out+=dec.get(b[p:p+n],'<'+b[p:p+n].hex()+'>');p+=n
 return out
def segments(b):
 out=[];p=0
 while p<len(b):
  n=struct.unpack_from('>I',b,p)[0];assert p+4+n<=len(b)
  end=(p+4+n+15)//16*16;out.append((p,b[p+4:p+4+n],b[p:end]));p=end
 return out
def names(ss,k):
 ptr=ss[k*2][1];data=ss[k*2+1][1]
 return [data[o:data.index(0,o)] for (o,) in struct.iter_unpack('>H',ptr)]
