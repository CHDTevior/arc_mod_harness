# R215：保留认可版本，局部调整入场嘴角与近景相机

**最新状态：2026-09-22，用户已明确接受 R215 的 V3 入场嘴部与相机 B 两项改动，完整 R215 已独立永久归档。**用户决定为“不错，这两个改动都接受”，依据见第 7 节。V3 相对 R214 下收 6 mm，显式取代用户认为仍上翘的 2.2 mm V2；root 的制作选择与安装核验已由这次用户决定补齐。此前认可的 R214 仍永久保留。用户随后指出 2HS 披风偏前、中心位置不合适，作为 R216 的独立修正范围；这不撤销嘴部 V3 / 相机 B 的认可，也不表示全部动作已无缺陷。

本案接续 [R214 配色与 shader 修复](gold-r214-color-transition-example.md)。通用的时钟与消费者检查见 [动画呈现](animation-presentation.md)，交付层级见 [Cook 与安装](cook-install-example.md)。以下证据均为私有项目的相对标识，公开仓库不包含资产、捕获图片、作者工具或机器路径。

## 1. 先固定认可基线和小改范围

R214 的 ZIP、PAK、原安装器及其 manifest、说明和卸载/迁移脚本均已另存认可归档；原发布目录与作者资源也保留。批准 PAK 的 SHA-256 为 `eb5a40ed828253f411ef5c8d8a86825200543eabdd274e5655c157270c0551da`，ZIP 为 `0793aba961567ab522d0f2d35ee6ad5921fb7a00728df400dd5144bcf90356c4`。后续候选使用新版本和新输出目录。

R215 两项改动获认可后，其完整 ZIP、PAK、原安装器与发布文件另存于 `releases/approved/GoldShip_R215_UserApproved_20260922`，原发布和作者资源保持不变；PAK / ZIP 身份与第 6 节一致。该归档独立于 R214 认可归档，后续 2HS 修正从已认可的 R215 继续，不覆盖这两个保留版本。

| 本次反馈 | 受限改动 | 保持原样 |
| --- | --- | --- |
| 最终入场说话的闭口嘴角抬得稍高 | V2 的 2.2 mm 经用户反馈仍不足；V3 对同一组根表情与首闭口 liptype 控制，相对 R214 总计下收 6 mm，已由 root 选作制作方案 | 张口样本、其他表情曲线、公共头部几何与 morph、法线、眼鼻线、材质和骨轨 |
| Last Horizon 年轻头近景略挤 | 一个 CameraAnim 的指定位置键窗口，下移 4 cm、沿镜头视轴后退 8 cm | 旋转、FOV、光轨、其他位置键、切镜时钟、人物动作及 FX |

这两条制作分支没有增加 BBS/COL 或判定数据改动，也没有重做身体动作、语音、物理或 R214 配色修复。结论来自受限交付清单与保护检查；它不等于重新证明所有动画/socket 对战斗的间接影响。该区别见 [判定数据与动画间接路径](gold-r214-gameplay-preservation-example.md)。

## 2. 入场闭口：根表情和 liptype 必须一起核对

本节先保留 **V2 的技术实现和失败探索**，再列独立 V3。消费者联动、时钟保护与镜像验证方法继续使用；2.2 mm 幅度并非已获认可的视觉方案。

实际目标是 `sly903cs_headhigh01` / 镜像 `sly904cs_headhigh01` 的最终入场根表情，以及 `sly_liptype00_headhigh01` / `sly_liptype01_headhigh01`。名称相近的 m903/m904/m905 属于更早的过场。本页的“根表情”指表情播放消费者，不是移动角色的 RootMotion。

首轮仅修根表情时，原生相邻帧 1355/1356 短暂使用闭口 liptype，嘴角返回旧值。V2 因此同步修改对应 liptype 的首个闭口 hold，而不改变任何张口采样。只看闭口代表帧，会漏掉这个消费者切换。

