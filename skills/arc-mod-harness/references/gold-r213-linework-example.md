# R213 线条：眼褶曲面裁分与鼻梁侧短线

这是第八类方法记录，接续[修复脚本索引](gold-r213-fix-methods.md)。[证据指纹](gold-r213-linework-evidence.json)只保存私有案例的相对标识和摘要，不分发模型、图像或引擎工具。以下脚本是实施来源，不是 harness 的便携命令。

**当前结论：**眼褶裁分后的原生镜头消除了已定位的断缝；鼻梁侧新设计在原后处理、2560×1440 的 780/820 局部镜头中出现可读的深色短线，项目 root 将其接受为试玩候选。共同三头源、fresh native、最终一次 Cook、同版 323 张请求原生图审与最终交付清单收据已齐；图审按实际可见范围通过为试玩候选，并保留下文限制。这不是用户美术决定，也不是零售验收。

## 1. 两个问题分别归因

### 眼褶：顶点在脸前，三角内部仍可穿过皮肤

最初支持片位于脸后约 1–4 mm。把顶点重新贴到前表面后，实际变形镜头仍有白色断缝。原生蒙皮和像素射线分析进一步定位到长眼褶三角跨越弯曲皮肤，以及源 futae 细动在斜面上的法向分量：820 左侧 1966 个采样像素中 298 个在皮肤后，位置与三条白缝对应。新旧皮肤锚的变形差接近浮点误差，**FBX 四边形对角线差异在此案中被排除，不能写成根因**。

修复把每片线条沿实际 native 皮肤三角边界裁开。每个输出三角只属于一个皮肤三角；位置、完整蒙皮及 1323 个位置形变使用同一组皮肤重心权重。黑边和支持片分别前移 0.20/0.10 mm。仅 24 个 C091/C092 细动保留原残差乘 XYZ=(.15,.05,.15)，再投影到皮肤切平面；相邻重复边使用共享投影法线，避免各片投影方向不同造成裂缝。

黑边从 88 三角变为 380 三角，支持片从 36 变为 172；分别有 848/380 数据行。旧 44 支持点各复用一次，原 36 面槽放入前 36 个新支持三角，其余追加，保护原有非眼褶面角索引。最终薄边设计只把黑边向外的横向厚度缩短 30%，不移动内边界或长度端点。全 2877 源帧数值守卫和实际 native 镜头分别保存，数值预测不代替图审。

支持片原有材质控制另有一个有界修复：先确认三头 family 1 普通皮肤只占用 UV=(.125,.25)，再把支持片采样设为同肤色块内未占用的 (.0625,.25)。仅该点周围 32×32 ILM 像素由 RGBA=(50,128,0,255) 改为全零；Base/SSS 和全部其他像素不变，Cook 保原 BC7。该控制区别用于原生支持片表现；它不能替代后续解决穿皮的几何裁分。

### 鼻线：不能套用眼褶的单一根因

旧鼻线有正确的 UV、深色 ink 采样、位置和形变数据，但这些事实没有证明其最终片元结果。运行时读取确认 16 个鼻点的 UV0–3、颜色、TangentZ 和位置与导入数据一致，12 个有向三角在选中 LOD 的活动 section 索引范围内各出现一次。该检查是 RenderData CPU backing 及代理范围证据，**不是 D3D draw/片元深度捕获**。

只裁分旧鼻轮廓后仍未达到目标；恒绿试验只证明部分鼻片元响应到达画面。最终成功来自把短线移到更朝前的鼻梁侧，增加投影尺寸，再将整片裁分贴面。旧鼻线为何在 GPU 中偏淡没有得到单一机制证明，不把它改写为“鼻线也因长三角穿皮”。

## 2. 成功版本的具体输入与构造

相对目录简写：`F = work/retail_visual_r213/face`，`E = work/retail_visual_r213/eyelid_native`，`D = E/triangle_diagnostic`，`S = work/retail_visual_r213/sol_rigid`。

