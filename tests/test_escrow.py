import random
from escrow import Escrow, corrupt, verify_signature


def test_valid_commitment_verifies():
    e = Escrow()
    payload, sig = e.issue_commitment("g1", 40)
    assert verify_signature(e.public_key_hex, payload, sig)


def test_tampered_payload_fails():
    e = Escrow()
    payload, sig = e.issue_commitment("g1", 40)
    assert not verify_signature(e.public_key_hex, {**payload, "share_percent": 90}, sig)


def test_broken_commitment_fails():
    e = Escrow()
    payload, sig = e.issue_commitment("g1", 40, broken=True)
    assert not verify_signature(e.public_key_hex, payload, sig)


def test_other_escrow_key_fails():
    a, b = Escrow(), Escrow()
    payload, sig = a.issue_commitment("g1", 40)
    assert not verify_signature(b.public_key_hex, payload, sig)


def test_credential_signed_only_when_true():
    e, rng = Escrow(), random.Random(1)
    p, s = e.issue_credential("g", "fair", "fair", rng)
    assert verify_signature(e.public_key_hex, p, s)
    p, s = e.issue_credential("g", "fair", "self_interested", rng)      # a lie
    assert not verify_signature(e.public_key_hex, p, s)
    p, s = e.issue_credential("g", "self_interested", "self_interested", rng, broken=True)
    assert not verify_signature(e.public_key_hex, p, s)


def test_missing_or_garbage_signature_fails():
    e = Escrow()
    payload, sig = e.issue_commitment("g1", 10)
    assert not verify_signature(e.public_key_hex, payload, None)
    assert not verify_signature(e.public_key_hex, payload, "zz")
    assert corrupt(sig) != sig