| 消费者 | 仅改的曲线 | 时间范围与值保护 |
| --- | --- | --- |
| 903 根表情 / liptype00 | `R207_C018_T2`、`R207_C035_T2` | 根片段两个键：0 与 float32 的约 1.4 s，均下收；liptype 仅改 0 s 的第一个值 |
| 904 镜像根表情 / liptype01 | `R207_C017_T2`、`R207_C034_T2` | 同样规则，分别从各自原数据计算，保留两侧原有微小数值差 |
| 两条 liptype 的其他键 | 全部保持原值 | 原键时约 0.079525、0.162858337、0.25 s 不改；Constant 插值使首个值保持至下一个键 |

`mouth/build_candidate.py` 读取已冻结曲线和控制 basis scale，将物理位移映射到 T2 权重并按 float32 写入输入。**2.2 mm 不是直接给曲线减 2.2，也不是对整个 liptype 加常数。**该实现按控制各自比例换算，根片段两值都改，liptype 只改第一个值；其他曲线数据、键时、插值及 hold 数量逐值检查。

私有管线按以下顺序运行，公共文档只记录方法，不提供可直接操作游戏的脚本：

| 入口（相对 `work/retail_polish_r215/mouth`） | 输入 → 输出 / 作用 |
| --- | --- |
| `setup_lane.py` | 冻结基线与资源提供者 → 隔离原生制作工程；提供者只读 |
| `build_candidate.py` | 原曲线、控制比例、原 writer jobs → `clips_v2`、writer 输入、`CANDIDATE_V2.json` |
| 既有原生 curve writer / Cook | 精确曲线输入 → 保存并 fresh reload 的四个作者 AnimSequence → 原路径八个 Cooked companions |
| `run_entry.py` | 同版头部、服装、原生 AB、GPU morph、原镜头/光照/材质 → 1P、2P 及相邻帧捕获和 trace |
| `make_review.py`、`encode_motion.py` | 原图 → 原像素对照、51 帧原时钟 60 fps 无声片段；不用于证明包内容 |
| `freeze_delivery.py` | 作者 / Cooked / 保护检查 / 预览证据 → 唯一合并入口 `DELIVERY.json` |

### 检查与失败记录

- Fresh reload 验证 1,370 条曲线、4,338 个键和 11,644 个压缩采样，最大误差 0；Constant 插值保留。
- 四份 guard 与原对应 guard 字节相同，覆盖 Skeleton、帧数、长度、播放率、轨道映射/名称、Additive、Notifies、骨压缩设置及全部原骨轨 Pos/Rot/Scale 键。7,723 个其他私有 Content 文件不变；四包的八个基线 Cooked 文件与 R214 输入逐字节相同。
- 闭口主对照为 1480 帧；1334–1384 连续 51 帧用于核对闭口、张口与恢复。1200 尚未进入目标片段，1280/1357/1358 张口整张 PNG 与基线相同。闭口差异超过 3 级 RGB 的像素限制在 54×73 的口角区域；区域外仍有最多 3 级的渲染舍入/后处理差异，不能写成完全逐像素一致。
- 两次镜像试验因重复命令行 ini 覆盖只得到另一角色图，已排除。有效镜像证据改用私有 Config，并在 trace 实际确认 `ADV_obj2p` 的 root904，再比较 1120 帧。仅将截图左右翻转不能替代镜像消费者验证。

`CANDIDATE_V2.json` 内的 `NATIVE_REVIEW_PENDING` 是生成候选时状态；本页引用的 `DELIVERY.json` 和 `README_ZH.md` 指纹记录随后完成的 V2 制作检查。首轮 `CANDIDATE.json` / `review` 已被 V2 替代。V2 原本意图保留轻微笑意，但用户看过对照后指出仍有些上翘，说明技术通过不代表视觉目标达成。后续进入 V3 继续收平；现有 V2 技术收据不能继续作为最终嘴部选用或发布批准。

### V3：独立输入、明确取代 V2、保留开放口型

V3 从 R214 继承的原曲线重新计算，**相对 R214 总计下收 6.0 mm，不是在 V2 的 2.2 mm 上再减 6 mm**。同一侧上下唇末端沿真实脸空间 Z 同步调整：下唇端约 +6.111 → +0.111 mm，上唇端约 +9.033 → +3.033 mm。该方案继续保留轻笑，不改共同 REST 或用屏幕平移伪造嘴形。

