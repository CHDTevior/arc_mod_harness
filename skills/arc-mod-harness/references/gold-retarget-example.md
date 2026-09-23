# Gold Demo：从源动作到可操作 UE 角色的具体例子

本例补充[通用重定向流程](retargeting-workflow.md)，记录 Gold 替换 Slayer 时实际采用的
数据链和后来修正的问题。以下案例事实来自私有工程的 R193–R197 报告与脚本；本次仅整理
这些记录，未重新运行 UE。公开仓库附带的[合成示例](../examples/retarget_tqs_demo.py)
只验证局部 T/Q/S 数学，不包含游戏动画、角色模型或私有引擎适配器。

主要记录的相对标识与SHA256见 [案例证据索引](gold-demo-evidence.json) 的G01–G07。
索引提供来源追溯，不代替未分发的原始报告或实际游戏检查。

后续R213修复的脚本顺序、输入输出和已否定路线集中见[修复实施索引](gold-r213-fix-methods.md)。

## 已做到什么，证据到哪里

| 对象 | 实际范围与证据 |
|---|---|
| 身体骨架 | native **465 骨**；保留骨名、父链及原绑定，按骨名写轨，不把某次导出的索引当通用接口 |
| 原始入口 | 实际 Default 身体动画表 **99 条**，与 BBS 状态引用及其哈希对照；分类为普通 **92**、特殊 **7** |
| R193 普通动作 | **90** 条新原生 T/Q/S 动作，加沿用已验证的 `sly000`、`sly030`，共 **92** 条路由；独立重开确认全部 90 条的帧数/轨数及 local P/Q，常量 scale 折叠最大差 `4.76837158203125e-6` |
| 后续基础接入 | R195–R197 记录普通 92 + 特殊 7 = **99** 条主身体路由，另有 **99** 条自然身体路由；后者是显示变体对应表，不是额外 99 个不同动作 |
| 实际镜头 | 开发 UE 的真实 Battle 摄像机记录了走停、后退循环、蹲跳、攻击、受击、5K、闪现显隐、Dust 头挂接、脱衣及恢复；并非所有对局分支均已验收 |
| 尚未完成 | 正式 retail Cook/安装包未完成；普通表情尚未制作/接入，当前中性头随身体头挂点运动；头发/耳尾独立动态与特殊演出精修仍有后续工作 |

计数依据为 `work/ordinary_retarget_r193/ordinary_coverage.json`、
`work/interactive_demo_r191/review.json`、`reviews/ANIMATION_SEQUENCE_R197_ZH.md`。
最终开发试玩范围见 `work/interactive_demo_r195/README_ZH.md` 与
`combined_final_root_review.json`。这些均是**私有工程相对索引**，不随 harness 分发。

## 1. 把状态、原 raw 轨和时钟绑在一起

先读取真实动画表的 `state/name → AnimSequence`，再解析 BBS 的 cell、loop、显隐和换模事件。
例如后退与换体动作必须带上实际循环区间及消费者；仅按 `slyNNN` 文件名分类无法覆盖它们。
特殊 7 条在 R193 中后置，后来才接基础运输；不要沿用旧报告的阶段划分宣称当前缺失或通过。

`inventory_export_sources.py` 与 `decode_sources.py` 做了这些实际工作：

1. 复制并记录源资源哈希，读取 raw 位移 T、四元数 Q、缩放 S，以及 `TrackToSkeletonMap`。
   PSA 用来交叉验证位置/旋转，缩放从源 raw 数据取得。
2. 按 `bAnimRotationOnly`、`UseTranslationBoneNames` 应用原平移规则；缺轨从 reference bind
   补全。不能把每根骨的位移全部抹掉，也不能把非 1 的 scale 当导出噪声。
3. 用已核对的引擎父子 T/Q/S 规则重建 world 与 skin 变换，保存源 bind、轴/单位及骨名父链。
4. 保存 `raw_index`、`seconds`、源 `SeqLength` 和 hold。案例 raw 时钟为 `index/60`；求解时
   可以对完全相同的姿态只算一次，再按原索引展开，输出仍保留每个 raw 帧及原停帧。

输出合同是“骨名/父链 + 原始 T/Q/S + bind + 实际时钟 + 翻译规则 + 来源哈希”，
不能只有逐帧位置截图。60 Hz 和 Step 是本案例的已知合同，换项目应读取实际值。

## 2. 围绕目标关节运输，再按真实支撑修正

`retarget_solver.py` 使用冻结的 R129E 目标自然 REST 关节与骨段长度。设源参考绑定为 `N`，
源世界骨矩阵为 `Wsource`，则动作增量为 `Dsource = Wsource × inverse(N)`。
目标关节点 `H` 必须来自 Gold 的实际解剖位置；它可能与保留 native bind 后的骨原点不同。

主链先按目标骨段长度运输关节：用源动作旋转/缩放作用于目标 REST 骨段，另将源平移残量
按长度比例转换。接触求解得到目标关节点 `P`，保留的旋转/伸缩线性部分为 `A`，再构造：

```text
Dtarget.linear      = A
Dtarget.translation = P - A * H
Etarget             = Dtarget * N
```

这样 `Dtarget` 绕 Gold 关节作用，`Etarget` 仍可写到原骨架的动画轨。衣物/辅助骨保留其相对
已适配祖先的源运动，而非一律冻结。检查旋转、源伸缩和实际蒙皮表面；相同骨数/骨名不足以
证明手指 pivot、掌指根权重或衣物消费者正确。

接地只约束真实支撑脚。该实现为经 BBS 确认的空中、浮空、墙面、倒地状态走无足底约束的
比例 FK 路径；地面状态才调用接触求解并检查实际鞋底。记录支撑分类、root 修正、骨长及
有限值检查。若求解退回 FK，要把原因记入结果，不将异常替换成待机。

