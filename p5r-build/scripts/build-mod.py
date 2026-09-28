"""Build the current name table directly from config/changes.json."""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT.parent / 'p5rpc.skillrename'


def build():
    from tablelib import segments, names, decode, enc

    rule_bytes = (ROOT / 'config/changes.json').read_bytes()
    rules = json.loads(rule_bytes.decode('utf-8-sig'))['changes']
    config = json.loads((MOD / 'ModConfig.json').read_text(encoding='utf-8-sig'))
    original = (ROOT / 'input/SC-NAME.TBL').read_bytes()
    source = segments(original)
    if len(source) != 38:
        raise ValueError('Expected 38 table segments.')
    changes = {}
    for rule in rules:
        key = (rule['section'], rule['id'])
        if key in changes or key[0] not in (1, 2, 14) or not isinstance(key[1], int) or key[1] < 0:
            raise ValueError(f'Duplicate or invalid rule: {key}')
        entries = names(source, key[0])
        if key[1] >= len(entries) or decode(entries[key[1]]) != rule['old']:
            raise ValueError(f'Original name mismatch: {key}')
        if not isinstance(rule['new'], str) or not rule['new'] or '\0' in rule['new']:
            raise ValueError(f'Invalid name: {key}')
        if rule['new'] == rule['old']:
            raise ValueError(f'Unchanged rule: {key}; remove it to restore the original name.')
        changes[key] = rule
    parts = [part[2] for part in source]
    expected = {}
    ordered = []
    for section in (1, 2, 14):
        ptr, data = bytearray(source[section * 2][1]), bytearray(source[section * 2 + 1][1])
        for index in range(len(names(source, section))):
            rule = changes.get((section, index))
            if rule is None:
                continue
            encoded = b''.join(bytes([ord(c)]) if ord(c) < 128 else enc[c] for c in rule['new'])
            if len(data) + len(encoded) + 1 >= 65536:
                raise ValueError(f'Name table offset overflow: {section}/{index}')
            struct.pack_into('>H', ptr, index * 2, len(data))
            data.extend(encoded + b'\0')
            expected[section, index] = encoded
            ordered.append(rule)
        for offset, content in ((0, ptr), (1, data)):
            packed = struct.pack('>I', len(content)) + content
            parts[section * 2 + offset] = packed + b'\0' * (-len(packed) % 16)
    blob = b''.join(parts)
    after = segments(blob)
    actual = {}
    for section in range(19):
        before_names, after_names = names(source, section), names(after, section)
        if len(before_names) != len(after_names):
            raise ValueError('Entry count changed.')
        for index, (before, current) in enumerate(zip(before_names, after_names)):
            if before != current:
                actual[section, index] = current
    if actual != expected:
        raise ValueError('Output differs from configured changes.')
    for index in range(38):
        if index not in (2, 3, 4, 5, 28, 29) and source[index][2] != after[index][2]:
            raise ValueError('Unrelated section changed.')
    report = dict(version=config['ModVersion'], sha256=hashlib.sha256(blob).hexdigest(),
                  config_sha256=hashlib.sha256(rule_bytes).hexdigest(),
                  changed_skill_ids=sum(r['section'] == 1 for r in ordered),
                  changed_skill_card_entries=sum(r['section'] == 14 for r in ordered),
                  changed_entries=len(ordered), changes=ordered)
    guide = (ROOT / 'config/naming-guide.md').read_text(encoding='utf-8')
    guide = guide.replace('{{version}}', config['ModVersion'])
    output = ROOT / 'temp/current'
    output.mkdir(parents=True, exist_ok=True)
    (MOD / 'Data').mkdir(exist_ok=True)
    (output / 'NAME.TBL').write_bytes(blob)
    (output / 'changes.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (MOD / 'Data/NAME.TBL').write_bytes(blob)
    (MOD / '技能名称对照表.md').write_text(guide, encoding='utf-8')
    print(f"PASS: {len(ordered)} changes; SHA256={report['sha256']}")


if __name__ == '__main__':
    try:
        build()
    except (OSError, ValueError, KeyError, AssertionError, struct.error) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        sys.exit(1)
