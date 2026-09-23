# R218：补齐外部受招路由，修复 FD 着色器缓存，区分性能证据

本例延续 [R213 脸部结构线](gold-r213-linework-example.md)与[原生动画呈现](animation-presentation.md)方法，记录一次由具体游戏画面反馈驱动的局部修复。本文公开方法、接口和计数，不分发游戏资产、人物源文件、私有脚本或机器路径。以下脚本名和证据名表示制作过程中的职责与输出约定，复现者应在自己有权使用的项目中实现。

**状态：外部受招身体/披风、专用表情、FD 和身体 section 候选已完成技术验证、整包合并与安装核验；2026-09-23 用户对当前安装的 R218 暂时验收通过，反馈暂未发现问题。** 身体/披风以最终 `VICTIM_MOTION_DELIVERY` 为准，不使用第一轮 retarget-only 候选。性能工作从静态预算推进到同材质 section 合并与开发引擎 A/B/A；提交量下降与总帧时间改善分别判断，不把它写成“零售 30 FPS 根因已解决”或“所有硬件 60 FPS”。

## 1. 先把四个问题拆成有输入、有消费者的诊断

| 观察 | 首先核查的真实输入 | 不能直接推出的结论 |
| --- | --- | --- |
| 被 Faust/Potemkin 超杀时头身演出失常 | 攻击方脚本、受招者 `VS_*` AS、同钟 body/coat/head、最终包条目 | Default 动画已适配，所以外部演出也已适配 |
| Faust 近景脸不够可爱或失真 | 修好身体后的原始相机、完整表演阶段、专用头 clip 曲线 | 换共用脸、抹掉线条或给全段静态微笑 |
| FD 浮动手出现红黑块 | 粒子实际 mesh/材质、UV、贴图、配色表、MIC 继承及编译代码 | 手套贴图错了，全部强制白色即可 |
| 外部反馈约 30 FPS | 当前安装版本、同机帧时间、CPU/GPU/呈现与资源驻留 | Kawaii 一定太重，或包大等于显存同时占满 |

固定制作边界：只改已确认消费者的必要资源。共享脸部几何、法线、线条、墨镜、角色身份、既有口型/相机/单招披风、语音等接受过的内容继续绑定原版本。不同负责人只写自己的私有工程；最终整合按精确包路径和哈希选择输出。

## 2. 动画覆盖必须从当前游戏路由反推

### 2.1 不只枚举 Default，也不只枚举本角色脚本

从当前游戏包读取 `AnimArray → AnimSet → AnimSequence`，独立枚举 Default、选人、ADV、每个 `VS_*`。再从双方脚本、mesh set、显隐命令与强制受击 cell 找实际消费者。完整 package 路径是关联键；短动作名和资源总数都不够。

本例实际确认的专用路由包括：

| 攻击方触发 | 受招者实际组合 | 修复前的真实包覆盖 |
| --- | --- | --- |
| Faust `exciting → excitingexe`，632146H 命中 | `VS_FAU` 的 `sly_fau500cs_body01`、`coat01`、`headhigh01` | head 已替换；body/coat 两包缺失，回退 stock |
| Potemkin `HeavenlyPBuster → HeavenlyPBusterExe`，632146S 且目标在空中 | `VS_POT` 的 `sly_pot500cs_body01`、`coat01`、`headhigh01` | head 已替换；body/coat 两包缺失，回退 stock |
| 敌方 Slayer 的超杀执行状态 | `VS_SLY` 的独立组合 | 先前已单独修复；不能推广为另两组也完成 |

这些路径的组件 AS 复用 Default 相应 AB；“AB 相同”不等于“Sequence 使用 Default”。攻击方的 `ControlObject21 → PlayAnime xxx_*500cs → MeshSetChange` 能直接驱动受招者的专用组合。本轮看到 Faust 通用脚本里另有 501cs 条件分支，但 SLY 的对应 AS 只有 500cs，因此没有臆造 501cs 替换包。

高头也不是摄像机一靠近就自动启用：实际由 mesh set 和显隐命令选择。入场/结算、追击跳跃、自己超杀、高头转年轻头、被他人超杀都应独立列行。分层口型/头发输入不能当成额外的独立切头场景。Sharon 等原生配角组件应按原合同保留，不能把未替换配角计为 Gold 漏包。

本次审计的修复前快照：451 个 AS 组件入口；Body 112 条实际入口中替换 110 条，Coat 107 中替换 105 条；Low 105、High 24、Young 2 的基础头曲线已在包内。所谓 347 个 AnimSequence，是 110 个原路径 body、1 个专用自然体 body、105 个 coat、131 个 head，**不是 347 套完整且美术通过的动作**。

