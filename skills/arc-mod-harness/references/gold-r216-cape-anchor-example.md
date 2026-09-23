# R216：按动作胸锚修正 2HS 披风位置，保留原停帧与展开形状

**记录状态：2026-09-22，R216 A 已完成私有原生画面预检查、独立重开读回与正常 Cook；用户零售验收仍为 `false`。**本页以 `FINAL_EVIDENCE.json` 的 `PASS_TECHNICAL_NATIVE_VISUAL_AND_COOK_HANDOFF` 为结论上限，不把制作交接写成用户认可或最终安装完成。R215 的入场嘴部 V3 与相机 B 已获用户认可；本次从该基线继续，只处理用户随后指出的 2HS 披风偏前、上部中心不贴肩背问题。

本例接续 [R215 局部修正](gold-r215-entry-camera-example.md)。时钟与消费者原则见 [动画呈现](animation-presentation.md)，保护结论的边界见 [判定数据与动画间接路径](gold-r214-gameplay-preservation-example.md)。以下 `E` 表示私有项目的相对证据根 `work/cape_2hs_r216`，`A=E/animation`。公开仓库只记录相对标识、脚本角色与摘要，不包含游戏资产、私有工具、截图或机器路径。

## 1. 先从当前零售路由确定唯一资源

不要根据招式名猜动画编号。只读审计把缓存条目与当前主 PAK 重新比较，并验证 PAK 索引和条目摘要，再沿下面的真实消费者链定位：

| 层级 | 本例查到的结果 |
| --- | --- |
| 输入与 BBS state | 内部 `D` 对应 HS；2HS 为 `NmlAtk2D` |
| 当前 BBS cell | `sly233_00` 至 `sly233_16`，共 17 个 |
| 当前 COL image / 动画名 | 同名 `sly233_XX.jpg`，动画名 `sly233` |
| Mesh / AnimSet 选择 | `MeshArray` 的 `Coat` 为 index 4、默认显示、`AnimSetName=Coat`；Default `AnimArray` 的 `Coat` 为 index 2，使用原 `AB_coat` / `AS_coat` |
| AnimSet 唯一匹配 | `AS_coat.AnimSeqArray` 中 `Name=sly233` |
| 修改包 | `/Game/Chara/SLY/Costume01/Animation/Default/coat/sly233_coat01` |

R215 没有覆盖对应的 body / headlow / coat AnimSet，仍通过原 AnimSet 解析原路径。无需修改 BBS、COL 或 AnimSet 来让新动画生效。当前 `NmlAtk2D` 块的 SHA-256 为 `621bbceac4b42db06db0f4d6515d140cba26e0a20cd6e670576707cf89fc73cc`；完整路由和作者来源分别保存在 `route_audit/ROUTE_EVIDENCE.json` 与 `NATIVE_CONTAINER_ROUTE.json`。

**这不是按招式隔离的运行时补偿。**完整当前 BBS/SLYEF 消费者扫描发现，`3on3_r` 的一个段落共用全部 17 个 cell、相同时长和此 AnimSequence。修改会同时作用于该共享段。`NmlAtk2D_Buff` 在这里是统计标签，不能据此另猜一条 buff 动画。当前多个版本的 BBS 时长表一致，但这不替代对共享模式的实际回放；本轮没有单独播放 `3on3_r` 团队模式生命周期。

## 2. 诊断：全局 D 适配没有补上动作期的胸锚差

R215 继承已认可的完整披风 D 适配：根缩放为原来的 0.90，下移 10 cm，并沿 Gold 肩部右方向移 3 cm。直接解码当前零售与 R215 的目标披风，差异只有 track 0 的 T/S；根旋转 Q 与 167 条非根轨道的值、采样表均保持原值。该基线身份由 `R215_COAT_BASELINE_CHANGED_CHANNELS.json` 固定，不能把旧草稿或另一作者副本当输入。

这套全局比例与偏移保留了原 Slayer 披风形状，但 Gold 身体已经重定向。2HS 展开时，Gold 的 `G_chest` 与当前零售 Slayer 同时刻胸锚出现明显位移。原 Slayer 胸锚与原披风 `G_coat_cns` 在 86 个样本内几乎重合，最大距离约 `0.000031704 cm`；因此应先测量动作期的锚点差，再决定是否需要改变披风局部形状。

