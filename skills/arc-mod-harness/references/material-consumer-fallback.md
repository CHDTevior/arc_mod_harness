# 组件材质正确，实际绘制却用了默认材质

R213 私有制作案例：刚性眼镜前框在一个角色上消失，镜片仍可见；重跑后缺框侧会随原生深度排序交换。最终问题在材质用途与 section 映射之间，组件参数同步检查未覆盖真正绘制的材质。

本页只保存可复用方法与相对证据标识。原游戏资产、机器路径、PDB 偏移和诊断 DLL 不随 harness 分发。原生开发场景验证与零售游戏验收分开记录。

## 1. 先保护几何，建立证据层级

按以下顺序核对，每层只能证明本层事实：

| 层级 | 本例检查 | 不能由此推断 |
|---|---|---|
| 作者与实际导入 | 框与片同刚性骨、权重1、全部1323 morph 无眼镜位移 | GPU 实际用同一个材质 |
| 实际姿态 | 双角色 CPU 骨骼与 morph 后几何刚性相同，前框未埋脸 | CPU 投影已包含材质 WPO 与深度偏移 |
| 组件槽 | `GetMaterial(slot)` 指向对应原生 MID，参数正确 | 场景代理没有将它替换 |
| MID 渲染资源 | Flush 后核对 Owner、父链和直接标量覆盖，与游戏线程一致 | 实际 draw 绑定该资源或该常量缓冲区 |
| 编译资源 | GT/RT 同 shader map、编译完成，位置修改标志有效 | 最终 mesh batch 没有替代材质 |
| 场景代理 | section 缓存材质与组件槽逐指针、对象路径对照 | 自动代表任意时刻、任意 LOD 的最终 draw |
| 实际画面 | 相同镜头、两种朝向、原生深度排序的修复前后 | 用户已接受完整美术或零售发布 |

本例组件和 MID 渲染资源中的值都正确。真正决定下一步的是：场景代理的镜框 section 指向 `WorldGridMaterial`，而组件槽仍指向原生 MID。脸和镜片 section 均匹配组件槽。

## 2. 原始材质索引与绘制映射发生分歧

该引擎分支绘制骨骼网格时，通过 `LODMaterialMap` 将 section 映射到实际材质槽。表情用途扫描仍直接读取 section 的原始 `MaterialIndex`。

```text
有表情的口内 section → raw index 6 → 检查组件 slot 6（镜框）
同一口内 section    → draw remap 4 → 实际绘制组件 slot 4
刚性镜框 section 10 → draw remap 6 → 实际绘制组件 slot 6
```

实际口内 section 有156个非零 morph；刚性镜框自身没有 morph。只要存在活动表情，该扫描就遍历网格全部已存 morph，所以普通动作也会触发口内其他演出的 section 用途检查。扫描误选镜框材质后，未启用 Morph Targets 用途的原始母材质未通过检查。引擎随后只替换场景代理缓存的 base 材质，不替换组件槽中的 MID。这解释了为什么再次读组件参数或重编译同语义材质均不能修复。

相关工程源码入口：

- `USkinnedMeshComponent::UpdateMorphMaterialUsageOnProxy`：枚举 morph section，用原始 `MaterialIndex` 获取材质。
- `FSkeletalMeshSceneProxy` 构造：应用 `LODMaterialMap`，缓存 base 与 outline 材质。
- `FSkeletalMeshSceneProxy::UpdateMorphMaterialUsage_GameThread`：用途失败时排队将缓存 base 材质替换为默认材质。
- `CreateBaseMeshBatch` / `GetDynamicElementsSection`：消费缓存材质生成绘制数据。

这是已核验的引擎分支行为，不能假定所有 Unreal 项目均有相同重映射或同一源码实现。

## 3. 最小资产修复与保护范围

离线克隆原镜框母材质，只启用 `bUsedWithMorphTargets`，重新编译；克隆原中间实例并保留全部有效参数，原路径叶实例改为该私有父链。原生材质池继续负责动态参数。

独立读取保存后的资产，验证432个表达式、输入连接、渲染输出和参数 GUID 不变，原父链的标量、向量、纹理与静态开关有效值不变。唯一渲染语义差异是用途标志。编译缓存、资产身份和父引用的变化另行记录。

