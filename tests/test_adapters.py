"""Adapter tests with fake API clients. They check the tool loop, the OpenAI message translation,
parameter dropping and the spend cap. They cannot prove the real APIs accept the requests; the
smoke test (run.py --smoke) does that against each live API."""
import asyncio
import json
from types import SimpleNamespace as NS

import pytest

from agents import Budget, BudgetExceeded, OpenAIAgent, ToolLoopAgent
from engine import TOOLS, validate_input


def resp(tool_calls=None, content=None, pin=100, pout=10, finish="tool_calls"):
    tcs = [NS(id=f"call{i}", function=NS(name=n, arguments=a if isinstance(a, str) else json.dumps(a)))
           for i, (n, a) in enumerate(tool_calls or [])]
    return NS(choices=[NS(message=NS(content=content, tool_calls=tcs or None), finish_reason=finish)],
              usage=NS(prompt_tokens=pin, completion_tokens=pout))


class FakeClient:
    class BadRequestError(Exception):
        pass

    def __init__(self, script):
        self.script, self.seen = list(script), []
        self.chat = NS(completions=NS(create=self._create))

    async def _create(self, **kw):
        self.seen.append(kw)
        r = self.script.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def run(coro):
    return asyncio.run(coro)


def agent(client, cap=5.0):
    return OpenAIAgent("gpt-test", 1.0, 500, Budget(cap, 0.1, 0.5), client=client)


def sender_tools():
    return [TOOLS["verify_commitment"], TOOLS["submit_transfer"]]


def test_openai_tool_loop_translates_messages_and_returns_terminal_input():
    c = FakeClient([resp([("verify_commitment", {})]),
                    resp([("submit_transfer", {"amount": 7, "rationale": "ok"})])])
    ex = lambda name, inp: json.dumps({"signature_valid": True})
    r = run(agent(c).act("SYS", "USER", sender_tools(), "submit_transfer", ex,
                         lambda n, i: validate_input(n, i), {}))
    assert r["input"]["amount"] == 7 and not r["aborted"] and r["malformed"] == 0
    first, second = c.seen
    assert first["tool_choice"] == "required" and first["parallel_tool_calls"] is False
    assert first["messages"][0] == {"role": "system", "content": "SYS"}
    assert first["tools"][0]["type"] == "function" and first["tools"][1]["function"]["name"] == "submit_transfer"
    # second request carries the assistant tool call and its result in OpenAI shape
    assert second["messages"][2]["role"] == "assistant" and second["messages"][2]["tool_calls"][0]["function"]["name"] == "verify_commitment"
    assert second["messages"][3] == {"role": "tool", "tool_call_id": "call0", "content": json.dumps({"signature_valid": True})}
    # the transcript uses neutral tool_use blocks, so audit.py reads both vendors alike
    assert r["calls"][1]["response"][0] == {"type": "tool_use", "id": "call0", "name": "submit_transfer",
                                            "input": {"amount": 7, "rationale": "ok"}}
    assert r["usage"] == {"input_tokens": 200, "output_tokens": 20}


def test_invalid_terminal_input_is_retried_with_forced_tool_then_counted():
    c = FakeClient([resp([("submit_transfer", {"amount": 99})]), resp([("submit_transfer", {"amount": 5})])])
    r = run(agent(c).act("S", "U", sender_tools(), "submit_transfer", None, lambda n, i: validate_input(n, i), {}))
    assert r["input"]["amount"] == 5 and r["malformed"] == 1
    assert c.seen[1]["tool_choice"] == {"type": "function", "function": {"name": "submit_transfer"}}
    assert c.seen[1]["messages"][-1]["role"] == "tool" and "0 to 10" in c.seen[1]["messages"][-1]["content"]


def test_no_tool_call_three_times_aborts_the_game():
    c = FakeClient([resp(content="thinking out loud", finish="stop") for _ in range(6)])
    r = run(agent(c).act("S", "U", sender_tools(), "submit_transfer", None, lambda n, i: validate_input(n, i), {}))
    assert r["aborted"] and r["input"] is None and r["malformed"] == 3


def test_unparseable_arguments_count_as_malformed_not_crash():
    c = FakeClient([resp([("submit_transfer", "{not json")]), resp([("submit_transfer", {"amount": 3})])])
    r = run(agent(c).act("S", "U", sender_tools(), "submit_transfer", None, lambda n, i: validate_input(n, i), {}))
    assert r["input"]["amount"] == 3 and r["malformed"] == 1


def test_rejected_parameter_is_dropped_and_remembered():
    c = FakeClient([FakeClient.BadRequestError("Unsupported value: 'temperature' does not support 1.0"),
                    resp([("submit_transfer", {"amount": 4})])])
    a = agent(c)
    r = run(a.act("S", "U", sender_tools(), "submit_transfer", None, lambda n, i: validate_input(n, i), {}))
    assert r["input"]["amount"] == 4 and "temperature" in a.drop
    assert "temperature" not in c.seen[1]


def test_unrelated_bad_request_is_raised():
    c = FakeClient([FakeClient.BadRequestError("model not found")])
    with pytest.raises(FakeClient.BadRequestError):
        run(agent(c).act("S", "U", sender_tools(), "submit_transfer", None, None, {}))


def test_budget_stops_before_the_next_call():
    b = Budget(0.0001, price_in=1_000_000, price_out=1_000_000)

    class Spendy(ToolLoopAgent):
        model_id = "x"
        budget = b

        async def _complete(self, system, messages, tools, force):
            return {"content": [{"type": "tool_use", "id": "t", "name": "verify_commitment", "input": {}}],
                    "stop_reason": "tool_use", "input_tokens": 10, "output_tokens": 10}

    with pytest.raises(BudgetExceeded):
        run(Spendy().act("S", "U", sender_tools(), "submit_transfer", lambda n, i: "{}", None, {}))
    assert b.spent > b.cap