| 顺序 / 脚本 | 输入 | 输出和具体作用 |
| --- | --- | --- |
| `D/read_final_posed_depth.py`、`read_final_triangle_depth.py` | 冻结源、fresh native 拓扑、原生 CPU 蒙皮与相机数据 | `final_posed_depth/ROOT_CAUSE_AND_PROPOSAL_ZH.md`、像素深度和三角内部报告；定位眼褶断缝，区分顶点与整片 |
| `D/build_surface_conforming_crease.py` → `predict_surface_conforming_crease.py` | 原黑边/支持轮廓及实际 native 皮肤三角 | `surface_conforming/SURFACE_CONFORMING_CREASE.npz` 与 JSON/预测；逐片 XZ 相交裁分、皮肤重心锚、前移和源细动映射；仅输出数据 |
| `F/build_surface_fbx.py` → `check_surface_motion.py` | 上述数据、既有头部共同基线和明确局部法线白名单 | 三头 source manifest、全 2877 帧检查；共用边残差和薄黑边修订保留在冻结 builder/manifest 中 |
| `F/build_wedge_ilm.py` → `E/prepare_ilm.py`、`import_ilm.py`、`finalize_ilm.py` | 原 atlas、三头 UV 占用和 Base/SSS 同色证明 | 32×32 ILM patch、输入/Cook 守卫；仅 1024 像素及对应 BC7 块，原纹理路径和设置不变 |
| `F/build_nose_bridge_outline.py` | THIN 旧 16 鼻点身份和已批准鼻梁侧设计 | `nose_bridge_outline/NOSE_BRIDGE_OUTLINE.npz`、`MANIFEST.json`；只定义镜像 XZ 轮廓，暂存 Y 不能作为最终位置 |
| `D/build_surface_conforming_nose.py --contour <outline>` | 冻结新轮廓、THIN 保护字段、fresh native 前脸皮肤 | `final_posed_depth/nose_bridge_surface/SURFACE_CONFORMING_NOSE.npz`、JSON；输出 138 行/62 三角，每片只在一个实际皮肤三角内 |
| `F/build_nose_surface_fbx.py --all-heads --data <surface data> --art-outline <outline manifest>` | 同一 NPZ、新轮廓清单和三头 THIN 源 | `nose_bridge_final_fbx/EYELID_FBX_MANIFEST.json`；唯一 FBX 作者把同一鼻设计合到 Low/High/Young，保每个非鼻字段 |
| `S/attachment_guard_revision/verify_nose_bridge_diagnostic.py` → `verify_final_bridge_attachments.py`；`F/check_surface_motion.py` | manifest 绑定源、裁分 NPZ、既有 THIN 证明 | 全形变、接缝、蒙皮、层数据和非鼻完整树保护；既有 hair/SOL 守卫按输入哈希继承或刷新，不再另写一套头 |
| `E/import_final_heads.py` → `write_final_heads.py` → `verify_final_heads.py`、`verify_final_native_geometry.py` | 唯一冻结三头、原路径 native 合同 | 作者写入、fresh 导出、1323 形变/UV/材料/骨等守卫；最终收据按同一版本归档 |
| `E/apply_final_head_shadow.py` → `verify_final_head_shadow.py` → `cook_final_heads.py` → `verify_final_cooked.py`、`verify_final_cooked_uv.py`、`verify_final_cooked_shadow.py` → `finalize_final_delivery.py` | 已验三头及既定 32 段地影合同 | 原路径三头与完整 Cook 交付清单；顺序由唯一 native 作者执行，不让鼻修改覆盖 SOL/地影/前发或其他已确认变化 |

裁分方法按实际 native 三角与源多边形的**位置和 UV 面角对应**映射，不能仅凭重合位置选错 skin alias。对每个鼻轮廓三角，在 XZ 平面与候选前皮肤三角逐边裁切，三角化交集，并保留每行的皮肤索引和重心权重 `b`。构造：

```text
P = sum(b[i] * skin_P[i]) + [0, -0.020, 0] cm
D(shape) = sum(b[i] * skin_D(shape)[i])       # every one of 1323 shapes
skin_weight(bone) = sum(b[i] * skin_weight_i(bone))
```

同位置控制点也可能在某个表情通道中移动不同：本案两个重合别名在 C098 的 delta 不同。因此映射必须沿实际 native 三角回到源多边形（包括四边形）的正确位置+UV角点，不能只找最近 CP；旧小鼻已用锚点的全部 1323 delta 对应误差小于 `9.55e-6 cm`。

这里的负 Y 是本案例源坐标的前方，不是通用角色轴约定。鼻线没有眼褶的 legacy residual。原 16 CP 和 12 面槽各复用一次，追加 122 CP/50 三角。N/T/B 由旧鼻片的重心插值继承，常量 UV0–3、顶点颜色、原 lash ink、原 shader 和原后处理保留；没有新增骨、材质、运行时开关或桥接组件。

设计正侧 XZ 中心线（cm）为 `(.12,166.12), (.15,166.06), (.21,165.72), (.21,165.62)`，另一侧镜像 X。沿中心线垂线布带，四横截宽为 `[.03,1.45,1.65,.03] mm`，首尾维持细小非退化锥端。这是约 5 mm **设计投影高度**和 1.5–1.8 mm 目标中部投影宽，不是声称三维弧面尺寸相同：实际表面中宽为 1.915/2.525 mm、中心弦长 7.343 mm，另有 `ART_METRICS.json`。选择以实际 2K 图的可读性为依据。

## 3. 鼻线失败探索顺序与限度

以下按私有运行顺序归纳，保持一次改变一个因素。失败候选均未直接推广到三头，也未把诊断开关留在生产资产里。