控制白名单仍是 903 / liptype00 的 C018、C035 和 904 / liptype01 的 C017、C034，仅 T2。两个根片段保持 84 帧 / 1.4 s 常值 hold；两个 liptype 只改 `[0, 0.0795250088)` s 首闭口 hold。替换清单必须同时包含根与 liptype 四包，避免短暂选中闭口 liptype 时返回旧嘴角。

新流程：`build_candidate_v3.py` → `authoring_inputs_v3/jobs.json` / `clips_v3` → 原生 curve writer 保存并 fresh verify → `native/cook_curves.py --label mouth_v3`。`stage_candidate_v3.py` 只把四个新 author 放入私有完整角色场景；`finish_v3_visual.py` 捕获双侧连续区间并恢复私有玩家配置；`audit_v3.py` / `freeze_delivery_v3.py` 输出独立证明和 `DELIVERY_V3.json`。新资源存于 `delivery_v3`，旧 `DELIVERY.json` 所指 `delivery` 不覆盖；`proof_v3/V2_PRESERVED.json` 核对旧 12 文件与旧候选哈希仍相同。`DELIVERY_V3.json.supersedes` 明确只取代 entry-mouth 的四个原路径包，其他 lane 继续使用各自冻结来源。

| V3 检查 | 已证范围 |
| --- | --- |
| `proof_v3/SOURCE_CURVE_GUARD.json` | 1,370 曲线 / 4,338 标量中，仅八条曲线的 12 个值改变，4,326 个 float32 值精确保留；曲线顺序、元数据、键时与 hold 数量相同；两 liptype 的 1,924 个开放区键值逐值相同 |
| `proof_v3/guards/000..003.bin` | 与原对应 guard 完全相同；保护上文列出的 11 类字段，包括全部原骨轨 Pos/Rot/Scale 键 |
| `proof_v3/verify_readback.jsonl` | 重新启动并加载四个 author 后，1,370 曲线 / 4,338 键 / 11,644 个实际压缩采样，最大误差 0，Constant 插值和压缩数据有效 |
| 原生 Cook 与 `DELIVERY_V3.json` | 八个 Cooked 文件独立冻结，Cook 前后 author 哈希相同；本页写入时重新核对 12 个交付文件及 manifest 的七份 proof 哈希，全部匹配 |
| `review_v3/CONTINUOUS_REVIEW.json` | 1P 1334–1384 的 51 帧与真实 2P 945–1005 的 61 帧，共 112 张 2560×1440 原生 GPU 图逐张审阅；列明区间内未见闭口端单帧弹回原大钩或新增角部分离 / 张闭裂缝 |

fresh-load guard 和压缩求值是作者包检查；随后 Cook 成功并冻结哈希，**没有另开 Shipping 做 Cooked 语义回读**。112 帧检查也不覆盖每一种可能的语音口型调度。root 当时的合入决定属于制作方案选择；后续用户对 V3 的明确认可另记于第 7 节，不扩大这些技术检查的覆盖范围。

### 同编号帧不能自动视为同一口型

`review_v3/SAMPLING_PHASE_AUDIT.json` 将 root 时间、实际 lip montage 位置与 `Mouth_BoneBlendAlpha` 一起对照：

| 代表点 | R214 / V3 root 状态 | lip 采样与实际覆盖 | 结论 |
| --- | --- | --- | --- |
| 1P 1280 | 都是 root903，0.667666674 s | liptype00 分别在 0.200000018 / 0.0333333351 s；两侧口型覆盖权重均 1 | 实际使用不同离散样本，排除同姿像素比较 |
| 1P 1480 | 都是 root903，1.16766679 s | lip 都为 0.0333333351 s；口型覆盖权重均 0 | 稳定闭口，可以比较 |
| 2P 1120 | 都是 root904，0.83433336 s | liptype01 都为 0.0333333351 s；口型覆盖权重均 0 | 实际镜像消费者的稳定闭口，可以比较 |

稳定点前后各三个 trace 帧也确认 root 时间一致、口型覆盖一直为 0。1280 证明暂停 lip montage 选择不同，不证明 sequence 时钟改变；两次独立运行为什么选中不同口型，尚未进一步定位。trace 在 `core_tick_before_world`，HighResShot 又有异步提交，切换边缘不能只用图片编号把 trace 与最终像素强行配对。