`analyze.py` 从当前 Cooked 的 Step 采样表求 body/coat 姿态，结合各自骨层级与 REST 得到共同空间坐标，输出 `current_pose.npz` / `POSE_DIAGNOSIS.json`。代表胸锚差如下，单位为 cm：

| raw 样本 | GoldChest − currentSLYChest，分析空间 `(UE X, -UE Y, UE Z)` |
| --- | --- |
| 1 | `(4.4696, -17.7066, -6.0941)` |
| 31 | `(16.9705, 55.7598, 7.2921)` |
| 36 | `(23.5355, 57.3140, 4.6858)` |
| 81 | `(-10.2677, 3.2782, 7.4866)` |

起手、展开和恢复的差值不同，再叠加一个静态整体偏移不足以匹配动作。这里的数值是骨锚在共同坐标系内的位移，不是屏幕像素，也不能把分析空间的 Y 符号直接写入 UE 平移。

随后用原版 Slayer、R215 Gold 和候选 A 的真实原生角色/材质/游戏镜头核对同一停帧。代表证据 `A/evidence/source_baseline_candidate_375_native_crop.png` 显示：原版披风中心位于肩背；R215 Gold 的上部跨到口鼻前；候选将中心移回肩背关系。该观察支持本次根平移方案，不证明所有姿态都无穿插，也不是通过改变相机或图片位置得到的修复。

## 3. 修复：仅给 clip 根 T 加入按 hold 分组的胸部差

以 SHA-256 为 `04b1535459fe56d590b552d1eab544b59bc64178b39b8b76408f9c3ffdd9ceb7` 的 R215 作者包为固定输入。本轮只有候选 A，公式为：

```text
delta(i) = GoldChest(i) - currentRetailSlayerChest(i)
T_candidate(i) = T_R215(i) + envelope(i) * delta_UE_component(i)
```

`build_candidate.py` 把分析空间位移转换回 UE 组件空间：`(x, y, z) -> (x, -y, z)`，按 cm 加到既有 `G_coat_root` 平移并写为 float32。这里的根是独立披风根，平移作用于整件披风；不改变身体根轨迹。原 D 比例和原披风的局部形状继续保留。

envelope 是限制作用时段的权重。**按原有 hold 分组取常值，不能在同一停帧内逐样本渐变。**下面 raw 索引均从 0 起计：

| 原 raw 区间 | 权重 |
| --- | --- |
| 0–24 | 0 |
| 25–29 | 0.5 |
| 30–74 | 1 |
| 75–79 | 0.5 |
| 80–85 | 0 |

最终 55 个 raw 样本发生平移，最大位移约 `62.1351 cm`。raw 31 写入 UE 的完整增量为约 `(16.9705, -55.7598, 7.2921) cm`，与上一节分析空间的 Y 符号相反。完整 86 行增量、原作者摘要和权重在 `CANDIDATE_POLICY.json`；其早期 `FIRST_CANDIDATE_PENDING_NATIVE_REVIEW` 状态保留为生成记录，后续完成状态以 `FINAL_EVIDENCE.json` 为准。

原生 writer 使用 `UAnimSequence::AddNewRawTrack` 同名替换既有 `G_coat_root`，轨道索引仍为 0，再正常保存作者资产。保护白名单之外的内容：

- 168 条轨道的全部旋转 Q / 缩放 S；167 条非根轨道的全部 T/Q/S。
- 轨名、骨映射、原 key table、首尾 hold、Step、帧数和长度，以及 fresh guard 覆盖的其他元数据。
- Mesh、REST、bind、权重、材质，body/head、其他披风动画、FX、相机、R215 嘴部 V3 和相机 B。
- BBS、COL、SLYEF、攻击数据、通知和游戏事件时钟。

保护检查证明这次动画交付的具体改动边界，不扩展为所有动画/socket 间接玩法路径都已穷尽验证。

## 4. 三种时钟必须分开

| 时钟 | 本例事实 | 使用规则 |
| --- | --- | --- |
| AnimSequence raw / hold | 86 raw，`SequenceLength=1.4333332777023315`，Step；姿态变化点 `0,5,…,85` | 这些变化点用于限定 envelope 与保存原停帧 |
| COL cell 选择的源样本 | `CellFrame2Sec` 使用 `raw=5*cell+1`，17 个实际采样为 `1,6,…,81` | cell 1 应取 raw 6，不能取“动作已过的第几帧” |
| BBS 持续时间 | cell 00–07 各 2 帧，08 为 3 帧，09–16 各 4 帧；无暂停合计 51 帧 | 不把 86 raw 重采样或拉伸成 51 帧；实际游戏还会命中暂停 |

