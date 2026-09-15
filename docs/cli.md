# CLI 与数据合同

技能自包含说明见 [tooling.md](../skills/arc-mod-harness/references/tooling.md)。工具只管理
项目记录、复制审查素材和计算投影，不自行调用 Blender、UE、图像生成服务、游戏或上传。

```sh
python skills/arc-mod-harness/scripts/harness.py --help
python skills/arc-mod-harness/scripts/project_points.py --help
```

## 命令速查

| 命令 | 作用 | 写入 |
|---|---|---|
| init PROJECT --name NAME | 创建空项目，拒绝覆盖 | 新项目目录 |
| next PROJECT | 按 scope 返回下一问题 | 无 |
| answer PROJECT ID VALUE | 保存实际回答；scopes 用逗号分隔 | project.json |
| brief PROJECT --id ID --out PATH | 把当前回答写成可审查说明 | 新文件及登记 |
| add PROJECT ID PATH --kind KIND --stage STAGE | 登记现有文件、哈希和来源 | project.json |
| select PROJECT C --quote TEXT --source TEXT | 记录作者选择 | project.json |
| retire PROJECT ID --note TEXT | 老文件转 archive，保留实体和记录 | project.json |
| decision PROJECT STAGE accept/revise/defer ... | 记录明确审查意见 | project.json |
| feedback PROJECT ARTIFACT ... | 部位、目标、保留项和帧/坐标 | project.json |
| resolve PROJECT FEEDBACK --artifact NEW --note TEXT | 链接新候选和复查说明 | project.json |
| review-pack PROJECT --artifacts A B C --out DIR | 复制素材，生成本地审查页 | 新目录 |
| check PROJECT [--ready-for LEVEL] | 文件、依赖、过期决定、阶段证据检查 | 无 |
| release-plan PROJECT | 所选运行依赖闭包与排除清单 | stdout JSON |
| clean-plan PROJECT | 未引用 temporary 文件清单，不删除 | stdout JSON |

退出码：0 表示命令正常完成，不意味着 MOD 已通过游戏验收；`check` 有错误时为 1；
参数/结构/路径/缺资源等异常为 2。`release-plan` 可正常产生仍待审查的计划，需阅读其中
readiness；其 status 始终写明是声明依赖图计划。

## Artifact

每个 ID 只登记一次。文件修改后用新的 ID/路径，不刷新旧哈希假装原审查继续有效。
同一选中 variant 的旧运行文件用 retire 归档，避免同挂载路径重复。archive 文件本身
仍保留，旧决定及下游引用可能因此失效，需有意更新到新版本。

```json
{
  "path": "candidates/C/win.png",
  "kind": "engine_capture",
  "stage": "motion",
  "role": "evidence",
  "variant": "C",
  "dependencies": [],
  "built_from": ["win-cooked-C", "head-C", "camera-win"],
  "metadata": {
    "camera": "Win source camera",
    "source_camera": true,
    "reviewed_frames": [590, 591, 592],
    "frame": 592,
    "game_build": "项目实际版本"
  }
}
```

用 `--metadata metadata/win.json` 提交 metadata 对象；不是整个 artifact 对象。
`--depends-on` 和 `--built-from` 后接已经登记的 ID 列表。工具计算 sha256/bytes。
同一元数据文件后来变动，不会自动修改已登记记录；重登新候选。

kind 可选：brief、concept、reference、source、dcc_capture、projection、engine_capture、
game_capture、friend_capture、audio、technical_report、package_report、runtime_file、
stock_dependency。role 是 source/reference/evidence/runtime/stock/archive/temporary。
来源类型和角色用途分开：一张渲染可保留为 archive；concept 永远不能替代 motion/runtime
需要的实际 capture 类证据。工具不能鉴别用户虚报的 kind，仍需 AI 读取真实文件。

### Runtime 与来源分开

runtime_file 的 metadata 必须有 `package_path`。stock_dependency 的本地文件应是
查到该原生资源的证据，并有与 project game_build 匹配的 metadata.game_build。依赖指向
source/reference 而非 runtime/stock 时，release-plan 拒绝生成完整图。

package_report 用 `built_from` 关联全部选中运行文件；runtime 的 game_capture 再
`built_from` 关联实际测试的 package_report。新包的通过记录不能由旧包实机画面顶替。
工具核对声明的关系；真实包内资源/依赖需要适配器提取并登记，不能只登记手工想象的清单。

## 审查记录

```sh
python skills/arc-mod-harness/scripts/harness.py decision projects/my-mod motion accept --artifacts win-C win-projection-C --quote "C 的眼神可以" --source "作者在本轮审查的原话"
python skills/arc-mod-harness/scripts/harness.py feedback projects/my-mod win-C --part "character_R.black_pupil" --desired "略向下，保持黑瞳孔可见" --preserve "上眼皮和身体" --frame 592 --camera Win --point 0.53 0.68
```

只在作者实际说过后执行 decision/select。该 CLI 不认证人的身份，不可作为签名系统。
accept 会验证阶段所需证据类型和未解决反馈；revise/defer 允许保存不完整候选的反馈。
技术阶段可记录作者已经明确接受的具体结果，不要求每运行一个命令都重新确认。

`check --ready-for local-test` 检查到 package 的相关阶段；`share` 加 runtime；
`friend-verified` 再要求 delivery 中带环境信息的 friend_capture。记录校验不执行游戏，
也不保证作者真的逐帧看过。检查报告清楚列出 pending/stale/needs_revision/package_mismatch。

## 已知实现边界

- 单项目命令串行使用；无并发事务/锁、多用户身份认证、远程存储或自动预算管理。
- 文件必须项目内相对路径；不接受 symlink/junction。源图要复制/导出为工作副本再登记。
- 任何回答或 selected variant 改动使之前决定保守失效；暂未做逐问题影响范围最小化。
- 图像点击坐标只适用于静帧；视频对齐是编码时间，不是原动画 key 的自动映射。
- 不自动发现二进制资产依赖；不生成真实游戏 pak，不删除、不发消息、不自动上传。
- 对实际媒体来源、报告内容与审美的判断仍由作者/AI 完成，JSON 不能证明这些事。