### 2.2 再查普通外部强制受击

继续读取攻击角色的 `SetEnemysCell` / `AtkDamageCell` 等命令，经过受招者注册 cell，再解析当前 COL 图名，落到实际动画。这个快照读取 96 个无版本后缀 BBS 包，91 个动作表完整解码；442 条外部强制 cell 命令中，440 条能在 SLY 注册中解析。

失败和未知必须保留：5 个包及部分共同函数没有完整解码，不能跳过未知字节后称全覆盖。一个外部投技能落到有低头、没有原版 body/coat AS 的特殊 cell，应列为“待确认原生保持/回退行为”，不能直接造新动画或算作已证明漏包。debug 无效入口也应与生产消费者分开。

### 2.3 覆盖矩阵与最终包核验

每行至少记录：

```text
consumer/state/input → mesh set + visibility → AS row → full package path
→ authored source/hash → selected Cook/hash → actual PAK entry/hash
→ data checks → native scene checks → retail/user acceptance
```

分别填写“已制作”“已打包”“原生抽样通过”及零售/用户验收状态与实际覆盖范围，不要压成一个绿色通过格。重新读取实际 PAK 的 entry 和所有 companion，验证索引/载荷身份后与最终清单比对；制作目录存在文件不能证明交付包里存在。

历史对比也要按这个规则：另一个角色替换的实际发布包从一开始已列入 FAU/POT 的 body/high 组合，并做过比例适配。保留原骨名、父链与 Skeleton 引用只是兼容接口选择，不代表无需适配。其历史记录也没有完整实机演出验收；“以前没人报告”不能成为正确性证据。

## 3. 电影大位移与分体头：先修结构，再看脸

### 3.1 保住原镜头的空间语义

普通动作按身高差做比例适配的算法不能直接缩放电影场景的长距离 root 平移。它可能移动整个受招者相对于攻击者、镜头、握点和道具的摆位；当相机仍在原坐标时，会出现镜头进胸、头离开画面或上下身不同步。

电影候选应逐轨区分：

- 解剖比例需要适配的局部姿态。
- 原生电影的 root 世界位移、旋转/缩放切换与镜头摆位。
- BODY 的挂接 carrier、HEAD 中真实解剖头节点、头部独立动画和普通 HeadLink。
- 披风/附属物的独立序列与组件父链。

同名 `G_Head_Attach` 不保证是同一个解剖位置。先读当前实际 ComponentSpace 与 ComponentToWorld；不要只将新旧 carrier 坐标强行相等。电影模式可由 body/highhead 各播独立同钟动画，此时再叠加普通 HeadLink 会重复位移。

### 3.2 有条件使用电影专用头部位置锚定

在确认 retarget 的真实解剖头点后，可用每帧源头点和适配后头点求统一平移：

```text
delta(t) = source_anatomical_head_world(t) - retargeted_anatomical_head_world(t)
candidate_body_root_translation(t) += delta(t)
```

该修正只作用于这一电影 clip 的全身摆位，将增量最终只写入 `G_body_root` 的局部平移。它不是共用骨架改造，也不是随意向镜头挪动头。全部 840 个 body 帧保护非 root 平移、全部旋转与缩放、raw 索引和秒数，与初次比例 retarget 逐值一致。修正最大值约为 Faust 46.59 cm、Potemkin 393.62 cm，说明大位移不能按普通身高比例处理。

披风重用已接受的贴合方法对修正后身体生成：只拟合 `G_coat_root` 的位置/缩放，保护 root 旋转和全部非 root 原位置/旋转/非空缩放轨。原空缩放数组按既有原生 codec 前提转为 unit scale。两组分别保持当前源的 389 帧/6.483333 秒和 451 帧/7.516667 秒；Cook 后仍逐帧核对 Step 停顿和 key schedule。原相机、BBS、AS、AB 与 mesh 不需因此重写。

**失败例：** 首个比例候选保住了普通 pelvis/脚跟逻辑，但近景相机进入胸/领口；单独看头曲线完全无法修复。改用真实解剖头点约束后，原镜头能看到脸，随后才开展表情 A/B。另一种错误是继续按“让截图更居中”逐镜加任意 root 偏移，会破坏攻击者/配角接触。局部裁切需要先对照原角色镜头，再决定是否真是回归；本轮保留原 camera。

### 3.3 同钟全组件与进出状态验证

