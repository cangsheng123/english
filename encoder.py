"""英文句子视觉化语法标注编码器。

实现目标：
1) 使用 NLTK 分词 + 词性标注。
2) 为每个单词的每个字母输出 6 位数字编码：
   - 前三位：词性/字体粗细与灰度/下着重号。
   - 后三位：从句与非谓语边界/句子成分/语法辅助(被动、情态、虚拟等)。
3) 返回可直接用于后续 Word 样式渲染的数据结构和字符串。

说明：
- 由于自然语言存在歧义，部分“子类判定”采用可解释的启发式规则。
- 代码中将重复逻辑抽成独立方法，便于扩展。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple
import re

import nltk
from nltk import pos_tag, word_tokenize


# -----------------------------
# 数据结构
# -----------------------------


@dataclass
class LetterCode:
    char: str
    code: str  # 6位字符串


@dataclass
class TokenEncoding:
    token: str
    pos: str
    letters: List[LetterCode]

    @property
    def compact(self) -> str:
        """形如 d000100o000100 的紧凑输出。"""
        return "".join(f"{item.char}{item.code}" for item in self.letters)


class VisualGrammarEncoder:
    """将句子编码为每字母 6 位数字。"""

    def __init__(self) -> None:
        self._ensure_nltk_resources()

        # 前三位中的第一位（词性大类）
        self.first_digit_map: Dict[str, str] = {
            "VERB": "0",
            "NOUN": "1",
            "ADJ": "2",
            "PRON": "3",
            "ADV": "4",
            "DET": "5",
            "CONJ": "6",
            "UH": "7",
            "PREP": "8",
            "NUM": "9",
            "OTHER": "0",  # 无法识别时兜底
        }

        self.negative_words = {
            "not", "never", "no", "none", "neither", "nor", "hardly", "scarcely", "seldom",
            "few", "little", "barely", "without",
        }
        self.modal_words = {
            "can", "could", "may", "might", "must", "shall", "should", "will", "would", "ought",
        }
        self.future_modals = {"will", "shall"}
        self.future_in_past_modals = {"would", "should"}
        self.copulas = {"am", "is", "are", "was", "were", "be", "been", "being"}
        self.aux_verbs = {
            "am", "is", "are", "was", "were", "be", "been", "being",
            "do", "does", "did", "have", "has", "had",
        }
        self.causative_verbs = {"let", "make", "have", "get", "help"}

        self.subordinators = {
            "that", "which", "who", "whom", "whose", "when", "where", "why", "how",
            "if", "whether", "because", "although", "though", "while", "since", "before", "after",
            "unless", "until", "once",
        }

    # -----------------------------
    # 公共方法
    # -----------------------------

    def encode_sentence(self, sentence: str) -> List[TokenEncoding]:
        tokens = word_tokenize(sentence)
        tagged = pos_tag(tokens)

        # 先计算“后3位”的句法辅助上下文
        clause_marks = self._detect_clause_nonfinite_marks(tagged)
        component_marks = self._detect_sentence_components(tagged)
        grammar_marks = self._detect_grammar_aux_marks(tagged)

        results: List[TokenEncoding] = []
        for i, (token, pos) in enumerate(tagged):
            letters = self._encode_token_letters(
                token=token,
                pos=pos,
                tagged=tagged,
                index=i,
                clause_mark=clause_marks[i],
                component_mark=component_marks[i],
                grammar_mark=grammar_marks[i],
            )
            results.append(TokenEncoding(token=token, pos=pos, letters=letters))
        return results

    def encode_sentence_as_dict(self, sentence: str) -> List[Dict[str, object]]:
        """便于 JSON 序列化。"""
        encoded = self.encode_sentence(sentence)
        return [
            {
                "token": item.token,
                "pos": item.pos,
                "compact": item.compact,
                "letters": [{"char": l.char, "code": l.code} for l in item.letters],
            }
            for item in encoded
        ]

    # -----------------------------
    # NLTK 准备
    # -----------------------------

    def _ensure_nltk_resources(self) -> None:
        resources = [
            ("tokenizers/punkt", "punkt"),
            ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
        ]
        for resource_path, package in resources:
            try:
                nltk.data.find(resource_path)
            except LookupError:
                nltk.download(package, quiet=True)

    # -----------------------------
    # 编码核心
    # -----------------------------

    def _encode_token_letters(
        self,
        token: str,
        pos: str,
        tagged: Sequence[Tuple[str, str]],
        index: int,
        clause_mark: str,
        component_mark: str,
        grammar_mark: str,
    ) -> List[LetterCode]:
        # 纯数字 CD：按需求原样返回
        if pos == "CD" and token.isdigit():
            return [LetterCode(ch, "") for ch in token]

        chars = list(token)
        n = len(chars)
        digits = [["0", "0", "0"] for _ in range(n)]

        # 默认第一位
        first = self._category_first_digit(pos)
        for d in digits:
            d[0] = first

        # 基础前三位规则
        self._apply_pos_rules(token, pos, tagged, index, digits)

        # 拼接后3位
        final: List[LetterCode] = []
        for ch, d in zip(chars, digits):
            six = "".join(d) + clause_mark + component_mark + grammar_mark
            final.append(LetterCode(ch, six))
        return final

    def _category_first_digit(self, pos: str) -> str:
        if pos.startswith("VB") or pos == "MD":
            return self.first_digit_map["VERB"]
        if pos in {"NN", "NNS", "NNP", "NNPS", "POS"}:
            return self.first_digit_map["NOUN"]
        if pos.startswith("JJ"):
            return self.first_digit_map["ADJ"]
        if pos in {"PRP", "PRP$", "WP", "WP$", "WDT"}:
            return self.first_digit_map["PRON"]
        if pos in {"RB", "RBR", "RBS", "RP", "WRB", "EX"}:
            return self.first_digit_map["ADV"]
        if pos in {"DT", "PDT"}:
            return self.first_digit_map["DET"]
        if pos in {"CC"}:
            return self.first_digit_map["CONJ"]
        if pos == "UH":
            return self.first_digit_map["UH"]
        if pos == "TO":
            return self.first_digit_map["PREP"]
        if pos == "IN":
            return self.first_digit_map["PREP"]
        if pos == "CD":
            return self.first_digit_map["NUM"]
        return self.first_digit_map["OTHER"]

    # -----------------------------
    # 规则方法（可复用）
    # -----------------------------

    def _apply_pos_rules(
        self,
        token: str,
        pos: str,
        tagged: Sequence[Tuple[str, str]],
        index: int,
        digits: List[List[str]],
    ) -> None:
        lower = token.lower()

        if pos.startswith("VB") or pos == "MD" or (pos == "TO"):
            self._apply_verb_rules(lower, pos, tagged, index, digits)
            return

        if pos in {"NN", "NNS", "NNP", "NNPS", "POS"}:
            self._apply_noun_rules(lower, pos, digits)
            return

        if pos.startswith("JJ"):
            self._apply_adj_rules(lower, pos, digits)
            return

        if pos in {"PRP", "PRP$", "WP", "WP$", "WDT"}:
            self._apply_pron_rules(lower, pos, digits)
            return

        if pos in {"RB", "RBR", "RBS", "RP", "WRB", "EX"}:
            self._apply_adv_rules(lower, pos, digits)
            return

        if pos in {"DT", "PDT"}:
            self._apply_det_rules(lower, digits)
            return

        if pos in {"CC", "IN"}:
            self._apply_conj_or_prep_rules(lower, pos, digits)
            return

        if pos == "UH":
            self._apply_uh_rules(lower, digits)
            return

        if pos == "CD":
            self._apply_num_rules(lower, digits)
            return

        if pos in {"LS", "SYM", "FW"}:
            for d in digits:
                d[1], d[2] = "0", "0"

    def _apply_emphasis(self, digits: List[List[str]], indices: Iterable[int], second: str | None = None, third: str | None = None) -> None:
        for i in indices:
            if 0 <= i < len(digits):
                if second is not None:
                    digits[i][1] = second
                if third is not None:
                    digits[i][2] = third

    def _middle_index(self, n: int) -> int:
        return n // 2 if n > 0 else 0

    def _apply_verb_rules(self, lower: str, pos: str, tagged: Sequence[Tuple[str, str]], index: int, digits: List[List[str]]) -> None:
        n = len(digits)

        # TO: 介词to / 不定式to
        if pos == "TO":
            next_pos = tagged[index + 1][1] if index + 1 < len(tagged) else ""
            if next_pos == "VB":
                for d in digits:
                    d[0] = "0"  # 视为动词原形引导
            else:
                for d in digits:
                    d[0] = "8"  # 介词
            return

        # VB 原形
        if pos == "VB":
            if lower in self.causative_verbs and n >= 2:
                self._apply_emphasis(digits, [self._middle_index(n)], second="1")
            return

        # VBD 过去式：后两个下着重号=1
        if pos == "VBD":
            self._apply_emphasis(digits, range(max(0, n - 2), n), third="1")
            if lower in self.aux_verbs and n >= 1:
                self._apply_emphasis(digits, [0], second="1")
            return

        # VBG 现在分词：后三个加粗；若动名词 -> 后四个加粗
        if pos == "VBG":
            is_gerund = self._is_gerund_context(tagged, index)
            k = 4 if is_gerund else 3
            self._apply_emphasis(digits, range(max(0, n - k), n), second="1")
            return

        # VBN 过去分词：后两个加粗
        if pos == "VBN":
            self._apply_emphasis(digits, range(max(0, n - 2), n), second="1")
            return

        # VBP 非三单现在：默认全部加粗
        if pos == "VBP":
            self._apply_emphasis(digits, range(n), second="1")
            if lower in self.aux_verbs:
                if n <= 3:
                    # 短助动词只突出助动属性：首字母加粗，其余恢复常规
                    for i in range(1, n):
                        digits[i][1] = "0"
                    self._apply_emphasis(digits, [0], second="1")
                else:
                    self._apply_emphasis(digits, [0], second="1")
            mid = self._middle_index(n) if n > 2 else 0
            self._apply_emphasis(digits, [mid], second="1")
            return

        # VBZ 三单现在：末字母加粗 + 中间突出
        if pos == "VBZ":
            if n:
                self._apply_emphasis(digits, [n - 1], second="1")
            if lower in self.aux_verbs and n > 2:
                self._apply_emphasis(digits, [0], second="1")
            mid = self._middle_index(n) if n > 2 else 0
            self._apply_emphasis(digits, [mid], second="1")
            return

        # MD 情态动词
        if pos == "MD":
            # 前两位加粗
            self._apply_emphasis(digits, [0, 1], second="1")
            if lower in self.future_modals:
                # 前三位下着重号：将来
                self._apply_emphasis(digits, [0, 1, 2], third="1")
            elif lower in self.future_in_past_modals:
                # 前两后两下着重号：过去将来
                self._apply_emphasis(digits, [0, 1, n - 2, n - 1], third="1")
            else:
                # 一般情态：中间位下着重号
                self._apply_emphasis(digits, [self._middle_index(n)], third="1")
            return

    def _apply_noun_rules(self, lower: str, pos: str, digits: List[List[str]]) -> None:
        n = len(digits)
        if pos in {"NNS", "NNPS"} and n:
            self._apply_emphasis(digits, [n - 1], second="1")
        elif pos == "NN":
            # 启发式：不可数常见词
            if lower in {"water", "milk", "money", "information", "advice", "furniture", "news"}:
                self._apply_emphasis(digits, [n - 2, n - 1], second="1")
            # 抽象名词后缀
            elif re.search(r"(tion|sion|ness|ity|ment|ship|ism|age)$", lower):
                self._apply_emphasis(digits, [self._middle_index(n)], second="1")
            # 集体名词示例
            elif lower in {"team", "family", "group", "government", "staff", "audience"}:
                self._apply_emphasis(digits, [0, 1, 2], second="1")
        elif pos == "POS":
            for d in digits:
                d[1] = "2"

    def _apply_adj_rules(self, lower: str, pos: str, digits: List[List[str]]) -> None:
        n = len(digits)
        if lower in self.negative_words:
            self._apply_emphasis(digits, range(n), second="2")
            if n >= 2:
                self._apply_emphasis(digits, [self._middle_index(n)], second="1")
            return

        if pos == "JJR":
            self._apply_emphasis(digits, [n - 2, n - 1], second="1")
        elif pos == "JJS":
            self._apply_emphasis(digits, [n - 3, n - 2, n - 1], second="1")

    def _apply_pron_rules(self, lower: str, pos: str, digits: List[List[str]]) -> None:
        n = len(digits)
        object_pronouns = {"me", "him", "her", "us", "them", "you", "whom"}
        possessive_independent = {"mine", "yours", "his", "hers", "ours", "theirs"}

        if pos == "PRP":
            if lower in object_pronouns and n:
                self._apply_emphasis(digits, [n - 1], second="2")
        elif pos == "PRP$":
            if n:
                self._apply_emphasis(digits, [0], second="2")
            if lower in possessive_independent and n:
                self._apply_emphasis(digits, [self._middle_index(n)], second="2")
        elif pos == "WDT":
            self._apply_emphasis(digits, [0, 1], second="2")
        elif pos in {"WP", "WP$"}:
            if n >= 2:
                self._apply_emphasis(digits, [n - 2, n - 1], second="2")

    def _apply_adv_rules(self, lower: str, pos: str, digits: List[List[str]]) -> None:
        n = len(digits)
        if pos == "RB":
            if lower in self.negative_words:
                self._apply_emphasis(digits, range(n), second="2")
            elif lower in {"as", "so", "equally"} and n:
                self._apply_emphasis(digits, [n - 1], second="2")
        elif pos == "RBR":
            self._apply_emphasis(digits, [n - 2, n - 1], second="2")
        elif pos == "RBS":
            self._apply_emphasis(digits, [n - 3, n - 2, n - 1], second="2")
        elif pos == "RP" and n:
            self._apply_emphasis(digits, [0], second="2")
        elif pos == "WRB":
            self._apply_emphasis(digits, [0, 1], second="2")

    def _apply_det_rules(self, lower: str, digits: List[List[str]]) -> None:
        n = len(digits)
        if lower in self.negative_words or lower in {"no", "neither", "none", "few", "little"}:
            # 按需求：否定意义限定词以 410 风格呈现 -> 第一位属于副词类4
            for d in digits:
                d[0], d[1], d[2] = "4", "1", "0"
        else:
            for d in digits:
                d[0], d[1], d[2] = "5", "0", "0"

    def _apply_conj_or_prep_rules(self, lower: str, pos: str, digits: List[List[str]]) -> None:
        n = len(digits)
        paired = {"either", "neither", "nor", "both", "and", "not", "only", "or"}

        if pos == "CC":
            for d in digits:
                d[0], d[1], d[2] = "6", "0", "0"
            if lower in paired and n:
                self._apply_emphasis(digits, [0], second="2")
            return

        # IN: 可能是介词或从属连词
        if lower in self.subordinators:
            for d in digits:
                d[0], d[1], d[2] = "6", "0", "0"
            if n:
                self._apply_emphasis(digits, [n - 1], second="2")
        else:
            for d in digits:
                d[0], d[1], d[2] = "8", "0", "0"

    def _apply_uh_rules(self, lower: str, digits: List[List[str]]) -> None:
        greetings = {"morning", "evening", "hello", "hi"}
        if lower in greetings:
            # 问候语：末字母 710 其余 700
            for d in digits:
                d[0], d[1], d[2] = "7", "0", "0"
            if digits:
                digits[-1][1] = "1"
        else:
            for d in digits:
                d[0], d[1], d[2] = "7", "0", "0"

    def _apply_num_rules(self, lower: str, digits: List[List[str]]) -> None:
        n = len(digits)
        for d in digits:
            d[0], d[1], d[2] = "9", "0", "0"
        # 序数词启发式
        if re.search(r"(st|nd|rd|th)$", lower) and n >= 2:
            self._apply_emphasis(digits, [n - 2, n - 1], second="2")

    # -----------------------------
    # 后三位（语法辅助）
    # -----------------------------

    def _detect_clause_nonfinite_marks(self, tagged: Sequence[Tuple[str, str]]) -> List[str]:
        """第四位：从句/非谓语边界。
        0=无标记, 1=从句起点, 2=从句终点, 3=不定式起点, 4=VBG非谓语, 5=VBN非谓语
        """
        marks = ["0"] * len(tagged)

        for i, (tok, pos) in enumerate(tagged):
            lower = tok.lower()
            if lower in self.subordinators:
                marks[i] = "1"
            if pos == "TO" and i + 1 < len(tagged) and tagged[i + 1][1] == "VB":
                marks[i] = "3"
            if pos == "VBG":
                marks[i] = "4"
            if pos == "VBN":
                marks[i] = "5"

        # 简单从句终点：逗号/句末标点前一个词
        for i, (tok, _) in enumerate(tagged):
            if tok in {",", ";", ".", "!", "?"} and i - 1 >= 0 and marks[i - 1] == "0":
                marks[i - 1] = "2"
        return marks

    def _detect_sentence_components(self, tagged: Sequence[Tuple[str, str]]) -> List[str]:
        """第五位：句子成分。
        0=未标注, 1=主语候选, 2=谓语, 3=宾语, 4=表语, 5=状语
        """
        marks = ["0"] * len(tagged)

        first_finite = -1
        for i, (_, pos) in enumerate(tagged):
            if pos in {"VB", "VBP", "VBZ", "VBD", "MD"}:
                first_finite = i
                break

        if first_finite != -1:
            # 谓语
            marks[first_finite] = "2"

            # 主语候选：谓语前最近名词/代词短窗口
            for i in range(max(0, first_finite - 4), first_finite):
                if tagged[i][1] in {"PRP", "NN", "NNS", "NNP", "NNPS", "WP"}:
                    marks[i] = "1"

            # 宾语候选：谓语后名词/代词
            for i in range(first_finite + 1, min(len(tagged), first_finite + 6)):
                if tagged[i][1] in {"PRP", "NN", "NNS", "NNP", "NNPS"}:
                    marks[i] = "3"

            # 系动词后形容词 -> 表语
            if tagged[first_finite][0].lower() in self.copulas:
                for i in range(first_finite + 1, min(len(tagged), first_finite + 4)):
                    if tagged[i][1].startswith("JJ"):
                        marks[i] = "4"

        # 状语：副词/介词
        for i, (_, pos) in enumerate(tagged):
            if pos in {"RB", "RBR", "RBS", "WRB", "IN", "TO"} and marks[i] == "0":
                marks[i] = "5"

        return marks

    def _detect_grammar_aux_marks(self, tagged: Sequence[Tuple[str, str]]) -> List[str]:
        """第六位：语法辅助。
        0=无, 1=被动语态线索(VBN且前面be), 2=情态动词, 3=虚拟语气线索
        """
        marks = ["0"] * len(tagged)

        for i, (tok, pos) in enumerate(tagged):
            lower = tok.lower()
            if pos == "MD":
                marks[i] = "2"

            if pos == "VBN" and i - 1 >= 0 and tagged[i - 1][0].lower() in self.copulas:
                marks[i] = "1"

            # 虚拟语气线索：if + were / suggest|insist + that + VB
            if lower == "were" and i - 1 >= 0 and tagged[i - 1][0].lower() == "if":
                marks[i] = "3"
            if lower in {"suggest", "insist", "recommend", "demand"}:
                for j in range(i + 1, min(len(tagged), i + 5)):
                    if tagged[j][0].lower() == "that":
                        marks[j] = "3"

        return marks

    # -----------------------------
    # 语境判定
    # -----------------------------

    def _is_gerund_context(self, tagged: Sequence[Tuple[str, str]], index: int) -> bool:
        """VBG 是否更像动名词：前面是介词/限定词/所有格时倾向动名词。"""
        if index == 0:
            return False
        prev_word, prev_pos = tagged[index - 1]
        if prev_pos in {"IN", "DT", "PRP$", "POS"}:
            return True
        if prev_word.lower() in {"by", "for", "of", "about", "before", "after"}:
            return True
        return False


def demo() -> None:
    sentence = "Tom would have been doing the work in the room when I arrived."
    encoder = VisualGrammarEncoder()
    encoded = encoder.encode_sentence(sentence)

    for item in encoded:
        if item.letters and item.letters[0].code == "":
            # 纯数字
            print(f"{item.token}/{item.pos}: {item.token}")
        else:
            print(f"{item.token}/{item.pos}: {item.compact}")


if __name__ == "__main__":
    demo()
