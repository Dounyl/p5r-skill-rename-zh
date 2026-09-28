import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tablelib import *
import hashlib

base = ROOT / 'temp/history/release-040'
report = json.loads((base / 'changes.json').read_text(encoding='utf-8'))
ss = segments((base / 'NAME.TBL').read_bytes())
mapping = {}
for c in report['changes']:
    if c['section'] == 1:
        assert c['old'] not in mapping or mapping[c['old']] == c['new']
        mapping[c['old']] = c['new']

def encode(text):
    return b''.join(bytes([ord(c)]) if ord(c) < 128 else enc[c] for c in text)

def pack(data):
    b = struct.pack('>I', len(data)) + data
    return b + b'\0' * (-len(b) % 16)

ptr, data = bytearray(ss[28][1]), bytearray(ss[29][1])
cards = []
for i, raw in enumerate(names(ss, 14)):
    old = decode(raw)
    if old not in mapping:
        continue
    new = mapping[old]
    encoded = encode(new)
    assert len(data) + len(encoded) + 1 < 65536
    struct.pack_into('>H', ptr, i * 2, len(data))
    data.extend(encoded + b'\0')
    cards.append({'section': 14, 'id': i, 'old': old, 'new': new})
parts = [s[2] for s in ss]
parts[28], parts[29] = pack(ptr), pack(data)
out = b''.join(parts)
after = segments(out)
expected = {c['id']: encode(c['new']) for c in cards}
actual = {}
for k in range(19):
    before_names, after_names = names(ss, k), names(after, k)
    assert len(before_names) == len(after_names)
    for i, (a, b) in enumerate(zip(before_names, after_names)):
        if a != b:
            assert k == 14
            actual[i] = b
assert actual == expected and len(cards) == 102
assert all(ss[k][2] == after[k][2] for k in range(38) if k not in (28, 29))
report.update(version='0.4.1', changed_skill_card_entries=len(cards),
              changed_entries=len(report['changes']) + len(cards),
              sha256=hashlib.sha256(out).hexdigest())
report['changes'].extend(cards)
folder = ROOT / 'temp/history/release-041'
folder.mkdir(exist_ok=True)
(folder / 'NAME.TBL').write_bytes(out)
(folder / 'changes.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
doc = (base / '改名对照.md').read_text(encoding='utf-8').replace('技能改名 0.4.0', '技能改名 0.4.1')
doc += '\n\n## 技能卡同步\n\n另同步 102 条技能卡名称，沿用同一改名规则；卡片 ID 与技能 ID 独立。\n\n| 卡片 ID | 原名 | 新名 |\n|---|---|---|\n'
doc += '\n'.join(f"| {c['id']} | {c['old']} | {c['new']} |" for c in cards)
(folder / '改名对照.md').write_text(doc + '\n', encoding='utf-8')
print('PASS: 102 card names; all other sections byte-identical to 0.4.0;', report['sha256'])
