"""probe_sol.py - find which request shape gpt-6.1-sol accepts for function tools.
Makes a handful of tiny calls (a few cents at most). Prints PASS/FAIL per variant; never prints the key.
Usage (Windows): .venv\\Scripts\\python probe_sol.py   (asks for the OpenAI key, or reads OPENAI_API_KEY)"""
import asyncio, getpass, os, sys
import openai

MODEL = sys.argv[1] if len(sys.argv) > 1 else "gpt-6.1-sol"
TOOL = {"type": "function", "function": {"name": "submit_transfer", "description": "Send an amount.",
        "parameters": {"type": "object", "properties": {"amount": {"type": "integer"}}, "required": ["amount"]}}}
MSG = [{"role": "user", "content": "Call submit_transfer with amount 5."}]
RTOOL = {"type": "function", "name": "submit_transfer", "description": "Send an amount.",
         "parameters": TOOL["function"]["parameters"]}

async def main():
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI key (hidden): ").strip()
    c = openai.AsyncOpenAI(api_key=key, max_retries=2)
    chat = lambda **kw: c.chat.completions.create(model=MODEL, messages=MSG, tools=[TOOL], max_completion_tokens=200, **kw)
    variants = {
        "chat: reasoning_effort=none":            lambda: chat(reasoning_effort="none"),
        "chat: reasoning_effort omitted":         lambda: chat(),
        "chat: none + tool_choice required":      lambda: chat(reasoning_effort="none", tool_choice="required"),
        "chat: none + required + no parallel":    lambda: chat(reasoning_effort="none", tool_choice="required", parallel_tool_calls=False),
        "chat: none + required + temperature 1":  lambda: chat(reasoning_effort="none", tool_choice="required", temperature=1),
        "chat: reasoning_effort=minimal":         lambda: chat(reasoning_effort="minimal"),
        "chat: reasoning_effort=low":             lambda: chat(reasoning_effort="low"),
        "responses: reasoning none":              lambda: c.responses.create(model=MODEL, input=MSG[0]["content"], tools=[RTOOL],
                                                       reasoning={"effort": "none"}, max_output_tokens=200),
        "responses: default reasoning":           lambda: c.responses.create(model=MODEL, input=MSG[0]["content"], tools=[RTOOL],
                                                       max_output_tokens=200),
    }
    for name, fn in variants.items():
        try:
            r = await fn()
            print(f"PASS  {name}")
        except Exception as e:
            print(f"FAIL  {name}\n      {str(e)[:260]}")
asyncio.run(main())
