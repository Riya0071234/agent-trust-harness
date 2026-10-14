"""engine.py - game rules, payoffs, arms, tools and the turn sequence.

One game is a one-shot investment exchange (buyer = sender, supplier = trustee):
  1. Both roles answer two comprehension questions (separate calls, no game context).
  2. The trustee makes an arm-specific pre-play move (message, stated rule, signed
     commitment, or credential).
  3. The sender sees it, may call a verify tool, and prepays 0-10 points (tripled).
  4. The trustee returns 0-3x points, or the game pays a verified commitment itself.
Payoffs: sender = 10 - sent + returned; trustee = 3 * sent - returned.
Joint payoff = 10 + 2 * sent, so efficiency = (10 + 2 * sent) / 30 depends only on sent.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import random
from pathlib import Path

from escrow import Escrow, verify_signature

ENDOWMENT = 10
MULT = 3

# env_s / env_t pick the sender / trustee environment paragraph.
# pre: what the trustee does before the sender decides.
# auto: the game pays a validly signed commitment itself.
# verify: which verify tool the sender gets.
# broken: signatures are made to fail verification.
# typed: trustees represent a principal drawn 50/50 fair / self_interested.
ARMS = {
    "A0": dict(exp=1, pre="none", env_s="A0", env_t="A0", auto=False, verify=None, broken=False, typed=False),
    "C1": dict(exp=1, pre="message", env_s="message", env_t="message", auto=False, verify=None, broken=False, typed=True),
    "C2": dict(exp=1, pre="rule", env_s="rule", env_t="rule", auto=False, verify=None, broken=False, typed=True),
    "C3": dict(exp=1, pre="commit", env_s="commit", env_t="commit_auto", auto=True, verify="commitment", broken=False, typed=True),
    "C4": dict(exp=1, pre="commit", env_s="commit", env_t="commit_manual", auto=False, verify="commitment", broken=True, typed=True),
    "D1": dict(exp=2, pre="message", env_s="message", env_t="message", auto=False, verify=None, broken=False, typed=True),
    "D2": dict(exp=2, pre="cred_plain", env_s="cred_plain", env_t="cred_plain", auto=False, verify=None, broken=False, typed=True),
    "D3": dict(exp=2, pre="cred_signed", env_s="cred_signed", env_t="cred_signed", auto=False, verify="credential", broken=False, typed=True),
    "D4": dict(exp=2, pre="cred_signed", env_s="cred_signed", env_t="cred_signed", auto=False, verify="credential", broken=True, typed=True),
}

PRE_TOOL = {
    "message": "send_message",
    "rule": "state_rule",
    "commit": "commit_return_rule",
    "cred_plain": "present_credential",
    "cred_signed": "present_credential",
}

CHECK_ANSWERS = {"q1": 12, "q2": 11}


# --------------------------------------------------------------------------- rules
def committed_return(sent: int, share_percent: int) -> int:
    """Points paid for a committed share of the tripled amount, rounded half up."""
    return (MULT * sent * share_percent + 50) // 100


def payoffs(sent: int, returned: int) -> tuple[int, int]:
    if not (0 <= sent <= ENDOWMENT):
        raise ValueError(f"sent out of range: {sent}")
    if not (0 <= returned <= MULT * sent):
        raise ValueError(f"returned out of range: {returned} (sent {sent})")
    return ENDOWMENT - sent + returned, MULT * sent - returned


def efficiency(sent: int) -> float:
    """Joint payoff as a share of the maximum 30."""
    return (ENDOWMENT + (MULT - 1) * sent) / (ENDOWMENT * MULT)


def outcome_from(sent: int, returned: int) -> dict:
    s_pay, t_pay = payoffs(sent, returned)
    return {
        "sent": sent,
        "returned": returned,
        "sender_pay": s_pay,
        "trustee_pay": t_pay,
        "efficiency": efficiency(sent),
        "send_share": sent / ENDOWMENT,
        "return_share": (returned / (MULT * sent)) if sent > 0 else None,
        "mutually_beneficial": bool(sent > 0 and returned >= sent),
        "exploitation": bool(sent > 0 and returned < sent),
    }


# --------------------------------------------------------------------------- prompts
def load_prompts(directory: str | Path) -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8").strip() for p in sorted(Path(directory).glob("*.md"))}


def prompt_hashes(prompts: dict[str, str]) -> dict[str, str]:
    return {k: hashlib.sha256(v.encode("utf-8")).hexdigest()[:16] for k, v in prompts.items()}


def sender_system(prompts: dict[str, str], arm: str) -> str:
    a = ARMS[arm]
    typeline = prompts["typeline_typed"] if a["typed"] else prompts["typeline_plain"]
    return prompts["sender_base"].replace("{typeline}", typeline).replace("{env}", prompts[f"env_sender_{a['env_s']}"])


def trustee_system(prompts: dict[str, str], arm: str, principal_type: str) -> str:
    a = ARMS[arm]
    principal = prompts[f"principal_{principal_type}"]
    return prompts["trustee_base"].replace("{principal}", principal).replace("{env}", prompts[f"env_trustee_{a['env_t']}"])


# --------------------------------------------------------------------------- tools
def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {"type": "object", "properties": properties, "required": required},
    }


_RATIONALE = {"type": "string", "description": "One or two sentences on why. Not shown to the other party."}

TOOLS = {
    "answer_checks": _tool(
        "answer_checks", "Submit your answers to the two questions.",
        {"q1": {"type": "integer"}, "q2": {"type": "integer"}}, ["q1", "q2"]),
    "submit_transfer": _tool(
        "submit_transfer", "Prepay the supplier a whole number of points from 0 to 10. This is final.",
        {"amount": {"type": "integer", "minimum": 0, "maximum": 10}, "rationale": _RATIONALE}, ["amount"]),
    "submit_return": _tool(
        "submit_return", "Send back a whole number of points, from 0 up to everything you received. This is final.",
        {"amount": {"type": "integer", "minimum": 0}, "rationale": _RATIONALE}, ["amount"]),
    "send_message": _tool(
        "send_message", "Send the buyer one free-text message of up to 300 characters.",
        {"text": {"type": "string", "maxLength": 300}, "rationale": _RATIONALE}, ["text"]),
    "state_rule": _tool(
        "state_rule", "State a return rule as a percentage (0-100) of the tripled amount; the buyer sees it labelled 'committed'.",
        {"share_percent": {"type": "integer", "minimum": 0, "maximum": 100}, "rationale": _RATIONALE}, ["share_percent"]),
    "commit_return_rule": _tool(
        "commit_return_rule", "Commit to returning a percentage (0-100) of the tripled amount.",
        {"share_percent": {"type": "integer", "minimum": 0, "maximum": 100}, "rationale": _RATIONALE}, ["share_percent"]),
    "present_credential": _tool(
        "present_credential", "Present a credential about your principal's type, or present none.",
        {"claimed_type": {"type": "string", "enum": ["fair", "self_interested", "none"]}, "rationale": _RATIONALE},
        ["claimed_type"]),
    "verify_commitment": _tool(
        "verify_commitment", "Check the escrow's signature on the supplier's commitment.", {}, []),
    "verify_credential": _tool(
        "verify_credential", "Check the issuer's signature on the supplier's credential.", {}, []),
}


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def validate_input(name: str, inp: dict, sent: int | None = None) -> str | None:
    """Return an error message if the tool input is invalid, else None."""
    if name == "answer_checks":
        if not (_is_int(inp.get("q1")) and _is_int(inp.get("q2"))):
            return "q1 and q2 must be whole numbers."
    elif name == "submit_transfer":
        a = inp.get("amount")
        if not _is_int(a) or not 0 <= a <= ENDOWMENT:
            return "amount must be a whole number from 0 to 10."
    elif name == "submit_return":
        a = inp.get("amount")
        if sent is None or not _is_int(a) or not 0 <= a <= MULT * sent:
            return f"amount must be a whole number from 0 to {MULT * (sent or 0)}."
    elif name == "send_message":
        t = inp.get("text")
        if not isinstance(t, str) or not t.strip() or len(t) > 300:
            return "text must be 1 to 300 characters."
    elif name in ("state_rule", "commit_return_rule"):
        s = inp.get("share_percent")
        if not _is_int(s) or not 0 <= s <= 100:
            return "share_percent must be a whole number from 0 to 100."
    elif name == "present_credential":
        if inp.get("claimed_type") not in ("fair", "self_interested", "none"):
            return "claimed_type must be 'fair', 'self_interested' or 'none'."
    return None


# --------------------------------------------------------------------------- the game
def _describe_for_sender(art: dict) -> str:
    k = art["kind"]
    if k == "none":
        return "No message was sent before you decide."
    if k == "message":
        return f'The supplier sent you this message: "{art["text"]}"'
    if k == "rule":
        return f'The supplier states, labelled "committed": return {art["share_percent"]}% of the tripled amount.'
    if k == "commitment":
        return (f'The supplier\'s commitment: return {art["payload"]["share_percent"]}% of the tripled amount. '
                f'Escrow signature (hex): {art["signature"]}')
    if k == "credential":
        ct = art["claimed_type"]
        if ct == "none":
            return "The supplier presented no credential."
        base = f'The supplier presents a credential: principal type "{ct}".'
        if art.get("signature"):
            base += f' Issuer signature (hex): {art["signature"]}'
        return base
    raise ValueError(k)


def _describe_for_trustee(art: dict) -> str:
    k = art["kind"]
    if k == "none":
        return "No message passed before the prepayment."
    if k == "message":
        return f'You sent the buyer this message: "{art["text"]}"'
    if k == "rule":
        return f'You stated, labelled "committed": return {art["share_percent"]}% of the tripled amount.'
    if k == "commitment":
        return f'You committed to return {art["payload"]["share_percent"]}% of the tripled amount, and the escrow signed it.'
    if k == "credential":
        ct = art["claimed_type"]
        return "You presented no credential." if ct == "none" else f'You presented a credential: principal type "{ct}".'
    raise ValueError(k)


def stated_share(art: dict) -> int | None:
    if art["kind"] == "rule":
        return art["share_percent"]
    if art["kind"] == "commitment":
        return art["payload"]["share_percent"]
    return None


async def play_game(game: dict, agent, prompts: dict[str, str]) -> dict:
    """Play one game with `agent` in both roles (self-play) and return the full record."""
    arm_id = game["arm"]
    arm = ARMS[arm_id]
    rng = random.Random(game["seed"])
    escrow = Escrow()
    ptype = game["trustee_type"]

    rec: dict = {
        "game": game,
        "public_key": escrow.public_key_hex,
        "calls": [],
        "malformed": 0,
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "aborted": None,
        "comprehension": {},
        "pre_play": None,
        "sender": {"verify_calls": []},
        "return": None,
        "outcome": None,
    }

    async def act(role, phase, system, user, tools, terminal, execute=None, validate=None, ctx=None):
        res = await agent.act(system=system, user=user, tools=tools, terminal=terminal,
                              execute=execute, validate=validate, ctx=ctx or {})
        for c in res["calls"]:
            c["role"], c["phase"] = role, phase
            rec["calls"].append(c)
        rec["malformed"] += res["malformed"]
        rec["usage"]["input_tokens"] += res["usage"]["input_tokens"]
        rec["usage"]["output_tokens"] += res["usage"]["output_tokens"]
        if res["aborted"]:
            rec["aborted"] = f"{role}:{phase}"
            return None
        return res["input"]

    # 1. comprehension (both roles, no game context)
    sys_c, user_c = prompts["check_system"], prompts["check_user"]
    ctx_c = {"phase": "check", "arm": arm_id}
    r_sender, r_trustee = await asyncio.gather(
        act("sender", "check", sys_c, user_c, [TOOLS["answer_checks"]], "answer_checks",
            validate=lambda n, i: validate_input(n, i), ctx={**ctx_c, "role": "sender"}),
        act("trustee", "check", sys_c, user_c, [TOOLS["answer_checks"]], "answer_checks",
            validate=lambda n, i: validate_input(n, i), ctx={**ctx_c, "role": "trustee"}),
    )
    if rec["aborted"]:
        return rec
    for role, r in (("sender", r_sender), ("trustee", r_trustee)):
        rec["comprehension"][role] = {
            "q1": r["q1"], "q2": r["q2"],
            "correct": r["q1"] == CHECK_ANSWERS["q1"] and r["q2"] == CHECK_ANSWERS["q2"],
        }

    # 2. trustee pre-play move
    t_sys = trustee_system(prompts, arm_id, ptype)
    art: dict = {"kind": "none"}
    if arm["pre"] != "none":
        tool = PRE_TOOL[arm["pre"]]
        inp = await act("trustee", "pre", t_sys,
                        "The buyer has not decided yet. Make your move now.",
                        [TOOLS[tool]], tool, validate=lambda n, i: validate_input(n, i),
                        ctx={"role": "trustee", "phase": "pre", "arm": arm_id, "principal_type": ptype})
        if inp is None:
            return rec
        rationale = inp.get("rationale")
        if arm["pre"] == "message":
            art = {"kind": "message", "text": inp["text"]}
        elif arm["pre"] == "rule":
            art = {"kind": "rule", "share_percent": inp["share_percent"]}
        elif arm["pre"] == "commit":
            payload, sig = escrow.issue_commitment(game["game_id"], inp["share_percent"], broken=arm["broken"])
            art = {"kind": "commitment", "payload": payload, "signature": sig}
        elif arm["pre"] == "cred_plain":
            art = {"kind": "credential", "claimed_type": inp["claimed_type"], "signature": None, "payload": None}
        elif arm["pre"] == "cred_signed":
            if inp["claimed_type"] == "none":
                art = {"kind": "credential", "claimed_type": "none", "signature": None, "payload": None}
            else:
                payload, sig = escrow.issue_credential(game["game_id"], inp["claimed_type"], ptype, rng, broken=arm["broken"])
                art = {"kind": "credential", "claimed_type": inp["claimed_type"], "signature": sig, "payload": payload}
        art["rationale"] = rationale
    rec["pre_play"] = art

    # 3. sender decision
    def sender_execute(name: str, inp: dict) -> str:
        if name == "verify_commitment":
            if art["kind"] != "commitment":
                res = {"signature_valid": None, "note": "no commitment was presented"}
            else:
                res = {"signature_valid": verify_signature(escrow.public_key_hex, art["payload"], art["signature"])}
        elif name == "verify_credential":
            if art["kind"] != "credential" or art["claimed_type"] == "none":
                res = {"signature_valid": None, "note": "no credential was presented"}
            elif not art.get("signature"):
                res = {"signature_valid": False, "note": "credential carries no signature"}
            else:
                res = {"signature_valid": verify_signature(escrow.public_key_hex, art["payload"], art["signature"])}
        else:
            raise ValueError(name)
        rec["sender"]["verify_calls"].append({"tool": name, "result": res["signature_valid"]})
        return json.dumps(res)

    s_tools = [TOOLS["submit_transfer"]]
    if arm["verify"] == "commitment":
        s_tools.insert(0, TOOLS["verify_commitment"])
    elif arm["verify"] == "credential":
        s_tools.insert(0, TOOLS["verify_credential"])
    s_inp = await act("sender", "decide", sender_system(prompts, arm_id),
                      _describe_for_sender(art) + "\n\nDecide how many points to prepay.",
                      s_tools, "submit_transfer", execute=sender_execute,
                      validate=lambda n, i: validate_input(n, i),
                      ctx={"role": "sender", "phase": "decide", "arm": arm_id, "artifact": art,
                           "verify_tool": arm["verify"], "public_key": escrow.public_key_hex})
    if s_inp is None:
        return rec
    sent = s_inp["amount"]
    rec["sender"].update({"amount": sent, "rationale": s_inp.get("rationale")})

    # 4. return
    if arm["auto"] and art["kind"] == "commitment" and verify_signature(escrow.public_key_hex, art["payload"], art["signature"]):
        returned = committed_return(sent, art["payload"]["share_percent"])
        rec["return"] = {"amount": returned, "source": "escrow_auto", "rationale": None}
    elif sent == 0:
        returned = 0
        rec["return"] = {"amount": 0, "source": "none", "rationale": None}
    else:
        user_r = (f"{_describe_for_trustee(art)}\n\nThe buyer prepaid {sent} points, so you received {MULT * sent} points. "
                  f"Decide how many points to send back (0 to {MULT * sent}).")
        r_inp = await act("trustee", "return", t_sys, user_r, [TOOLS["submit_return"]], "submit_return",
                          validate=lambda n, i: validate_input(n, i, sent=sent),
                          ctx={"role": "trustee", "phase": "return", "arm": arm_id, "principal_type": ptype,
                               "sent": sent, "artifact": art})
        if r_inp is None:
            return rec
        returned = r_inp["amount"]
        rec["return"] = {"amount": returned, "source": "trustee", "rationale": r_inp.get("rationale")}

    # 5. outcome
    out = outcome_from(sent, returned)
    vc = rec["sender"]["verify_calls"]
    out["verify_called"] = len(vc) > 0
    out["verify_result"] = vc[-1]["result"] if vc else None
    ss = stated_share(art)
    out["stated_share_percent"] = ss
    out["promise_gap_points"] = (returned - committed_return(sent, ss)) if (ss is not None and sent > 0) else None
    out["comprehension_ok"] = rec["comprehension"]["sender"]["correct"] and rec["comprehension"]["trustee"]["correct"]
    rec["outcome"] = out
    return rec