原 BBS 在 cell 06（动作第 13 帧开始）有 `CreateObject SLY_233_attack` / `ReAttack`，cell 07（第 15 帧开始）调用 `cmn_AttackEnd`。这里只记录命令位置；不能单凭它们给出完整攻击框或有效命中帧解释。空间修正没有移动这些命令。

截图标签是第四种编号。有效原版、候选 1P 和镜像 trace 均确认 body/coat 在 core 356–421 使用 `sly233`，各有 66 个同步样本、两者时间差为 0。66 个观测样本包含命中暂停，不表示脚本动作被改成 66 帧。

主要的 PNG 375 对照位于持续多个 tick 的 `0.51666671 s` 停帧内。原版报告将宏标签 N 对应的截图与 core N+2 配对，这是根据引擎执行顺序作出的推断，**不是 GPU frame-id 的直接测量**。同编号 PNG 不能自动证明同姿；本例依赖消费者、实际动画时间及稳定 hold 的交叉核对，切换边界仍需更谨慎。

## 5. 从输入到交付的可复用流程

下列为私有脚本角色与产物，不是公共仓库中可直接执行的游戏工具：

| 相对入口 / 角色 | 输入 → 输出与验证 |
| --- | --- |
| `E/route_audit/audit_route.py` | 当前主 PAK、缓存、R215 来源 → 真实 state/cell/AnimSet/原路径、共享消费者、时钟及基线通道差异 |
| `A/setup.py` | 冻结 R215 作者与完整角色提供者 → 隔离私有场景、`ISOLATION.json`；所有可写目录与源隔离 |
| `A/analyze.py` | 当前零售与 Gold 的 body/coat、骨层级、REST → 同时钟世界姿态与胸锚差 |
| `A/build_candidate.py` | 精确 R215 baseline、胸锚差、原 hold → `candidate_root.bin` / `CANDIDATE_POLICY.json`；权重变化点必须属于原 hold 边界 |
| `A/native_writer.py` | 单根 payload → 原生保存；独立新进程重开并导出 raw、轨名与保护字段 |
| `A/verify_and_cook.py` | 保存前/独立读回数据 → 精确保护断言；正常 Cook → 解码 Cooked 通道差异、`NATIVE_COOK_GUARD.json` |
| `A/run_preview.py`、镜像 trace 角色 | 同版完整材质、角色和游戏镜头 → 基线/候选/连续/镜像 PNG、实际 body/coat 时间 |
| `A/source_reference/run_source.py` / `summarize.py` | 原版 Slayer 私有场景、有效输入 → 原版 13 图、原始来源摘要、`SOURCE_COMPARISON.json` |
| `A/make_evidence.py` / `finalize.py` | 有效图、trace、Cook guard → 比较图、正常时序视频、最终证据与单包交付清单 |

Fresh reload 的轨名/映射、保护属性、168 条 Q/S 和 167 条非根轨道均精确保留。正常 Cook 后重新解码，与 R215 比较，唯一改变的压缩通道为 `[[0,"T"]]`；根平移 key table 两侧均为 `0,5,…,85`，86 raw / 长度 / Step 也一致。这是作者读回及 Cooked 数据检查，不能改称 Shipping 零售运行验证。

有效原生画面包括基线和 A 各 13 张、候选连续 146 张、镜像 27 张，分辨率均为 2560×1440；连续视频为 60 fps、约 2.433 s。镜像证据来自实际镜像消费者与输入转发的私有测试，不能用图片水平翻转代替。原版有效目录仅为 `source_reference/captures/source_2hs_1p_valid`，状态为 `PASS_NATIVE_ORIGINAL_SLY_2HS_BODY_COAT_CAPTURE`。它记录原版作者身份及原生播放，不是用户游戏的零售截图。

最终 `DELIVERY_MANIFEST.json` 只交付该原路径的一份 author `.uasset` 和两份 Cooked companions；root 依据清单合入新完整包，不整拷私有场景或运行时测试插件。交付文件摘要如下：

| 文件角色 | SHA-256 |
| --- | --- |
| author `.uasset` | `278a94c4befdb388d9d05703b5d98db8a6dc08541925d3e216f3d19b16ba3b25` |
| Cooked `.uasset` | `b3e41918b20c36e6060beb15e5c16a490576f672e44e4b4306949b8d98c93df5` |
| Cooked `.uexp` | `a37bf297144bb8412d686b775cd0198cd1906ed72539312340b7bd4c0ba26b23` |

