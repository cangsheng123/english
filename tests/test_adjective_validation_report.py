import Extract_nouns as en


def test_get_adjective_validation_report_contains_change_record(monkeypatch) -> None:
    monkeypatch.setattr(en, "nltk", None)
    monkeypatch.setattr(en, "sent_tokenize", lambda text: [text])
    monkeypatch.setattr(en, "word_tokenize", lambda s: s.split())
    monkeypatch.setattr(en, "pos_tag", lambda toks: [("will", "MD"), ("better", "JJ"), ("go", "VB")])

    encoder = en.VisualGrammarEncoder()
    rows = encoder.get_adjective_validation_report("will better go")

    assert rows
    assert rows[0]["单词"] == "better"
    assert rows[0]["原词性"] == "JJ"
    assert rows[0]["验证后词性"] == "VB"
    assert rows[0]["动作"] == "修改"