### 5K：相同源 scale 为什么仍会出现细腿

`NmlAtk5B / sly201` 的横踢揭示了皮肤与服装消费者的差异。源 knee、calf helper 横向 scale
约 `0.48–0.50`；源裤子上小腿约 44% 权重走额外 `G_Cos_calfup` 补偿，Gold 裸腿主要吃
skin helper。调查未发现重复缩放或大旋转轴错误；源裤装的视觉宽度不能靠照抄 helper 数值继承。

R195 候选只对该动作 raw `6–30` 的 8 个右腿 helper 收缩主尺度作局部适配，保留 30% 源收缩，
保旋转、实际 pivot、扩张/纵向尺度及 hold。`0–5`、`31–55` 保持原结果；主腿、脚、趾轨迹
不改，`sly204`、`sly213` 留哈希作保护。70% 收缩削弱是本案造型决定，不是其他角色的默认系数。

制作诊断在 `work/kick_volume_r195/README_ZH.md`、`handoff_manifest.json`；这些早期文件明确
标为待原生检查。后续 `work/interactive_demo_r195/kick_native_verification.json` 才记录真实
Battle 的 source/baseline/repair 对照：getter 315/318 对应已求值 raw 16/21，脚/趾/踝/跟骨
保持一致。截图请求发生在前一阶段，不能直接把请求帧号当画面最终求值帧号。

### 后退 loop：修支撑分类，也修实际取样范围

旧接地 band 把抬起的脚误判为支撑，使双支撑求解选到远处解，出现 root 跳变。R195 初次修复
仍按请求 raw 范围处理，循环边界留下问题。R196 以 11 根未改骨匹配真实求值姿态：BBS 请求
`51,56,…,96`，实际 raw 为 `50,55,…,95`，其 hold 代表为 `46,51,…,91`。

修复按实际支撑重算 `46–95`，保 `0–45` 与 `96–120`，不改帧数、`SeqLength` 或 Step。
该动作依据源足底高度与两脚相对高度限制双支撑；不能把局部阈值推广成所有步态的通用值。
也不通过插值原停帧或给 root 加平滑曲线掩盖错误解。

`work/backwalk_eval_r196/README_ZH.md` 是制作候选说明；后续
`work/interactive_demo_r195/backwalk_native_comparison.json` 记录 source、baseline、R195 repair、
R196 四次同输入的真实 Battle 测试，持续按后退 14 秒。实际循环 `91→46` 的 component root
步距由约 **23.43 mm** 降为 **7.32 mm**；这是该边界的测量，不能改写为“零滑步”或所有步态通过。

### R200：补查起步段，并将细腿检查扩到真实皮肤消费者

后续试玩仍在第一次吐烟时跳变一次。新原生对照中请求348/356正常，352下坠；
getter351–357按时钟及11根未改骨对应到真实raw31。R196保留的首段还有旧双支撑远解，
而已修循环没有复发。31和81的腿姿态相近，但全身241根骨不同，不能拷贝81整帧覆盖表演。

R200在各自原姿态上只重算26–35、41–45三个错误支撑hold，共15/121 raw；其余106 raw与
已修循环的local T/Q/S逐值不变。实际14秒长按中235个姿态样本对应新目标，163个循环采样
保持旧结果。此阶段记录只到松开收步，稳定待机由最终整合片段另查；不能把“循环正确”外推
为“首次进入与退出都正确”。来源见私有`work/backwalk_transition_r200/native_candidate_verification.json`。

细腿也不是修一次5K就全部覆盖。按当前实际皮肤/权重筛查99路线、8628 raw和2020个不同姿态，
复用holds，比较主骨坐标下真实蒙皮截面与刚体参考，再核源服装补偿，确认另外三段：

| 真实状态/clip | 局部修正域 | 原生核验 |
|---|---|---|
| ThrowExe / 310 | 左腿26–60，8 helper | 地面投真实输入；精确骨匹配与可见抬腿轮廓 |
| NmlAtkAir5B / 251 | 左腿6–15，8 helper | 空中K真实输入；raw6/11同姿完整画面 |
| sly_SP_06 / 405 | 右腿16–20，8 helper | 根据注册输入214+K、再K进入；hitstop中的raw16实读，画面被FX部分遮挡 |

它们沿用局部弱化收缩的方法，保护主腿/足趾/髋/root轨迹、原停帧与窗口外动作；不是清除所有
非均匀scale。原生投技getter491实际对应raw36，不能将动画位置乘采样率直接当最终Step姿态。
405有hitstop重复显示同一pose，核输入、状态、未改骨和时钟后再标对应。

对手脚的筛查须区分三件事：皮肤辅助骨缺少原服装补偿；源手掌/指头有意造型缩放；旧枢轴或
局部权重错误。握拳使包围盒缩短不等于手指被错误缩放，靴内隐藏裸脚的包围盒变化也不等于
可见鞋变细。本案另将源手指缩放和空防卷足留作单独判断，未批量钳制；99条离线筛查不代表
99条逐镜头美术验收。来源见私有`work/throw_volume_r200/{screen_summary,native_throw_jump_pose_match,native_sp06_pose_match}.json`；
主要报告指纹见[证据索引](gold-demo-evidence.json)的G15–G18。

## 3. 精确反推 UE local T/Q/S

`build_ue_tqs.py` 先统一厘米、轴向和 XYZW 四元数约定，再从目标 world T/Q/S 逐骨反推 local。
父级非均匀 scale 与子旋转不交换；一般矩阵 `inverse(parent) × world` 分解可能引入 shear，
与该项目使用的 UE `FTransform` 组合结果不同。

