import os
import re
from typing import List


def split_start_symbol_and_word(sentence: str) -> str:
    """
    将句子开头的任意符号（含撇号/引号）与后续单词强制分隔。
    """
    if not isinstance(sentence, str) or len(sentence.strip()) == 0:
        return sentence

    stripped_sent = sentence.strip()
    match = re.match(r"^([^a-zA-Z0-9]+)(.*)$", stripped_sent)

    if match:
        start_symbols = match.group(1).strip()
        content = match.group(2).strip()
        if content:
            return f"{start_symbols} {content}"
        return start_symbols

    return stripped_sent


def normalize_single_quote_spacing(sentence: str) -> str:
    """
    将句子中的单引号统一处理为：空格 + ' + 空格。
    例如: I'm here -> I ' m here
    """
    if not isinstance(sentence, str) or len(sentence.strip()) == 0:
        return sentence

    sentence = sentence.replace("'", " ' ")
    sentence = re.sub(r"\s+", " ", sentence).strip()
    return sentence


def process_text_for_tokenize(text: str, sep: str = ". ") -> List[str]:
    """
    拆分句子 -> 处理开头符号 -> 处理单引号空格化。
    返回可直接分词的句子列表。
    """
    sentences = [s.strip() for s in text.split(sep) if s.strip()]
    processed_sentences = [
        normalize_single_quote_spacing(split_start_symbol_and_word(sent))
        for sent in sentences
    ]
    return processed_sentences


def process_word_number_combination(keywords: List[str], text: str) -> str:
    """
    1) 拆分“单词+数字”无空格拼接（如 Lesson7 -> Lesson 7）
    2) 给关键词后数字加逗号（如 Lesson 7 A -> Lesson 7, A）
    """
    if not isinstance(text, str) or len(text.strip()) == 0:
        return text

    split_pattern = re.compile(r"(?<=[a-zA-Z])(?=\d)")
    text = split_pattern.sub(" ", text)

    keyword_pattern = "|".join(keywords)
    comma_pattern = re.compile(
        r"(?i)({})\s+(\d+)(\s+)(?=[a-zA-Z])".format(keyword_pattern)
    )

    def add_comma(match: re.Match[str]) -> str:
        keyword = match.group(1)
        number = match.group(2)
        space = match.group(3)
        return f"{keyword} {number},{space}"

    processed_text = comma_pattern.sub(add_comma, text)
    return processed_text


if __name__ == "__main__":
    target_keywords = ["lesson", "chapter", "unit", "section"]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    text_file_path = os.path.join(current_dir, "ACCA.txt")

    if os.path.exists(text_file_path):
        with open(text_file_path, "r", encoding="UTF-8") as file:
            for line_num, line in enumerate(file, 1):
                if len(line.strip()) > 2:
                    text = process_word_number_combination(target_keywords, line)
                    processed_sentences = process_text_for_tokenize(text)
                    for sent in processed_sentences:
                        print(f"L{line_num}: {sent}")
