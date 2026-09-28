import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
"""Build 0.4.3 from original names and the explicitly approved audit groups."""
from tablelib import *
import hashlib
import re

audit = (ROOT / 'config/P5R-命名范围审查.md').read_text(encoding='utf-8')
rows = []
for title in ['## 严格只改音译时应恢复：', '## 建议恢复：已有中文含义的技能']:
    block = audit.split(title, 1)[1].split('\n## ', 1)[0]
    rows.extend((int(i), old, new) for i, old, new in
                re.findall(r'^\| (\d+) \| (.*?) \| (.*?) \|$', block, re.M))
assert len(rows) == 90
excluded = {i for i, old, new in rows if old.startswith('消除') or '概率' in old
            or old.endswith('之壁') or '增伤' in new}
assert len(excluded) == 44
base = json.loads((ROOT / 'temp/history/release-041/changes.json').read_text(encoding='utf-8'))
chosen = {c['id']: (c['old'], c['new']) for c in base['changes'] if c['section'] == 1}
for i, old, new in rows:
    if i not in excluded:
        chosen[i] = (old, new)
assert len(chosen) == 148
chosen[370] = ('提特拉康', '物理反射')
ss = segments((ROOT / 'input/SC-NAME.TBL').read_bytes())
parts = [s[2] for s in ss]
changes = []
mapping = {}
for old, new in chosen.values():
    assert old not in mapping or mapping[old] == new
    mapping[old] = new

def encode(text):
    return b''.join(bytes([ord(c)]) if ord(c) < 128 else enc[c] for c in text)

def pack(data):
    b = struct.pack('>I', len(data)) + data
    return b + b'\0' * (-len(b) % 16)

for k in [1, 2, 14]:
    ptr, data = bytearray(ss[k*2][1]), bytearray(ss[k*2+1][1])
    for i, raw in enumerate(names(ss, k)):
        old = decode(raw)
        if k == 14:
            new = mapping.get(old)
        else:
            pair = chosen.get(i)
            new = pair[1] if pair and pair[0] == old else None
        if new is None or new == old:
            continue
        encoded = encode(new)
        assert len(data) + len(encoded) + 1 < 65536
        struct.pack_into('>H', ptr, i*2, len(data))
        data.extend(encoded + b'\0')
        changes.append(dict(section=k, id=i, old=old, new=new))
    parts[k*2], parts[k*2+1] = pack(ptr), pack(data)
out = b''.join(parts)
after = segments(out)
expected = {(c['section'], c['id']): encode(c['new']) for c in changes}
actual = {}
for k in range(19):
    a, b = names(ss, k), names(after, k)
    assert len(a) == len(b)
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            actual[k, i] = y
assert actual == expected
for i, (old, new) in chosen.items():
    assert names(after, 1)[i] == encode(new), (i, old, new)
for i in excluded:
    for k in [1, 2]:
        assert names(after, k)[i] == names(ss, k)[i]
excluded_names = {old for i, old, new in rows if i in excluded}
for i, raw in enumerate(names(ss, 14)):
    if decode(raw) in excluded_names:
        assert names(after, 14)[i] == raw
for k in range(38):
    if k not in [2, 3, 4, 5, 28, 29]:
        assert ss[k][2] == after[k][2]
for i in [161, 171, 708, 713]:
    for k in [1, 2]:
        assert names(after, k)[i] == names(ss, k)[i]
assert encode('物理枪击反射') not in out
folder = ROOT / 'temp/history/release-043'
folder.mkdir(exist_ok=True)
report = dict(version='0.4.3', policy='沿用效果命名；消除属性防御、概率UP、防炎之壁等防御墙、强化及增伤被动保留原名；提特拉康统一为物理反射；不添加额外专用技能标签，不改对话。',
              changed_skill_ids=len(chosen), changed_skill_card_entries=sum(c['section']==14 for c in changes),
              changed_entries=len(changes), sha256=hashlib.sha256(out).hexdigest(), changes=changes)
(folder/'NAME.TBL').write_bytes(out)
(folder/'changes.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# 技能去异味 0.4.3 改名对照', '', report['policy'], '',
         f"共 {len(chosen)} 个技能 ID；{report['changed_skill_card_entries']} 条技能卡名称；合计 {len(changes)} 条名称记录。", '']
for k, title in [(1, '技能'), (14, '技能卡')]:
    lines += ['## '+title, '', '| ID | 原名 | 新名 |', '|---|---|---|']
    lines += [f"| {c['id']} | {c['old']} | {c['new']} |" for c in changes if c['section']==k]
    lines += ['']
lines += ['## 本次保留原名的项目', '', '| ID | 原名 |', '|---|---|']
lines += [f'| {i} | {old} |' for i, old, new in rows if i in excluded]
(folder/'改名对照.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['changes', 'policy']}))
print('PASS: all chosen names, 44 exceptions including cards, physical reflection, font encoding, full table diff and unchanged sections')