| 次序 / 试验 | 具体改变或检查 | 结果及能支持的结论 |
| --- | --- | --- |
| 1 Alpha | 只改 36 鼻面角 A=.14→0 | 780/820 鼻区 RGB 最多差 1；没有改善，不能用该开关解释淡线 |
| 2 周围 face outline | 只取消该描边绘制，代理读回确认 | 没有改善；原描边恢复 |
| 3 顶点 R | 255→254，实际 runtime VC/UV 读回 | 没有改善；UV0–2 同 ink 半精度采样、UV3 family 正确 |
| 4 法线 | 仅鼻 N 使用指定 donor 方向 | 原生导出与运行时 packed TangentZ 匹配，780/820 没有改善；不借机重算法线 |
| 5 实际索引 | 选中 LOD、12 个有向三角、section 范围/隐藏标志 | v2 读回有效；首次布局试验无效，不能引用它作证明；仍不等于实际 GPU draw 捕获 |
| 6 小深度 | 原 16 点残差从 0.06 mm 增至 0.20 mm，其余和全部 D 不变 | 仍浅淡；不扩展为生产三头 |
| 7 标准色差开关 | 标准 fringe CVar 的隔离试验 | 可见 RGB 分离没有消失；不能宣称已排除场景色分离，诊断配置恢复 |
| 8 旧位置加宽 | 固定端点/约 3.1 mm 长度，只加宽中段至实际 0.9567/1.1179 mm，并更新皮肤锚 | 数据、2877 帧检查通过，原后处理 2K 仍是浅淡/分色小印记；数据通过不等于美术通过 |
| 9 恒绿 ink | 独立候选使用恒绿，保持比较镜头 | 眼褶变绿，鼻只有少量浅绿响应；证明部分鼻片元有画面贡献，未证明整个线带正常可读 |
| 10 旧轮廓整片 surface | 68 行/28 三角，旧 16 点复用、52 新点，全部 1323 D 同皮肤锚，前移 0.20 mm | 原 2K 镜头仍未达目标；眼褶的穿皮根因不能因此转移给鼻 |
| 11 新鼻梁侧设计＋整片 surface | 上节位置、尺寸和 138 行/62 三角组合 | 原 ink/原后处理的 780/820 出现深色短线；root 接受为试玩候选，组合改善成立，单一 GPU 根因仍未证 |

## 4. 保护合同与证据层级

最终 source manifest 的 Young 与已审局部 BRIDGE 源字节一致。Low/High/Young 的共同黑边、支持片、鼻线位置、拓扑和全部 1323 个求值形变由 `COMMON_DETAIL_COVERAGE.json` 对照；形变在某个局部为零可合法，鼻线实际相关非零通道从旧版 24 变为 36，不添加伪非零 shape。

非鼻完整树与上一 THIN 输入精确相同，因此前发 217 CP/808 N/T/B、局部脸 N、眼褶、材料族、骨、绑定和原 morph 的旧证明可沿明确差异链继承。仅新鼻及其权重/形变/面角白名单变化。native 作者再在同版上应用既定地影，并保已验证 SOL 父材质；最终发布不得从旧诊断头覆盖这些修改。

独立 BRIDGE 源检查得到全部 1323 D 接缝最大误差约 `9.45e-14 cm`，静态三角内部无穿透。这是源数据证据。原生 2K 图中 820 有连续深色短线；780 近侧靠光影边界、远侧因视角较弱，是当前可见范围。最终同版 323 张请求原生图审已完成；LH 后半 156 帧另有独立逐页审查，对源出框及 ROI 错位帧补看完整 PNG。远景、后脑和特效遮挡处不冒充正脸逐线通过；用户零售/美术决定仍待后续验收。

最终三头只 Cook 一次。地影证明采用 native 修改前后完整 buffer 保全与最终 Cook 实际 32 个 section 标志核验，不声称存在本版修改前后两次 Cook 的二进制对照。Cook UV 读回中的 family 0 近零误差有明确容差，四权重导出不被拿来肯定完整蒙皮；完整权重属于源/native 的独立合同。

### 最终同版收据与可见限制

LH 810–813 的近闭眼上下睫间仍可见细浅亮带，无可见瞳孔；仅凭截图未判明浅色睫缘或眼白，不称“完全无亮缝”，也不构建未经证明的新回归归因。874/878 的接触表 ROI 没含实际可见脸，回原 PNG 已确认是审查裁切限制，不是模型消失。最终视觉收据保留这些观察；用户美术/零售验收仍是后续独立关口。

交付清单收录三头和局部 ILM 的 8 个 Cook companions，共 90,889,200 bytes；源、native、3969 个 position-only morph、四 UV 和 32 个 shadow flags 的同版守卫均单独绑定。收据只补录当前真实结果，不重写历史候选 manifest 的当时状态来制造一次性成功。