在私有原生场景以真实输入触发，保留原 AB、生产材质与原 camera。采样可见的 body、low/high head、coat 的完整 CS 数组、组件世界变换、挂接父节点、当前 montage/sequence 与播放时间。序列中段正确还不够：入口、命中、镜头切换、白闪、跌落、起身、回待机都要有 trace 与原图。

最终四个 body/coat 原路径包、八个 cooked companion 已冻结。独立进程 fresh read 校验 465 条命名 body 轨；author、Cook 与实际场景副本按哈希绑定。最终原生样本结果如下：

| 检查 | Faust | Potemkin |
| --- | ---: | ---: |
| 电影 CS 采样组数 | 77 | 90 |
| 全 465 骨位置相对 cooked 预测的最大误差 | 0.0001411 cm | 0.0015917 cm |
| 实际渲染 active 骨旋转最大误差 | 0.0000547° | 0.0000652° |
| 实际头 carrier/link 最大间隙 | 0.0000307 cm | 0.0003820 cm |
| 显示头与 source 解剖摆位的差异 | 0.09921 cm | 0.10011 cm |

约 0.1 cm 的解剖点差是保留的 reference bind 关系，不等于皮肤开缝。另一项有界 CPU skin 检查在 Potemkin 原生第 600 帧读身体和高头皮肤，颈口 57 顶点/57 边一一匹配，最大间隙 0.00024444 cm；这是**一个姿态的真实表面检查**，没有宣称逐帧皮肤接缝测量。

167 个披风 root 样本的位置和缩放完全匹配，最大旋转误差约 0.00000242°。从实际 LOD0 读取 `ActiveBoneIndices` 后发现，六个原服饰骨未用于当前渲染，CS 旋转仍有最高约 0.09685° 差异；结果明文列出，没有谎称所有骨 Q 完全相等。解码预测也须复现原 Float96NoW 的标量重建顺序：半转附近用不同的浮点分组求和，会人为放大角误差。

采样先辨明 before-world 回调和实际 render/Step 时钟差别，记录实际匹配的 raw 索引，不把截图文件编号直接当动画 raw 帧。Faust 在原生 526–913 帧用 high，914 回 low075，随后 idle000；Potemkin 488–935 用 high，936 回 low060，经过恢复段到 1250 已回 idle000。覆盖的触发到恢复帧与 source 路由、时钟、slot 状态逐项比较。

这些是供给开发引擎的完整消费者预览；其 BBS 启动停顿和回调与当前零售版本有差异。当前零售 clip 时长/帧停顿另由 fresh extraction 与 Cook 检查证明。没有把供给 BBS 放进交付，也没有把开发引擎播放说成当前零售完整验证。

## 4. 表情先保演出阶段，再做局部可爱化

Faust 原表演包含倒置惊讶、闭眼痛感、切走、闭眼逞强笑、被握痛后的惊讶。先看完整原镜头时间线，不能把最后整段误读为同一种痛苦，也不能用待机微笑替代剧情。

本例最终只改一条 `VS_FAU/headhigh` 的浮点表情曲线。使用既有脸部 affine morph 基底调整双眼共同视线、瞳孔收缩、嘴唇开口与牙齿/舌头协调、最后的内眉痛感。没有修改共用 mesh、morph delta、法线、UV、细线、材质或墨镜，也没有碰 body/root/head attachment 骨轨。

第一次候选把闭眼逞强的笑压得太平；原生 A/B 后恢复这一阶段全部原曲线。最终 V2 的 389 帧、6.483333 秒与原 Step 时钟保持，0–55 和 272–335 帧逐值相同，291 组原重复姿态停顿和闭眼权重保持。不要在最后一帧强制中立：剧情表情应持续到原本的高头切走，再由原恢复链回到中立。

验证分成两层：

1. **结构/数据：** 10 项原属性和全部原骨骼 T/Q/S 键 guard 与既有基线一致；428 条非零曲线、12457 键的 36943 个压缩运行时采样误差为 0。既有细线/支撑面 1366 顶点、614 三角形逐帧无反翻或低于 1% 面积的坍缩；787 个共享 Mesh/Material 文件哈希不变。
2. **原生呈现：** 正式墨镜、生产材质、原 camera 下，同机位比较源角色、修好动作的旧脸和新脸；看完整短片及阶段原图。去墨镜图只用于眼神/眼线诊断，不能替代正式交付效果。实例 trace 确认高头专用序列退出，随后回低头受击、起身和低头待机。