```text
Qlocal = inverse(Qparent) * Qworld
Slocal = Sworld / Sparent
Tlocal = rotate(inverse(Qparent), Tworld - Tparent) / Sparent

Tworld = Tparent + rotate(Qparent, Sparent * Tlocal)
Qworld = Qparent * Qlocal
Sworld = Sparent * Slocal
```

乘除 scale 均为逐分量操作，Q 为单位四元数。一般目标矩阵如果不能精确表示成 T/Q/S，需先
明确投影并报告损失；随后 local→world 的小误差不能证明前一步没有损失。案例分别记录
`world_TQS_projection_linear_max` 与 float32 的 FTransform 往返误差。

近零隐藏 scale 仍是动画数据。对于真正为零的父 scale，相应 local 位移和 scale 的 `0/0`
没有唯一解；可保留已知源 local 分量，再正向重建验证。若目标在塌缩轴上要求非零位移或
scale，则该约定下无解，应报告问题。数值零阈值必须结合源数据与误差报告，不得用 scale=1
偷偷改变姿态。统一 Q 的正负半球只改变表示，不增加任何插值帧。

## 4. 复制源 clip、写轨、保存，再由另一进程读取

本案确认 FBX 层级转换对非均匀缩放不等价后，走当前开发 UE 构建的原生适配器：

1. 复制原 `AnimSequence` 为新资源，保留原曲线与通知；不新建一个只有骨轨的空 clip。
2. 按骨名 `AddNewRawTrack` 写全 465 骨的 P/Q/S。记录准确帧数、时长、插值；本例使用 Step。
3. 标记 raw 修改，同步重压缩并保存。源资源及 Skeleton 使用独立副本和操作前后哈希保护；
   指向原目录的链接可能被导入器写穿，不能当隔离副本。
4. 独立进程重新打开新包，按骨名读取实际 P/Q/S、绑定、帧数、时长、插值，重建 world 并比较。
   再走正常压缩播放检查；编辑器的 raw 播放开关不是最终播放路径。

R193 的 90 条新资源确有上述 fresh read；scale 常量折叠误差单独报告，不能写成所有 T/Q/S
逐字节不变。引擎 API/ABI、结构和符号均与构建相关，私有写入脚本不是公开可移植工具。

## 5. 把动作接到真正显示的身体、头与材质

新动画表须持久化并读回确认。普通身体、自然身体、独立头、披风、服饰等各自需要正确 driver
与时间。案例的 99 条主表和 99 条自然表只是资源路由，还必须覆盖下列实际消费路径：

- **44/66 闪现：**独立 Gold 显示组同步源逻辑显隐与动态材质 MID。为隐藏源网格而手动关闭的
  main-pass 标志不代表游戏意图；直接照抄会让角色永久消失，完全不同步则出现可见平移。
- **脱衣/自然身体：**按实际 active body 从 component 0 切到 17，并跟踪独立 PawnEffect。
  释放、命中、结束及恢复分别读实际 mesh/动画消费者；只完成普通主表无法证明这个分支正确。
- **裸足动作：**穿鞋运输中的 foot 24° 与脚趾限幅不自动适用于自然裸足。R196 为自然身体
  建专用动作路由，保自然脚 REST，验证真实换体镜头；不能只隐藏鞋，继续共用穿鞋的足部姿态。
- **Dust/追击头挂接：**source 头根与 `G_Head_Attach` 相等仍不保证 Gold 解剖 pivot 正确。
  本案通过显示端 inverse-bind 补偿消除额外旋转造成的 orbit，源骨控制/动画保持原意。
- **残影与飞衣：**Step 静态粒子 mesh、1 tick PawnEffect、脱衣残留和布屑是独立消费者。
  飞衣从最后穿衣姿态释放，按发射器空间转换并在脱离后留在世界原处；还要保留冲击光、烟和拖尾。

材质接入同时核五图、实际 slot/MID、显隐和溶解，遮罩同步 base/outline/shadow/decal 的真实
使用 pass。保存材质图和参数读回之后仍查 shader 编译与 default-material fallback，再以同姿态
pass 隔离定位。`combined_final` 记录未发现该次 shader 编译失败或默认材质回退；这不保证
以后任意改图仍有效。材质、权重和骨轨分别保存版本，避免拿错误材质画面诊断骨架。

上述实现集中在 `work/interactive_demo_r195/build_display_sync.py`、`build_natural_routes.py`、
`head_pivot_verification.json`、`world_release_verification.json`。裸足制作候选另见
`work/natural_foot_r196`；后续接入及原生检查范围见 R195 Demo 的 README 和最终 review。

## 6. 用相同实际输入和游戏摄影验收

测试入口记录实际活跃 component 的动画引用、序列时间、已求值骨姿态、摄影及输入。
对照 source/current/candidate 保持相同状态与镜头，并标明 getter、截图请求和渲染所处阶段。
同名 AnimInstance 要按 outer 区分；开发分支按键要先实测，日志有发送按键不能证明已经出招。

连续测试初始/备用待机、走停、后退多轮 loop、蹲起、跳落、近远攻击、受击回归及变体恢复。
主画面保持完整角色、完整材质、真实 Battle camera 和同期原披风；DCC 裸模或局部侧视图只用于
诊断。R195 `combined_final` review 列出已看过的待机、5K、释放、命中、恢复帧及原生视频。
有代表片段通过的结论保留该范围，不能升格为零售部署完毕或普通表情已适配。

可操作启动器另做实际启动/组件/MID读回，交付入口保留自由控制。按键、截图、自动退出或
暂停只放在测试入口；宏解析成功、角色实际显示且窗口可响应都要有运行证据。

## 可随 harness 运行的合成小例子

在仓库根目录运行（仅 Python 3.10+ 标准库，无额外依赖、无引擎、无文件写入）：

