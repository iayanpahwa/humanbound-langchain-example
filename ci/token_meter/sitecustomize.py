# Token meter for the red-team job. Python loads this file at startup when
# its directory is on PYTHONPATH, so it wraps the HTTP call hb makes to
# OpenAI's chat completions endpoint and appends one JSON line of token
# totals per process when it exits. It only counts; it never changes a request.
import atexit
import json
import os

_totals = {"calls": 0, "input_tokens": 0, "output_tokens": 0}


def _install():
    try:
        import requests
    except Exception:
        return
    original = requests.post

    def metered(url, *args, **kwargs):
        response = original(url, *args, **kwargs)
        if "api.openai.com" in str(url):
            try:
                usage = response.json().get("usage") or {}
            except Exception:
                usage = {}
            if usage:
                _totals["calls"] += 1
                _totals["input_tokens"] += usage.get("prompt_tokens", 0)
                _totals["output_tokens"] += usage.get("completion_tokens", 0)
        return response

    requests.post = metered


def _flush():
    if _totals["calls"]:
        with open(os.environ.get("TOKEN_METER_FILE", "token-meter.jsonl"), "a") as f:
            f.write(json.dumps(_totals) + "\n")


_install()
atexit.register(_flush)
