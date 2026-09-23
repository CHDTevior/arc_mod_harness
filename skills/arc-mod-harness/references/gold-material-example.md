# Gold 身体与鞋：从统一色到实际材质的 worked example

适用于“贴图文件齐全，但细节/肤色/受光仍不对”的迁移工作。先读
[纹理、UV 与材质](texture-uv-material.md)；本页补实际操作、数据合同和验证范围。
以下 R191/R196/R198 数字来自 Gold/Slayer 私有制作案例，不能直接当其他角色参数。
末尾的 JSON 是**合成的可读配置例**，不代表本案例实测结果，也不是 harness/UE 导入器输入。

主要报告的相对标识与SHA256见 [案例证据索引](gold-demo-evidence.json) 的G08–G14。
下文MAT编号对应本页末尾的来源分组；原报告与游戏资源未分发，摘要不是重新执行验证。

R213 后续原生资产案例见 [组件材质正确却发生绘制材质替换](material-consumer-fallback.md)：
表情用途检查与 section 映射不一致，必须核对场景代理真正消费的材质。旧桥式参数同步记录
不作为该问题的修复方案；新例附可运行的纯合成控制流示例。

## 1. 先分清没有坐标、坐标错路和没有细节

旧身体使用16×16统一五图，首导出层是仅61个唯一坐标的旧眼妆字段
`HC_EyeMakeup_RestXZ`；真正继承的 pigment UV 是第6层 `UVMap`，Detail 是第2层
`UVMap.001`。统一色掩盖了采错层，换上供体图就会串色。[MAT01]

鞋的情况不同：R191前 `R142_Boots` 有7,164点/13,506三角，却没有任何UV层，只有
`R190_REST_BootIvory` 统一材料。增加纹理分辨率不会补出缺失的图案坐标。[MAT02]

操作：逐对象列出每层名称、索引、唯一坐标数、实际数组、材质采样通道和最终FBX层序。
保留原层归档；为生产层使用唯一名称，重新导入后按实际坐标核对索引。不能只比较层名，
也不能把供体Detail的点/线状坐标一律当坏UV展开：它可能就是作者指定的固定或Wrap取样。

## 2. 先确定来源，再搬图与控制

身体供体是用户提供的 **Nude Jam MOD**；官方莎伦提供暖肤色参照，官方Slayer专用身体
提供肌肉/结构对照。MOD身份不能写成官方Jam。该MOD覆盖四张图，没有材质实例或OLM覆盖；
OLM明确使用当时游戏原版Jam Color01作为补足。[MAT01]

沿原顶点/面角来源和三层供体UV追到真正的采样域。身体新图域的每个目标像素先求所在
目标三角的重心坐标，再用**同一面角对应**插值供体UV：Base/Sss/Ilm/Olm读源UV0，
Detail读源UV1。用原来的Wrap与双线性读RGBA原始数值，保留连续边缘，不硬量化成纯色。
新建颈/胸局部没有可靠来源时列出明确范围；本例10个诊断到的坏lookup面使用已定基线值。

对应可信度按字段分开记录。R196的VC侧表只证明43,628/55,837角，另12,209角未匹配，
含264角颜色歧义；这些fallback值不能算供体继承。后来N恢复重新建立了完整有序面角谱系，
没有把这份VC表当无歧义N映射。同位置、同UV仍可能有不同split N。[MAT01、MAT06]

## 3. 同一图域制作五图，并量实际覆盖

身体创建4096²专用atlas；鞋按几何组件/表面角色展开，设计白壳、棕护片、红结、金饰等，
不复制源照片中的高光/AO。鞋制作时保留分区材料便于编辑，导出时合并为一个atlas材料槽，
替换旧鞋槽，不要求运行时凭新增DCC槽自动建立路由。[MAT01、MAT02]

