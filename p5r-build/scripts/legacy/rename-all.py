import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tablelib import *
import hashlib,collections,sys
sys.stdout.reconfigure(encoding='utf-8')
p=ROOT/'vendor/fusion/megaten-fusion-tool-master/src/app/p5/data'
sk=json.loads((p/'skill-data.json').read_text());sk.update(json.loads((p/'roy-skill-data.json').read_text()))
original=(ROOT/'input/SC-NAME.TBL').read_bytes();ss=segments(original);ns=names(ss,1)
E={'fir':'火焰','ice':'冰冻','ele':'电击','win':'疾风','psy':'念动','nuk':'核热','ble':'祝福','cur':'诅咒','alm':'万能','phy':'物理','gun':'枪击'}
short={'fir':'火','ice':'冰','ele':'电','win':'风','psy':'念','nuk':'核','ble':'祝','cur':'咒','alm':'万能','phy':'物','gun':'枪','sup':'辅','rec':'疗'}
ail={'Burn':'燃烧','Freeze':'冻结','Shock':'触电','Dizzy':'晕眩','Forget':'遗忘','Hunger':'饥饿','Sleep':'睡眠','Confuse':'混乱','Fear':'恐惧','Rage':'狂怒','Despair':'绝望','Brainwash':'洗脑'}
roman={0:'微',1:'Ⅰ',2:'Ⅱ',3:'Ⅲ',4:'Ⅳ',5:'Ⅴ'}
M={};category={}
def put(i,new,cat):
 assert i<len(ns);M[i]=new;category[i]=cat
# Physical damage tiers represent per-hit description, not fusion inheritance rank.
phys_tiers={200:1,201:3,202:4,203:5,205:0,206:2,207:1,208:1,210:1,211:2,212:5,213:5,217:4,220:2,221:3,222:4,224:2,225:1,226:4,227:4,228:1,230:2,231:4,235:2,236:3,237:5,241:1,242:0,243:2,244:2,250:1,251:2,253:0,254:2,260:2,261:2,262:1,263:2,264:3,265:1,266:2,267:3,268:2,270:2,271:2,272:3,273:1,275:2,276:2,277:2,278:3}
for key,s in sk.items():
 i=int(key)
 if i>=len(ns):continue
 en,elem,target=s['a'];b=s['b'];c=s['c'];old=decode(ns[i]);group='群体' if target.startswith('All') else ''
 if i==716:put(i,'群体睡眠Ⅲ','异常');continue
 if b[0]==99 and elem in short:
  put(i,old+'('+short[elem]+')','专用');continue
 if elem in E and b[2]>0 and elem not in ['phy','gun']:
  if i in [70,71,72]:tier={70:2,71:3,72:4}[i]
  elif i>=120 and i not in range(190,196):tier=4
  else:tier=(b[0]+1)//2
  put(i,group+E[elem]+roman[tier],'伤害')
 elif i in phys_tiers:
  new=group+E[elem]+roman[phys_tiers[i]]
  tags=[]
  if b[4]>1:tags.append((str(b[3]) if b[3]==b[4] else str(b[3])+'-'+str(b[4]))+'连')
  if c[0] in ail:tags.append(ail[c[0]])
  if b[6]>=40:tags.append('高暴击')
  if 'Baton Pass' in c[0]:tags.append('换手强化')
  if i==220:tags.append('被包围强化')
  if tags:new+='・'+'・'.join(tags)
  put(i,new,'伤害')
 elif elem in ['ble','cur'] and c[0]=='instakill':put(i,group+E[elem]+'即死'+('Ⅰ' if b[7]<=30 else 'Ⅱ'),'即死')
 elif elem=='ail' and c[0] in ail:put(i,group+ail[c[0]]+('Ⅰ' if b[7]<=30 else 'Ⅱ' if b[7]<=60 else 'Ⅲ'),'异常')
