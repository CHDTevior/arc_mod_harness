# 第一次使用

## 给 AI 的起手消息

> 读取 `skills/arc-mod-harness/SKILL.md`，用它带我做 MOD。先读我已有的参考和对话，
> 再一轮问一到三个关键问题。我的目标是【游戏/角色/主要想法】，我最在意【实际镜头】。
> 先做可比较的参考；每一轮给我看实际结果后再决定风格。

不需要先准备完整游戏资源。可以只有一张图和一个想法：AI 先问想借哪里，帮你补参考，
然后调查本机工具链。不要先耗费长渲染或付费生成大量候选。

## Codex 技能安装

把 **整个** `skills/arc-mod-harness` 文件夹复制到自己的 Codex skills 目录。常见本地
位置是 `~/.codex/skills`；自定义了目录时以你的实际配置为准。复制前检查是否已有同名
技能，保留原版。下面脚本在目标已存在时停止，不覆盖。

在仓库根目录运行 PowerShell：

```powershell
$skillSource = Join-Path (Get-Location) 'skills/arc-mod-harness'
$skillDestination = Join-Path $env:USERPROFILE '.codex/skills/arc-mod-harness'
if (Test-Path -LiteralPath $skillDestination) { throw '目标已存在，请先检查旧版' }
New-Item -ItemType Directory -Force -Path (Split-Path $skillDestination) | Out-Null
Copy-Item -LiteralPath $skillSource -Destination $skillDestination -Recurse
```

新对话中调用 `$arc-mod-harness`。如果宿主尚未发现技能，可让 AI 直接读取复制后的
SKILL.md；无需先解决插件安装。工具脚本和 references/templates 随技能一起可用。

其他 AI：直接附上/指定 SKILL.md，按需读取引用文件。能执行 Python 时可使用记录工具；
不能执行时也能按模板管理 brief、候选和人工审查，但不要声称执行过自动检查。

## 建立项目

Python 3.10+。Windows 如果 `python` 不可用，可换成 `py -3` 或实际 Python 路径。
所有命令从仓库根运行；安装成技能后将脚本位置换成安装目录。

```sh
python skills/arc-mod-harness/scripts/harness.py init projects/my-mod --name "我的角色 MOD"
python skills/arc-mod-harness/scripts/harness.py next projects/my-mod
python skills/arc-mod-harness/scripts/harness.py answer projects/my-mod intent "保留人物身份，改身体服装，必杀表情更戏谑"
python skills/arc-mod-harness/scripts/harness.py answer projects/my-mod game_build "待从本机确认"
python skills/arc-mod-harness/scripts/harness.py answer projects/my-mod scopes "body,outfit,face,material,palette,voice"
python skills/arc-mod-harness/scripts/harness.py answer projects/my-mod success_scene "必杀特写、胜利和普通战斗"
python skills/arc-mod-harness/scripts/harness.py brief projects/my-mod --id brief-v1 --out reviews/brief-v1.md
```

先看这份 brief，继续填最相关的参考问题。`next` 只是问题队列，AI 应根据你实际说的话
调整提问；不会替你回答。项目内 `adapter.json` 是本地工具调查表，`replacement-matrix.md`
用来枚举真正需要替换的资源，`NEXT.md` 记录恢复点。

注册文件前把它保存在项目目录内，例如 `references/body-front.png`；登记使用正斜杠的
相对路径，避免迁移电脑后满篇绝对路径。源原件另行保留，不因登记而覆盖。

## 先看一遍示范

```sh
python examples/run_demo.py --out projects/demo
```

打开输出的 `projects/demo/reviews/compare/index.html`。该演练的图片、控制点和运行文件
全部是合成教学材料，**没有游戏渲染或安装包**。演练报告会显示 C 被选中、A/B 保留不入
清单、修改文件后旧决定失效、未完成实机步骤仍是待验收。

详细命令见 [CLI](cli.md)，完整演练说明见 [walkthrough.md](walkthrough.md)。
