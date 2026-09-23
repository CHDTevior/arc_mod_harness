# Gold 表情适配与镜头手 K：实际链路及后续制作例

这是 [动画与镜头方法](animation-presentation.md) 的具体补充。驱动链及 F/G/H 局部修复有开发 UE 证据；整体表情尚未获作者认可，**尚无已完成的特殊演出手 K 序列**。下面把已执行步骤和接下来可执行的手 K 方法分开。私有输入索引为项目根下 `work/face_full_coverage_r207`（W）、`work/cinematic_actor_routes_r207`（A）；不分发原游戏数据。

实际记录指纹见 [证据索引](gold-demo-evidence.json) G19–G21；这些记录不代替随输入变更而失效的运行验证。

## 1. 从实际活动源取得完整表情

| 私有脚本入口 | 输入 → 输出 | 已检查内容 |
|---|---|---|
| `A/prepare_actor_bridge.py`、`GoldActorRoutesR207.c` | 角色、实际可见源头/状态 → 活动 BTL low、高头、young 或 ADV 源 | 随换头切换源身份，读取动画完成合成后的 CS；不固定取待机低头 |
| `W/prepare_source_rigs.py`、`build_affine_payload.py`、`build_candidate_c.py` | source bind、Gold 控制点与权重、批准的 REST → 控制基底与形变 payload | 排除整头运动，再绕 Gold 对应控制枢轴表达相对平移、旋转和缩放 |
| `W/candidate_c/generate_runtime_data.py`、`export_affine_fbx.py` | payload → runtime headers 与 FBX | 本例102控制×12仿射分量，加99基础目标，共1323 morph；这是本工程合同，不是建议每个角色照搬此数量 |
| `GoldFaceAfterWorldR202.c`、`W/candidate_g/r207_runtime.h` | 完成 Root/Face/Mouth/Slow 合成后的源 CS → 目标系数、读回与源 hash | 115序列/2479姿态离线覆盖及代表镜头原生核验；不等于所有帧视觉通过 |

头部相对控制变换使用本例约定：`B_head × inverse(E_head) × E_control`，并与中性控制基底比较。不得因矩阵有数值变化便声称瞳孔已正确看向目标；还要检查实际蒙皮、眼白遮挡及镜头中双眼的落点。

clone 使用其生成时的独立源快照，并在回收/隐藏时清理；不能一直读取主角色后来切换到的头部。近零缩放、隐藏部件及无贡献的动画槽按实际语义处理，不能让非活动槽的诊断失败抹掉整个活动表情。

## 2. 三个已做的局部修复例

### F：虹膜底部像被切掉

`W/diagnose_iris_occlusion.py` → `build_candidate_f_runtime.py` → `candidate_f/verify_runtime_f.py`。

输入实际超杀600的源姿态、权重和眼层几何。旧额外深度位移使每眼14/152虹膜点进入眼白；只令虹膜、瞳孔、高光的深度随 eye base，保留其平面视线、旋转、缩放和层间关系。同源600/601、原4K及原像素眼裁图确认该处圆弧恢复。它没有证明所有眼神、眼形和高光均已漂亮。

### G：普通动作上翻、胜利下视受限

`W/build_candidate_g_runtime.py` → `candidate_g/audit_actual_gaze.py`。

给过强上视设连续软限制，并协调上睑/眉；正常大小瞳孔放宽下视范围，小瞳孔的惊讶模式保留不同界限。使用左右源/目标矩阵及眼白相对位置核查，避免硬编码某一截图帧。普通365改善不等于胜利780已准确双眼汇聚；视线目标和可爱程度仍需镜头审查。

### H：闭眼睫毛扭成针刺

`W/extract_lash_topology.py` → `prototype_lash_regularized.py` → `export_candidate_h_blink.py`。

先只激活 blink 来隔离形状本身。旧 blink 已产生约4倍边拉伸，不能归罪于源 Slayer 表情太夸张。合并同坐标分裂别名、固定皮肤连接点，按实际连接关系平滑自由睫毛位移。只替两个 blink 目标，保 REST、皮肤形状、其余1321形状和57颈缝。实际同源950超过2倍拉伸的边降到0，4K闭睫局部改善；眼下阴影仍另列未通过项。

每次都核实际导入的 morph position/index，以及导入器是否重算了 TangentZDelta。本项目明确保作者法线的目标需要位置/法线分开守护；保存重开再查。CPU目标一致不替代 GPU 的实际可见性和遮挡检查。

## 3. 镜头手 K：尚待制作的示例流程

此节是流程示例，不是已完成的游戏片段。

1. **锁定素材。** 对目标镜头记录动画段ID、真实源时间/hold、相机矩阵/FOV、当前头型、全身装配、灯光和材质。AI视频只提供经过筛选的表情意图，不以AI帧号直接替换原动画时间。
2. **先查驱动。** 分别看眉、睑/睫、眼白、虹膜/瞳孔/高光、唇、牙/舌的零权重、激活与恢复。源有宽笑而目标仅圆张嘴时，分清漏通道、范围限制和目标口型不合适；不以整体加倍所有权重代替诊断。
3. **按镜头画目标。** 在原始相机投影上标眼轮廓、瞳孔注视点、嘴角与脸颊边界；以可爱及身份为目标。影像裁图不改变原FOV，放大只作辅助，最终看完整游戏画面。
4. **局部校正。** 在基础驱动之后叠加镜头专用 shape/控制骨校正。允许改变透视、体积或使用临时部件，保护未要求改变的装配。确需换模型时，同时定义显示事件、阴影/描边、材质、骨架和表情源，不只换一个 mesh 名字。
5. **按原hold写键。** 将关键形状、局部校正和可见性绑定到实际镜头段/源时间，保留该段停帧节奏。不能仅设置全部constant插值就宣称还原原片；更不能全局统一15fps。切入、镜头变化、切出、回普通都要有明确状态。
6. **检查完整过渡。** 同镜头 full shader/light 看起势、最夸张、接触、恢复，核闭眼睫毛、瞳孔深度、唇齿和帽带。头发/尾巴物理继续运行，但关键造型可保护发根或使用明确的演出控制，防止动态破坏轮廓。

可保存如下**合成制作记录**；字段是记录合同，不是已存在的runtime命令：

```json
{
  "status": "proposed_not_played",
  "segment_id": "example_closeup",
  "time_basis": "source_clip_time_and_original_holds",
  "correction_order": ["base_face_driver", "camera_specific_shape"],
  "targets": ["pupil_focus", "upper_lid_arc", "mouth_corner"],
  "preserve": ["approved_rest_normals", "cape_fit", "other_character"],
  "review": ["entry", "peak", "camera_cut", "ordinary_recovery"],
  "required_evidence": ["source_pose_hash", "camera", "native_full_frame", "unscaled_face_crop"]
}
```

## 4. 同帧与实际完成的边界

使用每次run独立目录，截图立即对应源ID/hash、CS和权重，不能复用全局残留文件。案例中普通365旁边的旧CS实际来自胜利，因此被作废；某些引擎pause只暂停world而未暂停演出时钟，后续截图也不能当静止同姿态 A/B。

保留完整全身镜头：披风、头发、帽带、墨镜都能遮脸。裸脸审查用于定位，用户demo同时带默认佩镜及超杀/换体隐藏恢复。只在技术修复与当前用户要求的试玩范围满足后交付，并标明仍需作者选择的美术项；基础覆盖不冒充完成全部手K。
