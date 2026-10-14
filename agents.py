"""agents.py - model adapters. An agent exposes one coroutine, `act`, that runs a short
tool-calling exchange until a terminal tool is called, and returns the full call log.

AnthropicAgent talks to the Anthropic Messages API. MockAgent is a scripted stand-in used
for tests and dry runs; its output must never be reported as model results.
"""
from __future__ import annotations

import json
import os
import random
from typing import Callable

MAX_TURNS = 6          # model turns per act() including retries
MAX_MALFORMED = 2      # malformed outputs tolerated before the game is aborted


class BudgetExceeded(Exception):
    pass


class Budget:
    """Shared spend counter. Raises before a call is made once the cap is reached."""

    def __init__(self, cap_usd: float):
        self.cap = cap_usd
        self.spent = 0.0

    def check(self):
        if self.spent >= self.cap:
            raise BudgetExceeded(f"spend cap reached: ${self.spent:.2f} of ${self.cap:.2f}")

    def add(self, in_tokens: int, out_tokens: int, price_in: float, price_out: float):
        self.spent += in_tokens * price_in / 1e6 + out_tokens * price_out / 1e6


def _block_to_dict(b) -> dict:
    return b.model_dump(exclude_none=True) if hasattr(b, "model_dump") else dict(b)


class AnthropicAgent:
    def __init__(self, model_id: str, temperature: float, max_tokens: int, budget: Budget,
                 price_in: float, price_out: float, api_key: str | None = None):
        import anthropic  # imported lazily so mock runs need no key
        self._anthropic = anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"], max_retries=5)
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.budget = budget
        self.price_in, self.price_out = price_in, price_out
        self.send_temperature = True

    async def _call(self, system, messages, tools, tool_choice):
        self.budget.check()
        kwargs = dict(model=self.model_id, max_tokens=self.max_tokens, system=system,
                      messages=messages, tools=tools, tool_choice=tool_choice)
        if self.send_temperature:
            kwargs["temperature"] = self.temperature
        try:
            resp = await self.client.messages.create(**kwargs)
        except self._anthropic.BadRequestError as e:
            if self.send_temperature and "temperature" in str(e).lower():
                self.send_temperature = False   # this model rejects the parameter; recorded in manifest
                kwargs.pop("temperature", None)
                resp = await self.client.messages.create(**kwargs)
            else:
                raise
        self.budget.add(resp.usage.input_tokens, resp.usage.output_tokens, self.price_in, self.price_out)
        return resp

    async def act(self, system: str, user: str, tools: list[dict], terminal: str,
                  execute: Callable | None, validate: Callable | None, ctx: dict) -> dict:
        messages = [{"role": "user", "content": user}]
        calls, malformed = [], 0
        usage = {"input_tokens": 0, "output_tokens": 0}
        for turn in range(MAX_TURNS):
            if turn == MAX_TURNS - 1 or malformed > 0:
                tool_choice = {"type": "tool", "name": terminal}
            else:
                tool_choice = {"type": "any", "disable_parallel_tool_use": True}
            resp = await self._call(system, messages, tools, tool_choice)
            usage["input_tokens"] += resp.usage.input_tokens
            usage["output_tokens"] += resp.usage.output_tokens
            content = [_block_to_dict(b) for b in resp.content]
            calls.append({"model": self.model_id, "messages": json.loads(json.dumps(messages)),
                          "system": system, "response": content, "stop_reason": resp.stop_reason,
                          "usage": {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}})
            uses = [b for b in content if b.get("type") == "tool_use"]
            if not uses:
                malformed += 1
                if malformed > MAX_MALFORMED:
                    return {"input": None, "calls": calls, "malformed": malformed, "usage": usage, "aborted": True}
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": "Please respond by calling one of the tools."})
                continue
            use = uses[0]
            name, inp = use["name"], use["input"]
            err = validate(name, inp) if (validate and name == terminal) else None
            if err:
                malformed += 1
                if malformed > MAX_MALFORMED:
                    return {"input": None, "calls": calls, "malformed": malformed, "usage": usage, "aborted": True}
                result, is_error = err, True
            elif name == terminal:
                return {"input": inp, "calls": calls, "malformed": malformed, "usage": usage, "aborted": False}
            else:
                result, is_error = execute(name, inp), False
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": use["id"],
                                                          "content": result, "is_error": is_error}]})
        return {"input": None, "calls": calls, "malformed": malformed, "usage": usage, "aborted": True}


class MockAgent:
    """Scripted stand-in. Behaves roughly like a cautious buyer and a type-driven supplier.
    Used only to test the pipeline end to end without spending anything."""

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.model_id = "mock"

    async def act(self, system, user, tools, terminal, execute, validate, ctx):
        from escrow import verify_signature  # noqa: F401  (kept for clarity of what the mock sees)
        role, phase = ctx.get("role"), ctx.get("phase")
        calls = []

        def call(name, inp, text=""):
            calls.append({"model": "mock", "system": system, "messages": [{"role": "user", "content": user}],
                          "response": [{"type": "tool_use", "id": f"mock{len(calls)}", "name": name, "input": inp}],
                          "stop_reason": "tool_use", "usage": {"input_tokens": 0, "output_tokens": 0}})
            return inp

        if phase == "check":
            # the mock gets the questions right 90% of the time
            right = self.rng.random() < 0.9
            inp = call("answer_checks", {"q1": 12 if right else 9, "q2": 11})
        elif role == "trustee" and phase == "pre":
            ptype = ctx["principal_type"]
            fair = ptype == "fair"
            if terminal == "send_message":
                inp = call(terminal, {"text": "I will treat you fairly." if fair else "Trust me.", "rationale": "mock"})
            elif terminal in ("state_rule", "commit_return_rule"):
                inp = call(terminal, {"share_percent": 40 if fair else 20, "rationale": "mock"})
            else:  # present_credential
                claim = "fair" if (fair or self.rng.random() < 0.5) else "self_interested"
                inp = call(terminal, {"claimed_type": claim, "rationale": "mock"})
        elif role == "sender":
            art = ctx["artifact"]
            valid = None
            if ctx.get("verify_tool"):
                vt = "verify_commitment" if ctx["verify_tool"] == "commitment" else "verify_credential"
                res = json.loads(execute(vt, {}))
                calls.append({"model": "mock", "system": system, "messages": [{"role": "user", "content": user}],
                              "response": [{"type": "tool_use", "id": "mockv", "name": vt, "input": {}}],
                              "stop_reason": "tool_use", "usage": {"input_tokens": 0, "output_tokens": 0}})
                valid = res["signature_valid"]
            base = 3 if valid is None else (9 if valid else 2)
            if art["kind"] == "message" and "fairly" in art["text"]:
                base = 5
            inp = call("submit_transfer", {"amount": max(0, min(10, base + self.rng.choice([-1, 0, 1]))), "rationale": "mock"})
        else:  # trustee return
            sent = ctx["sent"]
            frac = 0.4 if ctx["principal_type"] == "fair" else 0.1
            inp = call("submit_return", {"amount": int(round(3 * sent * frac)), "rationale": "mock"})
        return {"input": inp, "calls": calls, "malformed": 0, "usage": {"input_tokens": 0, "output_tokens": 0}, "aborted": False}
