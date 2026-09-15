# 不需要游戏资产的演练

运行 `python examples/run_demo.py --out projects/demo`，输出目录必须不存在。脚本使用
手写 SVG 示意图和几字节的占位文件，所有模拟决定明确标注 `demo-fixture`，不是作者
实际批准，也不是完成了一套游戏 MOD。

## 看三个结果

1. `reviews/compare/index.html`：A/B/C 并排，来源标为 reference，显示 synthetic 元数据。
   本例 SVG 用来演示审查流程；真实 PNG/JPEG 静帧还可以点击记录归一坐标。
2. `evidence/projection.svg`：当前下眼缘、黑瞳孔示意控制点与目标箭头；单位矩阵是明确
   的合成正交相机。换真实模型时必须输入实际变形后的世界点与原相机矩阵。
3. `DEMO_RESULT.json`：选定运行 ID 只有 C；A/B 文件仍保留；临时修改参考文件会让旧
   决定失效；还没有制作和游戏审查的阶段保持 pending，不会变成“已验证 MOD”。

## 换成自己的项目

新建另一个项目，别把 demo 的批准或占位文件拷过去。先保存自己的原件副本和 brief。
以真实提取/导入/渲染结果注册 artifact，built_from 链接当前源，metadata 填实际相机、
帧映射、版本和已检查区间。图像生成结果登记 concept；真实引擎渲染登记 engine_capture；
游戏里的录像才登记 game_capture。

作者说“C 可以”之后才 select/decision。如果随后又说“左眉不平”，登记 feedback，
把原相机的当前/目标投影画出，做新候选；实际复查后 resolve 并给作者看新的整体结果。

完整包测试时，用真实适配器导出的运行清单填 runtime_file/dependencies；记录原生依赖
来源，不手填一个“都通过”的 JSON 作为替代。最后的 package_report 应引用所有选中
运行文件，实机证据再关联这份包报告。新包替换后需要新实机证据或明确标注未重测。
