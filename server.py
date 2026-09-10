# Wraps the LangChain agent behind the HTTP shape Humanbound expects.
# HB posts to /chat with {"message": "<attack>"}; we return {"reply": "<agent output>"}.
# This file is the whole integration: it doesn't know or care that the agent
# underneath is LangChain. Swap agent.run_agent for any other framework's
# call and nothing else here changes.
from fastapi import FastAPI, Request

from agent import run_agent

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    reply = run_agent(body.get("message", ""))
    return {"reply": reply}
