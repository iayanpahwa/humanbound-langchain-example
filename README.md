# humanbound-langchain-example

A small LangChain agent, wrapped in FastAPI, wired up for adversarial testing with
[Humanbound](https://humanbound.ai).

This is the companion code for the blog post "I built an AI agent. What's next?" It shows the one
piece that isn't obvious from Humanbound's own docs: how to point `hb test` at an agent built with a
real framework, not a bare LLM call.

## What's here

- `agent.py`: a LangChain agent (`create_agent`, LangChain 1.x) with two tools, `lookup_order` and
  `issue_refund`. It's deliberately under-guarded. It doesn't double-check that a refund amount
  matches the order it just looked up, and it trusts tool output at face value. A hardened agent
  gives Humanbound nothing interesting to find.
- `server.py`: a ~15-line FastAPI wrapper. `POST /chat` in, `{"reply": "..."}` out. This is the only
  file that has to exist for Humanbound to reach the agent. Swap `agent.run_agent` for any other
  framework's call and nothing else changes.
- `bot-config.json`: tells `hb test` where to send attacks and how to read the reply.
- `scope.yaml`: tells Humanbound what this agent is supposed to do, so it can tell the difference
  between a refusal and a scope violation.

## Setup

Requires Python 3.12+ and an [OpenRouter](https://openrouter.ai) API key (any OpenAI-compatible
provider works if you adjust `base_url` in `agent.py`).

```bash
uv venv -p 3.12 .venv
uv pip install -r requirements.txt --python .venv/bin/python
export OPENROUTER_API_KEY=your-key-here
```

## Run the agent

```bash
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000
```

Confirm it's alive:

```bash
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order ORD-1001?"}'
```

## Test it with Humanbound

Install the local engine:

```bash
pip install "humanbound[engine,firewall]"
```

Humanbound's own attacker and judge need a model too. Point them at any OpenAI-compatible provider:

```bash
export HB_PROVIDER=openai
export HB_API_KEY=your-openai-key
export HB_MODEL=gpt-4o-mini
```

Then, with the agent server still running in another terminal:

```bash
hb test --endpoint bot-config.json --scope scope.yaml --quick --wait
```

`--quick` runs a fast subset of the OWASP Agentic attack categories and finishes in minutes. Drop it
for a fuller run. Results land under `.humanbound/results/<experiment-id>/` as JSON and JSONL.

Want to run the attacker/judge through OpenRouter instead of a raw OpenAI key? The local engine's
`openai` provider currently hardcodes `api.openai.com` with no base-URL override. See
[humanbound#70](https://github.com/humanbound/humanbound/issues/70) for the open issue and a
one-line workaround.

## Trying it against a different agent

The only file specific to LangChain is `agent.py`. To point Humanbound at your own agent:

1. Write a function that takes a string and returns a string (or adapt `server.py`'s `/chat` handler
   directly to your agent's call signature).
2. Update `scope.yaml` to describe what your agent should and shouldn't do.
3. Run the same `hb test` command.

## What this is not

This agent is intentionally weak so a test run has something to find. Don't ship the refund tool as
written. A real one should verify the order and amount server-side, not trust the model to get it
right.
