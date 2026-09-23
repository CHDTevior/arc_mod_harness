# R213 音频原路径替换：制作成品与零售容器分开验证

这是第九类实施记录，入口为[修复方法索引](gold-r213-fix-methods.md)，来源指纹见[音频证据表](gold-r213-audio-evidence.json)。只公开方法、相对证据标识和摘要，不分发声音、模型、游戏包或含本机路径的生产脚本。

**已确认范围：**401 个原路径 SoundWave、802 个 cooked 文件，21,655,458 bytes，无 `.ubulk`；源映射、完整解码、独立解析回导和最终哈希均通过。未启动零售游戏，未完成事件触发、实际播放、混音或逐条人工听辨验收。

## 1. 先确定替换关系，保留原音不重新编码

用户提供的成品含 462 条唯一 WAV：398 条历史转换音频，64 条配角/双人合声原音。显式 replacement map 将它们对应到 467 个游戏 SoundWave：398 条转换覆盖 401 个资产，64 条原音对应 66 个资产。多资产共用一个声音是映射事实，不能把 462 与 467 的差异判为漏文件，也不能凭文件名猜包。

历史制作对 398 条使用 RVC **+8 半音**，再逐条匹配原音 RMS；+8 不是音量 dB。本轮直接使用最终 PCM16 成品，未再次升调、增益、变速、裁剪或加 limiter。64 条保留音是 FLOAT32，不能一律按 PCM16 读取。全部为 48 kHz 单声道，总计 45,361,885 采样帧。

源审计逐 WAV 比较交付 ZIP、展开文件夹与 v3 成品 SHA256；64 条保留 WAV 与原 OGG 解码结果逐样本相同。历史音量方法分为 157 条仅增益、191 条平滑峰值控制、50 条软拐点压缩，源审计复测最大 RMS 误差约 0.00001546 dB。它未重新听辨或重测历史真峰值，不能扩大为听感认可。

## 2. 实际入口、输入和输出

以下 `A` 代表相对证据目录 `work/retail_visual_r213/audio`。`build_audio.py` 是本案私有实现，表格用于复查方法，不能当作通用下载后即可运行的 harness 命令。

| 顺序 / 脚本或阶段 | 输入 | 输出与具体检查 |
| --- | --- | --- |
| 只读源审计 | 最终 ZIP、目录、制作映射、保留源 OGG | `A/source_audit/SOURCE_AUDIT.json`；462 份字节对应、WAV 类型、帧数与 64 份解码采样一致 |
| `A/build_audio.py inspect` | 显式 replacement map、当前零售包只读索引 | `ORIGINAL_MAPPING_AUDIT.json`；提取 467 套原 `.uasset/.uexp`，嵌入 OGG SHA 对上制作映射的 `source_sha256`，逐包确认布局与原属性 |
| `A/build_audio.py encode` | 398 条最终 PCM16 WAV | 每条只做一次 libvorbis q10 编码；`ENCODE_AUDIT.json` 记录工具哈希、全长原生 Vorbis 解码及第二解码、帧数、相关系数、RMS 和 SNR |
| `A/build_audio.py build` | 已验证原容器、已编码 OGG 与准确映射 | 原路径 401 套两文件、`COOKED_TECHNICAL_DETAILS.json`；仅替换压缩载荷及必要长度/偏移，独立 UModel 解析回导每个 OGG，并检查字节 SHA |
| 最终保留与交付核对 | 401 套输出、66 个应保留原资产、所有审计结果 | `PRESERVED_ORIGINALS.json`、`MANIFEST.json`；保留资产的 replacement files 为 0；802 文件逐项大小/哈希，flat `files` 含 `kind=cooked`、source、path、mount、package、bytes、sha256 |

本次只读复用此前已验证的 inline-OGG 布局、原生 Vorbis 解码与 PAK 提取工具；仍对本轮每个原包重新检查结构与映射，没有运行写死其他角色的旧构建脚本。最终游戏只消费原路径 cooked 资源，不依赖这些制作工具。

## 3. 容器中改什么、保护什么

每包必须恰有一个 SoundWave export、一个 OGG 压缩格式；要求 `NumChannels=1`、`SampleRate=48000`，并核对 `Duration=float32(frames/48000)`。原 `TotalSamples` 允许其浮点表示的一 ULP 差异，仅用于验证，不重写原属性。

已验证布局的 inline bulk flags 为 `0x48`；count 与 size 相同，inline offset 等于 `.uasset` 长度加数据位置。替换 `.uexp` 中的 OGG 后，仅更新 bulk count/size、export serial size 和 summary bulk start。原 NameMap、imports、属性 tags/value bytes、声道/采样率/时长/TotalSamples、尾部 16-byte compressed GUID 均原样保留。未知布局必须拒绝；本次 summary bulk 位置 169 是逐原包确认的断言，**不能当成其他版本固定偏移**。

66 个保留包完全不写入替换列表。本次没有用编辑器重新 Cook 声音，因此也不宣称“新 Cook 与原结构等价”；事实是保留已核当前零售 cooked 结构，写入经过全长解码验证的新压缩载荷。

## 4. 失败闸、验证与限度

第一批 q10 的严格 0.1 dB 编码 RMS 偏差闸，因一个短音频实测 +0.106433 dB 而拒绝。保留源与编码输出哈希后，复核同一个 OGG，没有重转码或额外调增益；有损编码容差明确修订为 0.25 dB。整批实际最大偏差仍为 0.106433 dB，最低相关系数约 0.999693143、最低 SNR 约 32.063615 dB。不得描述为 PCM 无损，或声称有损编码后的音量数值绝对不变。

398 个 OGG 全部由引擎原生 Vorbis DLL 完整解码，检查精确 granule 帧数，并用 ffmpeg 第二解码交叉检查；401 个输出包全部经 UModel 独立解析回导，OGG 字节哈希一致；最终 802 文件再按 manifest 核对。这些证明格式与数据对应，不证明零售事件接线、运行时混音或用户听感。后续实机/人工结果应另存同版收据，不能回写旧审计为已听过。
