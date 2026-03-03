# 名词块分析模块说明（可独立调用）

本文档将当前项目中“名词块分析”能力从 GUI 使用流程中抽离出来，集中说明后续复用时的调用入口、输入输出结构与推荐用法。

## 1. 模块位置

- 核心实现文件：`Extract_nouns.py`
- 核心类：`VisualGrammarEncoder`
- 主要入口：
  - `get_noun_phrases(text)`：返回原始结构化结果
  - `get_labeled_noun_results(text)`：返回适合展示/导出的两部分结果
  - `export_noun_results_to_excel(text, output_excel=...)`：导出 Excel
  - `format_noun_phrase_report(text)`：返回文本化报告

## 2. 分析流程

当前逻辑分为三层：

1. 句子切分 + 分词 + 词性标注（NLTK）。
2. 根据预定义 `noun_phrase_pattern_specs` 匹配 2 词及以上名词块。
3. 产出两类结果：
   - 第一部分：名词块文本 + 词性模式。
   - 第二部分：名词块中的名词，以及“去除该名词后的剩余词性组合”统计。

## 3. 原始结果（`get_noun_phrases`）

返回字典主要字段：

- `multiword_chunks`: 多词名词块明细
  - `sentence_index`, `start`, `end`, `text`, `tokens`, `tags`, `pattern`, `pos_pattern`
- `single_nouns_with_context`: 历史兼容字段（未进块单名词上下文）
- `multiword_pos_patterns`: 所有多词名词块的词性模式列表
- `single_noun_context_patterns`: 历史兼容字段（单名词上下文模式列表）
- `chunk_noun_rows`: 名词块内名词拆分明细
  - `sentence_index`, `chunk_text`, `chunk_pos_pattern`, `noun`, `noun_tag`, `remaining_pos_pattern`
- `chunk_noun_stats`: 对 `(noun, noun_tag, remaining_pos_pattern)` 的聚合统计
  - `noun`, `noun_tag`, `remaining_pos_pattern`, `count`

## 4. 展示结果（`get_labeled_noun_results`）

返回字典：

- `labeled_multiword`: 第一部分（多词名词块）
  - `标注类型`, `句子序号`, `名词块文本`, `词性组合模式`
- `labeled_single`: 第二部分（名词块内名词统计）
  - `标注类型`, `名词`, `名词词性`, `去除名词后剩余词性组合`, `频次`

## 5. 最小调用示例

```python
from Extract_nouns import VisualGrammarEncoder

text = "Just then, the telephone rang. It was my aunt Lucy."
encoder = VisualGrammarEncoder()

raw = encoder.get_noun_phrases(text)
print(raw["multiword_pos_patterns"])          # 所有名词块词性模式
print(raw["chunk_noun_stats"])                # 名词块内名词统计

labeled = encoder.get_labeled_noun_results(text)
print(labeled["labeled_multiword"])           # 第一部分
print(labeled["labeled_single"])              # 第二部分
```

## 6. Excel 导出说明

`export_noun_results_to_excel` 会生成两个 Sheet：

1. `2词及以上名词块模式`
   - 句子序号 / 名词块文本 / 词性组合模式
2. `名词块中的名词及剩余词性统计`
   - 名词 / 名词词性 / 去除名词后剩余词性组合 / 频次

## 7. 依赖与注意事项

- 依赖 NLTK（分词、分句、词性标注）。
- 首次运行可能需要下载 NLTK 资源（如 `punkt`、`averaged_perceptron_tagger`）。
- 若环境缺失资源，GUI 会提示初始化告警；建议先补齐 NLTK 资源再执行分析。

## 8. 后续集成建议

若后续要做“服务化调用”（API/批处理）：

- 建议直接以 `get_noun_phrases` 作为机器接口（字段更全）。
- 以 `get_labeled_noun_results` 作为前端展示接口（字段更稳定）。
- 前端若需要“词性模式频次”，可直接对 `multiword_pos_patterns` 做 `Counter` 统计。
