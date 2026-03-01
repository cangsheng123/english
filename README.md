# English Visual Grammar Encoder

基于 NLTK 的“英文句子视觉化语法标注”示例实现。

## 功能

- 对输入句子做分词 + 词性标注。
- 为每个单词每个字母输出 **6 位编码**：
  - 前 3 位：词性大类 + 字体样式 + 下着重号。
  - 后 3 位：从句/非谓语边界 + 句子成分 + 被动/情态/虚拟等语法辅助。
- 将重复逻辑拆成多个可复用方法，方便继续按你的规则扩展。

## 安装

```bash
pip install nltk
```

> 首次运行会自动下载 `punkt` 与 `averaged_perceptron_tagger` 资源。

## 运行

```bash
python encoder.py
```

## 作为库调用

```python
from encoder import VisualGrammarEncoder

encoder = VisualGrammarEncoder()
result = encoder.encode_sentence("He can finish the work quickly.")

for item in result:
    print(item.token, item.pos, item.compact)
```

## 输出说明

`item.compact` 形如：

```
d000100o000100
```

表示每个字母后跟一个 6 位数字编码。

## 注意

这版实现尽量贴合你的文档规则，但由于自然语言需要上下文/语义理解，
“使役动词、名词子类、否定限制、从句边界、句子成分”等部分使用了启发式判断，
你可以在 `encoder.py` 中继续增补词典与规则。
