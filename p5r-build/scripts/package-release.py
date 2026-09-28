"""Validate and package the locally prepared Mod; Python 3 standard library only."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[2]
FILES = (
    'ModConfig.json', 'README.md', '技能名称对照表.md',
    'SkillRename.dll', 'CriFs.V2.Hook.Interfaces.dll', 'Data/NAME.TBL',
)


def release_changes(changelog: Path, version: str) -> str:
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('更新日志版本号格式无效。')
    path = changelog / f'{version}.md'
    if not path.is_file():
        raise ValueError(f'缺少本版本更新日志：{path}')
    text = path.read_text(encoding='utf-8-sig').strip()
    title, _, body = text.partition('\n')
    if title.strip() != f'# {version}':
        raise ValueError(f'{path} 第一行应为「# {version}」。')
    body = body.strip()
    if re.search(r'^#[ \t]+', body, re.MULTILINE):
        raise ValueError(f'{path} 只能包含当前版本；分类请使用二级标题。')
    if not re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL).strip():
        raise ValueError(f'{path} 的更新说明为空，请填写本次改动。')
    return body


def package(mod: Path, output: Path, changelog: Path = ROOT / 'changelog') -> Path:
    # Load once so the bytes checked here are exactly the bytes in the ZIP.
    contents = {}
    for name in FILES:
        path = mod / name
        if not path.is_file():
            raise ValueError(f'缺少必要文件：{path}。请先准备完整的本地 Mod。')
        contents[name] = path.read_bytes()
        if not contents[name]:
            raise ValueError(f'文件为空：{path}')
    config = json.loads(contents['ModConfig.json'].decode('utf-8-sig'))
    report_path = ROOT / 'p5r-build/temp/current/changes.json'
    if not report_path.is_file():
        raise ValueError('缺少构建记录，请先运行 python p5r-build/scripts/build-mod.py。')
    report = json.loads(report_path.read_text(encoding='utf-8-sig'))
    rules = ROOT / 'p5r-build/config/changes.json'
    if hashlib.sha256(rules.read_bytes()).hexdigest() != report['config_sha256']:
        raise ValueError('改名配置已变化，请先重新运行 build-mod.py。')
    version = config['ModVersion']
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('ModVersion 应为 0.4.4 或 0.4.5-beta.1 这样的版本号。')
    if config['ModId'] != 'p5rpc.skillrename' or config['ModDll'] != 'SkillRename.dll':
        raise ValueError('ModId 或 ModDll 与当前打包规则不一致。')
    if report['version'] != version:
        raise ValueError('ModConfig.json 与 changes.json 的版本号不一致。')
    if hashlib.sha256(contents['Data/NAME.TBL']).hexdigest() != report['sha256']:
        raise ValueError('NAME.TBL 与 changes.json 的 SHA256 不一致，请同步名称表和改名记录。')
    for name in ('SkillRename.dll', 'CriFs.V2.Hook.Interfaces.dll'):
        if not contents[name].startswith(b'MZ'):
            raise ValueError(f'{name} 不是有效的 Windows 程序文件。')

    changes = release_changes(changelog, version)
    folder = output / f'v{version}'
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / f'p5rpc.skillrename-v{version}.zip'
    # A temporary file avoids leaving a partial ZIP on failure.
    with tempfile.TemporaryDirectory(prefix='package-', dir=folder) as staging:
        temporary = Path(staging) / archive.name
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as bundle:
            for name in FILES:
                entry = zipfile.ZipInfo(f'p5rpc.skillrename/{name}')
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                bundle.writestr(entry, contents[name])
        with zipfile.ZipFile(temporary) as bundle:
            if bundle.testzip() is not None:
                raise ValueError('ZIP 完整性校验失败。')
            for name in FILES:
                if bundle.read(f'p5rpc.skillrename/{name}') != contents[name]:
                    raise ValueError(f'ZIP 内容校验失败：{name}')
        temporary.replace(archive)

    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (folder / 'SHA256SUMS.txt').write_text(f'{checksum}  {archive.name}\n', encoding='utf-8')
    notes = (
        f"# {config['ModName']} v{version}\n\n"
        f"{config['ModDescription']}\n\n"
        f'## 本次更新\n\n{changes}\n\n'
        '## 安装与更新\n\n'
        f"请下载附件 `{archive.name}`，解压后将 `p5rpc.skillrename` 文件夹放入 "
        'Reloaded-II 的 Mods 目录，启用本 Mod 及其依赖。更新前关闭游戏。\n\n'
        '本 Mod 面向 P5R PC Xbox 版简体中文；需要 Persona Essentials 和 CriFs V2 Hook。'
        '名称表采用整表替换，与其他修改同一名称表的 Mod 可能冲突。\n\n'
        'GitHub 自动提供的 Source code 是源码包，不是可直接安装的 Mod。\n\n'
        '完整改名内容见安装包内的「技能名称对照表.md」。\n'
    )
    (folder / 'release-notes.md').write_text(notes, encoding='utf-8')
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description='校验本地 Mod 并生成 GitHub Release 安装包（不重新编译、不上传）。')
    parser.add_argument('--mod-dir', type=Path, default=ROOT / 'p5rpc.skillrename')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'p5r-build' / 'dist')
    parser.add_argument('--changelog-dir', type=Path, default=ROOT / 'changelog', help='按版本保存更新日志的目录')
    args = parser.parse_args()
    try:
        archive = package(args.mod_dir.resolve(), args.output_dir.resolve(), args.changelog_dir.resolve())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f'打包失败：{error}', file=sys.stderr)
        return 1
    print(f'打包成功：{archive}\n同目录已生成 SHA256SUMS.txt 和 release-notes.md。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
