# R214：切换配色时的 Morph 着色器查找失败

后续状态：用户已认可 R214 可用，批准版已永久归档；[R215 入场嘴角与近景相机候选](gold-r215-entry-camera-example.md)记录两项受限润色与保留回退方法。本页以下制作期证据及其当时验收边界仍按原记录保留，不自动扩展为对 R215 的认可。

本案延续[材质实际消费者案例](material-consumer-fallback.md)。用户反馈第一套配色可用，切第二套配色时选人界面退出，报 `LowLevelFatalError` 第 2138 行、`Fatal Error Material not found`。这条文字不能直接翻译为“少装一个材质包”。[证据指纹](gold-r214-color-transition-evidence.json)仅列私有资料的相对标识和摘要。

**已证：**该行是 `FMaterial::GetShader` 的缺失 shader 分支；已保存崩溃栈关联的具体类型是 `TBasePassVSFNoLightMapPolicy` 与 `TGPUSkinMorphVertexFactoryDefault`。初始 R213 的实际 17 套配色可解析，共享 Gold 材质叶；没有找到第二套配色特有的缺包证据。原生 BTL 材质消费者 A/B 已证明共通 Loading/Hidden 缺少精确 Morph shader 路径，候选消除了该缺口与默认材质回退。最终 WindowsNoEditor Cook 变体已与交付字节绑定，17 色及代表场景共 41 图和 4,788 条代理检查已通过。**限制：**fixture 未复现 Shipping Fatal，也不是完整异步 CharaSelect；具体失败 MaterialResource 名称未从 minidump 恢复。用户实机和审美验收仍独立记录。

## 1. 报错与转储能证明什么

本地 `MaterialShared.cpp` 第 2081–2142 行中，`FMaterial::GetShader` 先按 VertexFactory 找 RenderMeshShaderMap，再按 ShaderType 和 permutation 找 shader；取不到时，记录详细信息并在第 2138 行 Fatal。它不执行 `LoadObject`，也不是按包路径搜索材质。

最新已保存的同签名崩溃发生在选人状态、TaskGraph 工作线程。其 minidump header 时间为 2026-09-22 09:15:23 UTC，进程运行了 209 秒；CrashContext XML 没有显式 crash UTC 字段。它比后来只读观察到的另一进程启动早 93 秒，不能称为该后续进程的转储；与用户截图的错误签名一致，截图具体属于哪次进程未独立确定。小型转储保留两处重复的静态类型指针，却没有相关材质资源堆。诊断把该次指针换算为模块 RVA，用此前已存档、CodeView 记录/时间戳/映像大小/checksum 均匹配的运行期静态类型对象，找到当前 EXE 的只读名称字面量，从而恢复 ShaderType 和 VertexFactory。证据表保留每一级地址与摘要。

这是跨同构建静态对象的身份恢复，**不是**从旧转储猜本次材质实例。候选 MaterialResource 指针不在本次捕获范围，名称保持未知。磁盘受保护代码段的初次反汇编不是有效指令证据，已明确排除；这里使用的是可读名称、匹配元数据和当前栈指针。

## 2. 动态查找规则：颜色容器、过渡容器、类别槽