因此 V3 的旧 `original_pixel_transitions_1..3.png` / `PIXEL_DIFF.json` 保留为诊断，不用于证明同姿像素局部性或数据保护；1357/1358 开放图相同也仅为支持证据。保护结论来自字段与曲线检查，代表视觉比较来自已核实消费者相位的 1480 / 1120，连续图另检查切换过程。

## 3. 近景相机：只改位置窗口并保留原停帧

目标 `/Game/Chara/SLY/Common/Camera/sly501cs` 是 **CameraAnim**。原 BBS 调用 `PlayCameraAnime(sly501cs, centerObject=23, blendInFrame=-1, blendOutFrame=19)` 未改。`camera/audit_camera.py` 从当前零售 PAK 只读提取并核实索引/条目 SHA1，再逐键确认作者五条曲线与零售来源一致。

原资源有 225 个 60 Hz 键，长度约 3.733333349 s。唯一作者差异是 `InterpTrackMove_1.PosTrack.OutVal` 的 **key 121–188**：

1. 候选 A 下移 4 cm；候选 B 下移 4 cm 并沿该键镜头视轴后退 8 cm。制作比较选择 B，为嘴、下巴和握拳主体增加边界余量，仍保留脸部近景。
2. `make_candidates.py` 先按原位置和旋转相同的连续键识别停帧组。以组首键算渐入权重，而不是让同一 hold 内每个键产生不同偏移。
3. 从 key 121 渐入，152 起达到全偏移。实现令 `x=min(1,(holdstart-120)/32)`、`w=x*x*(3-2*x)`，使用原镜头旋转得到 forward，位移为 `-8*w*forward + (0,0,-4*w)` cm。
4. key 0–120 与 189–224 完全不变。所有 `InVal`、切入/切出时钟、插值、切线、旋转、约 20° FOV 和两条 `bLightAnimTrack` 光轨保留；除允许的作者 float payload 外，其他包字节不变。

`make_candidates.py` 只在已解析 tag 的作者 float payload 上生成隔离候选，再由 `cook_selected.py b_down4_back8` 进行原生 WindowsNoEditor Cook。**没有修改最终 Cooked 字节。**`TRACK_DIFF_AND_CLOCK_GUARD.json` 检查逐键/字节白名单，Cook 后再次解析五轨，所有曲线与所选作者精确一致。

制作流程为 `prepare_lane.py` → `audit_camera.py` → `make_candidates.py` → `run_preview.py` → `validate_native.py` / `review_images.py` → `cook_selected.py` → `finalize_evidence.py`。输入为零售认证来源及冻结角色内容，输出依次为来源审计、两候选、原生 trace/图、保护 guard、选中包的 `delivery/DELIVERY_MANIFEST.json` 与 `FINAL_EVIDENCE.json`。私有 Config、Saved、Intermediate、DDC、插件、日志和图片均隔离。

### 检查与失败记录

首次基线运行因沿用的配色 fixture 缺少 SOL BBS 提供者而失败；只在私有工程补齐原版只读依赖后重新运行。该失败不表明用户游戏缺包，也没有作为候选效果证据。

基线、A、B 各 18 张图，最终 B 再取 44 张，包括 809–844 逐帧及切入/恢复关键帧。四轮均正常退出，全部 2560×1440，使用真实原生角色状态和完整材质。动画/口部状态在 227 帧中与基线一致；136 个冻结共同作者资产哈希未变。首轮某些切出 PNG 可完全相同，最终相邻帧复跑仍有粒子差异，因此以轨道和事件时钟保护证明改动边界，不泛称所有后续 PNG 相同。

这些是私有原生制作预览。原闪光、手腕被下框部分裁切及合理头顶裁切仍存在；没有为了全部入框而大幅拉远。用户随后已明确接受相机 B，决定见第 7 节；该认可不将这些制作预览改称为零售捕获。

## 4. 原样 Cook 交付与批准版回退