```console
python skills/arc-mod-harness/examples/retarget_tqs_demo.py
```

父 T=`(10,-2,1)`、Q=`Rz(90°)`、S=`(2,3,0.5)`，给定目标 world T=`(4,6,4)`、
Q=`Rz(90°)Rx(90°)`、S=`(1,6,2)`。手算可得 local T=`(4,2,6)`、Q=`Rx(90°)`、
S=`(0.5,2,4)`：缩放后的位移 `(8,6,3)` 经 Z 轴 90° 旋转成为 `(-6,8,3)`，再加父 T。
脚本直接断言这些手算值，并用 world 旋转将 X/Y/Z 分别映到 Y/Z/X 的独立几何性质检查乘法顺序，
因此不只依赖一套正反函数互相抵消错误。

它还验证 6 个 synthetic raw 样本的三个 hold、原索引/时刻、近零隐藏 scale、非零但极小的
父 scale，以及零父 scale 下不同 local 得到同一 world 的非唯一性；不兼容目标会报错。
成功时输出 `synthetic; mathematical checks passed`。这仅演示已可表达 world T/Q/S 的局部求解，
不实现目标骨段/接触运输、负缩放矩阵分支、资源写入、压缩或真实游戏结果。
示例声明0.1秒含最后样本的1/60秒保持；真实资源的SeqLength独立读取，不能普遍按帧数/帧率推算。

## 私有工程索引：未打包的来源实现

以下入口相对于案例工程根目录，用于追溯步骤和输入/输出，**不属于安装后的 harness 命令**。
公开可运行内容仅为上面的合成 Python 文件。案例源码依赖私有资源、DCC 数值库及当前引擎构建，
复用时应实现同等合同，而不是复制固定角色路径、骨数、接地阈值或 ABI。

| 环节 | 私有相对入口 | 可追溯输出 |
|---|---|---|
| 状态覆盖 | `scripts/classify_ordinary_coverage_r193.py` | `work/ordinary_retarget_r193/ordinary_coverage.json` |
| 源动作与比例运输 | `work/ordinary_retarget_r193/inventory_export_sources.py`、`decode_sources.py`、`retarget_solver.py`、`solve_all_ordinary.py` | 来源哈希、raw T/Q/S、holds、目标 world、支撑日志 |
| UE local 输出 | `work/ordinary_retarget_r193/build_ue_tqs.py` | `ue_tqs_manifest.json`、骨名表、float32 P/Q/S payload、投影与往返误差 |
| 写入与独立重开 | `work/interactive_demo_r191/write_ue_actions.py`、`read_action_data.py`、`verify_action_data.py`、`verify_ue_raw_exact.py` | 新包、fresh read、帧/轨/绑定与误差 |
| 表与显示总装 | `work/interactive_demo_r191/build_action_routes.py`、`build_runtime.py`；后续 R195 的 `build_all_routes.py`、`build_display_sync.py`、`build_natural_routes.py` | 持久化主/自然表、active driver、完整材质与显隐 |
| 输入、时钟与摄影 | `work/interactive_demo_r191/runtime_clock_probe.py`、`test_transitions.py`、`encode_battle_videos.py`；R195 的 `run_test.py` | 实际引用/时间、Battle 视频、具体已查范围 |

## R213 补充：按原生消费者补齐选人与入场

**阶段说明：**上文 R193–R200 的显示组、driver、主/自然表及“尚未完成”均是当时的开发阶段
记录，保留用于解释制作过程，不能当作 R213 的当前资源架构或待办清单。R213 已制作并 Cook
本节的原路径修复；这里记录的是当前 retail 资源静态审计、开发 UE 原生组件测试和 cooked
数据验证，**不表示 R213 已获用户零售画面验收**。前文开发 Demo 的通过也不能代替这些检查。

本节来源的相对标识与 SHA-256 独立列在
[R213 原生消费者证据索引](gold-r213-native-consumer-evidence.json) RA01–RA16。
原报告、引擎适配器及游戏资源不随 harness 分发；索引本身不重现测量。

### 选人：有效的父组件不等于正确的骨骼来源

实际 `REDPawnCharaSelect` 调用 `SetupMesh`，但不调用 `SetupLinkBone`。头与身体都由原生
流程创建，头的 attach parent 此时是 Pawn 的 RootComponent。战斗/ADV 的挂接流程不同，
不能因为战斗中头部正常，就认定选人使用相同的组件父链。

R212 low-head 更新图只对 `GetAttachParent` 的结果做 `IsValid`，随后读取
`Gold_Head_Pivot_R211`。RootComponent 虽然有效，却没有该 socket；读取结果无法提供身体
头部枢轴，仍被送入头骨控制。真实原生选人设置的 R212 基线复现了约 **186.64711 cm** 的
头附件误差，而不是仅由截图推断原因。（RA03、RA05、RA07）

R213 在原路径 `Default/headlow/AB_headlow` 的 EventGraph 修正来源选择：

1. 先检查 attach parent 是否 `DoesSocketExist` 所需 Gold pivot；能提供 socket 时继续用
   真实挂接的组件，保留战斗中的 active-body/换体行为。
2. 同时经 `GetOwningActor` 取得原生 `REDPawn`，调用其 `GetMeshComponent("body")` 接口，
   作为父组件没有 socket 时的后备来源。本构建的 getter 是有执行引脚的 BlueprintCallable
   函数，必须连接执行链；仅连返回值
   可能被编译器裁掉。不要把固定 component 数组下标当作跨场景接口。
3. 六个原有身体 transform reader 都读取选定组件；有效标志改为再次检查所需 socket，
   不以 UObject 有效性代替骨骼能力检查。