| 本例生产层 | 身体名称 | 鞋名称 | 使用者 |
|---|---|---|---|
| UV0 | `R196_BodyAtlas_UV0` | `UV0_Shoe_R191` | Base/Sss/Ilm/Olm |
| UV1 | `R196_BodyAtlas_DetailUV1` | `UV1_Shoe_Detail_R191` | Detail |
| UV2 | `R196_BodyAtlas_AlternateUV2` | 本例鞋仅导出上述两层 | 身体alternate分支；布局与UV0相同 |
| UV3–5 | 三份供体坐标存档 | 不适用 | 身体制作追溯；不是当前皮肤采样层 |

身体18,615三角全在0–1、正面积重叠0；实际覆盖33.20%，最差方向密度中位1.679px/mm、
P1为1.194px/mm。鞋13,506三角同样域内/无正面积重叠，覆盖37.51%，中位2.403px/mm。
这些是此体型的测量，不是通用最低密度。[MAT01、MAT02]

身体104个极薄三角无像素中心命中：按边/重心向空闲像素保守落值，余下借相邻合法表面
padding供值，逐面记下实际填充数。鞋先扩大10个无独立图案薄面的UV载体，余3个同样
记录保守落值；不能以“UV有面积”声称每面都有独立纹理样本。

五图共享同一covered-owner表向空域扩边，本例32px排布余量；鞋保证至少16px padding。
鞋用每面7个重心采样，共94,542点，在4096→256的box缩小/bilinear读取中未见跨角色岛
或黑底污染；这不是UE压缩、驻留或任意更低mip验证。[MAT02]

AA（抗锯齿）与控制alpha分开。身体保留供体双线性连续取样；鞋用连续曲面参数及
smooth过渡画窄线。本例没有全表面多子样本AA通过记录。若改为子样本重烘，应只累计
命中且归属合法的样本，另外存覆盖率，不能以覆盖alpha替换游戏控制A；方法见前页第6节。

## 4. 写出参数、通道和编码合同，再接真实实例

下表只对应本例已追踪的GGST着色族，不能作为通用PBR材质解释。[MAT01、MAT03]

| UE纹理参数 | 通道意义 | 本例导入/控制 |
|---|---|---|
| `BaseMap` / UV0 | RGB固有色；A参与rim控制 | 全图sRGB=false，LinearColor；身体A=0，保留其RGB，不接透明度 |
| `SssMap` / UV0 | RGB独立暗部色；A参与TasteGradation | sRGB=false；本例保存身体A=0，不由Base颜色推算整张暗部 |
| `ilmMap` / UV0 | R高光强度，G受光/深度/VC阈值，B高光step区域，A描线混合 | sRGB=false；不能按normal map或PBR粗糙度导入 |
| `detailMap` / UV1 | RGB与ILM.A共同控制内线/填色；此主图A未用 | sRGB=false；`Lerp(innerline端点, shadedBody, ILM.A * Detail.RGB)`，端点未必黑 |
| `OutlineMulMap` / UV0 | 描边/内线颜色乘数 | sRGB=false；按真实outline实例与函数图核用途 |
| 顶点色VC | 独立线性控制值，参与受光和描边等 | 本例两身体实际导出均为`[1,1,.85,.14]`，**全供体继承未完成** |

材质追踪到真实实例：本例主链
`MI_GoldMorphBaseColor_R177 → MI_GoldMorphBaseBase_R177 → M_GoldMorphBase_R177`，
描边有对应Outline链。运行同步从当前body0或body17的同一源pass复制动态参数，然后恢复
各部件自己的五图；只改纹理文件或DCC材质名不能保证生效。

在已采样的头/身体状态中，69标量、35向量相同；例如共享`LightColor=(.5,.5,.5,1)`，
特效时`PointLightColor`随事件改变。这些是本例读回值，不是建议固定给所有角色的常量。
比较Parent、实际纹理对象、scalar/vector值及取样UV，不仅比较参数数量。[MAT03、MAT05]