| 阶段 | 真实规则 | 易漏的覆盖 |
| --- | --- | --- |
| 选人颜色路径 | `UpdateCharaAsset` 把零起始 costume/color enum 加 1，传给 `CharaMaterialPath`；后者生成 `Costume%02d/Material/Color%02d/PawnMaterials` 对象路径 | 颜色 2 对应 `Color02`；并非给每个材质叶自动追加 `_02` |
| 对战路径 | `GetColorIDForPathName` 可先经转换表再加 1；黑角色脚本可覆盖颜色 | 不能硬编码成 1–16，实际索引另有特殊配色 |
| 换色过渡 | 同角色颜色变化后，立即 `ChangePawnMaterials` 到 1P 或 2P 的共通 LoadingMaterials，并等 30 tick 后再切最终色 | 最终色静态 imports 不涵盖这条必要临时消费者 |
| Loading 设置 | `SetupMaterials(ColorLoading)` 不按当前 mesh 名称匹配，直接对每个组件使用第一个 Base set 的第一行 | 头、身体、附件都可能临时用相同 loading/hidden shader |
| 正常设置 | ExPawnMaterials 优先，再主容器；按请求 set 的精确 MeshName 搜索，完全没有行时才退回 Base 行；各类别取第一条非空引用 | 不是按材质名字的含义或颜色后缀猜槽 |
| 顺序赋槽 | Base、Outline、Shadow、Decal、Specular、UniqueA–E、DmgDecalA/B；只有找到 Parent 对象身份匹配的池 MID 并成功设置才使 slot 加 1 | 空类别不占槽；类别 enum 不是固定材料 slot |
| 池与父链 | `UseMaterials` 决定池中 MID 的 Parent 和 category flags；材质叶、父链/函数、纹理是对象引用 | 包存在、组件 MID 正确、实际编译变体可用是三个不同条件 |

诊断时的 R213 真实清单含 Color01–16 与 Color90，共 17 套；加 ADV 以及 1P/2P loading，共 20 条动态入口。只读矩阵列出 39 张容器/设置表及 392 个材质/父链节点。该基线的 Gold 最终叶在前两色共享，已修复的眼镜 Morph 父也相同。共通 Loading 和 Hidden 母材质序列化了 SkeletalMesh 等用途，但没有 MorphTargets；后续原生中间状态读回也证实两者实际缺少该 Morph VF，而候选补齐。第 6 节的新主题配色是之后的独立制作，不能把初始共享状态写成最终路由。

## 3. 私有脚本与受限候选

以下 `D = work/retail_colors_r214/diagnosis`，`M = work/retail_colors_r214/materials`；它们是实现来源，不是公共 harness 自带的游戏工具。

| 顺序 / 入口 | 输入 | 输出与保护 |
| --- | --- | --- |
| `D/inspect_shader_dump.py`、`build_diagnosis.py` | 新 crash 快照、已有匹配模块转储、当前 EXE、对应本地引擎代码 | `SHADER_VF_POINTER_PROOF.json`、`SOURCE_RULES.json`、`DIAGNOSIS_SUMMARY.json`；保留无法读取的 Resource 堆限制，不启动游戏 |
| `D/audit_crash_timeline.py` | 本地已保存 CrashContext/minidump header、另一次进程启动的只读观察 | `CRASH_TIMELINE.json`；区分文件时间、dump header UTC、运行时长和截图归属，避免同签名跨进程误配 |
| `M/audit_routes.py` | 认证的当前零售 PAK 索引、冻结 R213 有效资源 | `ROUTE_USAGE_INVENTORY.json`；真实颜色集合、容器行、UseMaterials、父链和用途逐项对照 |
| `D/build_diagnosis.py` | 上述矩阵与代码规则 | `DYNAMIC_MATERIAL_REQUIREMENTS.json`；20 入口的动态对象、必需包、父链和槽规则，超出单一静态 imports |
| `M/prepare_loading_candidate.py` | 原 Loading/Hidden 图和 1P/2P/Hidden 三叶 | 两个私有母图仅增加 `bUsedWithMorphTargets=True`，三原路径叶只换父；原共享母图、表、其他配色和模型不改；作者工程原叶最终恢复 |
| `D/verify_loading_graph.py` | 候选及归档 baseline 字节 | `LOADING_GRAPH_INDEPENDENT_GUARD.json`；复用 SOL 图/参数比较，24+2 节点无语义变化，三叶有效参数与参数 GUID 保留，五资产哈希绑定 |
| `native_scene/source/GoldNativeColorTraceR214.c`，各 run 的 `SPEC.json`/`TRACE_BUILD.json` | 已初始化双方 BTL Pawn、同版头部、stock 或候选五材质；原生两个换材质 API | `native_scene/LOADING_TRANSITION_AB.json`、逐 run trace/hash/原输入前后守卫；读取 GT/RT 精确 shader 与 SceneProxy，不保存资产，不属于最终安装运行组件 |

