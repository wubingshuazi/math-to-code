# 字符串拼接：第一项原生程序提速

在留出的 Adobe 字体名称字典上，修改后的 lazy-scs **批量处理耗时降低 19.3%～21.1%**，输出字节、长度和校验证书与原版一致。新增工程由 GPT 完成；数学算法、上游软件和成熟匹配算法保留原作者贡献。

## 它实际做什么

输入许多字符串，把它们拼成一条尽量短、包含所有输入的字符串。例如 `abc`、`bcd`、`cde` 可以合并为 `abcde`。共享名称表、重复片段存储是可能的使用场景；本次测量的是已有拼接程序处理真实名称表，尚未接入字体编译器。

我们沿用第 128 组成果的已有实现 [lazy-scs](https://github.com/nurric-ai/lazy-scs/tree/4ee86724b770c54bad400fe077b297288b087c4b)，固定在 `4ee86724b770c54bad400fe077b297288b087c4b`。该实现的拼接规则、计数、长度目标和独立验证器均保持原样。

改动集中在最后的裁剪：拼好字符串后，程序需要知道头尾哪些部分还能删掉。原版为此建立两次后缀自动机。新版本用 Aho–Corasick 多词匹配做两遍扫描，得到相同的裁剪位置；构建匹配器失败时回退原版。这里的收益来自成熟算法的工程组合。

第一遍找每个必需片段最后出现的起点，取其中最早的起点作为左边界；第二遍从这个新边界重新扫描，找覆盖全部片段所需的最早右边界。必须处理重叠匹配。例如 `abab` 包含 `ab`、`ba`，最终应保留 `bab`。

## 最终留出集结果

硬件：i9-14900HX、约 31.7 GiB 内存，Windows 11；Rust 1.99.1 GNU，`cargo build --release --locked`。两版均为无剖析代码的干净构建，启用原版 `--verify`。性能测量顺序执行，随机且基本平衡地交替原版/修改版。

| 同一字典的两个规模 | 原版中位耗时 | 修改版中位耗时 | 耗时降低 |
|---|---:|---:|---:|
| 留出集 512 个名称 | 439.450 ms | 354.510 ms | **19.33%** |
| 留出集全部 2,092 个名称 | 1,545.608 ms | 1,220.100 ms | **21.06%** |

每个进程使用现有 `--batch` 接口连续处理**同一份输入 40 次**，每版重复 9 个进程，表中是整个进程耗时的中位数，包含启动、解析、复制、求解、原生验证和输出。两组共 36 个计时进程、1,440 次求解，逐次进行独立包含关系和证书检查。表中的百分比是耗时降低，分别相当于约 1.24 倍和 1.27 倍吞吐。

这是重复输入的批处理吞吐测量；两个规模来自同一字典，不能当成两个独立应用，也不能当成单次调用的提速。额外计入 Python 保存输出和独立检查的外围耗时见原始报告的 `checked_wall_ns`，不要与表中原生进程耗时混用。

Adobe 字典固定在 [agl-aglfn 提交 4036a9c](https://github.com/adobe-type-tools/agl-aglfn/tree/4036a9ca80a62f64f9de4f7321a9a045ad0ecfd6)。按名称 SHA-256 首字节奇偶划分：2,189 个开发名称、2,092 个留出名称，交集为零。512 项是留出集的子集。数据选取种子 `1282026`，最终计时顺序种子 `1282028`。

开发集先测到约 18%～22% 的批处理耗时降低。随后先用干净 v1 在留出集确认收益，再因审查发现的错误处理问题增加构建失败回退，重新编译并完成上表最终 v2 复测。两次留出记录均保留；回退加固未调整正常匹配策略。

## 验证和没有成功的尝试

- 最终 Rust 裁剪测试 6 项通过：穷举短二进制文本、1,000 组固定种子随机输入、跨边界重叠、中文/emoji/任意字节、重复和包含片段、空要求、缺失片段，以及强制构建失败后的原版回退。
- 原生完整输出与证书逐项比较，并用独立 Python 检查包含关系、小输入的精确最优值和长度界。命令行无法表示的空输入/任意二进制输入由库测试覆盖；上游空输入 JSON 格式问题单独记录，没有把它混入性能数据。
- 首先试过计数事件扫描，原生正确性成立，但计数只占约 3.8%～9.3% 的内部工作，没有稳定通过整体收益门槛，停止沿该热点投入。
- 初次计数筛查的两个周期输入，原版先达到 60 秒上限，保留为失败记录；没有给候选版计时，也没有从中推断加速。
- Aho 的单进程开发筛查在合成 DNA/ASCII 数据上约为 -1.4%～11.3% 耗时降低，未达到 15% 门槛。最终主张仅限上表的真实字典批处理，未测出通用收益或内存收益。

## 复现与下载

独立组件版本为 `scs-aho-trim-v0.1.0`；Python 工具包仍为 `0.3.0`。下载见[组件发布页](https://github.com/wubingshuazi/math-to-code/releases/tag/scs-aho-trim-v0.1.0)。Windows 包附有同次比较的原版和修改版；源码补丁、许可证、原始计时和复现资料一并发布。

需要 Python 3.10+、Git、Rust/Cargo 1.99.1。使用未占用的目录：

```console
python experiments/prepare_scs_native.py --directory .verification/replay-original --variant original
python experiments/prepare_scs_native.py --directory .verification/replay-aho --variant aho-trim
cargo build --manifest-path .verification/replay-original/scs/scs-rs/Cargo.toml --release --locked
cargo test --manifest-path .verification/replay-aho/scs/scs-rs/Cargo.toml --release --locked
cargo build --manifest-path .verification/replay-aho/scs/scs-rs/Cargo.toml --release --locked
python experiments/prepare_scs_holdout.py --output-dir .verification/replay-holdout
```

然后指定两版可执行文件；Windows 使用 `.exe`，Linux 无此后缀：

```console
python experiments/check_scs_native.py --base .verification/replay-original/scs/scs-rs/target/release/scs-rs.exe --candidate .verification/replay-aho/scs/scs-rs/target/release/scs-rs.exe
python experiments/benchmark_scs_batch.py --inputs .verification/replay-holdout --base .verification/replay-original/scs/scs-rs/target/release/scs-rs.exe --candidate .verification/replay-aho/scs/scs-rs/target/release/scs-rs.exe --output results/scs-replay-001.json --work .verification/replay-batch-001 --repeats 9 --iterations 40 --case adobe --seed 1282028
```

在 Windows 使用 ASCII 路径可避免 GNU 链接器的 Unicode 路径问题。本机采用独立的 ASCII 构建目录，具体记录在阶段日志。复现程序核对固定上游文件、补丁及最终文件哈希；报告和日志保留最初字节，避免换行转换破坏校验。硬件负载不同会改变计时，重新构建也不承诺二进制逐字节一致。

## 可检查的证据

- [最终报告](../results/scs_aho_trim_batch_heldout_final.json) 与[逐次日志](../results/scs_aho_trim_batch_heldout_final.jsonl)
- [构建和实验溯源](../results/scs_native_build_provenance.json)
- [发布文件校验与跨平台检查](../results/scs_release_artifacts.json)，Windows/Linux 共 8 项 CI 通过；[31 个原生小例检查](../results/scs_native_correctness.json)
- [补丁、固定源码索引和第三方声明](../experiments/patches/lazy-scs/README.md)
- [开发集批处理](../results/scs_aho_trim_batch_development.json)、[首次留出测试](../results/scs_aho_trim_batch_heldout.json)、[单进程开发筛查](../results/scs_native_aho_trim_screen.json)
- [未通过性能门槛的计数尝试](../results/scs_native_screen.json)

下一阶段优先验证不同真实字典及持续运行中的多输入任务，补测峰值内存，再决定是否适合上游集成。当前已经交付独立可用的工程补丁，不把待验证的应用数量当作成果。