# Explicit support and cure mappings; never use a generic all-ailment label for partial cures.
explicit={
300:'治疗Ⅰ',301:'治疗Ⅱ',302:'完全治疗',305:'群体治疗Ⅰ',306:'群体治疗Ⅱ',307:'群体完全治疗',310:'复活',311:'完全复活',315:'全异常解除',316:'群体全异常解除',318:'群体完全治疗・全异常解除',
325:'晕眩遗忘饥饿睡眠解除',330:'群体晕眩遗忘饥饿睡眠解除',328:'混乱恐惧狂怒绝望洗脑解除',327:'群体混乱恐惧狂怒绝望洗脑解除',329:'燃烧冻结触电解除',331:'群体燃烧冻结触电解除',
335:'攻击力up',336:'防御力up',337:'命中回避up',338:'三项up',340:'群体攻击力up',341:'群体防御力up',342:'群体命中回避up',343:'群体三项up・被包围',345:'攻击力down',346:'防御力down',347:'命中回避down',348:'三项down',350:'群体攻击力down',351:'群体防御力down',352:'群体命中回避down',355:'群体友军弱化解除',356:'群体敌人强化消除',360:'物理蓄力',361:'魔法蓄力',365:'暴击率up',366:'敌我群体暴击率up',370:'物理反射',371:'魔法反射',372:'群体即死防护',375:'群体敌人物理反射消除',376:'群体敌人魔法反射消除',
110:'敌人异常易感up',111:'敌我群体异常易感up',113:'群体恐惧即死',160:'生命减半(祝)',170:'生命减半(咒)',
840:'自动攻击力up',841:'自动群体攻击力up',843:'自动防御力up',844:'自动群体防御力up',846:'自动命中回避up',847:'自动群体命中回避up',949:'自动命中回避up・换手',
906:'祝福即死成功率up',907:'诅咒即死成功率up'}
for i,new in explicit.items():put(i,new,'自动' if new.startswith('自动') else '治疗' if 300<=i<=331 else '辅助')
boostnames={'Fire':'火焰','Ice':'冰冻','Wind':'疾风','Elec':'电击','Nuke':'核热','Psy':'念动','Bless':'祝福','Curse':'诅咒','Gun':'枪击','Almighty':'万能','magic':'魔法'}
for key,s in sk.items():
 i=int(key)
 if i>=len(ns):continue
 c=s['c'];b=s['b']
 if c[1]=='FMTElemBoost' and c[0] in boostnames:
  put(i,boostnames[c[0]]+'增伤'+('Ⅱ' if b[7]==1150 else 'Ⅰ'),'增伤')
 if c[1]=='FMTAilmentBoost' and c[0] in ail:put(i,ail[c[0]]+'成功率up','异常被动')
 if c[1]=='FMTElemBreak' and c[0] in boostnames:put(i,'群体'+boostnames[c[0]]+'耐性消除','辅助')
# Keep physically distinct skills distinguishable when the effect summaries collide.
groups=collections.defaultdict(list)
for i,new in M.items():
 if category[i]=='伤害' and sk[str(i)]['a'][1] in ['phy','gun']:groups[new].append(i)
for new,ids in groups.items():
 if len(ids)>1:
  for i in ids:M[i]=new+'('+decode(ns[i])+')'
# Duplicate internal slots: only mirror if the original name is unambiguous.
byold=collections.defaultdict(set)
for i,new in M.items():byold[decode(ns[i])].add(new)
for i,n in enumerate(ns):
 old=decode(n)
 if i in [16,17] and i not in M and old in byold and len(byold[old])==1:
  put(i,next(iter(byold[old])),'同名内部记录')
# Approved 0.3.2 naming changes.
for i,new in {325:'异常解除A',330:'群体异常解除A',328:'异常解除B',327:'群体异常解除B',329:'元素异常解除',331:'群体元素异常解除'}.items():put(i,new,'治疗')
for key,spec in sk.items():
 i=int(key)
 if i>=len(ns):continue
 if spec['c'][1]=='FMTElemWall' and spec['c'][0] in boostnames:
  put(i,('群体' if spec['a'][2].startswith('All') else '')+boostnames[spec['c'][0]]+'防御up','属性Buff')
 if spec['a'][1] in ['phy','gun']:
  M.pop(i,None);category.pop(i,None)
