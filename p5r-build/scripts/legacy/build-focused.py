import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tablelib import *
import hashlib
source=(ROOT/'input/SC-NAME.TBL').read_bytes();ss=segments(source)
previous=json.loads((ROOT/'temp/history/release-032/changes.json').read_text(encoding='utf-8'))
# Explicit allowlist: transliterated spell names plus the agreed A/B cleansing family.
allow=set(range(10,79))|set(range(190,196))|{82,83,86,87,96,300,301,302,305,306,307,310,311,325,327,328,329,330,331,335,336,337,340,341,342,345,346,347,350,351,352,355,356,370,371,372,375,376,841,844,847,906,907}
changes=[c for c in previous['changes'] if c['id'] in allow]
def encode(text):return b''.join(bytes([ord(c)]) if ord(c)<128 else enc[c] for c in text)
def pack(data):
 b=struct.pack('>I',len(data))+data;return b+b'\0'*((-len(b))%16)
parts=[x[2] for x in ss]
for k in [1,2]:
 ptr=bytearray(ss[k*2][1]);data=bytearray(ss[k*2+1][1]);old=names(ss,k)
 for c in changes:
  if c['section']!=k:continue
  assert decode(old[c['id']])==c['old']
  z=encode(c['new']);assert len(data)+len(z)+1<65536
  struct.pack_into('>H',ptr,c['id']*2,len(data));data.extend(z+b'\0')
 parts[k*2]=pack(ptr);parts[k*2+1]=pack(data)
out=b''.join(parts);after=segments(out)
expected={(c['section'],c['id']):encode(c['new']) for c in changes};actual={}
for k in range(19):
 a,b=names(ss,k),names(after,k);assert len(a)==len(b)
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:actual[k,i]=y
assert actual==expected
for i in [716,383,820,821,708,161,171,360,361,338,348,200,225,315,316]:
 for k in [1,2]:assert names(ss,k)[i]==names(after,k)[i],i
for i,new in {325:'异常解除A',328:'异常解除B',330:'群体异常解除A',327:'群体异常解除B',370:'物理反射',371:'魔法反射',841:'自动群体攻击力↑'}.items():
 assert names(after,1)[i]==encode(new),i
folder=ROOT/'temp/history/release-040';folder.mkdir(exist_ok=True)
(folder/'NAME.TBL').write_bytes(out)
report={'version':'0.4.0','policy':'音译咒文名改写；异常解除A/B为整组例外；其他中文名恢复。','changed_skill_ids':len(set(c['id'] for c in changes)),'changed_entries':len(changes),'sha256':hashlib.sha256(out).hexdigest(),'changes':changes}
(folder/'changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 技能改名 0.4.0','','只改音译咒文名称及其衍生名称；异常解除 A/B 保留整组命名。','属性防御、增伤、专用技能及其他有中文含义的名称均恢复原版。','异常解除A：晕眩、遗忘、饥饿、睡眠；异常解除B：混乱、恐惧、狂怒、绝望、洗脑。','此范围不构成词源鉴定，不将所有音译名称认定为梵文。','',f"共 {report['changed_skill_ids']} 个技能 ID，{len(changes)} 条名称记录。",'', '| ID | 原名 | 新名 |','|---|---|---|']
lines += [f"| {c['id']} | {c['old']} | {c['new']} |" for c in changes if c['section']==1]
(folder/'改名对照.md').write_text('\n'.join(lines),encoding='utf-8')
print('PASS: allowlist, A/B, restores, all other entries unchanged. IDs=',report['changed_skill_ids'],'entries=',len(changes),'hash=',report['sha256'])