数字通过不能证明角色身份或可爱程度；原生审图也不能代替用户实际零售验收。交付只包含一包的 author 文件与两个 cooked companion，测试 DLL、输入宏和辅助 Skeleton 不进入 PAK。

## 5. FD：作者图正确，最终着色器仍可能是旧代码

### 5.1 从浮动手的实际消费者追到独立静态祖先

先核查九个原生手势粒子、实际 mesh、生产 UV、五张 cooked 贴图和 17 色 PTC。FD 叶材质已有 `GoldAtlasEnabled=0`，但这个旁路没有进入已交付的 shader cache。

实际继承链为：

```text
FD leaf → BaseColor MIC → BaseBase MIC (owns a static shader map) → master Material
```

master 的 77 条 OutputHash、完整压缩代码、原长度、频率与加入旁路前的旧 Cook 一致。作者 pre/post-bypass 的 StateId 原本也相同：旧制作脚本只导入属性并保存，没有走原生材质重编译/更改通知。中间 BaseBase 又拥有独立静态 map，所以**只修 master 仍会漏掉真正消费者使用的旧缓存**。

扫描最终全部 266 个 MIC，检查 36 个 master 后代的 own-static 行为，本例只发现 BaseBase 这一独立静态祖先。不要按命名猜层级，也不要把所有后代都重新写一遍。

### 5.2 原生重编译、最小 Cook、精确代码绑定

可复用顺序：

1. 在私有 ordinary-copy 工程中，对原作者 master 调用原生 `UMaterialEditingLibrary::RecompileMaterial`，然后 SavePackage。
2. 分别 CookSinglePackage master 和 own-static 祖先到独立输出。新 master StateId 促使祖先的目标缓存更新；本例 MIC 作者文件无需改字节。
3. 原生读取目标平台 cache：shader type/VF/permutation 查找 → resource index → OutputHash → 最终 `.uexp` 内完整压缩代码、原长度与频率。
4. 逐条核对 master 和祖先两个 map。这里四类 VF（MeshParticle、GPUSkinDefault、MorphDefault、Local）× BasePass VS/PS × 两个 map，共 16 条精确绑定；各 map 仍为 77 entries。
5. 最终仅交两个包的四个 companion；把交付副本的哈希重新与独立审查匹配。Cook 依赖副产物不能全部自动合并。

保护图与参数时要展开实际数组/结构体字节；只比较摘要中的 `[long]` 会漏差异。本例 master 的 463 exports 图身份/连线/参数保持，仅原生生成的 CachedExpressionData、LightingGuid、StateId 改变；MIC cooked 属性（含 StaticParameters、Parent、纹理/向量/标量）保持。已有 Enabled=1 的 24 个 custom 分支及输入连线保持，主体继续使用该分支，FD 叶节点使用 0。

### 5.3 画面、缓存和场景覆盖要各自说清

私有 BTL 场景用 pre-bypass 原作者图正常编译，重现红黑浮手；恢复已有旁路图并正常编译，默认色恢复白手。前者是**旧作者图重现**，不能称作加载 Shipping shader 的实机截图。独立 WindowsNoEditor 代码绑定补充了“最终 Cook 真正是什么代码”的证据；Cooked-in-Editor 的 frozen layout 与 editor layout 不同，不能绕过布局限制把重新编译说成 Shipping 执行。

17 色站立和蹲伏要逐色触发真实消费者。持续按住 FD 跨颜色切换时，存活粒子可能保留上一色 MID；有效蹲伏轮次在每色材质准备完成后重新按 FD。白、黑、红等手套遵从原配色，没有把全部颜色改白。

空中 fixture 的一个重要负例：正确启用跳跃后确实看到空中角色与绿球，但受影响的九个浮动手模板在观察窗口内实际活动记录为 0。因此它只证明空中 FD 场景被检查，**不证明空中浮手 shader 消费者覆盖**。同理，两侧 body 材质切换不等于两侧都执行 FD；原生 BTL 材质池检查也不等于异步选人生命周期。

## 6. 性能：从静态预算到同材质 section 合并与 A/B/A

### 6.1 已知的静态事实

本节是修复前 R217 的静态快照。该基线是完整单 PAK，历史 runtime bridge 已停用；旧分体 demo 的同步/日志成本不能算到这一版本。

