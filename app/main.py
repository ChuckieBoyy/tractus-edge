from app.modbus_client import read_coil, write_coil, read_holding_register, write_holding_register
from app.opcua_client import opcua_read, opcua_write
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Summary, make_asgi_app
from pydantic import BaseModel

app = FastAPI(title="Tractus Edge (Week1)")

# Prometheus
REQUEST_TIME = Summary("api_request_seconds", "Time spent in API handlers")
COMMANDS_TOTAL = Counter("commands_total", "Total pseudo-commands", ["kind"])
app.mount("/metrics", make_asgi_app())

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"hello": "world"}

# OPC UA endpoints (see opcua_client.py)

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
    value: int  # Int32 to match the sim; use float if you chose Double

@app.post("/opcua/write")
@REQUEST_TIME.time()
def ua_write(body: UAWriteBody):
    try:
        ok = opcua_write(body.url, body.node_id, body.value)
        COMMANDS_TOTAL.labels(kind="opcua_write").inc()
        return {"ok": ok}
    except Exception as e:
        # return the real reason instead of a generic 500
        raise HTTPException(status_code=400, detail=f"OPC UA write failed: {e}")

# Modbus endpoints (see modbus_client.py)

@app.get("/modbus/read_coil")
def mb_read_coil(host: str = "127.0.0.1", port: int = 5020, address: int = 1):
    return {"address": address, "value": read_coil(host, port, address)}

@app.post("/modbus/write_coil")
def mb_write_coil(host: str = "127.0.0.1", port: int = 5020, address: int = 1, value: bool = True):
    COMMANDS_TOTAL.labels(kind="modbus_write_coil").inc()
    return {"ok": write_coil(host, port, address, value)}

@app.get("/modbus/read_hr")
def mb_read_hr(host: str = "127.0.0.1", port: int = 5020, address: int = 1):
    return {"address": address, "value": read_holding_register(host, port, address)}

@app.post("/modbus/write_hr")
def mb_write_hr(host: str = "127.0.0.1", port: int = 5020, address: int = 1, value: int = 123):
    COMMANDS_TOTAL.labels(kind="modbus_write_hr").inc()
    return {"ok": write_holding_register(host, port, address, value)}