母图的原着色公式、透明/隐藏行为、静态开关、纹理和标量不为回避崩溃而简化。独立守卫显式列出旧资产保存规范化：过时函数依赖缓存移除、旧 Unlit 模型补为 bitfield 1；它们不被静默当成用途差异。旧 Hidden 叶是 UE4 version 508，export 的 serial size/offset 为 32 位，须按 `ObjectResource.cpp` 的版本分支读取，不能把现代 64 位布局强套进去。

## 4. 验证关口与不可泛化的结论

已执行的 A/B 使用 Editor `-game` 可渲染私有场景，实际 `GIsEditor=false`。在双方已初始化 BTL Pawn 上，第 320 帧调用 `ChangePawnMaterials(Color01, Base)`，第 400 帧调用原生拼写为 `ChangePawnMaterialsForColorLoaing` 的 API，按玩家侧分别装入 loading 池；持有 40 tick 后，第 440 帧切 Color02。第 350/405/435/475 帧读回，第 350/435/475 帧留图。40 tick 是用于观察的 fixture 时间，原选人源码的 loading 计数为 30，两者不能混称。

| 同一类读回 | 原材质 | 候选作者材质 |
| --- | --- | --- |
| 实际 SceneProxy 记录 | 240 条中 16 条使用 WorldGrid，位于两侧 loading 期间头部 section 0/1/6/10 | 240 条均正确，无 WorldGrid 回退 |
| Loading / Hidden 精确 mesh shader 查询 | 两个 root 的 GT/RT 均为 `vf_missing`，未找到所请求的 Morph VF | 92 次 component-slot 检查的 GT/RT 均找到精确 Morph VF、`TBasePassVSFNoLightMapPolicy`、permutation 0 |
| 运行结果 | 正常退出，回退而非 Shipping Fatal | 正常退出，消除上述 shader 缺口与回退 |

精确查询沿 `FShaderMapBase::GetContent → FMaterialShaderMapContent::GetMeshShaderMap → FShaderMapContent::GetShader`，使用 null-safe 只读检查和已 flush 的 RT map。该结果证明原生 loading 消费者的变体缺口及候选修正；没有复现完整异步选人状态机，也没有把本地新编的作者 shader map 当作包内 Cooked 证明。两次 trace 哈希已按收据核对。

修前/修后必须在同一组冻结头部与材质输入中运行真实 Loading→最终色路径，两侧分别核对实际 SceneProxy、编译资源和画面。覆盖 loading 与 hidden、所有使用槽、正常色及特殊色；不能只在静止 Color01 画面看到正常就宣布换色通过。Cook 后再核实际 compiled shader、父链、依赖和交付字节，原生 A/B 与用户零售验收分别记录。

## 5. Cook shader：保留失败路线，绑定正确的目标平台字节

### 5.1 直接 Cooked-in-Editor 加载没有通过

`native_scene/run_cooked_loading.py` 只向目标提供 Cooked companions，并预先启用 `cook.AllowCookedDataInEditorBuilds=1`。该开关使 Linker 接受过滤了 editor-only 数据的包、设置 `bIsCookedForEditor`，**不保证 shader 内存布局兼容**。实际 `COOKED_LOADING_EXACT_GATE.json` 为 `pass=false`：Game target 的冻结 `TBasePassVSFNoLightMapPolicy` 为 328 bytes，Editor 当前类型为 504；`FMaterialShaderMapContent` 分别为 404 和 480。`ShaderMap.cpp` 的尺寸/布局哈希校验拒绝内容。

两目标资源的 package cooked 标记为 true，但 `contains_inline_shaders=false`、`loaded_cooked_shader_map_id=false`。之后 Editor 用 DDC/重编所得的 map 仍可查到 exact shader；这 92 次 `present` **不算包内覆盖证明**。成功安装 inline map 后，`CacheShaders` 的 inline 分支确实禁止补编；本次恰恰未安装成功，不能套用该分支的性质。没有关闭布局检查或以 Editor-only recook 代替目标平台产物。`-noshaderworker` 也不等于禁止编译；`-NoShaderCompile` 会另行跳 shader type 初始化，不能作为无条件捷径。