| 项目 | 静态证据 | 实际含义和边界 |
| --- | --- | --- |
| 普通 body+low 几何 | 76290 → 88463 三角形 | 使用当前 stock 与最终 Cook 重新 CPU 回导的计数；不含原披风等双方不变部分 |
| base+outline 提交估计 | 128206 → 176530 三角提交；11 → 51 section 提交 | 按实际 OutlineMaterialIndex 语义估计；不是 GPU DrawCalls/耗时实测，不含额外深度/阴影/粒子 pass |
| body 同材质 section | 前 13 个使用同一 base/outline pair | 后续据此制作 14→2 候选；先核骨索引表与上限、完整权重及所有顶点通道，再实测提交与帧时间 |
| 贴图库存 | 200 图，约 4.64 GB platform payload；199 图 NeverStream | 所有颜色/特效库存，不是同时驻留显存 |
| 单色硬引用闭包 | 默认色约 445.61 MiB；两个检查色各约 590.92 MiB 的 mod texture provider | 包含 parent 默认 atlas 与子色 override；不是 shader 实际采样或 resident bytes，也未计 stock texture provider |
| Kawaii 资产配置 | 6 AB / 14 节点；一套 body+head 为 4 节点、17 真实链骨、2 dummy | 资产库存不等于同时运行；无 world collision、风或运行中 settings 更新 |
| 曲线与父姿态 | ModifyCurve 列表、父身体 transform/collider 读取有源代码与 CDO 证据 | 是否求值、分支权重、pose prerequisite 等待需要动态测量 |

五个被比较的 cooked mesh 均为单 LOD。上述提交估计按本引擎 `OutlineMaterialIndex` 的实际规则计算：`<=-2` 隐藏、`-1` 仅 base、`>=0` 再加 outline。不可把这套规则未经核查套到其它引擎分支。

低头成本增加不代表所有镜头都增加：高头与自然体/年轻头组合的三角提交反而下降。Kawaii 的 `TargetFramerate=60` 是积分系数，不是一帧循环 60 次；也不是对完整 Skeleton 每根骨做模拟。源代码显示隐藏 Body 为维持挂接仍可能更新，其它头受显隐门控；自然体和 clone 应检查实际并发实例，不能假设 14 个资产节点一直全开，也不能因此擅自关闭 body 更新。

固定列表计数也不等于每帧 GPU 同时运行全部 morph。应分别测 ModifyCurve 的 UID 查找/读写、BlueprintUpdateAnimation、Kawaii 与并行姿态等待。截图工具的强制 60 Hz、离屏渲染、NoTextureStreaming、对象 dump 和 shader 预热均会改变测量环境；这些验证日志不是性能 benchmark。

### 6.2 从原始导入数据合并，不能只改构建结果

本次只处理既有 body mesh。前 13 个导入 section 虽然分别保留历史 FBX 材质编号，实际都走 base slot 0 / outline slot 1；tail 单独走另一组。13 组骨索引并集为 108，低于本分支既有 256 上限。原生 builder 先按 raw face material 分组，再按骨上限拆组，因此这里是可合并的历史材质分区，并非必须保留的骨上限分区。

可复现的作者流程：

1. 在 ordinary-copy 私有工程中保存已接受 author 与 cooked 输入身份；隔离 DDC、临时目录、插件与日志，并验证 engine/PDB 身份。用真实 native 构造/load/copy/destructor API 读取 raw import data，证明重复载入和深复制一致。先做一次无修改 Build，检查定义明确的几何字段仍一致。
2. **只把 raw face 和 wedge 的材质索引 0..12 映射为 0。** 保留 tail 的 raw index 13、原材质名称、所有点、wedge、源法线/切线、UV0..3、顶点色、影响权重和骨。
3. 调用原生 `SaveLODImportedData`，使 derived-data GUID 失效，再调用 native `Build`。同步源 section 设置；真实 ASW 映射变为 base `(0,2)`、outline `(1,3)`、damage `(0,0)`。两组 cast-shadow 均保持 true，recompute-tangent/disabled 均保持 false。
4. 保持**既有 cooked/live** 的材质 UV-density。旧 author 的零值在 PostLoad 时初始化；把这些初始化值写回是明确记录的作者规范化，不能谎称 author 元数据全字节未变。最终九条材质记录须与接受过的 cooked 值一致，不能合并后重置为零任其按新分区重新计算。
5. Native SavePackage → 新进程 reload → 正常 NullRHI WindowsNoEditor Cook。只选择原 body 包的 `.uasset/.uexp`；不要手改 cooked 字节，也不要合入自动 Cook 出来的全部依赖。

结果是 **14→2 section，46984 顶点、55549 三角形不变**。身体 base+outline 的潜在提交为 28→4；最终整帧 RHI draw 的变化仍须实测，不能简单将 24 乘人物数当所有 pass 的结果。