当前制作方案为 **V3 四个 AnimSequence 加相机 B 的一个 CameraAnim，共五包、十个 Cooked companions**。V3 八文件显式取代旧 V2 四包；不得混用根 V3 与 liptype V2，也不得继续把旧 `DELIVERY.json` 当作最新嘴部交付。root 已选择并合入 V3，按最新 manifest 原样叠入继承 R214 的新完整单 PAK；最终打包 / 安装收据见第 6 节。合包不改变资源语义；作者工程、Python、诊断 DLL、运行桥和测试资源不进入分发。

相机交付两文件为 2,275 / 304,901 bytes，其 SHA 分别为 `5ef705928917dd135e4add59832083a542587493d1414229c374e7ebcfc2b3b9`、`430532c98dfae06ffdbe58e7f5232532d65e96ba47a8d281c0ccda76929efc48`。嘴部当前入口为 `mouth/DELIVERY_V3.json`；旧 `mouth/DELIVERY.json` SHA 仅标识 V2 历史检查。本页引用的 portable handoff 状态 `READY_FOR_ROOT_SINGLE_PAK_PORTABLE_BUILD` 是工具交接记录，不等于已安装，也不替代 V3 审阅决定。

`work/retail_portable_r215` 保留原生首载单 PAK、相对分发路径、SHA 校验、Steam 发现、可选 Unverum、当前目标 SIG、精确安装收据和 Paks 外备份。没有增加 EXE/build 白名单。`Build-Package.ps1` 只从 finalized integration manifest 和已完成的真实 PAK 制作新分发；测试、开发工具及外部运行依赖不进入 ZIP。

回退的实际问题是：旧迁移方式会留下禁用的空 R214 管理器行，而永久保存的原版 R214 安装器拒绝同名行。新 `Retire-R214.ps1` 只移除收据跟踪的 PAK 属性，再仅省略已空的 R214 行；完整原 Config / 手工字段先备份。含未跟踪 PAK 的同名行保持不动，需单独处理。**Retire 指迁移已安装副本，不删除认可归档、原 ZIP、发布目录或作者源。**

受控顺序：

1. 核实 R214 认可归档与原安装器仍完整；以新工具对已安装 R214 做只读迁移预览。
2. 获得部署授权后按预览执行 `Retire-R214`，再安装新的 R215 单 PAK。
3. 回退时先卸载 R215，处理卸载收据列出的保留/冲突文件，再用保存的原 R214 安装器回装；不用改写原安装器或删除 `removed` 收据。
4. 再升级时重新执行 `Retire-R214` → R215 Install，避免两个版本同时活动。

Windows PowerShell 5.1 的 29 项定向断言已通过，使用未修改的已保存 R214 Install/Uninstall/Common，覆盖完整升降级往返、Default 与 ModList、直接路径和数字优先级重命名、无管理器、后续 Config 修改保留、旧文件变更拒绝迁移、R212/R213 活动守卫及其他 MOD/存档/loadout/metadata 保留。旧 R214 的 28 项未改逻辑证据沿用，没有无理由重跑。合成包标记 synthetic，默认安装拒绝；它们不构成真实安装或零售画面验收。

## 5. 相对证据与状态边界

下表保留 V2 历史记录、相机 B 和新 V3 的独立指纹；`P=work/retail_polish_r215`，`T=work/retail_portable_r215`。必须按 revision 与摘要区分，不能只认文件名。最终 PAK/ZIP/安装证据另列第 6 节，不回写制作收据当时的状态。私有资料可能含本地路径，不在公共仓库重新分发；制作检查不替代用户认可。

