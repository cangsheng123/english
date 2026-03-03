from adjective_validator import AdjectiveValidator


def test_adjective_validator_keep_for_linking_verb_context() -> None:
    validator = AdjectiveValidator()
    tagged = [("operations", "NNS"), ("are", "VBP"), ("proving", "VBG"), ("difficult", "JJ")]
    fixed = validator.validate_and_correct(tagged)
    assert fixed[-1] == ("difficult", "JJ")


def test_adjective_validator_change_md_plus_jj_to_vb() -> None:
    validator = AdjectiveValidator()
    tagged = [("will", "MD"), ("better", "JJ"), ("go", "VB")]
    fixed, traces = validator.validate_with_trace(tagged)

    assert fixed[1] == ("better", "VB")
    assert traces[0]["action"] == "change"
    assert traces[0]["final"] == "VB"