## 6. 失败输入和保护断言必须影响证据资格

一次草稿把 envelope 起点误放在 raw 26/31，破坏了 25/30 的原 hold 边界；断言报错后，同一 shell 的后续 writer 仍曾执行。该私有草稿在任何预览/Cook 前从精确 R215 baseline 恢复，最终读回和 Cook 均来自修正后的边界。可复用教训是：保护断言失败必须阻止下游写入，恢复后重新生成证明，不能只修改报告状态。

另有角色配置或输入采样失败：镜像测试曾得到双 SOL，另一次只有 Gold 待机；原版首轮错误字符码也没有进入 `sly233`。这些输出明确标为 `INVALID_EVIDENCE`，不纳入 2HS 对照。必须先在 trace 中确认目标角色、目标片段和实际时间，再讨论图像差异；“有截图”“输入命令已发送”都不等于目标动作成功。有效镜像只使用 `candidate_mirror_reverse`，有效原版只使用 `source_2hs_1p_valid`。

## 7. 证据摘要与尚未完成的验收

本页的摘要固定所读版本；私有 JSON 可能含本地路径，不在公共仓库重新分发。证据或交付输入一旦变化，旧技术结论需要重新核对，用户决定也不能自动沿用。

| 相对证据 ID | SHA-256 |
| --- | --- |
| `E/route_audit/ROUTE_EVIDENCE.json` | `d0ce796c0f4668855054fea67de024e77e8175c6d9a229b25d566c91f9c2aa55` |
| `E/route_audit/NATIVE_CONTAINER_ROUTE.json` | `280590314090f58673bfcde66ccf962d1f70cd11727b01e87bc6e95598102ad4` |
| `E/route_audit/R215_COAT_BASELINE_CHANGED_CHANNELS.json` | `f86ac6345a9e5709cb2f1dac6f534b0933d1594246abad209968d569220aa888` |
| `A/POSE_DIAGNOSIS.json` | `196c0f705357f67bcf17b93fc4513f107742621c33627ae38e2e71c958f5bd97` |
| `A/CANDIDATE_POLICY.json` | `ffdda5cf122f81487fa69227c380c8571882b3e5d38c22d7468d346d147886d9` |
| `A/NATIVE_COOK_GUARD.json` | `c03a58aa0d63f4cef54d7ef43d510e0c1dff476de7bddc1f44b828b6994da611` |
| `A/source_reference/captures/source_2hs_1p_valid/SOURCE_COMPARISON.json` | `411719457d1f50b838f704c73282ea7ab8ce0662bcce6339c2de6f7ab7274d1d` |
| `A/FINAL_EVIDENCE.json` | `b7718a06c96e17661b73edb48772043babd4d79b1490712752c86812f674901c` |
| `A/DELIVERY_MANIFEST.json` | `10a00ae371b9deb2731482b64423236a04b6e34200bcaf66948ae80d3c6344ca` |

已证明的是：当前真实路由、动作期胸锚差、仅根平移的作者与 Cooked 改动范围、原停帧保护，以及限定场景中的原生视觉改善。仍需由完整交付流程和用户补齐 R216 零售外观验收；`3on3_r` 共享段的独立生命周期也未验证。本页没有记录 R216 的人类批准，不因 R215 已获认可而继承该决定。

## 8. 后续完整打包与安装记录

本例随后已合入认可 R215 的完整基线：1328 个资产、2657 个 Cooked 文件；只替换
`sly233_coat01` 的两份 companions，其他2655文件逐字节保持，无新增资源。完整类型依赖、
PAK Test/List、解包后的每文件哈希均通过。最终 PAK SHA-256 为
`82a1285cf7d9066dea61a07591d6af5c9428e0d48726f790adf3a2e106418f5b`。

用户确认退出游戏和管理器后，集成方再次检查进程，精确备份并退役登记的4份旧版PAK/SIG，
安装新完整包，再核对游戏/管理器文件与Config。46个无关PAK/SIG的大小和时间、无关管理器
设置保持；认可R215原件及永久归档不变。独立ZIP不依赖作者工具，不锁定游戏EXE/build。
安装证据ID为 `work/retail_deploy_r216/INSTALLATION_RESULT.json`。这补齐交付验证，
**仍不代表用户已认可R216外观**；共享团队模式生命周期也未因此升级为已实测。
