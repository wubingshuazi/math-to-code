# Math to Code · 从数学手稿到可复现实验

**首个成果：OpenAI 数学手稿第 276 组的广义振幅阻尼（GAD）计算工具与独立数值审计。**

本项目的新代码、文档与实验由 GPT 完成（100% GPT 贡献）；人类提供选题授权、计算资源与 GitHub 托管。数学成果及已有算法归原作者，不计作本项目原创。详见 [贡献说明](CREDITS.md)。本项目独立于 OpenAI 官方研究仓库。

## 能用来做什么

- 输入阻尼强度 `gamma` 与平衡激发态占据率 `nu`，计算单次使用的 Holevo 信息最优值（bit/次）和对应的两种信号态。
- 批量扫描噪声参数，导出 CSV，供量子通信仿真、参数敏感性分析使用。
- 独立使用 Kraus 算符、密度矩阵和特征值计算，检查论文的公式、纠缠输入熵界与矩形热熵不等式是否在所测实例上数值一致。

这不是量子纠错器或真实硬件的通信协议，也不计算量子信息容量。将单次 Holevo 值解释为任意长度编码的无辅助经典容量，依赖原手稿的可加性定理；本项目的随机实验不构成该定理的证明。

## 快速使用

运行计算器只需要 Python 3.10+，不需要 GPU、API 密钥或网络：

```console
python -m math_to_code gad --gamma 0.35 --nu 0.2
python -m math_to_code sweep --points 41 --output results/gad_grid.csv
```

第一条命令给出约 `0.557078890367 bit/次`，信号激发概率约 `p=0.46061004`。两个信号各以 1/2 概率发送：

```text
|phi+> = sqrt(1-p)|0> + sqrt(p)|1>
|phi-> = sqrt(1-p)|0> - sqrt(p)|1>
```

也可安装后使用命令行或 Python API：

```console
python -m pip install .
math-to-code gad --gamma 0.35 --nu 0.2
```

```python
from math_to_code.gad import optimize
result = optimize(gamma=0.35, nu=0.2)
print(result.capacity_bits, result.p)
```

`nu` 始终表示**平衡激发态**占据率。有些库使用基态权重，转换时要取 `1-nu`。输出的搜索区间属于浮点优化结果；`tolerance` 控制 `p` 搜索区间宽度，并非经过认证的容量误差界。尤其在阻尼接近 1、目标近乎平坦时，最优值比最优 `p` 更稳定。

## 复现实验

固定版本的完整审计环境需要 **Python 3.12+**（已测试 3.14）；计算器本身支持 Python 3.10+。以下为 Windows 的明确命令：

```console
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-audit.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe scripts/validate_quantum.py
.venv\Scripts\python.exe scripts/validate_thermal.py
.venv\Scripts\python.exe scripts/benchmark.py
```

Linux/macOS 将 `.venv\Scripts\python.exe` 换成 `.venv/bin/python`。固定种子、精度、样本数量和残差见 `results/`。审计采用 CPU 和 NumPy；矩阵规模很小，GPU 对这项工作没有必要。通过结果只覆盖所测样本，不验证全部数学证明，也不提供严格浮点区间证书。

## 722 篇里面，有多少值得做、又没人做？

**目前无法给出经过验证的总数。** 当前固定版本列出 719 篇手稿、372 组结果；初始 722 篇中有 3 篇撤回。分组编号最大值也不是结果组数。

本项目的 [筛查报告](research/screening.md) 和 [机器可读目录](research/catalogue.json) 提供可追踪的初筛，不把关键词命中当作实际可用，更不把搜索未命中当作“无人实现”。[已有工作调查](research/prior-art.md) 记录已找到的实现。第 128 组最短超串已有多个实现；GAD 的单次公式与通用信道库也早已存在。

本次新增的具体工作是：一个无运行依赖的专用公式实现，以及针对这篇手稿的独立、固定种子数值审计。我们不声称这是首个 GAD 计算器、数学新发现或工程性能突破。

## 来源与许可证

研究固定在 `openai/math` 提交 `1581d4cbdd69a0faf34b2089614fe2a814316a6a`（2026-10-12），检索日期为 2026-10-17。更新上游时需重新检查撤稿、公式与参数约定。

- [官方发布说明](https://openai.com/index/sharing-ai-progress-in-mathematics/)
- [固定版本的第 276 组论文与引用信息](https://github.com/openai/math/tree/1581d4cbdd69a0faf34b2089614fe2a814316a6a/preprints/Classical-capacity-and-entropy-inequalities-for-generalized-amplitude-damping-September-24-2026)
- [公式、参数约定和局限](docs/gad-method.md)

源代码采用 Apache-2.0；上游目录、摘要、手稿的原作者署名与许可证保留在 [NOTICE](NOTICE)。
