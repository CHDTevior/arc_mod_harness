# v0.1 验证记录

日期：2026-09-15。此记录针对 harness，不是新的游戏 MOD 测试报告。

| 项目 | 本次结果 |
|---|---|
| Python 单元/集成测试 | Windows 本地 Python 3.12，47 项通过 |
| 完整记录路线 | 合成 material 项目的 brief → reference → look → motion → package → runtime → friend delivery 记录检查通过 |
| 负向检查 | 旧文件/输入/相机/版本、漏依赖、跨候选引用、旧包实机、新反馈、路径越界均有拒绝用例 |
| 合成演练 | C 单独进入声明运行清单，A/B 留存，文件变化使决定失效，未测步骤保持待验收 |
| 投影 CLI | 实际执行，生成 SVG/JSON；已知矩阵坐标、透视除法、越界/无序边等用例通过 |
| Skill 格式 | skill-creator 的 quick_validate.py 通过；仅验证器环境临时安装 PyYAML 6.0.3，工具本身无第三方依赖 |
| 静态仓库检查 | 本地 Markdown 链接、UTF-8/JSON、生产二进制/机器路径/明显令牌模式检查通过 |
| 浏览器目视检查 | 未完成；浏览器 URL 安全策略拒绝本地 file URL，未绕过限制 |
| GitHub CI | 提供 Windows/Linux × Python 3.10/3.12 配置；具体远端结果以仓库 Actions 为准 |
| 独立新手测试 | 尚未进行；方案见 evals/scenarios.md |

自动测试验证脚本行为与记录一致性，不能替代 AI 对实际媒体来源的检查或作者的审美判断。
原游戏资源解析、图像生成调用、绑定求解、Cook 和实机操作仍需对应宿主工具和游戏适配器。