| 相对证据 ID | SHA-256 |
| --- | --- |
| `P/APPROVED_BASELINE.json` | `b48f15f14ed85209a074ac9f9c951897ae55316310a9be2ac577f6467059f978` |
| `P/mouth/CANDIDATE_V2.json` | `115ab3ed78ae64f018129e86249a4b83f20612662d53ffe822095459f577c8cd` |
| `P/mouth/DELIVERY.json` | `505c9849ac844d7f927d2915557d77b7bf6cf163d8fd0c3cb64bbc76af06fe1a` |
| `P/mouth/README_ZH.md` | `147e88d25528cc3ac4e81461f536fb17b8dcdb54f161535206a48fc66c6fa290` |
| `P/mouth/CANDIDATE_V3.json` | `e2de2b2c6a319b3f850d881f06de3786034ec0ff02b8e30f4f20522aaab84a73` |
| `P/mouth/DELIVERY_V3.json` | `cbbb0ee038753c9544b1deae5200fe6c8374cde1c3dd89fd861c73070f8d53e3` |
| `P/mouth/README_V3.md` | `21854b63d0865fcc6fe55a85ad1504d2abefcf364a51983aaab20d4e36847949` |
| `P/mouth/proof_v3/SOURCE_CURVE_GUARD.json` | `5d393959b850388af4c784e07358a3c89023b8806785f7c1f4fa7d918d045a4f` |
| `P/mouth/proof_v3/V2_PRESERVED.json` | `2fbf18e98097097f87a5de9b741a51e229fd37a75d7e19174a2fd0262ff81839` |
| `P/mouth/proof_v3/verify_readback.jsonl` | `e8aac5f982bcc59b34d171c129811d8caff6972d175f185532afe1a3d01b9006` |
| `P/mouth/review_v3/SAMPLING_PHASE_AUDIT.json` | `e2d446f691d154404efd7c5ddbc6ea5f28f4b1ccccbf7b555238b797661d6a3c` |
| `P/mouth/review_v3/CONTINUOUS_REVIEW.json` | `ef8fcb732a964eaeea6bb9830ef4dc64d1c2046700f3ad378e4bdbc1c34e2cd2` |
| `P/camera/candidates/b_down4_back8/TRACK_DIFF_AND_CLOCK_GUARD.json` | `cca375861e930b69452efbcba0119a1541b754912ffd6dcfc4c5fbf79007e6e2` |
| `P/camera/delivery/DELIVERY_MANIFEST.json` | `8c288eff003d93fb17accde99b10368b4b62f139a1f8efeea935f7b0477e484b` |
| `P/camera/FINAL_EVIDENCE.json` | `9982b8b71fb533c73bd9d7fa35330e948d43a3aa38b24b5579c8e0d043d89d43` |
| `P/camera/HANDOFF_ZH.md` | `1c77ec3c328c65d2a96cb0f6a8b4b3b9ed92833bb09961e368ffd5e8faf953e1` |
| `T/HANDOFF_R215.json` | `fd1c2d9e3ab40cbd3b6f99480ceeb633549017180f6b91f96b03f6480dde1b02` |
| `T/MIGRATION_VALIDATION.json` | `d789c1cf79151fafacd31390cac81b5587f437a9e713690dceaeebf41868beb0` |

## 6. 最终打包与真实安装收据

最终产物使用 `mouth_v3` 包集，相机保持 B。`STAGED_CHANGE_GUARD.json` 记录 R214 的 2,655 文件基线到 R215 的 2,657 文件：2,647 文件逐字节保留，其余为明确列出的嘴部替换与相机新增。最终单 PAK 含 **1,328 包 / 2,657 文件**，原生 Cook、typed dependency closure、创建 / 测试 / 列表 / 全量解包哈希检查通过；包内没有 BBS 或运行桥 / 插件二进制。安装收据记录判定数据覆盖为 0、修改动画的原时钟与骨轨保留。这里沿用整合者的验证收据，没有为撰写文档重新打包或扫描运行中游戏。

| 最终产物 | bytes | SHA-256 |
| --- | ---: | --- |
| `GoldShip_R215_Native_P.pak`（`mouth_v3`） | 181,718,501 | `e888dd38ce2da1ed7866a2f051e4f62c1b9bd4b1c5c8f37a8fbf25dd367a2614` |
| `GoldShip_R215_20260922.zip` | 170,520,653 | `cef3ea9e0bd2dfcb91601ea95c0641fc95ca80d93b747259f8ad7c2094a185bc` |

`INSTALLATION_RESULT.json` 于 2026-09-22 13:52:26 UTC 记录 `INSTALLED_R215_CANDIDATE_R214_APPROVED_PRESERVED`：游戏安装路径和管理器中的 PAK 均匹配上表摘要，各自 SIG 也经收据校验；独立分发不依赖开发工具，没有增加游戏 EXE/build 白名单。代理当时没有启动游戏，将测试交给用户；这份安装收据早于第 7 节的认可记录。

