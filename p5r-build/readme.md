# 开发与构建

项目根目录保留 `p5r-build/` 和 `p5rpc.skillrename/` 两个名称。

| 目录 | 内容 | Git |
|---|---|---|
| `src/` | 加载器和加载检查源码 | 提交 |
| `scripts/` | 当前构建、检查、打包、发布脚本；`legacy/` 保留历史实现 | 提交 |
| `config/` | 当前改名规则及命名范围审查资料 | 提交 |
| `vendor/` | 下载的依赖、参考源码、字库、接口程序集 | 忽略 |
| `input/` | 从本地游戏提取的原始资源 | 忽略 |
| `temp/` | 编译产物、构建记录、历史产物、备份、重复源码归档 | 忽略 |
| `dist/` | 对外发布的安装 ZIP、校验文件和发布说明 | 忽略 |

## 当前构建所需的本地材料

- Python 3。
- `input/SC-NAME.TBL`：从对应版本的游戏简中资源提取的原始名称表。
- `vendor/source/P5NameTBLEditor-main/P5NameTBLEditor/Charsets/P5R_CHS.tsv`：来自 P5NameTBLEditor 的简中字库，保留项目许可。
- 编译加载器另需支持 Roslyn 的 PowerShell 7、`vendor/net9ref/ref/net9.0/` 下的 .NET 9 引用程序集，以及 `vendor/Reloaded.Mod.Interfaces.dll`、`vendor/CriFs.V2.Hook.Interfaces.dll`。两个接口程序集来自本地 Reloaded-II 及其 CriFs 依赖。

当前电脑上的这些材料已归位。它们不提交 Git，另一台电脑需自行准备相同材料。参考项目分别为 DeathChaos25/P5NameTBLEditor、Reloaded-Project/Reloaded-II 和 Sewer56/CriFs.V2.Hook.ReloadedII。

## 修改名称并构建

日常修改 `config/changes.json` 的 `changes` 列表，每条包含 `section`、`id`、`old`、`new`。`section` 1 和 2 是两组技能名称，14 是技能卡名称；保留正确的原名和 ID，只调整需要修改的名称。恢复原名时删除对应规则。
版本号只在 `../p5rpc.skillrename/ModConfig.json` 的 `ModVersion` 中维护。

在项目根目录执行：

```powershell
python .\p5r-build\scripts\build-mod.py
```

脚本直接读取原始表和当前规则，检查原名、重复 ID、名称编码、偏移范围以及所有未修改条目。生成：

- `p5rpc.skillrename/Data/NAME.TBL`：当前 Mod 名称表。
- `p5rpc.skillrename/技能名称对照表.md`：按规则整理的玩家说明，由 `config/naming-guide.md` 填入版本生成，提交 Git。
- `p5r-build/temp/current/changes.json`：自动计算的版本、配置哈希及名称表校验记录，不提交。
- `p5r-build/temp/current/NAME.TBL`：构建输出副本。

当前构建不依赖任何历史 `release-*` 目录。首次整理后生成的名称表与原有 0.4.4 成品逐字节一致。

## 修改加载器

只改名称不必重新编译加载器。修改 `src/SkillRename.cs` 后，在项目根目录执行：

```powershell
pwsh -NoProfile -File .\p5r-build\scripts\compile-net9.ps1
pwsh -NoProfile -File .\p5r-build\scripts\test-bind.ps1
```

新 DLL 输出到 `temp/loader/SkillRename.dll`。检查通过后，将其复制到 `p5rpc.skillrename/SkillRename.dll`，并保留同目录的 `CriFs.V2.Hook.Interfaces.dll`。脚本不会自动替换正在使用的加载器。
`compile-check.ps1` 可编译 `src/Check.cs`；运行该检查程序时的三个参数分别是加载器 DLL、名称表和 vendor 目录。需要本地 .NET 9 运行时。
编译中旧接口程序集可能产生 CS1701 版本兼容警告；绑定检查不代替游戏内验证。

## 打包与发布

准备版本内容和 `changelog/版本号.md`，先构建、验证、提交，再执行：

```powershell
python .\p5r-build\scripts\release.py --check
python .\p5r-build\scripts\release.py
```

第一条仅本地打包预演，第二条推送并发布。打包会拒绝过期的配置、版本或名称表。详细首次设置见 [发布指南](发布指南.md)。

## 历史材料

旧脚本在 `scripts/legacy/` 中供追溯，不是当前构建入口；部分仍依赖旧安装路径或试验材料。
历史生成目录在 `temp/history/`，Mod 备份在 `temp/Backups/`，原 Mod 内的重复源码在 `temp/previous/mod-source/`。这些本地归档都保留，但不提交或发布。
历史更新说明始终保存在项目根目录 `changelog/` 中。
