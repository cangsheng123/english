from adjective_validator import AdjectiveValidator


def test_linking_verb_plus_jj_kept() -> None:
    tagged = [("operations", "NNS"), ("are", "VBP"), ("proving", "VBG"), ("difficult", "JJ")]
    fixed = AdjectiveValidator().validate_and_correct(tagged)
    assert fixed[-1] == ("difficult", "JJ")


def test_md_plus_jj_corrected_to_vb() -> None:
    tagged = [("will", "MD"), ("better", "JJ"), ("it", "PRP")]
    fixed = AdjectiveValidator().validate_and_correct(tagged)
    assert fixed[1] == ("better", "VB")
