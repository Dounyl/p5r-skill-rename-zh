import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tablelib import *
import hashlib

base = json.loads((ROOT/'temp/history/release-043/changes.json').read_text(encoding='utf-8'))
ss = segments((ROOT/'input/SC-NAME.TBL').read_bytes())
prior = {(c['section'], c['id']): c['new'] for c in base['changes']}
parts = [s[2] for s in ss]
changes = []
def encode(text):
    return b''.join(bytes([ord(c)]) if ord(c)<128 else enc[c] for c in text)
def pack(data):
    b = struct.pack('>I', len(data)) + data
    return b + b'\0' * (-len(b)%16)
for k in [1, 2, 14]:
    ptr, data = bytearray(ss[k*2][1]), bytearray(ss[k*2+1][1])
    for i, raw in enumerate(names(ss, k)):
        old = decode(raw)
        new = prior.get((k,i), old)
        if old == '救世主之愈':
            new = old
        new = new.replace('ＵＰ', '↑')
        if new == old:
            continue
        encoded = encode(new)
        assert len(data)+len(encoded)+1 < 65536
        struct.pack_into('>H', ptr, i*2, len(data))
        data.extend(encoded+b'\0')
        changes.append(dict(section=k,id=i,old=old,new=new))
    parts[k*2], parts[k*2+1] = pack(ptr), pack(data)
out = b''.join(parts)
after = segments(out)
expected = {(c['section'],c['id']):encode(c['new']) for c in changes}
actual = {}
for k in range(19):
    a,b = names(ss,k),names(after,k)
    assert len(a)==len(b)
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:
            actual[k,i]=y
        if k in [1,2,14]:
            assert 'ＵＰ' not in decode(y)
            if decode(x)=='救世主之愈':
                assert x==y
assert actual==expected
for k in range(38):
    if k not in [2,3,4,5,28,29]:
        assert ss[k][2]==after[k][2]
report = dict(version='0.4.4', policy='沿用0.4.3；救世主之愈恢复原名，所有技能及技能卡名称中的ＵＰ替换为↑。',
    changed_skill_ids=sum(c['section']==1 for c in changes),
    changed_skill_card_entries=sum(c['section']==14 for c in changes),
    changed_entries=len(changes), sha256=hashlib.sha256(out).hexdigest(), changes=changes)
folder = ROOT/'temp/history/release-044'
folder.mkdir(exist_ok=True)
(folder/'NAME.TBL').write_bytes(out)
(folder/'changes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['policy','changes']}))
print('PASS: full table comparison, Salvation restored, no fullwidth UP in skills/cards, unrelated sections unchanged')