迁移只处理收据证明属于 R214 的四个已安装 PAK/SIG 文件，备份移至 Paks 外；R214 认可归档和原发布保持。其他 46 个 PAK/SIG 的文件状态检查保持一致，无关管理器配置保持，旧运行桥继续禁用。这里的其他文件保护是收据记载的 **stat 检查**，不冒称重新哈希了全部其他 MOD。退回批准版仍使用第 4 节已验证的卸载 R215 → 原 R214 安装器回装顺序。

| 相对收据 ID | SHA-256 | 证据层级 |
| --- | --- | --- |
| `work/retail_native_assets_r215/final_package_plan/STAGED_CHANGE_GUARD.json` | `930b0e319c6663c0ad40ab0140d595bad3575d257272fbe68dff7bd7cdb7a5f9` | 基线继承与明确改动清单 |
| `work/retail_native_assets_r215/final_package_plan/PAK_VALIDATION.json` | `b95b1f41b34e33df611ec732241c281ccb53dac780bfb8f8883421c9bc89fb83` | 创建 / 解包 / 哈希与包内闭合，记录时 `installed=false` |
| `work/retail_polish_r215/FINAL_INTEGRATION_CONTRACT.json` | `cb449982b80f1c8b5565eaefc5471ed5429aea6ed75e00c16ca34174df9606ab` | 13:48:27 UTC 的最终包合同，当时等待安装与用户审阅 |
| `work/retail_deploy_r215/INSTALLATION_RESULT.json` | `c15f0f18064afdfdb2e6631fe49d422ee7495894aa2ec7e8fb54efacd3ab4fa0` | 13:52:26 UTC 的真实安装与保留检查 |
| 安装收据所指 `GoldShip_Mod_Backups/R215/install.json` | `29a189762b134aa012b37e0f10fc31b713ec443896aec3736b229bd9c6ac6540` | 实际安装文件 / 管理器配置身份；摘要由最终安装收据绑定 |

包验证与整合合同中“待安装”是各自生成时的历史状态，由后续安装收据补齐，而非把旧记录改写成另一次观察。历史安装收据中的 `retail_visual_accepted=false` 保留原值；第 7 节新增独立的用户认可证据，不能用旧收据当时的值否认后续决定，也不回写旧收据冒充当时已经认可。

已证的范围是：R214 获用户认可并保留；V2 技术通过后仍被用户指出嘴角偏翘；V3 完成字段、压缩求值、双侧连续图与 Cook 检查，由 root 选为制作方案；V3 加相机 B 的最终 PAK/ZIP 已构建并安装核验；随后用户明确接受这两项改动，完整 R215 作为新的认可版本独立保留。

## 7. 后续用户认可与独立的新问题

2026-09-22 19:30:56 UTC 的认可记录状态为 `USER_APPROVED_R215_MOUTH_V3_CAMERA_B_PRESERVED`。用户明确表示“不错，这两个改动都接受”，对应本页的 V3 入场嘴部和 Last Horizon 相机 B。认可归档中的 PAK / ZIP 摘要与第 6 节最终交付一致；此决定基于此前可用的 R214，不撤销 R214 的保留要求。

| 相对认可证据 ID | SHA-256 | 作用 |
| --- | --- | --- |
| `work/cape_2hs_r216/APPROVED_BASELINE.json` | `aa006b9c17892e432b1232f76847e8f5f4d69ce331bb323551429d7368e21662` | 为后续 2HS 工作固定已认可的 R215 基线、保留字段与新问题范围 |
| `releases/approved/GoldShip_R215_UserApproved_20260922/USER_APPROVAL.json` | `aa006b9c17892e432b1232f76847e8f5f4d69ce331bb323551429d7368e21662` | 将明确用户决定绑定到独立永久归档的 R215 PAK / ZIP 和原发布文件 |

同一轮反馈还指出 2HS 披风太靠前、中心位置不合适。后续 R216 只在最新认可基础上处理这一动作的披风位置；已认可嘴部 V3、相机 B 以及其它受保护资源继续保留。两项改动的认可与新动作缺陷可以同时成立，不能据此宣称所有动作已完美，也不能倒退为 R215 两项仍待用户决定。