4. 对现有头组件添加身体 tick prerequisite，让读到的身体姿态属于正确的求值顺序。
   保留原有 socket 空间、缓存与头附件控制，不靠重挂接、另造显示组件或播放待机掩盖错误。

独立读回确认 low-head AnimGraph 的 **70 个节点（其中 39 个 pose 节点）**、属性、pin
和连接都未改；原三个 Kawaii 节点保留。来源选择和 tick 依赖的改动位于 EventGraph。
原生选人 stand/ready 共 28 个采样，含 14 个未执行 SetupLinkBone 的实际场景和 14 个
已挂接对照，最大头附件误差 **0.00003052 cm**，无非有限骨变换。（RA04、RA06）

### 入场：900cs 存在不能证明整段已覆盖

必须联合检查**当前游戏脚本、AnimArray、AS 行和实际可见组件**，再决定需要替换哪些 clip。
只检索已制作文件或首段 `sly900cs` 会漏掉中间可见段。此次当前脚本静态核对发现：

| 实际分段 | 当前脚本消费者 |
|---|---|
| 1P 初始镜头 | `sly900cs` |
| 1P 中间可见段 | `sly_m903`，delay 92，再循环 `sly_m904` |
| 2P 中间可见段 | `sly_m903` 从 frame 20 开始，delay 72，再 `sly_m904`，最后 `sly_m905`；默认/服装分支的后续 delay 分别为 152/172 |
| 1P 最终台词段 | `sly901cs`，delay 156，再循环 `sly903cs` |
| 2P 最终台词段 | `sly902cs`，delay 156，再循环 `sly904cs` |

R212 已替换 m903–905 的头，却未替换仍可见的 body/coat 六资源。原生 ADV AnimArray 的
Body 已指向自己的 `AB_body`/`AS_body`，AS 行也已指向这六个正确的原路径；遗漏的是覆盖
资源，不能误写成动画表本身漏行。R213 补齐
`/Game/Adv/Avatar/SLY/Animation/{body,coat}/sly_m90{3,4,5}_{body,coat}01`，不改脚本或
重定向到另一个动画名。大括号只是文档中的六路径简写。（RA01、RA02、RA16）

同时，原生 ADV body AB 具有 **82 个 pose 节点、28 个 Slot 节点**，以及 layered blend、
ModifyBone 等原生控制。Default body AB 的 23 个 pose 节点/三个 Slot 不能替代这套结构。
修复在 ADV 原图末端增加已批准的 Gold pivot/tail 六个 pose 节点，成为 88 个；保留其
原父类、全部 Slot、分层控制与脚本输入。读回比较 290 个既有图节点的全部属性，只明确
归一化编译器分配的 LinkID/SourceLinkID，未发现语义属性变化。末端接入新节点的连接变化
单独记录，不能以忽略整张图差异来宣称保护成功。（RA01、RA04、RA09）

### 保持当前时钟、停帧和非目标动画

三个 body/coat 的实际 frame count 分别为 **92/80/100**，SequenceLength 的 float32
实际值为 **1.5333333015441895 / 1.3333333730697632 / 1.6666666269302368 秒**，均为
Step。Body 独立姿态数为 **24/21/26**，coat 为 **24/20/26**；m904 coat 的最后 frame 79
仍保持前姿，不能为凑统一模板而增加终点变化。准确时长独立读取，不能仅由帧数推算。

Body 沿用已批准的运输方法，以当前 cooked 姿态为源，保持 465 轨及现有 holds。Coat 的
批准 D 变换只写 root 平移/scale，保留 root Q 和 167 个非 root 骨的原 P/Q/S；再检查
Cook 后的实际 key 值和 frame table。最终全帧 body/coat 验证分别独立保存。（RA02、RA11、RA12）

保护清单另对 208 个已有动画作者资源逐文件比较：Default body 100/coat 94、选人 body
2/coat 2、旧 ADV body 5/coat 5。它们是资源文件数，既不是新的主表路由数，也不是 208 次
零售美术通过。原有 99 条普通/特殊主身体路由、批准的披风、脚本 timing 与特殊分支仍需
由整包差异检查保护，不能因修入场而重写所有动画或覆盖共享 Skeleton。（RA13、RA16）

### 可复用验证合同：原生组件、实际求值与发布字段

以下是需由具体引擎适配器实现的合同，不是 harness 已提供的可移植 UE 命令：

1. **真实消费者夹具。**创建实际 `REDPawnCharaSelect` / `REDPawnAdvAvatar`，让原生
   `SetupMesh` 读取原路径 MeshArray/AnimArray；按该场景实际行为调用 SetupLinkBone。
   旧开发 Demo 的 16 层显示 driver 可能修饰或绕开错误，不能替代这项检查。（RA07、RA08）
2. **原生时钟。**ADV 使用 `ChangeAnimeAdv`、`SetAnimeFramePosition` 和
   `UpdateRoot(false)` 应用位置，再求值 body/head。该构建的时间为 `frame/60 + .001`，
   限制在 `[1/60, sequence_length - 1/60]`；它是实查的 native endpoint 规则，不能向其他
   引擎推广。请求帧、序列时间、Step/hold 的实际姿态分别记录。（RA08、RA10）
3. **实际骨匹配。**按骨名读 component-space pose，检查 finite、body pivot/head anchor
   和缓存。R213 覆盖上述八个入场 clip 的 56 样本；再用直接 sequence compressed getter
   对照三个新增 body 的 21 姿态 × 465 骨，共 9,765 检查。最大差为 **0.0001163 cm /
   0.000030° / 7.81e-7 scale**，使用原定 `.005 cm / .05° / 1e-5` 门限。（RA06、RA10）
