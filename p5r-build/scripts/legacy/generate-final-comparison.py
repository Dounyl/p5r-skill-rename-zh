import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tablelib import *
import hashlib

mod = Path(r'C:\Users\dan\Desktop\Reloaded-II\Mods\p5rpc.skillrename')
report = json.loads((mod / 'changes.json').read_text(encoding='utf-8-sig'))
config = json.loads((mod / 'ModConfig.json').read_text(encoding='utf-8-sig'))
blob = (mod / 'Data/NAME.TBL').read_bytes()
assert hashlib.sha256(blob).hexdigest() == report['sha256']
assert config['ModVersion'] == report['version']
before = segments((ROOT / 'input/SC-NAME.TBL').read_bytes())
after = segments(blob)
def encode(text):
    return b''.join(bytes([ord(c)]) if ord(c) < 128 else enc[c] for c in text)
expected = {(c['section'], c['id']): c for c in report['changes']}
actual = set()
for k in range(19):
    a, b = names(before, k), names(after, k)
    assert len(a) == len(b)
    for i, (old, new) in enumerate(zip(a, b)):
        if old != new:
            actual.add((k, i))
            entry = expected[k, i]
            assert decode(old) == entry['old'] and new == encode(entry['new'])
assert actual == set(expected)
skills = [c for c in report['changes'] if c['section'] == 1]
cards = [c for c in report['changes'] if c['section'] == 14]
assert len(skills) == report['changed_skill_ids']
assert len(cards) == report['changed_skill_card_entries']
preserved = []
for i, raw in enumerate(names(before, 1)):
    old = decode(raw)
    if (old.endswith('之壁') or '概率ＵＰ' in old or old.startswith('消除')
            or '强化' in old or old in ['魔导才能', '救世主之愈']) and (1, i) not in actual:
        preserved.append((i, old))
lines = [f"# {config['ModName']}：最终名称对照表", '',
         f"对应版本：**{report['version']}**。本表按已安装的 `Data/NAME.TBL` 与原版简中名称表逐项核对生成。", '',
         f"共修改 **{len(skills)} 个技能 ID**、**{len(cards)} 条技能卡名称**；两组技能名称记录与技能卡合计 **{len(actual)} 条名称记录**。", '',
         '## 最终规则', '',
         '- 以下改名采用已确认的效果名称；技能卡与对应技能保持一致。',
         '- 防炎之壁等防御墙、疾风强化及高级强化等增伤被动保留原名。',
         '- 消除火焰防御等技能和救世主之愈保留原名；技能及技能卡名称中的「ＵＰ」统一替换为「↑」，例如「晕眩概率↑」。',
         '- 哈玛／姆多成功率ＵＰ仍按音译衍生技能改名，具体见表。',
         '- 反射名称为「物理反射／魔法反射」。',
         '- 不改对话，不改技能效果、数值或 ID；未列入改名表的名称保留原版。', '',
         '异常解除A：晕眩、遗忘、饥饿、睡眠；异常解除B：混乱、恐惧、狂怒、绝望、洗脑。元素异常解除：燃烧、冻结、触电。群体技能保留群体前缀。', '',
         '## 技能名称', '', '同名但 ID 不同的技能分别列出；游戏中的两组技能名称表在这里合并展示。', '',
         '| 技能 ID | 原版名称 | 最终名称 |', '|---|---|---|']
lines += [f"| {c['id']} | {c['old']} | {c['new']} |" for c in skills]
lines += ['', '## 技能卡名称', '', '卡片 ID 与技能 ID 属于不同列表，不可互换。', '',
          '| 卡片 ID | 原版名称 | 最终名称 |', '|---|---|---|']
lines += [f"| {c['id']} | {c['old']} | {c['new']} |" for c in cards]
lines += ['', '## 保留原名的相关类别', '', '以下列出本次讨论的防御墙、强化、消除防御及概率被动等类别中未改名的条目；不是全部未修改技能的清单。', '',
          '| 技能 ID | 保留名称 |', '|---|---|']
lines += [f'| {i} | {old} |' for i, old in preserved]
lines += ['', '## 文件核对信息', '', f"- ModId：`{config['ModId']}`", f"- NAME.TBL SHA-256：`{report['sha256']}`", '- 已核对全部名称记录及改名清单；此核对不代替游戏界面显示验证。', '']
target = ROOT / ('release-' + report['version'].replace('.', '') + '/最终名称对照表.md')
target.write_text('\n'.join(lines), encoding='utf-8')
print(f'PASS: {len(skills)} skills, {len(cards)} cards, {len(actual)} verified changes; {target.name}')
