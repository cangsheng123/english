from text_preprocess import normalize_single_quote_spacing, process_text_for_tokenize


def test_normalize_single_quote_spacing_splits_single_quote_with_spaces() -> None:
    src = "I'm sure it's John's book."
    out = normalize_single_quote_spacing(src)
    assert out == "I ' m sure it ' s John ' s book."


def test_process_text_for_tokenize_keeps_single_quote_spaced_in_each_sentence() -> None:
    text = "I've arrived. It's fine."
    result = process_text_for_tokenize(text)
    assert result == ["I ' ve arrived", "It ' s fine."]