4. **原图对照与压缩分层。**同一批资源在原始 ADV AB 与扩展 AB 上比较 56 姿态，465 根
   旧骨差异仅为 float32 舍入量。m904 两个纽扣 helper 在编辑器中被保持为第一 key；这种
   行为已出现在 direct raw/compressed getter，原 ADV 图也相同，故不能归因于新增图。
   它符合微小旋转的 trivial-key 条件，但未追踪到确切加载函数；记录该限制。实际流到组件
   的严格门限保持不变，最终 Cook 保留目标 keys 的全帧检查另做，不能混为一项。（RA09–RA12）
5. **Cook 后字段所有者审计。**R212 Fatal 已证明 `CollisionLimitBase.Guid` 在编辑器中
   存在、Shipping 中不存在。可选 pin 重建时未显式隐藏它，会生成无效的成员赋值；编辑器
   编译/Cook 成功不足以保证发布版安全。作者图需显式关闭 editor-only 输入并重编译，保留
   Kawaii 功能。最终 staged 图的全部 Kismet 函数按实际 owner/member 解析，兼查静态节点
   默认值与 collider 字段，不能只扫描字符串 `Guid` 或仅查新增节点。此时快照扫 622 包，
   找到六个 Kawaii AB/14 节点，64 函数的 2,554 个字段引用全部解析，无缺失；该计数属于
   此快照。资源或插件布局变化后重新审计，不对最终 cooked 字节码打补丁。（RA14、RA15）

最后，最小交付清单只含八个原路径资源、16 个 cooked 伴随文件；不整拷 Cook 产生的
Skeleton、Mesh、材质或测试插件依赖。核哈希、包依赖及保护差异之后，仍需完整材质与真实
原生相机预览，并明确标记 **editor preview**。本节的 CPU 骨姿、Cook 和字段通过不等于
零售摄影、用户审美或完整运行通过；用户决定必须来自对相应成品的实际反馈。任何资源、
输入或图的修改都会使受影响的旧比较/验收失效，需重新关联版本与证据。（RA16）

### R213 补充：只修一个 Last Horizon 手部火焰挂点

这一补充来自另一条明确限定的反馈：只移动圈出的手部火焰，其他原特效位置暂时保留。
它不是全角色 FX 重定向许可。证据索引见
[gold-r213-fx-anchor-evidence.json](gold-r213-fx-anchor-evidence.json)；索引只含相对标识和
摘要，不分发游戏粒子、动画、私有引擎代码或机器路径，也不是可直接执行的移植工具。

**先找实际消费者，再找几何偏差。** 当前 BBS 的 `sly_ULT_01_exe` 在计数 127 切到
`sly501cs`，计数 197 创建 `SLY_501CS_handaura`；后者实际引用原路径
`/Game/Chara/SLY/Common/Effect/Particles/SLY_PTC02/PTC/sly_500_handaura`。
动作名的 501 和资源名的 500 是这条原生路由的事实，不能据数字不同另换资源。
计数 345 才创建 `_charge`，它是另一阶段，必须单独保护。native 原相机夹具在请求帧
723 首次记录前者、871 首次记录后者；记录点为 `core_tick_before_world`，不能把这个
探针时刻和截图请求帧当成同一个引擎求值阶段。（RF01、RF02）

此例 Attachment 为 Body / `handR`，位置随骨，旋转和缩放由原 BBS 独立控制；socket
本地偏移为零，骨为 `G_hand_R`，body mesh 没有覆盖 socket。原版同相机图中火焰包住
手掌；Gold 的 native 图中火焰悬在手掌上方。绑定矩阵给出 Gold 解剖手点相对原生手骨
的固定本地点；将它代入实际 component-space pose，得到约 **24.0449 cm** 的世界位移
差，方向随手旋转。不能用一个常量世界偏移推广到全部姿态，也不能只因 socket 有效就
认为挂点正确。（RF03、RF04、RF05）

**限定一个包和五个早段发射器。** 圈出画面中的两层火焰和三层同期热扭曲属于同一早段
呈现。只在这五个 emitter 追加位置补偿；同包六个后发 emitter、两个禁用 emitter，以及
独立 `_charge` 包保持原样。共享的 body / `handR` / Skeleton、BBS、判定和已冻结的八个
动画修复资源都不改。两条看似方便的路线被否决：修改全局 socket 会波及普通技能；该
引擎的 Bone/Socket Location 模块会覆盖粒子位置，并重置 mesh rotation，不能用于保持
原火焰形状的纯位置修正。（RF01、RF06、RF07）

**原生时钟和出生帧必须实测。** 此例所有相关 emitter 都是一次循环，但 `EmitterTime`
仍会在 duration 边界回绕；“Loops=1”不等于绝对时间。为在粒子存活期间使用连续时钟，
四个共享 Required 对象的 duration 改为 3.1 秒，两层火焰的 Rate 用精确阶跃限制在原来的
`[0,2)` 发射窗口；原 burst、RateScale、寿命与所有后发模块不变。Rate 曲线必须显式
`bCanBeBaked=false`：默认 RawDistribution 烘焙会重新等距采样并线性插值，把阶跃变成
短斜坡。位置曲线也关闭烘焙，保留实际 Step/hold，且用实际 PSC 缩放把世界差转换到粒子
本地差。该快照包含 186 个采样点。（RF06、RF08）

这改变了内部 LoopCount 重置和完成时刻，不能声称全部内部时钟字节不变。实测的原生
短步长、正常出生和 BBS 关联对象生命周期下，原发射计数、SpawnFraction 和粒子死亡
轨迹完全相同；首个 tick 就跨过两秒、发射一直被抑制到两秒之后等异常初始化并不等价。
这些限制必须随候选记录，不能把固定场景的通过写成任意 dt / 任意初始化保证。（RF08）

