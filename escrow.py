"""escrow.py - signing and verifying commitments and credentials.

The escrow holds an Ed25519 key, standing in for the key a TEE's hardware would hold.
The signatures and checks are real cryptography; only the hardware is simulated.
The same interface could later point at a real TEE attestation or a Polytune computation.
"""
from __future__ import annotations

import json
import random

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def canonical(payload: dict) -> bytes:
    """Deterministic byte encoding of a payload, so signer and verifier agree."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_signature(public_key_hex: str, payload: dict, signature_hex: str | None) -> bool:
    """True only if signature_hex is a valid Ed25519 signature over payload."""
    if not signature_hex:
        return False
    try:
        pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        pk.verify(bytes.fromhex(signature_hex), canonical(payload))
        return True
    except (InvalidSignature, ValueError):
        return False


def corrupt(signature_hex: str) -> str:
    """Flip one byte so a once-valid signature fails verification."""
    raw = bytearray(bytes.fromhex(signature_hex))
    raw[-1] ^= 0xFF
    return bytes(raw).hex()


class Escrow:
    """One escrow per game. A fresh key per game means the public key stored in each
    transcript is all an auditor needs; nothing has to persist across a resumed run."""

    def __init__(self, private_key: Ed25519PrivateKey | None = None):
        self._sk = private_key or Ed25519PrivateKey.generate()
        self.public_key_hex = self._sk.public_key().public_bytes_raw().hex()

    def _sign(self, payload: dict) -> str:
        return self._sk.sign(canonical(payload)).hex()

    def issue_commitment(self, game_id: str, share_percent: int, broken: bool = False):
        """Sign a return rule. If broken, the signature fails verification."""
        payload = {
            "kind": "commitment",
            "game_id": game_id,
            "trustee_id": "trustee",
            "share_percent": int(share_percent),
        }
        sig = self._sign(payload)
        return payload, (corrupt(sig) if broken else sig)

    def issue_credential(
        self,
        game_id: str,
        claimed_type: str,
        true_type: str,
        rng: random.Random,
        broken: bool = False,
    ):
        """Sign a credential only if it matches the principal's true type.

        A mismatching claim gets a random 64-byte string instead of a signature, so the
        sender's verification fails for a lie. If broken, even a true claim fails.
        """
        payload = {
            "kind": "credential",
            "game_id": game_id,
            "trustee_id": "trustee",
            "principal_type": claimed_type,
        }
        if claimed_type != true_type:
            return payload, bytes(rng.getrandbits(8) for _ in range(64)).hex()
        sig = self._sign(payload)
        return payload, (corrupt(sig) if broken else sig)
