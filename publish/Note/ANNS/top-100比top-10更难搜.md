---
tags:
TODO:
public: true
star:
link: https://gemini.google.com/share/6bc8e7282d02
---
# 1. 召回率随着k的增大降低
```
k=10 召回率: 0.9965
k=50 召回率: 0.9907
k=100 召回率: 0.9829
```
![recall_vs_k_chart.png](https://file.quaternijkon.online/2026/01/1b3d34e424b5d95c56c01e26f9765790.png)


## 1.1. 邻居的“难易程度”不同
在 SIFT1M（以及大多数高维真实数据）中，Top-1 甚至 Top-10 通常离 Query 非常近，且与其他非近邻点区分度很高。随着 $k$ 的增大，它们与 Query 的距离通常已经变得比较远，且彼此之间的距离差异非常小。
> gemini给出比较有说服力的原因是可能不存在100个那么多明显的最近邻，可能与query聚集的点就只有十几个，几十个，之后其他的点与query实际上都不是那么相关了，就导致距离上的差异变小。从数学上来说获得真实的最近邻的难度变大，但从实际考虑出发可能实际上不需要这么多结果。而且gemini不认为在SIFT1B上这种情况会缓解。



## 1.2. `ef` 参数的相对稀释（Search Budget）

## 1.3. 统计学上的平均拉低


