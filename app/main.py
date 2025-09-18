# app/main.py
from app.opcua_client import opcua_read, opcua_write
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

@app.get("/opcua/read")
@REQUEST_TIME.time()
def ua_read(url: str = "opc.tcp://localhost:4840/freeopcua/server/",
            node_id: str = "ns=2;s=Demo/SpeedRpm"):
    try:
        val = opcua_read(url, node_id)
        return {"node_id": node_id, "value": val}
    except Exception as e:
        raise HTTPException(500, f"OPC UA read failed: {e}")

class UAWriteBody(BaseModel):
    url: str = "opc.tcp://localhost:4840/freeopcua/server/"
    node_id: str = "ns=2;s=Demo/SpeedRpm"
    value: float

@app.post("/opcua/write")
@REQUEST_TIME.time()
def ua_write(body: UAWriteBody):
    ok = opcua_write(body.url, body.node_id, body.value)
    COMMANDS_TOTAL.labels(kind="opcua_write").inc()
    return {"ok": ok}