PNG导入关闭zero-alpha RGB填充；不做控制通道gamma或绿色翻转。R196五张加R196B两张
替换图的已保存SourceArt，经正确处理TSF_BGRA8字节顺序后与合同PNG逐RGBA一致，
包括A=0处RGB。实存sRGB=false、`TC_VectorDisplacementmap`、NeverStream=true；
这不是源DXT压缩复刻，也不证明GPU格式/运行mip。压缩与streaming应由目标平台另验，
不要把这次隔离预览设置推广为发布要求。[MAT04]

## 5. 头身先同公式，再判断需不需要改色

R196旧DCC头将Non-Color Base直接接Principled，身体却使用五图、末端Power(2.2)和
不同roughness/emission。同一原始RGB`(238,199,174)`在两套显示路径约成
`(247,229,215)`与`(239,200,175)`，白颈边界因此不能直接证明身体Base太暗。[MAT03]

先让两者共享完整预览公式、光照和色彩管理，并保留源像素；白颈切口明显消退。
再只试局部控制连续性：R196B中央颈ILM渐变到`(50,128,0,255)`，OLM到
`(36,23,32,255)`；Base/Sss/Detail文件逐字节不变，没有漂白全身或新增gamma补偿。
这是两步因果检查；匹配DCC公式仍不等于最终原生肤色已接受。

## 6. N场独立于贴图；每种身体按自己的REST运输

早期灰模重建只带P/面/UV/权重、没有回写N，丢了供体角方向。R198按确定性删面/焊接、
原点映射和有序面角恢复55,464角来源，保护373生成角；同法线映射不能由最近表面代替。
源cooked N与面积加权几何N不同，只证明存储场不同，不能单凭偏差宣称全部人工逐点调整。

第一轮只改8,300腿角；R198B共24,124角，增加肩臂/前胸/侧接。用准确点对应估计局部
REST变形并逆转置运输，改/保边界沿拓扑渐退。腹前、肚脐、背腰、手足及获准颈脸保护域
保持，不能为了消影把膝、肩、腋下大结构一并抹平。[MAT06]

穿衣与自然身体的胸部支撑形状不同，因此保存`N_candidate_clothed`与
`N_candidate_natural`；独立自然体残像也使用后者。六个base/outline消费者分别
检查，不能把穿衣N或旧整个场景复制到自然体。贴图/UV可共享，不代表所有N场可共享。

## 7. 同姿态实际镜头才是受光对照

R198B实际Battle比较315横踢与826脱衣前冲，带完整角色材质和同期原披风；826取强
冲击FX遮挡前。两次295待机处于不同循环相位，只能作全身背景，不能当同pose法线AB。
协调者亲看后选择B为局部制作基线：腿尖亮岛改善较清楚，上身边界更连贯，仍保大明暗。
这不是用户对全部普通动作/材质/正式包的最终接受。[MAT06]

B对original/A：24组源骨、96组皮肤MID属性、8组头发/头部CPU数据保持；六消费者
保存重开后目标N最大误差0.001405°。P/有序面/UV0–2/VC/按骨名权重/bind保持。
有一个明确例外：五份消费者各一个**归档UV3**面角差0.0001220703125，另一份无差；
输入六FBX所有UV未改。不能写“原生所有UV逐值不变”。实际主/描边父链30个材质/函数包，
含坐标、默认采样坐标及Custom code，仅使用UV0/1/2，没有UV3使用者，因此该例外不影响
本次采样；该结论只适用于已核这条链。[MAT06]

## 8. 可复制的合同例与私有来源索引

[skin-material-contract.json](../examples/skin-material-contract.json) 是纯合成文档数据：
示范记录来源置信、UV/五图、导入意图、VC状态、各N消费者及待补证据。`null`表示尚未核实；
logical ID不是随附资产。先替换成自己已核参数，再编写适合项目的导入器，不能直接传给UE
或`harness.py`执行。没有网格/贴图、机器路径或假指纹。

