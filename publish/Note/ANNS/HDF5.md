---
tags:
TODO: true
public: true
star:
AIGC: true
---

# 1. 📚 HDF5 核心知识速查笔记

## 1.1. HDF5 是什么？

HDF5 (`.h5`, `.hdf5`) 是一种为存储和管理大规模数据设计的**二进制文件格式**。

- **形象比喻**：它是一个**“文件内的文件系统”**。
- **核心结构**：
    - **Groups (组)**：相当于“文件夹”。
    - **Datasets (数据集)**：相当于“文件”，通常存储多维数组（Tensor/Matrix）。
    - **Attributes (属性)**：相当于“元数据”，用于描述数据（如单位、距离类型）。

## 1.2. 物理存储与读取机制

相较于 CSV/TXT 的文本流，HDF5 更加高效：

- **随机读取 (Random Access)**：类似查字典。读取第 100 万行数据不需要扫描前 99 万行。
- **分块存储 (Chunking)**：大矩阵被切分成小的 Chunks 散落在磁盘上，通过 **B-Tree** 索引连接。
- **切片 (Slicing)**：支持 `data[start:end]` 操作，只读取所需部分到内存，**极大节省 RAM**。

## 1.3. Python `h5py` 操作速查

Python

```
import h5py

# 1. 打开文件 (仅获取句柄，不加载数据，内存占用极低)
with h5py.File("data.hdf5", "r") as f:
    
    # 2. 查看结构
    print(list(f.keys()))    # 查看根目录下的 Datasets/Groups
    print(f.attrs.keys())    # 查看元数据 (如 distance 类型)

    # 3. 读取数据 (关键区别!)
    # ❌ 危险操作：加载整个数据集到内存 (OOM 风险)
    all_data = f['train'][...] 
    
    # ✅ 推荐操作：切片读取 (只读前 1000 行)
    part_data = f['train'][:1000]
    
    # 4. 获取数据属性 (不读取内容)
    print(f['train'].shape)  # (1000000, 128)
    print(f['train'].dtype)  # float32
```

## 1.4. 向量检索数据集的“潜规则”

在 ANN-Benchmarks 标准数据集（如 `glove`, `deep-image`, `sift`）中，HDF5 的组织方式有特定含义：

### 1.4.1. A. 数据集结构

- **`train`**：通常由两部分组成：
    1. **底库 (Base/Database)**：被搜索的全量数据。
    2. **训练集 (Learn)**：用于训练索引（如聚类中心）。
    - _注：很多数据集不区分 learn，直接用 train 的一部分或全部作为底库。_
- **`test`**：查询集 (Query)，用来做测试。
- **`distances`**：Ground Truth (GT) 的距离值。
- **`neighbors`**：Ground Truth 的 ID 索引。

### 1.4.2. B. 距离度量 (最重要的坑)

通过 `f.attrs['distance']` 查看度量类型：

|**属性值**|**Angular (余弦)**|**Euclidean (欧氏)**|
|---|---|---|
|**原始向量**|**未归一化** (保留模长信息)|未归一化|
|**Faiss处理**|必须 **L2 Normalize** + `METRIC_INNER_PRODUCT`|直接用 `METRIC_L2`|
|**GT含义**|通常存 **Cosine Distance** ($1 - \cos\theta$)|存 L2 距离 (或其平方)|
|**结果解读**|GT 值越**小**越相似|GT 值越**小**越相似|

### 1.4.3. C. 为什么 Angular 数据是未归一化的？

- **原因**：原始模长包含物理意义（如词频、光照强度）。
- **逻辑**：标签 "Angular" 是**指令**（Instruction），告诉你“使用前请归一化”，而不是**状态**（State）描述。

## 1.5. 常见误区纠正

1. **误区**：HDF5 读起来像 CSV，必须从头读。
    - **正解**：HDF5 支持切片，利用 `dset[start:end]` 可实现分批处理大文件。
2. **误区**：Angular 数据集里的数据已经归一化了。
    - **正解**：通常没有。必须在代码里手动 `l2_normalize(x)`。
3. **误区**：Faiss 有 `METRIC_COSINE`。
    - **正解**：Faiss 没有。只能通过 `归一化 + 内积` 模拟。
4. **误区**：可以直接用 Euclidean 的 GT 来测 Angular 算法。
    - **正解**：不行。模长会干扰结果。必须重新生成基于 Normalized IP 的 GT。

## 1.6. 验证 GT 类型的万能逻辑

如果不确定 `distances` 存的是什么，用以下代码验证：

Python

```
# 取一个 query 和它对应的 GT neighbor
sim = dot(normalize(Q), normalize(Target)) # 计算余弦相似度
dist = 1.0 - sim                           # 计算余弦距离

# 比对 HDF5 里的值：
# 1. 如果等于 dist -> 存的是 Cosine Distance (最常见)
# 2. 如果等于 sim  -> 存的是 Cosine Similarity
# 3. 都不对       -> 可能是 L2
```