### 5.2 通过的方法：WindowsNoEditor cache 到最终 `.uexp`

| 步骤 / 私有入口 | 具体操作与输出 |
| --- | --- |
| `M/read_cook_map_pdb.py` | 为本次开发 DLL 校验身份并记录 `CachedMaterialResourcesForCooking`、资源代码数组和目标平台接口布局，输出 `COOK_MAP_PDB_LAYOUT.json`。这些布局守卫不进入安装器白名单。 |
| `M/run_cook_map_proof.py` + `cook_map_proof.c` | 对冻结作者输入调用 `BeginCacheForCookedPlatformData(WindowsNoEditor)`，等待 `FinishCompilation` / `IsCachedCookedPlatformDataLoaded`；只读取以该 target 指针为 key 的 Cook cache，不拿 Editor 渲染 map 冒充。无作者保存。 |
| 精确 shader 查询 | 以实际 hashed VF/type 和 permutation 0 找 shader，读取 `GetResourceIndex`、`GetOutputHash`、`GetResourceCode`。要求 `ShaderHashes[index] == OutputHash`，记录 ResourceHash、完整 compressed code、uncompressed size、vertex frequency，且目标 layout 不含 editor-only 位。 |
| `M/bind_cooked_shader_proof.py` | 从冻结清单指定的最终 `.uexp` 定位唯一 ResourceHash，解析完整 `ShaderHashes` 和 `ShaderEntries` 数组；匹配精确 index 的 hash、完整压缩代码字节、原始大小与 frequency，并在前置 frozen content 中确认 VF/type hashed identity。输出 `cook_shader_proof/COOKED_EXACT_SHADER_BINDING.json`。 |
| 三片继承叶 | 检查 Cooked Parent 指向已验证的两个 root，且 `bHasStaticPermutationResource=false`，因此没有另一套未经检查的独立 static map。 |

本次实际目标是 WindowsNoEditor，platform 0 / quality 1 / feature 3，layout flags 41、editor-only 位关闭。Loading shader 绑定 `ShaderHashes[56]`：1,539 bytes 压缩码、3,995 bytes 解压大小；Hidden 绑定 `[34]`：1,145 / 2,886 bytes，两者 frequency 0。完整 code 与最终交付 `.uexp` 切片逐字节相等，而非只看 usage 标志、字符串存在、DDC 命中或另一次 shader 编译成功。证明阶段的目标 cache 可执行 Cook 编译，但只有与既有最终包的完整字节相等才获接收；作者资产与交付文件均未改。

这证明所需 shader 确实包装在交付中，不代表任意引擎版本兼容，也不升级为用户运行过异步选人界面。失败的直接 Editor load 收据继续保留 `pass=false`。

## 6. 全配色制作：语义区域、原设置与动态表一起闭合

切换修复与完整主题配色是两项工作。Color01 的获认可外观、MIC 参数和纹理沿用 R213。其余 Color02–16/90 共 16 套，通过以下管线生成 128 张 Base/Sss 纹理、160 个实例；不以全局染色覆盖皮肤、脸墨线、眼睛或 SOL。

