# R214：判定数据未改，仍须检查动画的间接定位路径

角色替换不能仅用“没有打包 BBS”证明一切战斗行为等价。需分别检查最终载荷、当前原版 provider、脚本参数的真实类型，以及模型/动画/socket 是否可能通过引擎调用改变战斗对象位置。本例的[相对证据指纹](gold-r214-color-transition-evidence.json)只索引私有审计结果，不发布游戏代码或资产。

**已证范围：**最终 R214 集合未覆盖攻击框、受击框、技能判定范围和命中/选帧时序数据；本机当前原版 BBS/COL 仍为这些文件的 provider。R214 配色修复还逐字节保留 R213 的模型、动画、物理和音频载荷。静态审计未找到 Slayer 脚本使用 3D 骨/socket 参数改变位置的路径。**未证范围：**全角色、全部原生代码分支及实际对战的行为完全等价；本例没有实机输入回放、碰撞覆盖图或 Shipping 全调用链验证。

## 1. 先锁最终集合和真正的原版来源

以下 `G = work/retail_colors_r214/gameplay_audit`，为私有实现来源。

| 入口 / 输出 | 检查内容 | 本次证据 |
| --- | --- | --- |
| `G/audit_gameplay.py` → `FINAL_STAGE_FILES.json`、`FINAL_STAGE_EXPORT_CLASSES.json`、`FINAL_STAGE_CLASSIFICATION.json` | 每个最终 companion 哈希对冻结清单；按真实 export class 与 package 路径分类，不只搜文件名 | 1,327 包、2,655 文件无差异；没有 REDBBSData、REDCollisionData 或战斗规则类。视觉 StaticMesh 的 BodySetup/NavCollision 保留其物理/导航含义，不误报成攻击框 |
| 同入口 → `CURRENT_RETAIL_SLY_GAMEPLAY_DATA.json` | 校验当前主 PAK 索引 SHA1、entry SHA1、解压载荷 SHA256，覆盖角色全部 Data 历史版本 | 162 个文件对同一本机当前零售快照相等；包括无后缀及历史版本，未凭名称猜当前生效版本 |
| 同入口 → `INSTALLED_PAK_PROVIDER_AUDIT.json` | 递归读取审计时磁盘全部附加 PAK，验证索引并与全游戏 BBS/COL/JON、角色 Data 路径求交集 | 审计时 23 包（含当时安装的 R213）零覆盖，v4/v9 索引解析无失败；这是安装前磁盘候选快照，不是 R214 安装后或运行时 mount trace |
| 集成者 `R213_PROTECTED_PAYLOADS.json` | 本轮差异和历史制作分开，逐字节比较保留资产 | 1,542 个模型/动画/物理/声音文件不变；不能由此断言 R213 从未改过动画 |

安装器与制作期审计用途不同。诊断可使用当前引擎/PAK 身份保证解析可靠，但不要把这些身份做成朋友机安装的 EXE/build 白名单。

## 2. 沿消费路径检查 typed 参数，不能只 grep 名字

本地源码解释普通判定为 JON 矩形加战斗对象位置、方向和缩放。另一方面，`PosType2Position` 的 3D 分支可读取真实 socket；`MoveToPosType`、`WarpBase`、`SetGripPosition` 和对象初始化可把结果写入战斗坐标。这条间接通路必须承认，再检查实际脚本是否使用它。

`G/audit_animation_and_global_bbs.py` 结合 `BBS_CommandDefine.h` 的 `BBS_WRITE(POS_TYPE, …)` 参数类型与 `obj_ScriptInc.h` 枚举数值，严格解码实际 BBS 指令。它找的是 typed 数值，而不是脚本文本中是否含某骨名，也不在未知 opcode 后跳字节继续假装完整。

- Slayer/SLYEF 共 32 个当前及历史包、6,428 状态、208,695 指令完整解码，`POS_*_3D` 参数为 0；共同 CMN/CMNEF 的 24,201 指令也为 0。
- `ALL_SLY_VERSIONED_GRIP_PROVENANCE.json` 记录 176 次 `SetGripPosition` 的前驱：每次紧前一条均为 `ExPointFReset`。保存点 `POS_EX_POINT_F` 不能误解为骨/socket，也不能直接当作 JON 点。
- 普通/空投的 `POS_ZERO` 加脚本常量、咬人保存点加常量，与敌方颈/腹等 JON collision point 各按来源解释，不能因为抓投与身体接触就推断读取动画骨。

外部角色也可能读取替换身体。扩大调查的 126 包中，121 包、865,247 指令成功，5 包因未知 opcode/状态边界保留失败；确有 213 条 3D 位置命令，多见于粒子与演出，但未完成全部原生行为证明。因此“Slayer 的直接参数为 0”不等于“所有外部消费者都不存在”。成功项和失败清单共同进入 `GLOBAL_AND_VERSIONED_BBS_SOCKET_AUDIT.json`。

## 3. 动画长度相同不是全部时序证明

同入口输出 `FINAL_ANIMATION_ROOT_MOTION_METADATA.json` 与 `FINAL_ANIMATION_NOTIFY_COMPARISON.json`：

- 347 个 AnimSequence 全部解析；346 个同原路径序列的 `NumFrames`、`SequenceLength` 与当前零售相等；1 个新增自然身体片段单列，不能伪造原版对应项。
- 347 个均未序列化启用 `bEnableRootMotion`；提供的引擎构造函数默认值为 false，故缺字段按经过源码确认的默认值解释。RED 源码未查到 RootMotion 消费符号，只是有界源码检查，不能宣称已反汇编当前 Shipping 的全部通路。
- 4 个带 Notify 的胜利序列共 8 个 `LoopStart/LoopEnd`，按语义与原版相等；其余 343 个无序列化 Notify。
- 命中时刻的主要保护依据仍是未覆盖的 BBS/JON 指令。动画长度、Notify、Root Motion、动作 key、骨/socket 和实际战斗坐标各是不同层，不能任选一个通过便代替其余。

## 4. 配置、历史日志与最终措辞

`INSTALLED_SCRIPT_CONFIGURATION.json` 核对审计时 UE4SS 的实际控制配置、唯一 mods.txt 和 enabled 标记。旧日志曾显示桥启动，但日志时间早于禁用配置；不能把旧日志当作当前仍启用，也不能把磁盘禁用快照升级为进程内 hook 检查。第三方 loader/ASI 保持原样，未用清理其他 MOD 的方式制造结论。

适合交付的表述是：“本包未改攻击框、受击框、技能判定范围和命中时序数据；当前原版 BBS/COL 保持权威。R214 材质变更保持 R213 动画载荷，静态审计未发现 Slayer 直接通过 3D 骨/socket 参数改判定位置的脚本路径。”仍保留外部消费者、5 包解码失败、未做实际对战与 Shipping 全调用链验证的限制。

`G/EVIDENCE_MANIFEST.json` 锁定 15 份报告/脚本摘要；`CONCLUSION_ZH.md` 给出结论与例外。整个审计只读最终资源和安装信息，没有修改资产、运行游戏、保存包或改变判定以适配新外观。