单个 Update-only Orbit 仍不合格：引擎先更新旧粒子再生成新粒子，新生首帧会留在旧
挂点。该实际火焰的新生 alpha 约 0.0333，不能说它完全不可见，也不能修改 alpha 掩盖。
本例使用四个现有原生 Orbit 模块，旋转与角速度都显式置零：

| 模块顺序 | 组合 | Spawn 取值 | Update 取值 | 作用 |
| --- | --- | --- | --- | --- |
| A | Add | `D_birth` | 不更新 | 保存出生差 |
| B | Scale | 不处理，初始零 | `(-1,-1,-1)` | 下一帧起抵消出生差 |
| C | Add | `D_birth` | `D_now` | 出生立即补位，之后追踪当前差 |
| D | Add | 不处理，初始零 | 不处理 | 保存最终 render payload 的上一帧位置 |

新生帧为 `D_birth * 0 + D_birth = D_birth`；后续帧为
`D_birth * -1 + (D_birth + D_now) = D_now`。最后的零模块保留 PreviousOffset，避免第三
模块在 Update 时用出生值覆盖历史位置。这里的代数依赖经核对的引擎 Reset / Spawn /
UpdateOrbitData 顺序；其他引擎版本需重新检查，不能直接照抄参数。（RF08、RF09）

**验证闭环和证据边界。** 私有观察器只读原生 REDPawn / PSC，没有创建替身、隐藏 body、
改变镜头或修改运行时姿态。读取内部 payload 前，先核对实际 Engine DLL 与 PDB 的
GUID/age，并由该 PDB 获得字段布局；不要把这次偏移硬编码成通用或零售 DLL 布局。
原版、Gold 修改前和修改后使用同一输入宏及原相机。此轮 2,252 个 emitter 行的原发射
计数、余数和年龄一致；1,494 个粒子样本的原 128 字节基础数据及全部旧模块 payload
逐字节一致，包含颜色、alpha、寿命、大小、速度和 mesh rotation。20 个新生样本同样
立即补位，最大世界分量误差 **4.185e-6 cm**，旧粒子的 PreviousOffset 误差为零。
全部 465 根 native 骨不变；另一 pawn 的四根附加 Kawaii 尾骨出现独立运行的微小浮点
差异，最大位置分量为 6.104e-5 cm，需如实区分资源变化与物理求值差异。（RF09、RF10）

最终检查按完整 outer 路径比较子对象，不能按重新保存后的 export 序号比较。保护旧
材质、纹理、灯光设置、burst、随机种子、旋转和所有后段发射器；核对 Cook 后非烘焙
分布对象确实保留，以及仅有既存外部依赖。本次交付只有上述原路径粒子的 `.uasset`
和 `.uexp`，共 255,450 字节，不夹带编辑器观察器、Skeleton、BBS 或 Cook 顺手产出的
依赖。仍保留上一节 R212 的 Fatal 字段规则；本例没有新增 Kismet 图或 runtime DLL，
不代表今后的图修改可跳过实际 Shipping owner/member 检查。（RF06、RF07、RF11、RF12）

以上相机图与动态数据均为**开发 UE 的实际原生消费者预览**。它们证明本候选对该拍摄
时段的定位和数据保护，不是零售用户已经验收，也没有授权移动任何其他特效。资源、
BBS 时钟、骨绑定或相机输入改变后，应使受影响的旧证据失效并重新关联。（RF05、RF12）

### R213 补充：同一招式还要覆盖受害者

上文八个选人/入场修复资源是当时范围的快照，并不证明所有角色身份均已覆盖。
Last Horizon 的攻击者 `sly501cs` 已适配，也不能证明被抓方的 `VS_SLY` 路由已适配。
这一例的实际 Gold 受害者仍读取原版 Slayer body/coat，配上已适配的 Gold head 后，
错误的身体变形会看似“飞头”。覆盖矩阵应加入 **招式 × 攻击者/受害者 × 场景/组件 ×
实际原路径**，逐条追踪消费者。独立证据索引见
[gold-r213-victim-consumer-evidence.json](gold-r213-victim-consumer-evidence.json)；只记录
相对标识和 SHA-256，不分发游戏资产或机器路径。（RV01、RV09）

**先区分挂点和变形。** 实测 body/head 的组件变换与 attachment link 原本已一致；
旧身体的解剖头部支点离 Gold 目标约 **30.0923 cm**，修正后误差为 **6.652e-5 cm**。
头部绑定的约 0.099 cm 固定残差前后均存在，不是新引入的脱落；这些数值仅描述支点，
不能直接称为皮肤缝隙。最小修复因此针对两条受害者原路径动画，而非移动头部挂点：

- `/Game/Chara/SLY/Costume01/Animation/VS_SLY/body/sly_sly500cs_body01`
- `/Game/Chara/SLY/Costume01/Animation/VS_SLY/coat/sly_sly500cs_coat01`

两条动画仍为 128 帧、float32 时长 2.133333444595337 秒、Step 插值。body 的姿态切换帧
`[0,7,32,127]` 与 coat 的 `[0,5,6,7,32,127]` 分别保留；不能用身体的 hold 表覆盖披风。
沿用已批准的 Gold 解算和 D 披风适配，仅披风 root P/S 有意改变；原非 root P/Q 和非空
S 保持。167 条空 S 经原生 codec 保存为常量单位缩放，求值等价，但不能声称空数组字节
不变。交付仅两资源、四个 Cook 伴随文件，不改 head 几何/表情、Skeleton/socket、AB/AS、
AnimArray、BBS 或其他动作，也不分发诊断 helper。（RV02、RV03、RV07、RV08）