| 入口 | 输入 / 方法 | 输出与保护 |
| --- | --- | --- |
| `palette/stock/audit_stock.py`、`build_palette_audit.py` 及区域审计 | 当前零售 17 色 swatch、Gold atlas/UV 实际使用范围，区分衣料、皮革、金属、袖口、帽徽、发尾 | 真实色表、联合色端点 mask、袖口 UV mask、帽徽覆盖率合同，作为后续输入指纹 |
| `M/build_color_textures.py` | 各语义角色、Base/Sss 分别用 `Gold.H += stockXX.H - stock01.H`、`S += Δstock.S`、`V *= stockXX.V / stock01.V`，再 clamp、round RGB | 混合族用 Base/Sss **联合精确端点** mask；袖口用实际 UV 消费且含双线性边界的 mask；帽徽保留原 8-bit 连续覆盖率；发尾只改认证 tile。Color01 bypass，所有 alpha、皮肤、区域外像素及控制图保留 |
| `M/build_fd_color_textures.py` | 从已转色 Body 的 glove/cuff 两族各通道独立双线性缩至 992×992，edge pad 16，再左右拼接 | 先用原图精确重建旧 FD RGBA，再输出各色 FD Base/Sss；避免战斗手套与本体不同色或丢 alpha |
| `M/import_color_textures.py`、`match_original_texture_settings.py` | 原生导入后逐域对照 R213，恢复 compression/sRGB、mip/LOD、NeverStream、filter、address、max size 等采样字段 | 32 张 Body 已正确；96 张 HairTail/Hat/FD 的初始默认设置需纠正。全部 128 source PNG 与 Source 内容身份不变；独立 V2 守卫确认原设置 |
| `M/author_color_routes.py` | 克隆每色 10 个现有 MIC，仅改 BaseMap/SssMap 指针；原 Base 表只替换五个 Gold mesh 行对应引用，保留 32 行顺序及重复项 | 16 个 Base 表与 16 个 PawnMaterials，native PreSave 后读回 35 项 `UseMaterials` 池；父链、标量、向量、静态开关和其他参数受独立作用域守卫保护 |
| 同入口的 PTC 路由 | 两个现有 Gold FD `MaterialTable` 行切对应色实例；不改 `ColorTable` 和原行结构 | 普通、FD 和头部共用该色输入，实际 particle consumer 另验，不以表内引用存在代替使用证明 |
| `M/repair_ptc_stock_providers.py` | 对照当前零售，补私有作者工程缺失的 stock Eff providers，然后原生保存原引用 | 修复 Color01–16 四行各一个旧 `[None]`，共 64 项；Color90 四项原本完整。68 个 source Eff 的直接参数/parent 对零售核验；stock 包由认证零售提供，不把作者依赖整个复制进交付 |

PTC 空引用不是一律合法，也不是一律错误。`palette/audit_required_tables.py` 对最终 56 张表按实际零售必需引用、原生合法 null、已获认可的隐藏替换分别验证；保留 8 个辅助隐藏行的既定替换与其他 19 行的零售值，不能为“零 null”抹掉合法结构。Color01 外观保持的声明也不能误写成该色 PTC 逐字节未变，因为其中四个 Eff 引用确实修复了。

`M/audit_color_texture_budget.py` 读取最终 Cooked 格式、尺寸、mip 和 payload 大小：128 张纹理逐域与 R213 相等。每套被转色纹理合计 192,919,360 GPU bytes，16 套文件目录的对应 payload 合计 3,086,709,760 bytes；后一个数不是所有颜色同时驻留显存的声明，两种同场颜色仍各需自己的分配。不能只凭 PNG 尺寸声称预算未增加。

## 7. 同一最终输入的验证与交付

最终 V2 输入由 `FINAL_COLOR_AUTHOR_INPUTS_V2.json` 锁定。`native_scene/audit_all17.py` 与 `audit_representatives.py` 合并为 `FINAL_V2_NATIVE_PREVIEW_RECEIPT.json`：41 张 2560×1440 原生 GPU 图，17 色双方普通姿态、Color12–16/90 的代表 LH，以及 Color12/13/90 的实际 FD particle；1,980 条普通/过渡代理加 2,808 条代表场景代理，共 4,788 条、零默认材质回退，另有 736 次 loading 精确 GT/RT shader 查询。独立视觉 reviewer 逐张看过 41 图，未发现阻塞配色回归；保留烟雾/FX 遮挡和小脸细节不可据远景验收的限制。制作脚本、图片与报告哈希均绑定同版输入。

