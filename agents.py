"""agents.py - model adapters. An agent exposes one coroutine, `act`, that runs a short
tool-calling exchange until a terminal tool is called, and returns the full call log.

AnthropicAgent and OpenAIAgent share one tool loop (ToolLoopAgent) and differ only in how
they talk to their API. Conversations are kept in one neutral format (Anthropic-style
content blocks) so transcripts from both vendors have the same shape and audit.py reads
both. MockAgent is a scripted stand-in for tests and dry runs; its output must never be
reported as model results.
"""
from __future__ import annotations

import json
import os
import random
from typing import Callable

MAX_TURNS = 6          # model turns per act() including retries
MAX_MALFORMED = 2      # malformed outputs tolerated per call before the game is aborted


class BudgetExceeded(Exception):
    pass


class Budget:
    """Spend counter for one model. Raises before a call is made once the cap is reached."""

    def __init__(self, cap_usd: float, price_in: float, price_out: float):
        self.cap, self.price_in, self.price_out = cap_usd, price_in, price_out
        self.spent = 0.0

    def check(self):
        if self.spent >= self.cap:
            raise BudgetExceeded(f"spend cap reached: ${self.spent:.2f} of ${self.cap:.2f}")

    def add(self, in_tokens: int, out_tokens: int):
        self.spent += in_tokens * self.price_in / 1e6 + out_tokens * self.price_out / 1e6


class ToolLoopAgent:
    """Runs the tool loop. Subclasses implement `_complete`."""

    model_id: str
    budget: Budget

    async def _complete(self, system: str, messages: list, tools: list, force: str | None) -> dict:
        """Return {"content": [blocks], "stop_reason": str, "input_tokens": int, "output_tokens": int}.
        `force` is the name of a tool that must be called, or None for 'any tool'."""
        raise NotImplementedError

    async def act(self, system: str, user: str, tools: list[dict], terminal: str,
                  execute: Callable | None, validate: Callable | None, ctx: dict) -> dict:
        messages = [{"role": "user", "content": user}]
        calls, malformed = [], 0
        usage = {"input_tokens": 0, "output_tokens": 0}

        def done(inp, aborted):
            return {"input": inp, "calls": calls, "malformed": malformed, "usage": usage, "aborted": aborted}

        for turn in range(MAX_TURNS):
            self.budget.check()
            force = terminal if (turn == MAX_TURNS - 1 or malformed > 0) else None
            r = await self._complete(system, messages, tools, force)
            self.budget.add(r["input_tokens"], r["output_tokens"])
            usage["input_tokens"] += r["input_tokens"]
            usage["output_tokens"] += r["output_tokens"]
            content = r["content"]
            calls.append({"model": self.model_id, "messages": json.loads(json.dumps(messages)), "system": system,
                          "response": content, "stop_reason": r["stop_reason"],
                          "usage": {"input_tokens": r["input_tokens"], "output_tokens": r["output_tokens"]}})
            uses = [b for b in content if b.get("type") == "tool_use"]
            if not uses:
                malformed += 1
                if malformed > MAX_MALFORMED:
                    return done(None, True)
                messages.append({"role": "assistant", "content": content or [{"type": "text", "text": "(no output)"}]})
                messages.append({"role": "user", "content": "Please respond by calling one of the tools."})
                continue
            use = uses[0]
            name, inp = use["name"], use["input"]
            err = validate(name, inp) if (validate and name == terminal) else None
            if err:
                malformed += 1
                if malformed > MAX_MALFORMED:
                    return done(None, True)
                result, is_error = err, True
            elif name == terminal:
                return done(inp, False)
            else:
                result, is_error = execute(name, inp), False
            messages.append({"role": "assistant", "content": [use]})
            messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": use["id"],
                                                          "content": result, "is_error": is_error}]})
        return done(None, True)


