# English Visual Grammar Encoder（含名词块分析 GUI）

本项目提供两类能力：

1. **英文语法编码**：对 token 生成逐字母 6 位编码。  
2. **名词块分析**：提取 2 词及以上名词块，并输出名词块内名词拆分结果与词性模式频次。

---

## 1. 项目结构

- `Extract_nouns.py`：核心算法（编码 + 名词块分析 + Excel/Word 导出）
- `app.py`：Tkinter 图形界面
- `NOUN_CHUNK_ANALYSIS.md`：名词块分析模块的独立调用文档

---

## 2. 安装依赖

```bash
pip install nltk openpyxl
```

> 首次运行会尝试下载 NLTK 资源（如 `punkt`、`averaged_perceptron_tagger`）。

---

## 3. 运行方式

### 3.1 启动图形界面

```bash
python app.py
```

界面支持：
- 输入多行英文文本（含滚动条）
- 语法编码展示
- 名词块分析（三段输出）
- 导出名词分析 Excel
- 导出编码 Word

### 3.2 命令行演示（核心模块）

```bash
python Extract_nouns.py
```

---

## 4. 名词块分析（当前实现）

点击 GUI 的「名词块分析」后，输出分三段：

1. **第一部分：两个及以上单词组成的名词块模式**
   - 如：`the telephone -> DT_NN`
2. **第二部分：名词块中的名词及去名词后词性组合**
   - 例如名词块 `PRP$_NN_NNP` 中，名词 `aunt/NN` 去掉后剩余 `PRP$_NNP`
3. **最后：名词块词性模式频次统计**
   - 统计当前输入文本中各 `multiword_pos_patterns` 出现次数

> 详细字段定义请看 `NOUN_CHUNK_ANALYSIS.md`。

---

## 5. 作为库调用（推荐）

```python
from Extract_nouns import VisualGrammarEncoder

text = "Just then, the telephone rang. It was my aunt Lucy."
enc = VisualGrammarEncoder()

# 原始结构化结果
raw = enc.get_noun_phrases(text)
print(raw["multiword_chunks"])
print(raw["multiword_pos_patterns"])
print(raw["chunk_noun_stats"])

# 界面/导出友好结果
labeled = enc.get_labeled_noun_results(text)
print(labeled["labeled_multiword"])
print(labeled["labeled_single"])
```

---

## 6. 导出能力

### 6.1 名词分析导出 Excel

```python
saved = enc.export_noun_results_to_excel(text, "名词块分析结果.xlsx")
print(saved)
```

Excel 默认两个工作表：

1. `2词及以上名词块模式`
   - 句子序号 / 名词块文本 / 词性组合模式
2. `名词块中的名词及剩余词性统计`
   - 名词 / 名词词性 / 去除名词后剩余词性组合 / 频次

### 6.2 编码导出 Word

```python
saved = enc.save_encoded_text_to_word(text, "编码结果.docx")
print(saved)
```

---

## 7. GUI 初始化说明（重要）

`app.py` 采用了更稳健的延迟初始化方式：

- 窗口会优先显示；
- 若 NLTK 资源暂时不可用，会在状态栏与弹窗中给出提示；
- 分析按钮会在需要时重试初始化编码器。

---

## 8. 常见问题

### Q1: 界面可以打开，但点击分析报错 NLTK 相关错误？
先确保已安装依赖并能下载 NLTK 资源：

```bash
pip install nltk
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

### Q2: 我只想复用名词块分析逻辑，不要 GUI。
直接参考并调用 `NOUN_CHUNK_ANALYSIS.md` 中的 API 说明与示例。