for i,new in list(M.items()):M[i]=new.replace('down','↓').replace('up','↑')

# Encode strictly: missing glyphs fail the build rather than silently falling back.
def encode(text):
 out=b''
 for ch in text:
  if ord(ch)<128:out+=bytes([ord(ch)])
  else:
   if ch not in enc:raise ValueError('Missing glyph U+%04X in %s' % (ord(ch),ascii(text)))
   out+=enc[ch]
 return out
# ASCII decoding follows glyph charset in original encoder; verify non-ASCII output and raw re-encoding.
def pack(data):
 raw=struct.pack('>I',len(data))+data;return raw+b'\0'*((-len(raw))%16)
parts=[s[2] for s in ss];changes=[]
for k in [1,2]:
 old=names(ss,k);ptr=bytearray(ss[2*k][1]);data=bytearray(ss[2*k+1][1])
 for i,new in sorted(M.items()):
  if i>=len(old) or old[i]!=ns[i]:continue
  z=encode(new)
  if z==old[i]:continue
  offset=len(data);assert offset+len(z)+1<65536
  data.extend(z+b'\0');struct.pack_into('>H',ptr,i*2,offset)
  changes.append({'section':k,'id':i,'old':decode(old[i]),'new':new,'category':category[i]})
 parts[2*k]=pack(ptr);parts[2*k+1]=pack(data)
out=b''.join(parts);check=segments(out)
expected={(c['section'],c['id']):encode(c['new']) for c in changes};actual={}
for k in range(19):
 old,new=names(ss,k),names(check,k);assert len(old)==len(new)
 for i,(a,b) in enumerate(zip(old,new)):
  if a!=b:actual[k,i]=b
assert actual==expected
for key,spec in sk.items():
 i=int(key)
 if spec['a'][1] in ['phy','gun']:
  for k in [1,2]:
   old=names(ss,k);new=names(check,k)
   if i<len(old):assert old[i]==new[i], ('physical altered',k,i)
for i,new in {325:'异常解除A',330:'群体异常解除A',328:'异常解除B',327:'群体异常解除B',383:'疾风防御↑',345:'攻击力↓'}.items():assert M[i]==new
assert not any('up' in n or 'down' in n for n in M.values())
assert M[716]=='群体睡眠Ⅲ' and M[841]=='自动群体攻击力↑' and M[708]=='辉箭(祝)'
output=ROOT/'temp/history/release-032';output.mkdir(exist_ok=True)
(output/'NAME.TBL').write_bytes(out)
report={'version':'0.3.2','changed_skill_ids':len({c['id'] for c in changes}),'changed_entries':len(changes),'sha256':hashlib.sha256(out).hexdigest(),'unchanged_other_sections':True,'source':'https://github.com/aqiu384/megaten-fusion-tool/tree/master/src/app/p5/data','changes':changes}
(output/'changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 技能改名 0.3.2','',f"共修改 {report['changed_skill_ids']} 个技能 ID；两组名称表合计 {len(changes)} 条。",'', '伤害等级：微量=微，小=Ⅰ，中=Ⅱ，大=Ⅲ，特大=Ⅳ，超特大=Ⅴ。物理及枪击主动技能恢复原名。','异常成功率：基础概率≤30%=Ⅰ，31–60%=Ⅱ，>60%=Ⅲ；同级不代表概率完全相同。','增伤：25%=Ⅰ，50%=Ⅱ；可以叠加的不同被动仍是独立技能。','未改技能数值、说明、技能卡名称。特殊辅助/恢复技能保留原名加(辅)/(疗)。','异常解除A：晕眩、遗忘、饥饿、睡眠。异常解除B：混乱、恐惧、狂怒、绝望、洗脑。元素异常解除：燃烧、冻结、触电。群体加前缀。属性防御Buff与其他up/down均使用↑/↓。','', '| ID | 原名 | 新名 |','|---|---|---|']
for c in changes:
 if c['section']==1:lines.append(f"| {c['id']} | {c['old']} | {c['new']} |")
(output/'改名对照.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='changes'},ensure_ascii=False))
print('Longest:',sorted(set(M.values()),key=len)[-5:])
