# Gold R213：已确认修复的方法与脚本索引

本页补充“具体由哪个脚本把什么输入变成什么输出”。原因、实际字段、失败探索和测量细节仍以各项链接的案例正文为准。这里的通过指对应版本的作者、Cook 或开发引擎原生消费者检查，**不表示用户已经验收 R213 零售成品**。

以下路径都是私有案例工程的相对证据标识，不是随 harness 安装的命令。脚本依赖原资产和匹配的引擎工具链；不要按此表盲目重跑作者脚本。先确认当前输入哈希、唯一资产作者和冻结版本；已通过且输入未变的检查复用原报告。修改输入后只重做受影响的检查。

为缩短表格，使用这些相对目录：

| 记号 | 私有相对目录 |
| --- | --- |
| A | `work/retail_visual_r213/animation` |
| V | `work/retail_visual_r213/victim_head` |
| F | `work/retail_visual_r213/fx_anchor` |
| M | `work/retail_visual_r213/materials` |
| G | `work/retail_visual_r213/ground_shadow` |
| S | `work/retail_visual_r213/sol_rigid` |
| K | `work/retail_fatal_r212/reference_audit` |

## 1. 选人头部来源与 ADV 原图

字段、基线失败和原生组件方法见[选人/ADV 案例](gold-retarget-example.md#r213-补充按原生消费者补齐选人与入场)，指纹见[RA 证据索引](gold-r213-native-consumer-evidence.json)。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `A/route_audit/audit_entry_routes.py` | 当前零售脚本、AnimArray/AS、ADV AB、R212 覆盖清单 | `CURRENT_ADV_SCRIPTS.json`、`CURRENT_ADV_TABLES.json`、`CURRENT_ADV_BODY_AB.json`、`R212_COVERAGE.json`；先确定真实消费者，避免从已做文件反推覆盖 |
| `A/prepare_private.py` | 已修 R212 私有作者和依赖 | 独立作者副本、`PRIVATE_INPUTS.json`、原 low-head 备份；避免写穿共享资产 |
| `A/select_fix.c.in`、`adv_fix.c.in`，由 `build_helper.py` 组成作者工具；`run_private.py` 执行指定模式 | 原 low-head EventGraph、原 ADV body 图与已批准 pivot/tail 阶段 | low-head 按 `DoesSocketExist` 选择 attach parent 或 `REDPawn.GetMeshComponent("body")`，连上 getter 执行链并加 tick prerequisite；ADV 只在原 82-pose-node 图末端加六阶段，保全部28 Slot |
| `A/compare_graph.py`、`check_adv_body.py` | 作者前后节点/属性/引脚记录、原 ADV 控制组 | 图差异和身体旧骨对照；只归一化编译分配的 LinkID，不忽略整图差异 |
| `A/native_pose.c.in`、`native_adv_pose.c.in` 与相应 `run_pose.py`、`run_adv_control.py`；`validate_pose.py` 汇总 | 实际原生 select/ADV SetupMesh、各自 SetupLinkBone 规则、原生时钟 | `NATIVE_POSE_GUARD.json`、`native_adv_control/BODY_POSE_COMPARISON.json`；覆盖28选人样本、56 ADV样本和原图控制 |
| `A/cook_ab.py` | 冻结的两个原路径 AB | `AB_DELIVERY.json` 的四个 Cook 文件；字段安全仍由下文 Kawaii 守卫单独确认 |

**保留的失败经验：**有效 RootComponent 不等于有 pivot socket；只连 BlueprintCallable 的返回值可能被编译器裁掉；Default body 的少量 Slot 不能替代完整 ADV 图；旧显示 driver 不能证明原生选人路径正确。186.64711 cm 的原生基线误差修到0.00003052 cm，只证明该来源/姿态问题，不代替最终摄影验收。

## 2. 入场 m903–m905 的六条可见动画

时钟、holds、保护范围见[入场分段与原生求值](gold-retarget-example.md#入场900cs-存在不能证明整段已覆盖)。AS 行本来存在；缺的是三条 body 和三条 coat 原路径替换。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `A/route_audit/audit_entry_routes.py` | 当前 BBS/脚本与 cooked 序列 | `CURRENT_M903_M905_CLOCKS.json`；记录92/80/100帧、独立时长、双方起始偏移和 delay |
| `A/entry_body/prepare_and_decode.py` → `build_entry_body.py` | 当前 cooked held poses、已批准 Gold 运输参数 | `source_npz` → `motion`、`special_solver_manifest.json`；保原 raw-to-solution/hold，不对 cinematic 强加接地锁 |
| `A/entry_body/build_ue_tqs.py` → `authoring/prepare_authoring.py` | 解算 world T/Q/S、源 local 和骨名 | `ue_tqs_manifest.json` 与 P/Q/S payload → 原路径作者；按 UE FTransform 分量反推 local，保零 scale 与四元数约定 |
| `A/entry_body/build_coat3.py` → `build_coat_root_payloads.py`，再由 `coat_authoring/run_coat3.py` 写入 | 当前 coat、批准 D 拟合、原 root Q 和非 root 数据 | `COAT_UE_TQS_MANIFEST.json`、`ROOT_ONLY_MANIFEST.json`；只写 root P/S，保披风自己的 hold 表 |
| `A/entry_body/validate_direct_native_pose.py`、`verify_cooked_animations.py`、`verify_cooked_coats.py` | 直接序列 getter、实际 ADV 已求值骨、最终 Cook key/frame table | `DIRECT_SEQUENCE_NATIVE_POSE_GUARD.json`、两份 `COOKED_*_VALIDATION.json`；分开编辑器流与发布 keys |
| `A/entry_body/cook_and_validate.py`、`cook_coats.py` | 冻结的 body/coat 作者 | 六资源的 Cook 伴随文件与 `COMBINED_DELIVERY.json`，再与两个 AB 汇入 `A/ANIMATION_DELIVERY.json` |

**保留的失败经验：**只有900cs不能代表整个入场；m904 coat末帧仍保持前姿，不能补一个模板终点。两个极小纽扣旋转在编辑器 raw/compressed getter 和原 ADV 图中都成为首 key hold，故不能归罪新增图或放宽门限；确切加载减键函数未定位，Cook全帧保真另验。矩阵逆后分解也不能替代 UE 非均匀父 scale 的分量计算。

## 3. VS_SLY 受害者“飞头”

详见[受害者消费者与颈口](gold-retarget-example.md#r213-补充同一招式还要覆盖受害者)及[RV 指纹](gold-r213-victim-consumer-evidence.json)。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `V/audit_routes.py`、`prepare_victim_body.py` | 实际 `VS_SLY` 路由和新鲜原 PAK 中 body/coat/headhigh | `ROUTE_AUDIT.json`、`CURRENT_SOURCE_EXTRACTION.json`；区分攻击者与受害者，不复用攻击者覆盖结论 |
| `V/body/build_entry_body.py`、`build_ue_tqs.py` 及作者工具 | 受害者当前128帧和独立 holds、批准 Gold solver | 受害者 body 原路径作者；不挪 head attachment |
| `V/coat/build_payload.py`、`build_coat_root_payloads.py` 与 coat 作者 | 当前 coat、批准 D 拟合 | coat root P/S；保 root Q、非 root P/Q/非空 S，记录167条空S被codec规范化成单位轨 |
| `V/measure_head_contract.py`、`validate_full_native_body.py` | source/current/candidate 的组件变换、attach link和465根已求值骨 | `HEAD_ATTACHMENT_NUMERICAL.json`、`NATIVE_FULL_BODY_GUARD.json`；定位身体支点偏差，不用截图单独推断脱头 |
| `V/analyze_neck_surface.py`、`validate_neck_seam.py` | 同一冻结网格的 CPU skin 与 PDB确认的LOD索引/section | `NECK_SEAM_GUARD.json`；57点/57边对应和未经取整的距离，补上 anchor不能证明的皮肤接缝 |
| body/coat各自 `verify_cooked_animations.py` / `verify_cooked_coats.py` → `V/finalize_delivery.py` | 所有 keys/holds、作者和Cook文件、骨姿/接缝守卫 | 两原路径资源、四个Cook文件的 `DELIVERY.json` |

**保留的失败经验：**攻击者适配完成不代表受害者完成；组件挂接本来正确，移动头会修错层。30.0923 cm的解剖支点误差修到6.652e−5 cm；约0.099 cm的原绑定残差前后均在。57点皮肤边界的最大差0.0000305176 cm证明被质疑姿态的几何接合，不能升级成全动画或材质法线连续性通过。

## 4. 只移动获授权的 LH 手部火焰

模块代数、出生帧与时钟限制见[限定火焰修复](gold-retarget-example.md#r213-补充只修一个-last-horizon-手部火焰挂点)，指纹见[RF 索引](gold-r213-fx-anchor-evidence.json)。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `F/route_audit/collect_routes.py`、`detail_particles.py`、`emitter_timing.py` | 当前BBS、ParticleData、socket和粒子子对象 | `CURRENT_LH_BBS.json`、路由/时间记录；确认501动作实际用500包，charge独立保护 |
| `F/build_fx_lane.py`、`run_scene.py` 与只读 `source/GoldFxTraceR213.c.in` | 匹配引擎、原相机宏、原生body/PSC | `runs/*/fx_trace.jsonl` 与740/780/820/900原图；记录骨、PSC、发射器和粒子payload |
| `F/prepare_candidate.py` | `PIVOT_GEOMETRY.json`、基线body/PSC/EmitterTime记录 | `OFFSET_CURVE.json` 和私有作者工具；186个PSC本地Step点，五个早段emitter加四Orbit，旋转/角速度置零，`bCanBeBaked=False` |
| `F/route_audit/review_offset_clock.py` | 原/候选模块时钟、Rate、正常与异常dt条件 | `OFFSET_CLOCK_REVIEW.json`；区分发射轨迹等价与内部LoopCount/完成时间变化 |
| `F/verify_native_payload.py` | baseline/candidate trace的原粒子与新模块payload | `NATIVE_PARTICLE_GUARD.json`；原128字节及旧模块完整保留，核新生D_birth/后续D_now/PreviousOffset |
| `F/route_audit/finalize_author_guard.py`、`finalize_cooked_guard.py`，`F/cook_particle.py` | 按完整outer路径匹配的作者前后和最终Cook | 作者/发布字段守卫、`PARTICLE_DELIVERY.json`；只交单包两文件 |

**保留的失败经验：**全局socket或常量世界偏移会误伤范围；Bone/Socket Location覆盖位置并重置mesh rotation；Update-only Orbit漏掉新生首帧；Loops=1仍会回绕EmitterTime；默认distribution烘焙会把Rate阶跃变成斜坡。四模块按Add/Scale/Add/Add保出生、当前与上一帧偏移，且只在已验证的原生短步长、正常出生和BBS生命周期下等价，不能承诺异常初始化也等价。

## 5. 身体13材质族错采肤色

完整根因和四层证据见[UV类型序号案例](gold-material-example.md#10-r213贴图正确cook-后却让衣服手套和鞋全采到肤色)，指纹见[材质修复索引](gold-material-r213-evidence.json)。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `M/diagnose_native.py`、`read_native_uv.py` | 实际native mesh与材质参数 | 原生UV和消费者基线；区分图集正确与采样坐标正确 |
| `M/repair_uv_metadata.py` | 冻结 `GoldBodyNativeTail7_R211.fbx` | `GoldBodyNativeTail7_R213.fbx`、`FBX_REPAIR_PROOF.json`；只修LayerElementUV类型数组顺序/连续编号/Layer.TypedIndex及唯一层名，保数值和其他字段 |
| `M/build_inspector.py`、`inspect_fbx.cpp` | 前后FBX | `sdk_before.txt`、`sdk_after.txt`；由FBX SDK实际Layer读取证明路由，不只读原文本 |
| `M/import_body.py` → `write_original_body.py` | 已修FBX、原mesh作者合同与review导入 | 原路径`sly_body`；恢复`Materials`、`LODMaterialMap`、`OutlineMaterialIndex`、`DamageLevel`，重新导出`sly_body_after.fbx` |
| `M/verify_native.py`、`verify_skin.py` | 实际fresh native导出和冻结原输入 | `NATIVE_UV_REPAIR_GUARD.json`、`FULL_SKIN_WEIGHT_GUARD.json`；13族UV3.x=0–12与全部473clusters的权重/bind保护 |
| `M/cook_body.py` → `verify_cooked.py` → `finalize_delivery.py` | 冻结原路径作者、实际Cook render buffer | `COOKED_UV_REPAIR_GUARD.json`、`delivery/MANIFEST.json`；仅一mesh、两Cook伴随文件 |

**保留的失败经验：**“FamilyUV存在且数值正确”不证明SDK按它读；TypedIndex是类型数组序号，稀疏标签不是独立键。身体错误指向旧UV，鞋/手套越界变成UV NONE；重新上色、加分辨率或补参数不会修复此问题。四权重glTF不能证明完整蒙皮。冻结delivery早期写有shader preview待验状态，后来独立`NATIVE_SHADER_PREVIEW.json`补足开发UE画面证据；不改旧清单伪造同次验收，零售仍待。

## 6. 身体地影缺失

详见[section地影案例](gold-retarget-example.md#r213-补充只有披风地影先查网格-section)及[RS 指纹](gold-r213-ground-shadow-evidence.json)。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `G/prepare_probe.py`、`run_probe.py`、`read_pdb.py` | 原角色/Gold native组件与匹配引擎 | baseline/source trace、`PDB_LAYOUT.json`；区分组件`CastShadow`与RenderSection开关 |
| `G/prepare_flag_trial.py`、`flag_trial.py --body-only` | 已修13UV族身体和原natural作者 | 原路径body的14段、natural的2段`bCastShadow=True`，同步`UserSectionsData`并scoped `PostEditChange`；重存后恢复输入材质UV-density |
| `G/verify_author.py` | 冻结作者、写入前后mesh记录 | `AUTHOR_MESH_GUARD.json`；保P/N/T/B、VC、全部UV、12槽权重、骨/bind、材料与ASW表，列明原生规范化例外 |
| `G/cook_bodies.py` → `verify_cooked.py` | 原/新cooked body与natural | `COOKED_MESH_GUARD.json`；完整export仅14＋2布尔字节变化，复原后整段精确相同 |
| `G/prepare_movement.py`、`run_probe.py` movement → `finalize.py` | 站立、前进、蹲姿同原生相机图与trace | `NATIVE_MOVEMENT_GUARD.json`、`HEAD_PATCH_CONTRACT.json`、`DELIVERY.json`；身体两包四文件，头部交唯一作者合入 |

**保留的失败经验：**组件CastShadow=True、Bounds相同仍可每段不投影。该ASW importer按槽名中的小写`shadow`初始化section开关；无需先做影actor或新影子网格。该分支开关也影响early depth，必须看主pass/遮挡/描边。地影试验没有修好SOL失框，不能合并结论。Natural当时隐藏，只有数据守卫；头部合同不等于最终三头艺术验收。

## 7. SOL组件材质正确，实际绘制却退回默认材质

实际消费者证据、映射示例和排除路线见[材质替换案例](material-consumer-fallback.md)与[SOL指纹](gold-r213-sol-material-consumer-evidence.json)。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `S/audit_morph_material_index.py` | fresh native section、LODMaterialMap、全部stored morph覆盖 | `MORPH_RAW_VS_DRAW_MATERIAL_ROUTE.json`；raw口内section6误选slot6，实际口内画slot4、镜框section10画slot6 |
| `S/shader_audit/sol_renderproxy_insertion.c`、`sol_compiled_material_insertion.c`、`sol_sceneproxy_insertion.c` | 匹配DLL/PDB、实际原生组件、已flush checkpoint | GT/RT、编译资源、真正SceneProxy缓存逐层trace；仅最后一层证明两个镜框均被换成WorldGrid而组件MID未变 |
| `S/prepare_frame_base_morph_candidate.py` | 原stock master、SOL中间实例与原路径leaf | 私有原图克隆仅`bUsedWithMorphTargets=True`；中间实例保全部参数，leaf只换私有父链 |
| `S/verify_frame_base_morph_candidate.py` | 保存后的候选和原三层链 | `frame_base_morph_candidate/INDEPENDENT_GRAPH_GUARD.json`；432表达式/输出/参数GUID/有效参数精确，明确排除重编译缓存与资产身份 |
| `S/prove_sol_fix.py` | 修前/修后proxy trace及同普通镜头原图 | `PROVEN_SOL_MATERIAL_CONSUMER_FAILURE.json`；24sections全部cache=component、default fallback=0，双向框片完整，保P2 idle姿态差异限制 |
| `work/retail_visual_r213/face/native/run_sol_ratio.py` 的指定label/manifest入口；`work/retail_visual_r213/eyelid_native/cook_accepted_sol.py`、同目录`freeze_accepted_sol.py` | 已核候选、唯一场景/作者工程与明确运行label | 场景input snapshot/恢复记录、最终三资产六Cook文件及第2版清单；名字中的ratio是复用的私有夹具，不代表把0.2倍率纳入最终方案 |
| `S/verify_sol_stock_providers.py`、`verify_accepted_sol_cooked.py` | 已冻结三作者、六Cook文件、实际原PAK索引 | `ACCEPTED_SOL_RETAIL_STOCK_PROVIDERS.json`、`ACCEPTED_SOL_COOKED_INDEPENDENT_GUARD.json`；用途flag/父链及24stock外部来源确认 |

**保留的失败经验：**刚性几何、组件GT/RT标量和编译map都正确仍不等于actual draw。描边倍率0.2、等语义重编译、投影标志试验都未修失框，不能混进最终修复。缺框跟随Z=−3只是线索；决定性证据是SceneProxy替换。用途检查在有活动morph后遍历全部stored morph、使用raw MaterialIndex，而绘制用LODMaterialMap；离线启用所需用途即可，未改引擎索引逻辑。FaceSkin试绑和RenderDoc后续捕获取消，不能写成已执行证据。

Cook清单第一版误把临时Cook目录存在的依赖视为交付闭合；第2版改为精确交付/继承/原游戏provider。修正的是来源声明，六文件字节未改，不因此整拷原游戏依赖。公开可运行的[合成示例](../examples/material_consumer_fallback_demo.py)只展示该路由控制流，不渲染GPU。

旧候选manifest的“未Cook/未接受”和早期探针的“suspected”描述当时状态；最终范围由hash绑定的proof和交付清单确认，不重写旧证据制造同一次成功。

## 8. R212 Kawaii 仅编辑器字段导致选人 Fatal

严格证据链见[Cook字段兼容案例](cook-install-example.md#9-制作蓝图时就排除仅编辑器存在的成员)和[Kawaii字段证据指纹](gold-r212-kawaii-field-evidence.json)。`Guid` 的字符串出现不是判据，必须解析声明owner与指令操作数。

| 顺序 / 实现 | 输入 | 输出与检查目的 |
| --- | --- | --- |
| `work/retail_fatal_r212/dump/inspect_dump.py`、`report_frames.py`、`correlate_bytecode.py` | 已归档minidump、匹配映像、cooked函数 | 帧/脚本偏移报告；不从缺失堆凭空声称读到实例名称 |
| `K/audit_kismet_refs.py`、`decode_generated_properties.py`、`reconstruct_retail_layout.py` | 完整Kismet、生成类属性顺序、实际零售native大小/对齐 | `COOKED_STRUCT_REFS_SCAN.json`、生成布局；交叉定位low-head及56无效owner/member引用 |
| `K/private_fix/prepare_private.py`、`build_helper.py`、`fix_helper.c.in`、`run_private.py` | 原四头AB及独立依赖副本 | 逐 `K2Node_StructMemberSet` 枚举 `ShowPinForProperties`，解析native属性的`CPF_EditorOnly`；28个Guid置`bShowPin=False`，旧未连pin调用`SetSavePinIfOrphaned(false)`后reconstruct，再compile/save四AB |
| `K/private_fix/validate_private.py` | 编辑前、保存后、fresh进程反射和碰撞计算结果 | `AUTHOR_AND_FRESH_GUARD.json`：1041节点/274 CDO记录保护、252位置尺寸检查；不删除Kawaii功能 |
| `K/compare_kismet_semantics.py`、`audit_all_kawaii.py`、`native_owners/join_cooked_refs.py` | 修前修后严格解码指令、目标native owner字段集合、完整包imports | `FIXED_KISMET_SEMANTIC_GUARD.json`、`FIXED_ALL_KAWAII_REFERENCE_GUARD.json`；只减28赋值、其余控制流/常量不变，所有实际字段解析 |
| `work/retail_visual_r213/audit_final_kawaii.py` | R213实际staged包和新增ADV消费者 | `KAWAII_FIELD_GUARD.json`；针对新输入重新扩到六AB/14节点/2554引用，不照抄R212五AB的计数 |

**保留的失败经验：**只列runtime optional pins仍可能重建出默认显示的editor-only pin；编辑器函数能执行、Cook成功、依赖包存在都不证明Shipping字段存在。不对cooked字节码做十六进制删除，不因Kawaii出现在堆栈就移除物理求解器。另有DDC路径过长和UTF-8报告被默认GBK读取的工具失败：保留日志，修路径/显式编码后利用已成功输出，不无故重复UE运行。

## 9. 第八类：眼褶与鼻线的具体构造

完整的脚本输入输出、1323 形变和非鼻保护合同、鼻线失败探索顺序见[线条实施案例](gold-r213-linework-example.md)及[证据指纹](gold-r213-linework-evidence.json)。眼褶长三角内部穿皮已有定位；鼻线最终是鼻梁侧位置、尺寸和整片贴面的组合改善，旧鼻 GPU 偏淡机制尚未证实，不能套用眼褶根因。

鼻梁侧 BRIDGE 在原后处理的 2K 局部镜头中已由 root 接受为试玩候选；共同三头源、fresh native、最终一次 Cook、同版 323 张请求原生图审和交付清单收据已齐。近闭眼细浅亮带及远景/后脑/FX不可细判范围明确保留。该技术记录不代表用户美术决定或零售验收。数值守卫、实际原生预览和用户决定必须分开保存。

## 10. 第九类：成品语音与原生 SoundWave 容器

详见[音频实施案例](gold-r213-audio-example.md)及[证据指纹](gold-r213-audio-evidence.json)。显式映射把 398 条已转换成品对应到 401 个替换资产，64 条原音对应 66 个保留资产；本轮只做一次 q10 编码和原容器 inline OGG 替换，没有再次升调或调音量。全部 398 完整解码、401 包独立回导、802 文件哈希通过，保留原音与原 OGG 解码逐样本一致。记录具体 bulk/export/summary 长度字段、未知布局拒绝和 0.106433 dB 编码偏差闸的复核，不声称零售播放或逐条人工听辨验收。