下列均为**私有源项目相对标识，未随skill打包**；文章本身给出方法和限制，不要求能打开它们。
脚本名说明各自职责，不是本仓库的可运行命令。复用时重写路径、骨架、材质和采样合同。

| 证据 | 私有相对标识 | 具体内容/脚本职责 |
|---|---|---|
| MAT01 | `work/body_material_r196/{native_contract,source_material_contract,uv_final_audit,texture_bake_report,resolved_body_source}.json` | UV/五图/VC合同；`analyze_uv_ancestry.py`查源层，`bake_body_maps.py`按面角重烘，`apply_body_material.py`仅搬UV/材质 |
| MAT02 | `work/shoe_texture_r191/{source_inspection,texture_audit,mip_padding_audit,native_material_contract}.json` | 无UV诊断、密度/覆盖、五图；`build_uv.py`展开，`paint_textures.py`画字段，`audit_mips.py`查离线串岛 |
| MAT03 | `work/body_material_r196b/{palette_audit,native_contract}.json` | 不同预览公式根因；`build_neck_controls.py`只改颈ILM/OLM |
| MAT04 | `work/body_texture_saved_verify_r196/{README_ZH.md,handoff.json}` | `verify_saved_body_textures.py`核已存SourceArt/设置，非GPU采样 |
| MAT05 | `work/interactive_demo_r195/body_r196b_native_review.json` | `verify_body_color.py`同姿骨数据与实际头身MID核对 |
| MAT06 | `reviews/BODY_NORMALS_R198_ZH.md`；`work/body_normals_r198/{accepted_manifest.json,native/skin_uv_channel_audit.json,candidate/native_semantic_guard_B.json}` | `candidate/replay_body_lineage.py`恢复角来源；当前各REST的N字段、原生AB与UV3例外 |

## 9. 饰件看似歪移，也要核实际材质深度

本节原生复现报告的指纹见[案例证据索引](gold-demo-evidence.json)的G23。

R209眼镜只剩远侧一小块，画面像是整副转歪。先查几何：同一次冻结姿态中，真实原生镜框
顶点投影覆盖双眼；按实际1323项形变权重重建脸部后，260个镜片顶点及1584个面内样本
没有被脸挡住，镜片距后方脸面最近1.454cm。这些检查不包含材质最终修改的深度，不能据此
称画面正确，更不能用额外旋转或前移去补未知的渲染错误。

原生角色每帧写入`ScreenSpaceZOffset`，新饰件却只同步光照等部分参数。本次实际角色值
为-3，三份眼镜MID仍为0。其材质使用`ScreenSpaceZOffset + ScreenSpaceLocalZOffset`
修改屏幕深度。冻结同一帧，仅把角色当前的前一参数复制到三份饰件MID，镜框和双镜片恢复；
后一参数仍为0，位置/权重、父材质、原GPU形变路径和其他参数都不变。

修复在每帧同步入口读取当前角色的实际值，**不能把-3写成通用常量**。保留饰件自己的局部
深度和镜片专用参数，再检查动作、镜头切换和重新启动。之前换脸描边或切CPU形变的一次
成功，在重复同姿试验中不稳定，已撤回，不能写成根因或正式修法。

私有复现入口为`work/parallel_r209/sol/runtime/GoldSOLRuntimeR207.c`的`sync_environment`；
单变量证据在`work/parallel_r209/sol/runs/h_screen_depth_samepose/logs/depth_parameters.jsonl`，
前后原生图在`renders/parallel_r209/sol/h_screen_depth_samepose/`。此例说明：同一骨矩阵和
相机投影不等于同一最终可见像素，应核对实际材质实例及角色运行时补充的参数。

## 10. R213：贴图正确，Cook 后却让衣服、手套和鞋全采到肤色

