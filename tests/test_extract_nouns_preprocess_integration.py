import Extract_nouns as en


def test_encode_sentence_applies_single_quote_preprocess(monkeypatch) -> None:
    monkeypatch.setattr(en, "nltk", None)
    monkeypatch.setattr(en, "word_tokenize", lambda s: s.split())
    monkeypatch.setattr(en, "pos_tag", lambda toks: [(t, "NN") for t in toks])

    encoder = en.VisualGrammarEncoder()
    encoded = encoder.encode_sentence("I'm")

    assert [item.token for item in encoded] == ["I", "'", "m"]