**挂点重合不等于颈口接合。** native 帧 599/600/601 的 465 根 post-graph 骨通过
0.005 cm / 0.05 度 / 1e-5 缩放门限；最大误差分别为 0.000249717 cm / 0.0279723 度 /
4.77e-7。这三个样本共享一个 held source pose，全量 key/hold 另由源数据及 Cook 守卫
验证。进一步读取原 GPU 场景帧 600 的 `GetCPUSkinnedVertices`：body skin section 0
与 high-head skin section 1 的实际变形顶点，加上同一冻结 mesh 的 LOD0 索引/section
拓扑。拓扑由匹配 Engine PDB 的独立 NullRHI 只读运行取得，不能称作另一次 GPU 渲染。
以 0.0001 cm 位置焊接识别边界后，身体颈口全部 **57 点、57 边** 一一对应头部边界；
距离使用未经取整的原 CPU 坐标，最大 **0.0000305176 cm**、平均 **0.0000119467 cm**，
低于 0.001 cm 门限。这才是该受质疑姿态的几何接合证据，不能用 anchor 对齐替代。
它不证明材质、法线、阴影的视觉连续性，也不证明所有动画帧。（RV04、RV05）

原版对照、Gold 修改前后均保留同一原生相机图；前景特效与头发遮挡时，以上直接皮肤
数据补充画面判断。它们均为**开发 UE 的实际原生消费者预览**，原版对照也不是零售
截图。所有候选仍未获零售用户验收；脸部审美评审另行保留，不由骨姿或颈口数值代替。
输入变化后使受影响的比较失效，并重新绑定证据版本。（RV02、RV05、RV06）

### R213 补充：只有披风地影，先查网格 section

实际反馈为普通战斗仅有披风地面投影，身体与腿脚的影子缺失。证据见
[gold-r213-ground-shadow-evidence.json](gold-r213-ground-shadow-evidence.json)。先对照
原 Slayer 与 Gold 的实际 native 组件：`CastShadow`、`bCastDynamicShadow` 均为 True，
`BoundsScale` 同为 40000；只看组件开关无法解释差异。原 Slayer body 有两个投影
section、普通头有一个，原披风有一个；Gold body 的 14 个、普通头的 12 个 section
却全部 `bCastShadow=False`，披风保留原 section 的 True。（RS01）

根因在这套 ASW 导入器：它仅在材料槽名含小写 `shadow` 时开启 section 投影。重建
Gold 材料槽时没有该名称，导入得到的 False 一路进入实际资源。原角色另用
`M_CharaShadow` 的 shadow-only 分支：主 pass 丢弃像素、阴影 pass 保留。这解释了
原版结构，但不代表每个替换体都必须新增投影几何。此工具链的私有试验只开启已有
可见 section 的投影，即恢复完整地影，不需补影 actor、平面黑片或新运行时控制器。
**该引擎还把 section 投影标志接到 early depth pass 的跳过条件**，所以必须实拍检查
主 pass、遮挡与描边，不能仅凭通用 UE 属性名认定安全。（RS01、RS04）

最小身体改动为 `sly_body` 的 LOD0 section 0–13 和 `sly_bodynaked` 的 0–1 开启投影。
离线作者步骤沿用原生编辑器语义：改 imported section 的 `bCastShadow`，同步
`UserSectionsData`，执行 scoped `PostEditChange`，再保存、fresh load 与 Cook。
基于实际 DLL/PDB 匹配取得布局；私有观察/作者 helper 不随包分发。身体以此前修好的
13 个 UV3 族资源为输入，逐值保护位置、法线、切线、颜色、所有 UV、全部 **12 槽**
蒙皮权重、骨映射、绑定、材料、bounds、ASW outline/damage/LOD 表。不能拿最多只导出
四个权重的 glTF 结果代替完整蒙皮证明。（RS02、RS07）

原生加载/重建会初始化材质 UV-density 元数据，作者保存前恢复输入值；少量弃用的
cloth-LOD 作者字节也被原生重存规范化，报告列明，不能把作者文件称为字节不变。
更强的发布检查在 **完整 cooked SkeletalMesh export** 上进行：两条资源分别为
4,945,735 与 2,167,007 字节，差异恰为 **14＋2 处 0→1**。由实际 section 身份和
序列化顺序独立定位每个布尔值，将这 16 字节还原后，整段与各自既有 Cook 精确相同；
所有外部 imports 也相同。这既证明修到发布数据，也保护其余顶点与材质数据。（RS03）

头部必须由最终头部作者合入，不能交回试验时的旧脸覆盖新的表情/眼褶。此快照语义为
low/high section 0–9 的脸、头发和饰件，以及 10 的不透明镜框可以投影，**11 的透明
镜片保持 False**；young 只有 0–9。若最终 section 顺序变化，先重新按几何/材料解析。
这是需最终作者验证的 patch contract，不是已完成的最终三头验收。该开关试验也没有
解决独立的 SOL 前框可见性缺陷，不应合并两个问题的结论。（RS05）

同一原生相机保留原版、Gold 修改前后原图；另以原生输入走站立、前进、蹲姿，实际
消费者分别读 `sly000_body01`、`sly030_body01`、`sly010_body01`，影子随位置和姿态变化，
主角色与描边仍可见。只读探针在 `core_tick_before_world` 帧 349/379/419 记录，截图
请求为 350/380/420，不混淆两种时刻。自然身体的两个开关已由 fresh native load 和
完整 Cook 核实，但它在本轮普通动作中隐藏，不能声称已拍摄其特殊招式。（RS04）

此 lane 冻结交付仅两条身体原路径、四个 Cook 伴随文件；不整拷 Skeleton、材质或 Cook
顺带生成的依赖，也不改动作、BBS 或此前冻结动画。以上是**开发 UE 实际原生消费者
预览与数据守卫**，包括协调者看图在内都不等于零售用户验收。最终头部和整包视觉仍需
按对应版本验证；所有候选的零售用户接受状态保持待定。（RS04、RS06）
