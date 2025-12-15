# 查询扩展（同义词库）功能

## 概述

查询扩展功能通过同义词库自动扩展用户查询，提升检索召回率。当用户查询"设备维护"时，系统会自动添加"装置保养"、"机器检修"等同义词，从而找到更多相关文档。

## 功能特性

### 1. 多种同义词来源

- **内置词典**：包含工业领域常用同义词（设备、维护、故障等）
- **自定义词典**：支持从 JSON 文件加载自定义同义词
- **LLM 生成**：可选使用 LLM 动态生成同义词（需要配置）

### 2. 智能查询扩展

- 自动识别查询中的关键词
- 匹配同义词并添加到查询中
- 支持中英文查询扩展

### 3. 无缝集成

- 自动集成到检索流程中
- 在向量检索和 BM25 检索前自动扩展查询
- 不影响原有检索逻辑

## 使用方法

### 1. 基本配置

在 `.env` 文件中配置：

```bash
# 启用查询扩展（默认 true）
ENABLE_QUERY_EXPANSION=true

# 自定义同义词词典路径（可选，留空使用内置词典）
SYNONYM_DICT_PATH=data/synonyms.json

# 是否使用 LLM 生成扩展词（可选，默认 false）
USE_LLM_EXPANSION=false
```

### 2. 创建自定义同义词词典

创建 JSON 格式的同义词词典文件：

```json
{
  "设备": ["装置", "机器", "器械", "设施", "装备"],
  "维护": ["保养", "检修", "维修", "养护", "维护保养"],
  "故障": ["问题", "异常", "错误", "缺陷", "毛病"],
  "检查": ["检测", "检验", "查看", "审查", "查验"]
}
```

**格式说明**：
- 键：原始词
- 值：同义词数组

### 3. 使用示例

#### 示例 1: 使用内置词典

```python
from app.rag.synonyms import SynonymDict, QueryExpander

# 创建同义词词典（使用内置词典）
syn_dict = SynonymDict()

# 创建查询扩展器
expander = QueryExpander(synonym_dict=syn_dict)

# 扩展查询
original_query = "设备维护方法"
expanded_query = expander.expand(original_query)
# 结果: "设备维护方法 装置 机器 器械 保养 检修 维修"
```

#### 示例 2: 使用自定义词典

```python
from app.rag.synonyms import SynonymDict, QueryExpander

# 从文件加载自定义词典
syn_dict = SynonymDict(dict_path="data/synonyms.json")

# 创建查询扩展器
expander = QueryExpander(synonym_dict=syn_dict)

# 扩展查询
expanded = expander.expand("设备故障检查")
```

#### 示例 3: 在检索中使用

查询扩展已自动集成到 `HybridRetriever` 中：

```python
from app.deps import get_retriever

retriever = get_retriever()

# 执行检索（自动应用查询扩展）
results = await retriever.search(
    query="设备维护",
    top_k=5
)
# 实际检索的查询会被扩展为: "设备维护 装置 机器 器械 保养 检修 维修"
```

## 内置同义词

系统内置了以下工业领域常用同义词：

| 原词 | 同义词 |
|------|--------|
| 设备 | 装置、机器、器械、设施 |
| 维护 | 保养、检修、维修、养护 |
| 故障 | 问题、异常、错误、缺陷 |
| 检查 | 检测、检验、查看、审查 |
| 操作 | 运行、使用、执行、操控 |
| 安全 | 防护、保护、保障 |
| 温度 | 热度、气温 |
| 压力 | 压强、应力 |
| 系统 | 体系、机制 |
| 流程 | 过程、工序、步骤 |
| 生产 | 制造、加工 |
| 质量 | 品质、质地 |
| 效率 | 效能、性能 |
| 优化 | 改进、提升、改善 |
| 分析 | 解析、研究、评估 |

## LLM 查询扩展（可选）

如果需要使用 LLM 动态生成同义词，可以启用 LLM 扩展：

```python
from app.rag.synonyms import LLMQueryExpander, QueryExpander
from app.rag.pipeline import RAGPipeline

# 创建 LLM 扩展器（需要先配置 LLM）
llm = ...  # 你的 LLM 实例
llm_expander = LLMQueryExpander(llm=llm)

# 创建查询扩展器（结合词典和 LLM）
expander = QueryExpander(
    synonym_dict=syn_dict,
    llm_expander=llm_expander
)

# 异步扩展（支持 LLM）
expanded = await expander.expand_async("设备维护", use_llm=True)
```

**注意**：LLM 扩展会增加延迟和成本，建议仅在必要时使用。

## 检索流程

查询扩展在检索流程中的位置：

```
用户查询
    ↓
查询扩展（同义词）
    ↓
┌──────────────┬──────────────┐
│  向量检索    │  BM25 检索   │
└──────────────┴──────────────┘
    ↓                ↓
    └─────── RRF 融合 ───────┘
              ↓
    重排序
              ↓
    返回结果
```

## 配置选项

### 环境变量

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `ENABLE_QUERY_EXPANSION` | bool | `true` | 是否启用查询扩展 |
| `SYNONYM_DICT_PATH` | str | `""` | 同义词词典文件路径（留空使用内置） |
| `USE_LLM_EXPANSION` | bool | `false` | 是否使用 LLM 生成扩展词 |

### 代码配置

```python
from app.core.config import Settings

settings = Settings(
    enable_query_expansion=True,
    synonym_dict_path="data/synonyms.json",
    use_llm_expansion=False
)
```

## 性能影响

### 优势

- **提升召回率**：通过同义词扩展，找到更多相关文档
- **处理同义词**：自动处理"设备"和"装置"等同义词
- **零配置**：内置词典开箱即用

### 开销

- **查询时间**：增加约 1-5ms（词典查找）
- **检索范围**：扩展后的查询可能匹配更多文档（这是预期行为）
- **LLM 扩展**：如果启用，会增加 100-500ms 延迟

## 最佳实践

### 1. 领域定制

根据你的业务领域，创建自定义同义词词典：

```json
{
  "泵": ["水泵", "抽水机", "泵体"],
  "阀门": ["阀", "阀门装置", "控制阀"],
  "管道": ["管路", "管线", "管道系统"]
}
```

### 2. 适度扩展

- 每个词的同义词数量建议控制在 3-5 个
- 避免添加不相关的词，以免引入噪声

### 3. 定期更新

- 根据用户查询反馈，持续优化同义词词典
- 添加高频查询的同义词

### 4. 测试验证

在启用查询扩展后，测试检索效果：

```python
# 测试查询扩展效果
query = "设备维护"
expanded = expander.expand(query)
print(f"扩展后: {expanded}")

# 对比检索结果
results_with_expansion = await retriever.search(query, top_k=5)
# 检查是否找到了更多相关文档
```

## 故障排查

### 问题 1: 查询扩展未生效

**检查**：
1. 确认 `ENABLE_QUERY_EXPANSION=true`
2. 检查日志中是否有"查询扩展"的调试信息
3. 验证同义词词典是否正确加载

### 问题 2: 扩展词过多导致噪声

**解决**：
1. 减少每个词的同义词数量（`max_expansions` 参数）
2. 优化同义词词典，移除不相关的词
3. 考虑禁用 LLM 扩展（如果启用）

### 问题 3: 自定义词典未加载

**检查**：
1. 确认文件路径正确
2. 检查 JSON 格式是否正确
3. 查看日志中的加载信息

## 总结

查询扩展功能通过同义词库自动扩展用户查询，提升检索召回率。系统内置了工业领域常用同义词，也支持自定义词典和 LLM 生成。功能已自动集成到检索流程中，无需额外配置即可使用。