只改已经构建好的 Sections 不持久：缓存失效时会从 raw 源重建。通用 runtime mesh merge 也不自动保留本工程的原始导入源、ASW 特殊映射、morph 和材质合同，因此没有把它当替代捷径。

### 6.3 完整蒙皮、材质和隐式消费者保护

四权重 glTF/PSK 回导不能作为此合并的完整蒙皮证明。作者 soft vertex 有 **12 个 influence slot**，本次 cooked buffer 固定 **8 slot**；逐顶点独立扫描确认最高非零 slot 为 5，即最多六个非零影响，作者 slot 6..11 全为零。对两侧 cooked 的全部八槽按原顺序读取，用每 section 的真实 BoneMap 还原全局骨号；仅零权重槽的无意义骨号可归一化。

比较必须保留顶点重复次数及全部位置/法线/切线（含打包分量）、UV0..3、顶点色与有序骨号/权重对。三角形按真实解析的 base/outline/damage/shadow 路由比较**有向重复次数**：允许循环轮换，不能把反向绕序当相同。独立顺序解析 cooked 流的 skeleton、section、BoneMap、全部 index、顶点/skin/color 及可选分支，不用启发式扫描或导出器截断后的数据代替。

同时保护 reference bind、bounds、active/required bones、材质身份与 UV-density、precision/color 标志、cloth、imports/exports。该 body 没有 morph target 或 source morph 数组；头与表情 mesh 没变。保留 raw tail material 13 合法，是因为 scene proxy 先用真实 LODMaterialMap 解析到 slot 2；不能仅看 raw 13 就认定越界，也不能硬编码“最后 section 一定是 tail”。

还要检查合并对外部 section 索引、重算切线和细分曲面的影响。本例供给的 RED 源代码中未找到按 section 索引控制的调用，mesh set/粒子走命名 component/MID，但这不等于穷尽当前零售可执行文件与 Blueprint。275 个身体 adjacency patch 因重排不同；现用 master 无 tessellation，tail patch 不变。重复顶点组由 native builder 重建，各 section 不重算切线；实际 fixture 还须核对运行时未强制重算。未来启用 tessellation、强制切线重算或额外 section 控制时要重新验证。

以上数据等价也不能自动证明像素相同。顶点/三角顺序可能改变同深度重叠的覆盖顺序和 shader 浮点计算，应再做生产材质的原生图像对照，记录差异，而非仅凭面数相同就给美术通过。

### 6.4 A/B/A 实测：提交量下降不等于帧时间下降

实际机器为 Ryzen 9 9950X3D / RTX 5090（驱动 591.86）；使用 Win64 Development Editor 的 `-game` 原生 BTL、D3D11、2560×1440、离屏、NoVSync 普通双人待机。关闭私有项目的 fixed/smooth frame rate，设置 `t.MaxFPS 0`，不用 `-Deterministic` 或 `-FPS=60`。每轮预热 16000 帧、采样 6000 帧；日志中的无上限预热约 32.6–43.7 秒，捕获约 10.0–13.9 秒。使用原生缓冲 CSV profiler，采样窗口没有截图、stats HUD、逐帧对象 dump 或编译记录，没有关闭物理/AB。不要用另行开着诊断探针的画面捕获替代这个时间窗口。

两个基线的含义必须公开：author-stock 恢复供给的原始角色树和 LoadingMaterial，共 5144 文件，实际活动 body/head/coat 与六个对应 mesh/AB 包逐字节核对原始文件，stock AB 无 Kawaii 节点；它不是 Shipping cooked stock。Mod fixture 是 R214 全原生作者场景加 R218 FD 同图重编译，普通 body 与 R217 接受版相同，也不是完整 R217/R218 零售分支。**Mod 与合并候选的 21967 个 Content 文件中仅 body 作者文件改变**，其余材质、贴图、动作、AB、物理和表情曲线保持。

CSV 全局 `ActorCount/REDPawnPlayer=19` 不等于可见 19 人；单独的组件 census 锁定两位可见战斗角色、各自 mesh 与实际 AnimClass。资产目录里仍有其他 Review 文件也不代表 stock 正在使用它们，必须读活动消费者身份。

实际顺序为未合并 mod A1 → 合并候选 B → 恢复未合并 mod A2；对应输入 body 哈希、窗口、日志与 CSV 都保留。下面时间单位为毫秒，时间列用中位数，工作量列用每帧平均数：

