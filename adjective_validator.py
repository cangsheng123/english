"""JJ 词性验证与纠偏模块。"""

from __future__ import annotations

from typing import List, Sequence, Tuple


class AdjectiveValidator:
    def __init__(self) -> None:
        self.noun_tags = {"NN", "NNS", "NNP", "NNPS"}
        self.verb_tags = {"VB", "VBN", "VBZ", "VBP", "VBG", "VBD"}
        self.linking_verbs = {
            "be", "am", "is", "are", "was", "were", "been", "being",
            "seem", "seems", "seemed", "appear", "appears", "appeared",
            "become", "becomes", "became", "remain", "remains", "remained",
            "prove", "proves", "proved", "proving",
            "ring", "rang",
            "feel", "feels", "felt", "look", "looks", "looked",
            "smell", "smells", "smelled", "sound", "sounds", "sounded",
        }
        self.indefinite_pronouns = {
            "many", "few", "several", "one", "other", "another", "some", "any", "each", "either", "neither",
        }

    def validate_and_correct(self, tagged: Sequence[Tuple[str, str]]) -> List[Tuple[str, str]]:
        fixed = list(tagged)
        for i, (tok, pos) in enumerate(fixed):
            if pos not in {"JJ", "JJR", "JJS"}:
                continue
            if self._is_valid_adj(fixed, i):
                continue
            fixed[i] = (tok, self._correct_adj(fixed, i))
        return fixed

    def _is_valid_adj(self, tagged: Sequence[Tuple[str, str]], i: int) -> bool:
        tok, pos = tagged[i]
        prev_pos = tagged[i - 1][1] if i > 0 else "<BOS>"
        next_pos = tagged[i + 1][1] if i + 1 < len(tagged) else "<EOS>"
        prev_word = tagged[i - 1][0].lower() if i > 0 else ""

        if i == 0 or prev_pos in {",", ".", ";", ":", "!", "?"}:
            return True
        if prev_pos == "WRB":
            return True
        if prev_word in self.linking_verbs:
            return True
        if i >= 2 and tagged[i - 2][0].lower() in self.linking_verbs and prev_pos in {"RB", "RBR", "RBS", "JJR"}:
            return True
        if i >= 2 and tagged[i - 2][1] == "VBN" and prev_word in {"is", "are", "was", "were", "been", "be", "being"}:
            return True
        if prev_pos == "CD" and next_pos in self.noun_tags:
            return True
        if prev_pos in self.noun_tags:
            return True
        if prev_pos == "RP" or (next_pos == "CC" and i + 2 < len(tagged) and tagged[i + 2][1] in {"JJ", "JJR", "JJS"}):
            return True
        if prev_pos == "DT" and i > 0 and tagged[i - 1][0].lower() == "the":
            return True
        if prev_pos == "CC" and i >= 2 and tagged[i - 1][1] == "RB":
            return True
        if prev_pos == "RB" and i >= 2 and tagged[i - 2][1] in {"CC", "IN"}:
            return True
        # 形容词在名词语块中：后续是名词
        if next_pos in self.noun_tags:
            return True
        # 动宾补粗略模式：V + (PRP/名词) + JJ
        if i >= 2 and tagged[i - 2][1] in self.verb_tags and tagged[i - 1][1] in {"PRP", *self.noun_tags}:
            return True
        return False

    def _correct_adj(self, tagged: Sequence[Tuple[str, str]], i: int) -> str:
        word = tagged[i][0].lower()
        prev_pos = tagged[i - 1][1] if i > 0 else "<BOS>"
        prev_word = tagged[i - 1][0].lower() if i > 0 else ""

        if prev_pos == "MD":
            return "VB"
        if prev_pos == "PRP$":
            return "NN"
        if prev_pos == "DT" and prev_word != "the":
            return "NN"
        if prev_pos == "IN":
            return "NN"
        if prev_pos == "TO":
            return "NN"
        if prev_pos in self.verb_tags and prev_word not in self.linking_verbs:
            return "NN"
        if word in self.indefinite_pronouns:
            return "PRP"
        return "NN"
