# app/main.py
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Summary, make_asgi_app
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Tractus Edge (Week1)")

# Prometheus
REQUEST_TIME = Summary("api_request_seconds", "Time spent in API handlers")
COMMANDS_TOTAL = Counter("commands_total", "Total pseudo-commands", ["kind"])
app.mount("/metrics", make_asgi_app())  # exposes Prometheus metrics

@app.get("/healthz")
def healthz():
  return {"status": "ok"}

@app.get("/")
def root():
  return {"hello": "world"}
