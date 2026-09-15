# 使用随技能附带的工具

Python 3.10+，标准库即可。在技能目录中运行 `python scripts/harness.py --help`。
项目是新目录；init 不覆盖现有目录。目录中的 `project.json` 是当前记录，`NEXT.md` 是
人和 AI 恢复上下文的简短入口。命令必须串行运行，同一个文件不要由多个进程同时写。

init 还复制四张可填写工作表：`base-assessment.md`、`component-plan.md`、
`subtask-handoff.md`、`surface-audit.md`。它们不自动登记为完成证据，不会强制语音项目
做身体。已有项目可从技能 templates 复制所需表到新文件，不覆盖当前记录。
填好后以新版本登记 `technical_report`，用 built_from 关联实际候选与检查文件；CLI
校验哈希/来源，不会解析文字内容自动决定体型或纹理是否合格。

## 常用流程

```sh
python scripts/harness.py init MY_PROJECT --name "My mod"
python scripts/harness.py next MY_PROJECT
python scripts/harness.py answer MY_PROJECT scopes "body,outfit,face,material,palette,voice"
python scripts/harness.py brief MY_PROJECT --id brief-v1 --out reviews/brief-v1.md
python scripts/harness.py check MY_PROJECT
```

其他回答 ID 在 `templates/questions.json`。`answer --proposal` 表示 AI 待定提案，不能
作为已确认 brief 通过；实际获得回答后重新 answer。缺工具/版本时写待检查，继续能做的工作。

登记实际文件：

```sh
python scripts/harness.py add MY_PROJECT mesh-C source/mesh-C.blend --kind source --stage rig --role source --variant C
python scripts/harness.py add MY_PROJECT win-C evidence/win-C.mp4 --kind engine_capture --stage motion --variant C --built-from mesh-C --metadata evidence/win-metadata.json
python scripts/harness.py select MY_PROJECT C --quote "我选 C，其他保留" --source "当前作者消息"
python scripts/harness.py review-pack MY_PROJECT --artifacts win-A win-B win-C --out reviews/compare-v1
```

上例里的 A/B 文件也要先登记。metadata 是单独 JSON 对象，例如：

```json
{"camera":"Win-source","source_camera":true,"reviewed_frames":[590,591,592],"fps":60,"game_build":"实际版本"}
```

reviewed_frames 填**实际检查过的帧**。face motion 的 accept 还需要 projection 类型证据。
先登记投影，再在用户给出真实决定后执行：

```sh
python scripts/harness.py decision MY_PROJECT motion accept --artifacts win-C projection-C --quote "C 可以" --source "作者本轮审查"
```

用 feedback 登记局部问题；用 resolve 链接新的已检查候选和说明。retire 把旧运行版本
转成 archive，文件保留。版本、回答、输入和文件变化会使旧决定失效；先 check 再推进。

## 打包与清理

kind=runtime_file、role=runtime 的 metadata 要包含相对 `package_path`。dependencies
写运行加载依赖，built_from 写制作来源。stock 专指目标游戏当前版本原生已有资源，
必须附对应查询记录和 game_build。

```sh
python scripts/harness.py release-plan MY_PROJECT
python scripts/harness.py check MY_PROJECT --ready-for local-test
python scripts/harness.py check MY_PROJECT --ready-for share
python scripts/harness.py check MY_PROJECT --ready-for friend-verified
python scripts/harness.py clean-plan MY_PROJECT
```

这些命令不执行 Cook/安装/删除。release-plan 只核对已登记的运行图；从最终二进制包提取
真实清单由适配器完成。clean-plan 只列明确标为 temporary 且没有被来源、审查、反馈引用
的文件，全部 protected/archived 文件保留。

## 2D 投影

```sh
python scripts/project_points.py actual-points.json --out projection-v1
```

输入字段：camera、frame、viewport=[width,height]、matrix_convention 固定
`row_major_times_column_vector`，ndc_depth 为 `minus_one_to_one` 或 `zero_to_one`，
world_to_clip 为 4×4 行主序矩阵，points 为 id/group/world/visible/可选 target_pixel，
edges 是显式两个 ID 的配对列表。原点在输出画面左上角。

输出 projection.svg 和 projection.json。矩阵必须由真实相机推导；工具不回收截图中的
3D 信息、不检查遮挡、不求骨架变形。不要连接无序边界点。