本节属于后来的**原路径 PAK**迁移阶段，不沿用第4、9节历史 Demo 的额外显示组件或参数同步桥。
用户在 R212 零售选人及对战中都看到了错误肤色。R213 已完成下面的数据修复与原生 UE 画面检查；
尚不能据此宣布完整 R213 零售包或新增面部结构获用户认可。来源见
[R213 材质证据索引](gold-material-r213-evidence.json)。
具体制作与守卫脚本的输入输出见[修复实施索引](gold-r213-fix-methods.md#5-身体13材质族错采肤色)。

### 先查真正的采样坐标，而不是先重新上色

该阶段把13个材质族合进原身体 Base/Outline 池，以 **UV3.x 的整数0–12**选择对应图集区域。
这里 UV3 已是生产选择器，不能继续套用 R198“UV3 只是归档、shader 不读取”的旧结论。
Natural 和 FD 有独立路由，尾巴也使用自己的材质，必须分别读取实际消费者。

本案已保存的材质父链、五张图集和实际 Pawn 参数正确：Body 启用图集且不固定族；
Natural 有意固定 skin 族；FD 有意绕过图集选择。问题在 FBX 的类型元素数组与 Layer 引用：

1. 生成器保留稀疏的 `LayerElementUV` 编号，又把新“编号3”的材质族 UV 放在类型数组末尾。
2. 原始文本中可以找到正确的 UV 数值，数值自检也通过；但 FBX SDK 通过**类型数组序号**
   解析 `TypedIndex`。标签中的数字不是可任意使用的独立查找键。
3. 身体 Layer3 实际指向旧供体 UV；鞋与手套 Layer3 越过元素数组，SDK 读回 `UV NONE`。
4. UE 保存后的 mesh 和实际 cooked render buffer 都丢失了预期的整数族选择，衣鞋因此取到 skin 区域。

这解释了为什么材质始终错误，也解释了为什么增加贴图分辨率、调光或补运行时参数不会修好。
只看到文件中存在名为“FamilyUV”的层，并不能证明引擎使用了它。

### 最小修复及可复用检查链

只重排 UV 类型元素、使用连续序号，并使每个 Layer 的 `TypedIndex` 对应实际数组；
给生产层使用唯一名称。原 UV 数值、P/N/T、顶点色、蒙皮和贴图不变。
重新导入**原身体资源路径**，恢复并核对既有材质槽、`LODMaterialMap`、
`OutlineMaterialIndex` 和伤害分组。不得把本次 Cook 顺带输出的旧 Skeleton 或其他依赖整批覆盖进包。

依次保存下面四层证据：

| 层次 | 检查 | 本案观察 |
|---|---|---|
| FBX SDK | 实际 `GetElementUV` / Layer 解析结果、每个面的族值 | 修后鞋1、手套2、袖片3、衣服4，其他族直至12 |
| UE 保存重开 | 真正导入的 UV 通道及原生再导出数据 | 13族逐三角按合同取值；UV0–2、P/N/T/B、VC及三角一致 |
| Cooked buffer | 独立工具读取发布用 mesh 的 section/UV | 各 section 的 `round(UV3.x)` 为0–12；保留量化差异说明 |
| 实际原生画面 | 原角色组件、材质池、shader、完整相机 | 两角色衣服/手套/鞋恢复各自颜色；这是 UE 原生预览，非零售验收 |

UModel 在该 cooked 数据中把半精度零报告为约 `3.05e-5`；材质实际对族号 round，
因此不能把这项显示误差当新族值，也不能泛化成所有 UV 都允许随意误差。
完整蒙皮另由原生导出的473个 cluster 核对全部影响、权重和 bind；不能用独立查看器的四权重上限
代替完整蒙皮证明。13族和473 cluster 是此资产的计数，复用时从当前资产读取。

该修复没有新增运行模块，成品变化限一个 mesh 的两个 cooked companion。发布仍须通过依赖闭合、
原生描边 section、动画形变和完整包检查；安装器校验分发文件完整性，不要求目标游戏 EXE 与制作时哈希相同。