`M/freeze_and_cook.py`、`freeze_delivery.py`、`finalize_delivery.py` 输出只含本轮必要替换的清单：342 包、684 Cooked companions、3,090,983,762 bytes。`FINAL_VALIDATION_RECEIPT.json` 对 root 已取走的 immutable manifest 补充最终证据，确认 payload ledger 未改变；不要用整个临时 Cook 目录替代交付集合。依赖只认可本轮交付、保留的 R213 包、认证的当前零售 provider。该批没有网格、骨架、morph、动画、物理或音频文件；整体 MOD 的历史制作影响另按[判定数据与动画间接定位审计](gold-r214-gameplay-preservation-example.md)分层证明，不能由“本轮未改”推成全项目未改。

集成者把保留 R213 与本轮 delta 合为一个 PAK：1,327 包、2,655 文件、181,700,613 bytes；`PAK_VALIDATION.json` 记录 create/test/list/extract 后所有解包文件哈希与最终清单相等，PAK SHA256 为 `eb5a40ed828253f411ef5c8d8a86825200543eabdd274e5655c157270c0551da`。该建包收据的 `installed=false` 是当时阶段状态，不改写它冒充后续安装证明。

独立 ZIP 与安装迁移已另有收据，见第 9 节；用户零售体验仍待确认。原生 BTL fixture 调用了真实材质/PTC 消费者，但没有执行完整异步 CharaSelect UI 状态机。没有把作者预览、Cook 字节证明或安装成功写成用户试玩通过。

## 8. 失败探索应保留的界限

| 尝试或漏项 | 为什么不够 / 纠正方法 |
| --- | --- |
| 从 `Material not found` 猜缺包 | 先定位 `GetShader`，恢复精确 VF/type；别把丢失 Resource 堆补成确定名字 |
| 只查最终颜色 imports、只看 usage 标志 | 动态 Loading/Hidden 与所有类别槽也要枚举，实际 shader 和 SceneProxy 分别读回 |
| 把较旧同签名 dump 绑定到重启后的 PID | 用 dump header UTC、运行时长和进程启动记录分开归属 |
| 磁盘受保护代码乱码反汇编 | 标为无效指令证据，转用经身份验证的静态类型与可读字面量 |
| 统一按现代 64-bit export 格式读旧 Hidden | 按 package version 508 的 32-bit serial size/offset 分支解析 |
| Cooked 包已加载、exact shader 又存在 | 本案 frozen layout 被拒后发生 Editor 重编；必须检查 inline 位，失败路线不改称成功 |
| 只重新编译一个 shader 就称最终包通过 | 读取正确 target cache，并绑定最终 `.uexp` 的 index/hash/完整 code bytes |
| 贴图默认导入设置、只看作者图正确 | 恢复各域原采样设置，再查 Cooked mip/format/GPU bytes；V2 是最终接受版 |
| 原作者 Eff 指针非空就视为 Cook 后仍存在 | 查实际 Cooked 表；缺作者 provider 会丢引用，恢复认证 provider 后重读最终表 |

这些是制作期诊断和离线原生资源修复，没有新增运行时桥，也不向安装器添加 EXE/build 白名单。

## 9. 单 PAK 便携迁移：按收据归属，保留其他设置

私有工具根为 `work/retail_portable_r214`。制作工具与朋友用分发包分开：`Build-Package.ps1` 只整理整合者已完成的单 PAK、验证文件/ZIP 内容，不执行 UE、Python、UnrealPak 或 Cook。输入 manifest 必须有 `resource_status=integrator_finalized`、相对 PAK 路径、大小和 SHA256；不完整资源及未知额外组件拒绝。测试脚本、fixture 和构建工具不进入朋友安装 ZIP。

具体调用顺序为 `Build-Package.ps1 → Retire-R213.ps1` 默认只读预览 `→ Retire-R213.ps1 -Apply → Install.ps1`。游戏目录由明确参数或 Steam 注册信息/libraryfolders/安装清单定位；不唯一时要求选定。Unverum 可选，若退役凭据记录了管理器，则必须匹配那一个目录。