class AnthropicAgent(ToolLoopAgent):
    def __init__(self, model_id: str, temperature: float, max_tokens: int, budget: Budget,
                 api_key: str | None = None):
        import anthropic  # imported lazily so mock runs need no SDK or key
        self._anthropic = anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"], max_retries=5)
        self.model_id, self.temperature, self.max_tokens, self.budget = model_id, temperature, max_tokens, budget
        self.send_temperature = True
        self.auto_choice = False   # set if the model rejects forced tool use; then a missing tool call is retried by the loop

    async def _complete(self, system, messages, tools, force):
        if self.auto_choice:
            tool_choice = {"type": "auto", "disable_parallel_tool_use": True}
        else:
            tool_choice = ({"type": "tool", "name": force} if force
                           else {"type": "any", "disable_parallel_tool_use": True})
        kwargs = dict(model=self.model_id, max_tokens=self.max_tokens, system=system,
                      messages=messages, tools=tools, tool_choice=tool_choice)
        if self.send_temperature:
            # newer SDKs no longer list temperature as a named argument; extra_body reaches the API either way
            kwargs["extra_body"] = {"temperature": self.temperature}
        try:
            resp = await self.client.messages.create(**kwargs)
        except self._anthropic.BadRequestError as e:
            if self.send_temperature and "temperature" in str(e).lower():
                self.send_temperature = False   # this model rejects the parameter; recorded in the manifest
                kwargs.pop("extra_body")
                resp = await self.client.messages.create(**kwargs)
            elif kwargs["tool_choice"]["type"] != "auto" and "tool_choice" in str(e).lower():   # concurrent calls may race here
                self.auto_choice = True         # this model rejects forced tool use (claude-sonnet-5-5); use 'auto'
                kwargs["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": True}
                resp = await self.client.messages.create(**kwargs)
            else:
                raise
        return {"content": [b.model_dump(exclude_none=True) for b in resp.content],
                "stop_reason": resp.stop_reason,
                "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}


class OpenAIAgent(ToolLoopAgent):
    """OpenAI Chat Completions with function tools. Tool definitions and messages are translated
    from the neutral format; the response is translated back into tool_use blocks."""

    def __init__(self, model_id: str, temperature: float, max_tokens: int, budget: Budget,
                 reasoning_effort: str | None = None, api_key: str | None = None, client=None):
        if client is None:
            import openai  # imported lazily
            client = openai.AsyncOpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"], max_retries=5)
            self._bad_request = openai.BadRequestError
        else:  # tests inject a fake client
            self._bad_request = type(client).BadRequestError if hasattr(type(client), "BadRequestError") else Exception
        self.client = client
        self.model_id, self.temperature, self.max_tokens, self.budget = model_id, temperature, max_tokens, budget
        self.reasoning_effort = reasoning_effort
        self.drop: set[str] = set()      # parameters this model rejected; recorded in the manifest

    @staticmethod
    def _tools(tools):
        return [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                  "parameters": t["input_schema"]}} for t in tools]

    @staticmethod
    def _messages(system, messages):
        out = [{"role": "system", "content": system}]
        for m in messages:
            c = m["content"]
            if m["role"] == "user":
                if isinstance(c, str):
                    out.append({"role": "user", "content": c})
                else:
                    for b in c:
                        out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": b["content"]})
            else:
                text = "".join(b.get("text", "") for b in c if b.get("type") == "text") or None
                calls = [{"id": b["id"], "type": "function",
                          "function": {"name": b["name"], "arguments": json.dumps(b["input"])}}
                         for b in c if b.get("type") == "tool_use"]
                msg = {"role": "assistant", "content": text}
                if calls:
                    msg["tool_calls"] = calls
                out.append(msg)
        return out

    async def _complete(self, system, messages, tools, force):
        kwargs = dict(model=self.model_id, messages=self._messages(system, messages), tools=self._tools(tools),
                      tool_choice=({"type": "function", "function": {"name": force}} if force else "required"),
                      parallel_tool_calls=False, max_completion_tokens=self.max_tokens,
                      temperature=self.temperature)
        # gpt-6.1-sol doesn't support reasoning_effort with function tools
        if self.reasoning_effort and "gpt-6.1" not in self.model_id:
            kwargs["reasoning_effort"] = self.reasoning_effort
        for p in self.drop:
            kwargs.pop(p, None)
        for _ in range(4):
            try:
                resp = await self.client.chat.completions.create(**kwargs)
                break
            except self._bad_request as e:
                bad = next((p for p in ("temperature", "parallel_tool_calls", "reasoning_effort")
                            if p in str(e) and p in kwargs), None)
                if bad is None:
                    raise
                self.drop.add(bad)
                kwargs.pop(bad)
        choice = resp.choices[0]
        blocks = []
        if choice.message.content:
            blocks.append({"type": "text", "text": choice.message.content})
        for tc in choice.message.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
                if not isinstance(args, dict):
                    args = {}
            except json.JSONDecodeError:
                args = {}
            blocks.append({"type": "tool_use", "id": tc.id, "name": tc.function.name, "input": args})
        return {"content": blocks, "stop_reason": choice.finish_reason,
                "input_tokens": resp.usage.prompt_tokens, "output_tokens": resp.usage.completion_tokens}


class MockAgent:
    """Scripted stand-in. Behaves roughly like a cautious buyer and a type-driven supplier.
    Used only to test the pipeline end to end without spending anything."""

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.model_id = "mock"
        self.budget = Budget(1e9, 0, 0)

    async def act(self, system, user, tools, terminal, execute, validate, ctx):
        role, phase = ctx.get("role"), ctx.get("phase")
        calls = []

        def call(name, inp):
            calls.append({"model": "mock", "system": system, "messages": [{"role": "user", "content": user}],
                          "response": [{"type": "tool_use", "id": f"mock{len(calls)}", "name": name, "input": inp}],
                          "stop_reason": "tool_use", "usage": {"input_tokens": 0, "output_tokens": 0}})
            return inp

        if phase == "check":
            right = self.rng.random() < 0.9      # gets the questions right 90% of the time
            inp = call("answer_checks", {"q1": 12 if right else 9, "q2": 11})
        elif role == "trustee" and phase == "pre":
            fair = ctx["principal_type"] == "fair"
            if terminal == "send_message":
                inp = call(terminal, {"text": "I will treat you fairly." if fair else "Trust me.", "rationale": "mock"})
            elif terminal in ("state_rule", "commit_return_rule"):
                inp = call(terminal, {"share_percent": 40 if fair else 20, "rationale": "mock"})
            else:  # present_credential
                claim = "fair" if (fair or self.rng.random() < 0.5) else "self_interested"
                inp = call(terminal, {"claimed_type": claim, "rationale": "mock"})
        elif role == "sender":
            art, valid = ctx["artifact"], None
            if ctx.get("verify_tool"):
                vt = "verify_commitment" if ctx["verify_tool"] == "commitment" else "verify_credential"
                valid = json.loads(execute(vt, {}))["signature_valid"]
                call(vt, {})
            base = 3 if valid is None else (9 if valid else 2)
            if art["kind"] == "message" and "fairly" in art["text"]:
                base = 5
            inp = call("submit_transfer", {"amount": max(0, min(10, base + self.rng.choice([-1, 0, 1]))), "rationale": "mock"})
        else:  # trustee return
            frac = 0.4 if ctx["principal_type"] == "fair" else 0.1
            inp = call("submit_return", {"amount": int(round(3 * ctx["sent"] * frac)), "rationale": "mock"})
        return {"input": inp, "calls": calls, "malformed": 0, "usage": {"input_tokens": 0, "output_tokens": 0}, "aborted": False}
