"""Package and publish the prepared, committed version to GitHub."""

import argparse
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(*args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise ValueError(f"命令失败：{' '.join(args)}\n{result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def publish(check_only=False):
    spec = importlib.util.spec_from_file_location('packager', Path(__file__).with_name('package-release.py'))
    packager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packager)
    if not check_only:
        for command in ('git', 'gh'):
            if not shutil.which(command):
                raise ValueError(f'找不到 {command}。首次设置步骤见 p5r-build/发布指南.md。')
        run('gh', 'auth', 'status', '--hostname', 'github.com')
        origin = run('git', 'remote', 'get-url', 'origin')
        match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+/[\w.-]+?)(?:\.git)?/?', origin)
        if not match:
            raise ValueError('origin 必须指向 GitHub.com 仓库，请先配置远程仓库。')
        repo = match.group(1)
        commit = run('git', 'rev-parse', '--verify', 'HEAD')
        branch = run('git', 'symbolic-ref', '--short', 'HEAD')
        if run('git', 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError('请先提交源码、版本号和更新日志，再运行发布命令。')
        run('gh', 'repo', 'view', repo, '--json', 'nameWithOwner')

    archive = packager.package(ROOT / 'p5rpc.skillrename', ROOT / 'p5r-build/dist')
    config = json.loads((ROOT / 'p5rpc.skillrename/ModConfig.json').read_text(encoding='utf-8-sig'))
    tag = f"v{config['ModVersion']}"
    print(f'校验和打包成功：{archive}', flush=True)
    if check_only:
        print(f'本地预演完成，准备发布 {tag}；未连接 GitHub，未推送或发布。')
        return

    releases = json.loads(run('gh', 'release', 'list', '--repo', repo, '--limit', '1000', '--json', 'tagName,isDraft'))
    if any(release['tagName'] == tag for release in releases):
        raise ValueError(f'{tag} 已有 Release 或草稿，不会覆盖。若上次失败，请按发布指南恢复草稿。')
    if run('git', 'ls-remote', '--tags', 'origin', f'refs/tags/{tag}'):
        raise ValueError(f'远程标签 {tag} 已存在，不会移动它；请检查已有版本或使用新版本号。')
    if run('git', 'status', '--porcelain', '--untracked-files=all') or run('git', 'rev-parse', 'HEAD') != commit:
        raise ValueError('打包期间源码发生变化，请提交后重试。')
    print(f'推送 {branch} 到 {repo}，发布 {tag}…', flush=True)
    run('git', 'push', 'origin', f'{commit}:refs/heads/{branch}')
    remote = run('git', 'ls-remote', '--heads', 'origin', f'refs/heads/{branch}')
    if not remote or remote.split()[0] != commit:
        raise ValueError('远程分支与本次提交不一致，已停止发布。')
    options = ['--prerelease'] if '-' in config['ModVersion'] else []
    # Keep the release hidden until both assets have uploaded successfully.
    run('gh', 'release', 'create', tag, str(archive), str(archive.parent / 'SHA256SUMS.txt'),
        '--repo', repo, '--target', commit, '--title', f"{config['ModName']} {tag}",
        '--notes-file', str(archive.parent / 'release-notes.md'), '--draft', *options)
    assets = json.loads(run('gh', 'release', 'view', tag, '--repo', repo, '--json', 'assets'))['assets']
    expected = {path.name: path.stat().st_size for path in (archive, archive.parent / 'SHA256SUMS.txt')}
    actual = {asset['name']: asset['size'] for asset in assets}
    if actual != expected:
        raise ValueError('远程附件清单或大小不匹配，已保留草稿，请检查后再发布。')
    run('gh', 'release', 'edit', tag, '--repo', repo, '--draft=false')
    state = json.loads(run('gh', 'release', 'view', tag, '--repo', repo, '--json', 'isDraft,url'))
    if state['isDraft']:
        raise ValueError('Release 仍是草稿，请在 GitHub 检查。')
    print(f"发布成功：{state['url']}")


def main():
    parser = argparse.ArgumentParser(description='一键校验、打包、生成说明、推送源码并发布 GitHub Release。')
    parser.add_argument('--check', action='store_true', help='仅本地校验并生成安装包和说明，不连接 GitHub')
    args = parser.parse_args()
    try:
        publish(args.check)
    except (OSError, ValueError, KeyError) as error:
        print(f'发布未完成：{error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
