# English Visual Grammar Encoder

基于 NLTK 的“英文句子视觉化语法标注”示例实现。

## 功能

- 对输入句子做分词 + 词性标注。
- 为每个单词每个字母输出 **6 位编码**：
  - 前 3 位：词性大类 + 字体样式 + 下着重号。
  - 后 3 位：从句/非谓语边界 + 句子成分 + 被动/情态/虚拟等语法辅助。
- 将重复逻辑拆成多个可复用方法，方便继续按你的规则扩展。
- 新增 **NLTK 结果纠偏层**（rule-based re-tagging），对整段文本常见误标（如 can/MD、冠词 DT、to 不定式、纯数字 CD）做二次修正。

## 安装

```bash
pip install nltk
```

> 首次运行会自动下载 `punkt` 与 `averaged_perceptron_tagger` 资源。

## 运行

```bash
python Extract_nouns.py
```

运行后会在当前目录生成 `encoded_output.docx`，内容包含原句与每个 token 的编码结果。


## 图形界面（简化系统）

你可以直接运行一个桌面界面版本（Tkinter，无需额外安装 GUI 库）：

```bash
python app.py
```

界面支持：
- 输入整句或多段英文文本。
- 一键编码，输出 `token/POS: 紧凑编码`。
- 一键导出 `.docx`。

## 作为库调用

```python
from Extract_nouns import VisualGrammarEncoder

encoder = VisualGrammarEncoder()
result = encoder.encode_sentence("He can finish the work quickly.")

for item in result:
    print(item.token, item.pos, item.compact)

saved = encoder.save_sentence_to_word("He can finish the work quickly.", "my_result.docx")
print(saved)
```

> `save_sentence_to_word` 不依赖 `python-docx`，会直接生成可被 Word 打开的 `.docx` 文件。

## 输出说明

`item.compact` 形如：

```
d000100o000100
```

表示每个字母后跟一个 6 位数字编码。

## 注意

这版实现尽量贴合你的文档规则，但由于自然语言需要上下文/语义理解，
“使役动词、名词子类、否定限制、从句边界、句子成分”等部分使用了启发式判断，
你可以在 `Extract_nouns.py` 中继续增补词典与规则。

## 新增：整段文本编码/解码

```python
from Extract_nouns import VisualGrammarEncoder

enc = VisualGrammarEncoder()

text = """Lesson 1 A private conversation
Last week I went to the theatre.
I did not enjoy it.
"""

# 1) 编码整段文本并保存到Word
path = enc.save_encoded_text_to_word(text, "lesson_encoded.docx")
print(path)

# 2) 单词紧凑编码反解
print(enc.decode_compact_token("d000100o000100"))  # do
```

如果你已有形如 `token/POS: c123456h123456...` 的多行结果，可用：

```python
decoded_text = enc.decode_compact_text(encoded_lines_text)
print(decoded_text)
```


## Noun Phrase Extraction (2+ tokens)

```python
from Extract_nouns import VisualGrammarEncoder

enc = VisualGrammarEncoder()
text = "The old city park is open. John's book cover is red."
result = enc.get_noun_phrases(text)

# 1) 两个或以上单词构成的名词语块
for chunk in result["multiword_chunks"]:
    print(chunk["text"], chunk["pattern"], chunk["tags"])

# 2) 不构成名词语块的单个名词（输出前后词性）
for item in result["single_nouns_with_context"]:
    print(item["token"], item["context_pattern"])
```

返回结构包含：
- `multiword_chunks`：匹配到的 2+ 词名词语块（含原文、tag 序列、命中的模式）。
- `single_nouns_with_context`：未被 2+ 语块覆盖的单个名词，附 `前词性_名词词性_后词性`。

## GitHub PR 显示 "This branch has conflicts" 怎么办

当你在 GitHub 看到 `This branch has conflicts that must be resolved`（例如冲突文件是
`README.md`、`Extract_nouns.py`）时，表示你的分支和目标分支都改了同一段内容，需要先手动合并。

### 命令行解决（推荐）

假设你的 PR 是 `work` 分支合并到 `main`：

```bash
# 1) 拉取最新远程信息
git fetch origin

# 2) 切到你的开发分支
git checkout work

# 3) 把目标分支合进来（也可用 rebase）
git merge origin/main
```

出现冲突后：

```bash
# 4) 打开冲突文件，处理 <<<<<<< ======= >>>>>>> 标记
#    处理完成后标记为已解决
git add README.md Extract_nouns.py

# 5) 完成合并提交
git commit -m "Resolve merge conflicts with main"

# 6) 推送到远程，PR 会自动更新
git push origin work
```

### 用 GitHub 网页解决

1. 在 PR 页面点击 **Resolve conflicts**。
2. 逐个文件编辑并保留正确内容。
3. 点击 **Mark as resolved**，再 **Commit merge**。
4. 返回 PR 页面后即可继续合并。

### 小提示

- 冲突不是代码“坏了”，只是两个分支改了同一位置。
- 建议先备份当前改动，再解决冲突。
- 解决后务必本地运行：

```bash
python -m py_compile Extract_nouns.py
```
## 编码整本书（txt）

```python
from pathlib import Path
from Extract_nouns import VisualGrammarEncoder

encoder = VisualGrammarEncoder()
book_text = Path("book.txt").read_text(encoding="utf-8")
output = encoder.save_encoded_text_to_word(book_text, "book_encoded.docx")
print(output)
```

实现上会先按段落，再按句子分割后编码，比“整段直接一次性标注”更稳定。


## 如何进一步提升 NLTK 误判（建议路线）

当前仓库已加入“NLTK + 规则纠偏”两段式标注。对复杂句可继续做：

1. **多模型投票**：NLTK 与 spaCy/Stanza 并行标注，冲突位置再走规则判定。  
2. **规则分层**：把“时态、助动词、从句边界、非谓语”拆成独立 pass，降低单规则副作用。  
3. **领域词典**：加入你的教学词表（不可数名词、集体名词、否定限定词等），命中时强制标签。  
4. **可解释日志**：每个 token 记录“原标签→修正标签→触发规则”，便于教师回查。  
5. **人工回标闭环**：把老师改过的结果沉淀为 YAML/JSON 规则，持续提高准确率。  