| 工具 / 问题 | 实现方法与验证点 |
| --- | --- |
| `Retire-R213.ps1` | 仅认旧产品、旧 receipt、exact owned 路径/命名和 PAK/SIG hash；支持同模组经 Unverum 重映射与数字优先级的文件。先备份并校验到整个 Paks 树之外，再逐文件移除；不递归清目录，不猜无凭据安装归属 |
| `Install.ps1` / `Portable.Common.ps1` | 校验分发包的长度/hash，只安装一个 PAK；SIG 从目标游戏当前主 SIG 复制为伴随文件，不声称重新签名。无需开发依赖，也没有 EXE/Steam build 白名单；不修改游戏 Config、save、Binaries 或已有 loader |
| Unverum 设置 | 只增删本模组被跟踪的 name/path/PAK 属性；旧空行禁用，保留手动 metadata、其他 loadout 和全局设置。配置快照与实际变更单留档，不能用整份旧 Config 覆盖用户后续改动 |
| 同 hash 预放文件漏登记 | 旧快捷返回不写 `changes`，会使卸载/下一版退役失去归属。新版本仍备份、记录同路径同 hash 的预存 PAK/SIG；卸载恢复其预存状态，不能无凭据声称它们是本次创建的文件 |
| 朋友机还在 R212 | 新安装同时阻止有效 R213 与 R212 receipt。R212 由对应旧版退役/卸载工具处理，不以宽泛删除旧 Gold 名称的方式避免叠装 |
| `Uninstall.ps1` | 按本次 receipt 和安装后 hash 操作，可识别本模组的重映射路径；用户改过的文件保留并报告，有备份才恢复。安装失败按自己的事务回滚，不悄悄重新启用旧包 |

`Test-Migration.ps1` 在 Windows PowerShell 5.1 的私有 sandbox 中实跑 28 项调用/断言：管理器/独立安装、旧包重映射、整个 Paks 外备份、同名同 hash 的其他 MOD 保留、修改文件拒绝、同 hash 预存收据、旧 R212 阻挡、当前 SIG 更新、不同 EXE 字节、包损坏和未完成资源拒绝、配置/save 保护等。文本 PAK/SIG/EXE 为明确标记的替身，不执行假 EXE；普通安装拒绝 synthetic fixture。`MIGRATION_VALIDATION.json` 是这批合成测试收据，不能替代真实安装。

本轮实际独立 ZIP 已构建：169,990,481 bytes，SHA256 `0793aba961567ab522d0f2d35ee6ad5921fb7a00728df400dd5144bcf90356c4`。`GoldShip_R214_20260922.build.json` 记录单 PAK、非 fixture 与分发 manifest 指纹，状态仍为 `BUILT_NOT_RETAIL_VERIFIED`。

`work/retail_deploy_r214/INSTALLATION_RESULT.json` 记录真实安装完成，游戏端 receipt 为 `state=installed`：live PAK/SIG、Unverum library PAK/SIG、manager config 共五条变化均已应用。旧 R213 四个精确归属文件已备份到整个 Paks 之外并退役。集成者核实非本模组的 Unverum 配置保持、其他 22 个 PAK 的大小/mtime 未变、旧 R210 桥磁盘配置继续禁用；大小/mtime 检查不写成另做了全量其他 MOD 内容哈希。新 PAK 与构建收据 SHA 一致，SIG 来自目标游戏当前主 SIG。

最终 `FINAL_INTEGRATION_CONTRACT.json` 将材料、PAK、保护载荷、判定审计和安装结果连起来。文档 lane 只核对并快照小型收据、manifest 哈希和阶段关系，没有重算全部 PAK、重安装或启动游戏。迁移工具准备时 `real_game_modified=false` 的交接记录保持其历史意义，不覆盖成事后成功。`retail_visual_accepted=false`、`user_all_color_accepted=false` 与 `game_launched_by_agent=false` 继续保留：安装完成不等于换色、视觉、语音或判定的用户实机验收。