保护框片几何、绑定、1323 morph、UV、法线、原纹理、镜片及描边。没有加入运行时同步桥，没有把描边倍率试验或临时脸部母材质混入修复。用途标志允许正确原生变体；并不让刚性眼镜产生表情变形。

修复前：两角色镜框缓存均为默认材质，而脸/镜片正常。修复后：两个角色全部24个 section 的缓存材质都与组件槽一致，默认材质替换数为0；镜框实际 MID 的原生深度值分别为−3和0。原3840×2160 D3D 场景图中两侧框片均完整。第二角色该次 idle 姿态有所变化，因此只主张相同普通场景镜头的双向结果，不主张相同姿态像素差分。

这完成了原生开发场景的消费者与画面闭环。随后独立检查了3个材质包的6个 Cook 文件：用途标志和父链正确，作者字节与实测版本一致；24项外部材质函数和贴图由新鲜认证的原游戏 PAK 索引逐项证明。临时 Cook 目录中存在的依赖不能直接算作交付内容，清单已按包内、继承包和原游戏来源区分。用户零售游戏验收仍待。没有为了修复而改引擎索引逻辑，也没有运行或宣称 RenderDoc draw/常量缓冲区捕获成功。

## 4. 失败试验与可运行示例

描边局部倍率0.2、等语义重编译、改变投影阴影 section 标志均没有恢复镜框。它们各自只能排除对应假说。缺框跟随深度排序而非固定玩家，也不等于已证明参数漏同步。

运行标准库合成示例：

```sh
python skills/arc-mod-harness/examples/material_consumer_fallback_demo.py
```

示例用虚构 section 与材质对象重现“组件正确、缓存被替换”的控制流，并检查离线用途修复。它不渲染 GPU，不是游戏适配器，不能替代私有原生场景验证。

## 5. 工程证据索引

修复前后trace、画面、图守卫及摘要的SHA256见 [相对证据与指纹](gold-r213-sol-material-consumer-evidence.json)。

指纹索引的 `relative_evidence` 均从私有案例工程根目录解析。实际场景trace/图位于 `work/retail_visual_r213/face/native/native_scene_v2/captures`；下列制作报告位于 `work/retail_visual_r213/sol_rigid`：

- `MORPH_RAW_VS_DRAW_MATERIAL_ROUTE.json`：实际导入 section、映射与 morph 覆盖。
- `NATIVE_SOL_RIGIDITY_THIN_SHADOW_NATIVE_FROZEN.json`：最终几何与绑定保护。
- `LIVE_SOL_RT_RATIO_350.json`、`LIVE_SOL_COMPILED_350.json`：各自层级的通过与限制。
- `PROVEN_SOL_MATERIAL_CONSUMER_FAILURE.json`：实际场景代理的修复前后证据摘要。
- `frame_base_morph_candidate/INDEPENDENT_GRAPH_GUARD.json`：唯一用途差异与原参数保护。
- `ACCEPTED_SOL_COOKED_INDEPENDENT_GUARD.json`：最终清单第2版、6个 Cook 文件及实际用途标志和父链。
- `ACCEPTED_SOL_RETAIL_STOCK_PROVIDERS.json`：24项原游戏依赖及其 companion 的精确挂载路径、大小和索引哈希。

这些是工程索引，不包含私有文件，也不声称公共 harness 能独立重跑游戏验证。诊断用匹配 PDB 的布局守卫只适用于该次开发构建，不应作为可移植安装器的 EXE 白名单。

## 6. 后续：颜色过渡中的缺失着色器

[R214 颜色过渡案例](gold-r214-color-transition-example.md)记录另一种消费者缺口：最终颜色正常，临时 loading/hidden 路径请求缺失的 Morph shader。`Material not found` 文本对应 `GetShader` 失败，不能据此认定缺包。该例保留转储能恢复的精确 ShaderType/VF、不能恢复的 Resource 堆、动态颜色/过渡/槽规则及独立图守卫。原生 BTL 消费者 A/B 已证原图缺精确 Morph VF、16 次默认材质回退，候选补齐并消除回退；该 fixture 未复现 Shipping Fatal。直接 Cooked-in-Editor 路线因冻结布局拒绝而失败，最终改以真实 WindowsNoEditor cache 的精确 index/hash/code bytes 绑定交付 `.uexp`，并完成 17 色原生矩阵；用户零售验收仍单列。