| 指标 | 原始 author-stock | A1：14 sections | B：2 sections | A2：回滚 14 sections |
| --- | ---: | ---: | ---: | ---: |
| FrameTime 中位 | 1.5930 | 2.1867 | 2.1924 | 2.1592 |
| GameThreadTime 中位 | 1.5427 | 2.1235 | 2.1330 | 2.0905 |
| RenderThreadTime 中位 | 1.3864 | 1.6511 | 1.6045 | 1.6421 |
| GPUTime 中位 | 1.5316 | 1.9224 | 1.8750 | 1.8599 |
| RHI DrawCalls 平均 | 227.70 | 439.70 | 319.70 | 439.70 |
| RHI PrimitivesDrawn 平均 | 654673.38 | 1032767.38 | 1032767.38 | 1032767.38 |

对应 6000 行 CSV 逐行确认 **每帧少 120 次 RHI 提交，约 27.3%，primitive 差为 0**；回滚后提交数恢复，验证变化来自这个候选。RenderThread 中位观察到约 0.04 ms 的下降，但总帧中位没有改善，仍更接近 GameThread 耗时；GPU 差异落在 A/B/A 波动范围内。单个候选窗口不足以主张普遍速度收益。各线程/GPU 有重叠，时间不能相加；也不能把 draw 减少换算成 FPS 提升，或用强机结果否定弱显卡反馈。

单独的 1200 帧动画 stats 诊断记录到 Kawaii Eval 各打印上下文平均值之和约 0.032 ms。它是跨树上下文/线程的 inclusive 统计，精度仅三位小数，并且另开了仪表；不是关键路径帧时间，不与 child scope 重复相加，也不混入 A/B/A。Eval 包含模拟子项但不覆盖全部 AB 输入/更新；此分支没有独立 ModifyCurve scope，其成本仍未归因。这些数据不支持把未知零售 30 FPS 归因于 Kawaii。

正式记录冻结为 `TECHNICAL_VALIDATION_MANIFEST`，技术状态 `PASS_BOUNDED_NATIVE_DRAW_SUBMISSION_OPTIMIZATION`，其中帧时间/FPS 改善证明明确为 false；清单绑定输入 author、两个最终 cooked companion、独立语义审查、每轮 CSV/日志和图像证据。

额外原生读回确认实际 SceneProxy 每人 body 14→2，Color01 材质祖先、shadow 与组件材质槽无错配或 fallback，GT/RT 编译成功；另查 Color02 换色。`r.SkinCache.RecomputeTangents=2` 是按 section 标志触发，当前各 section 的重算标志为 false，`ForceRecomputeTangents=0`；不能把 mode 2 写成“全局关闭重算”。

原图复核包括两侧正式材质的 350、600 帧和 Color02 的 350 帧，未见衣物、手套、靴子、头/头发、墨镜、披风、尾巴、轮廓或投影明显丢失。但 350 帧左人近同姿、右披风不同，600 帧旧版左人摆手而候选待机，**不是严格同姿或逐像素一致对照**。外观结论结合完整 cooked 语义校验，只是普通场景有界接受，不能替代全招式或零售试玩。

复跑时先在空闲机器创建新的私有 fixture；每轮使用新 label，明确复制并核验旧/新 body，`sections` 参数本身不会安装候选。`run_benchmark` 输出窗口 SPEC、CSV 和日志，`summarize_benchmarks` 汇总分布，preview/对象读回与动画 stats 单独执行。一个初始无效 pilot 还暴露了本分支 `ExecMacro` 会对路径自动加前缀：宏目录包含它要求的字面 `Binaries` 后才执行成功。无效运行应标记并排除，不能因进程正常退出就算有测量。重新测量另建结果，保留本次冻结记录；不要覆盖既有 CSV。

### 6.5 为什么没有先删除或烘焙物理

这轮合并没有关闭物理、改 AB、降几何或降低贴图分辨率。静态链规模与总帧时间都不能单独把成本归到 Kawaii；应分别记录 Eval/Simulate/Init、ModifyCurve、BlueprintUpdateAnimation 和并行 pose 等待，再决定是否值得针对某项制作候选。

普通走停、转身、取消、瞬移、自然体/clone 切换的头发和尾巴具有历史状态。把一段固定动作的物理烘焙成骨动画，不能保证这些交互中的惯性和衔接；也不会自动消除脸曲线、父姿态读取、draw 或纹理成本。固定电影可以在确认收益后单独比较烘焙方案，但它不是未测瓶颈时的默认修复。

