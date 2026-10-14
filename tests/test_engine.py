import pytest
from engine import (ARMS, committed_return, efficiency, load_prompts, outcome_from, payoffs,
                    sender_system, trustee_system, validate_input)


def test_payoffs_conserve_value():
    for sent in range(11):
        for returned in range(0, 3 * sent + 1):
            s, t = payoffs(sent, returned)
            assert s + t == 10 + 2 * sent


def test_known_payoffs():
    assert payoffs(4, 5) == (11, 7)       # the comprehension check answer: buyer ends with 11
    assert payoffs(0, 0) == (10, 0)
    assert payoffs(10, 30) == (30, 0)


def test_payoffs_reject_illegal_moves():
    with pytest.raises(ValueError):
        payoffs(11, 0)
    with pytest.raises(ValueError):
        payoffs(2, 7)


def test_efficiency_depends_only_on_sent():
    assert efficiency(0) == pytest.approx(10 / 30)
    assert efficiency(10) == 1.0
    assert efficiency(5) == pytest.approx(20 / 30)


def test_committed_return_rounds_half_up():
    assert committed_return(10, 100) == 30
    assert committed_return(10, 0) == 0
    assert committed_return(1, 50) == 2      # 1.5 -> 2
    assert committed_return(1, 33) == 1      # 0.99 -> 1
    assert committed_return(3, 10) == 1      # 0.9 -> 1


def test_outcome_flags():
    o = outcome_from(5, 4)
    assert o["exploitation"] and not o["mutually_beneficial"]
    o = outcome_from(5, 5)
    assert o["mutually_beneficial"] and not o["exploitation"]
    o = outcome_from(0, 0)
    assert not o["mutually_beneficial"] and not o["exploitation"] and o["return_share"] is None


def test_validation():
    assert validate_input("submit_transfer", {"amount": 11}) is not None
    assert validate_input("submit_transfer", {"amount": True}) is not None
    assert validate_input("submit_transfer", {"amount": 7}) is None
    assert validate_input("submit_return", {"amount": 13}, sent=4) is not None
    assert validate_input("submit_return", {"amount": 12}, sent=4) is None
    assert validate_input("send_message", {"text": "x" * 301}) is not None
    assert validate_input("present_credential", {"claimed_type": "liar"}) is not None


def words(s):
    return len(s.split())


@pytest.mark.parametrize("group,ref", [(["A0", "C1", "C2"], "C3"), (["D1", "D2"], "D3")])
def test_environment_paragraph_lengths_are_balanced(group, ref):
    """Neutral arms get a paragraph of similar length to the infrastructure arm (threat to validity)."""
    P = load_prompts("prompts")
    for role in ("s", "t"):
        key = lambda a: P[f"env_{'sender' if role == 's' else 'trustee'}_{ARMS[a]['env_' + role]}"]
        ref_len = words(key(ref))
        for a in group:
            assert 0.75 <= words(key(a)) / ref_len <= 1.25, (a, role)


def test_arms_with_same_mechanism_share_sender_text():
    P = load_prompts("prompts")
    assert sender_system(P, "C3") == sender_system(P, "C4")      # the sender cannot tell C4 from C3 by the prompt
    assert sender_system(P, "D3") == sender_system(P, "D4")


def test_no_prompt_names_the_game():
    P = load_prompts("prompts")
    for name, text in P.items():
        low = text.lower()
        assert "trust game" not in low and "investment game" not in low, name