后续测量仍需固定版本、镜头、人物数和呈现方式，先热身，在无截图/dump 的窗口测 Frame/Game/Draw/GPU 分布、真实提交、纹理驻留与预算。普通 low、自然体/young、FD/clone 分开，记录每 mesh 的显隐、`bNoSkeletonUpdate`、实际链骨与本帧 eval 次数。只有相应证据支持时才继续做局部纹理或物理候选；不要为外部未复现的 30 FPS 反馈擅自改用户全局设置。

## 7. 脚本职责、输入输出与交付边界

| 职责示例 | 输入 | 必须产出的证据 |
| --- | --- | --- |
| `audit_routes` / `audit_functions` | 当前 PAK、AS/数组、完整有界脚本 | 当前数据身份、真实消费者、未解码边界 |
| `audit_external_damage` / `audit_col_and_compare` | 外部强制 cell、受招注册、COL、供给源与当前脚本 | resolved/unresolved 矩阵、源/零售差异 |
| `build_coverage` | 路由矩阵、作者清单、实际包条目 | 按 package 区分制作/打包/原生/零售状态 |
| motion decode/retarget/anchor/coat writer | 真实 source clip、绑定合同、原始时钟 | 受保护轨道差异、同钟世界姿态、原生 fresh read、Cook 清单 |
| face candidate/check/native writer | 已接受共用脸基底、原表情阶段、专用 clip | 曲线与骨轨 guard、细线检查、原相机 A/B、恢复中立 |
| `recompile_root` / `cook_root` | 已正确的作者图和实际静态继承链 | 原生编译输出、图/参数保护、最小候选 companions |
| shader proof / bind / independent review | target cache、最终 cooked 代码及交付副本 | 精确 lookup→resource→代码绑定，交付哈希绑定 |
| static resource / mesh / curve / physics budget | 当前最终 Cook、stock、相关源代码 | 可复查计数、假说与测量计划，不生成 FPS 结论 |
| native capture / pose trace / freeze delivery | 实际输入、原 camera、冻结候选 | 生产材质原图、完整阶段短片、active consumer trace、精确包清单 |

所有作者写入、Saved/Intermediate、日志、DDC、临时编译和宏均隔离到私有目录。只终止本任务启动的进程。发布集合排除测试插件、DLL、输入控制、私有模型与额外 Cook 依赖。

最终整合顺序是：按 manifest 合并指定包 → 从新 PAK 重新读取所有 companion 并验证哈希 → 核查受保护内容差异 → 按授权安装 → 用户实际试玩。原生预览、压缩采样、编译代码绑定、PAK 内容验证和用户接受是不同证据层级，任何一层的 PASS 都不能替代后续层级。

## 8. 完整包与安装核验

后续整合与安装结果记录于私有相对来源 `retail_deploy_r218/INSTALLATION_RESULT.json`；公开仓库不复制包含机器路径的原始收据或安装资产。

- 最终单 PAK 为 1,329 包、2,659 文件，全量提取哈希通过。相对 R217，8 个 cooked companion 改变、8 个新增，其余 2,643 文件保持；其中 v5 音频 796 文件保持一致。
- 变更仅为 Faust 专用头动画、身体 section 合并、材质 master 与独立静态祖先，以及新增 Faust/Potemkin 身体和披风动画。没有新增战斗判定数据覆盖或恢复运行时装配 bridge。
- 游戏目录和管理器库中的 PAK/SIG 安装副本已核对哈希。R217 旧安装四文件备份至 Paks 外，认可版归档完整保留；46 个无关 PAK/SIG 的大小与修改时间、无关管理器配置保持。
- 成品 PAK SHA256 为 `6a10ea30ed61760d711e2db951bcfd4b4a1bd6d16f1244d5a5ee03c9e61e1086`；完整 ZIP SHA256 为 `0188f5083f95309895f1a1671cf2048be3a0602883aa458d7cf30249225df0d4`；私有安装收据 SHA256 为 `74aecdf4f86e5e39627fb57d142a7393b99660830ee1d6e0833c7da12e6e380e`。

此前安装核验本身没有提供零售运行、用户美术认可或 FPS 改善证据。2026-09-23 后续用户反馈确认当前安装版在本轮暂时验收通过、暂未发现问题；独立记录于私有相对来源 `retail_deploy_r218/USER_PROVISIONAL_ACCEPTANCE_20260923.json`，绑定上述 PAK/ZIP 身份。历史安装收据和技术 manifest 保持原样。

本轮用户反馈未附逐招式、逐配色或量化帧时间清单，因此不扩写为所有组合或硬件通过。上述原生场景、画面裁切、空中 FD 消费者覆盖与性能测量的边界继续保留。
