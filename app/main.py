# app/main.py
import os, logging, time
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel
from app.opcua_client import opcua_read, opcua_write
from app.modbus_client import read_coil, write_coil, read_holding_register, write_holding_register
from dotenv import load_dotenv

load_dotenv()

# ---------- logging + version ----------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

for noisy in ("asyncua", "pymodbus", "uvicorn.access"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

SERVICE = os.getenv("SERVICE_NAME", "tractus-edge")
VERSION = os.getenv("SERVICE_VERSION", "0.1.0")
log = logging.getLogger(SERVICE)
LIB_LOG_LEVEL = os.getenv("LIB_LOG_LEVEL", "WARNING")
for noisy in ("asyncua", "pymodbus", "uvicorn.access"):
    logging.getLogger(noisy).setLevel(LIB_LOG_LEVEL)

app = FastAPI(title=f"{SERVICE} (Week1)")

# ---------- metrics ----------
REQ_LATENCY = Histogram(
    "api_request_seconds",
    "Request latency (s)",
    ["path", "method"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5)
)
REQ_TOTAL = Counter(
    "api_requests_total",
    "Total API requests",
    ["path", "method", "status"]
)
ERROR_TOTAL = Counter(
    "api_errors_total",
    "Total application errors",
    ["exception"]
)
COMMANDS_TOTAL = Counter("commands_total", "Total pseudo-commands", ["kind"])

# expose Prometheus metrics
app.mount("/metrics", make_asgi_app())

# ---------- middleware to record metrics ----------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # don't self-instrument the /metrics scrape
    if request.url.path == "/metrics":
        return await call_next(request)

    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        ERROR_TOTAL.labels(exception=exc.__class__.__name__).inc()
        log.exception("Unhandled error %s %s", request.method, request.url.path)
        return JSONResponse({"detail": "internal error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        dur = time.perf_counter() - start
        path = request.url.path
        method = request.method
        status = getattr(locals().get("response", None), "status_code", 500)
        REQ_LATENCY.labels(path=path, method=method).observe(dur)
        REQ_TOTAL.labels(path=path, method=method, status=str(status)).inc()

# ---------- lifecycle ----------
@app.on_event("startup")
async def _startup():
    log.info("starting service=%s version=%s", SERVICE, VERSION)

# ---------- basic endpoints ----------
@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"service": SERVICE, "version": VERSION}

@app.get("/")
def root():
    return {"hello": "world"}

# ---------- OPC UA ----------
@app.get("/opcua/read")
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
    value: int  # Int32 in your sim; switch to float if your node is Double

@app.post("/opcua/write")
def ua_write(body: UAWriteBody):
    try:
        new_val = opcua_write(body.url, body.node_id, body.value)
        COMMANDS_TOTAL.labels(kind="opcua_write").inc()
        return {"ok": True, "value": new_val}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OPC UA write failed: {e}")

# ---------- Modbus ----------
@app.get("/modbus/read_coil")
def mb_read_coil(host: str = "127.0.0.1", port: int = 5020, address: int = 1):
    try:
        v = read_coil(host, port, address)
        COMMANDS_TOTAL.labels(kind="modbus_read_coil").inc()
        return {"address": address, "value": v}
    except Exception as e:
        raise HTTPException(500, f"Modbus read_coil failed: {e}")

@app.post("/modbus/write_coil")
def mb_write_coil(host: str = "127.0.0.1", port: int = 5020, address: int = 1, value: bool = True):
    try:
        ok = write_coil(host, port, address, value)
        COMMANDS_TOTAL.labels(kind="modbus_write_coil").inc()
        return {"ok": ok}
    except Exception as e:
        raise HTTPException(500, f"Modbus write_coil failed: {e}")

@app.get("/modbus/read_hr")
def mb_read_hr(host: str = "127.0.0.1", port: int = 5020, address: int = 1):
    try:
        v = read_holding_register(host, port, address)
        COMMANDS_TOTAL.labels(kind="modbus_read_hr").inc()
        return {"address": address, "value": v}
    except Exception as e:
        raise HTTPException(500, f"Modbus read_hr failed: {e}")

@app.post("/modbus/write_hr")
def mb_write_hr(host: str = "127.0.0.1", port: int = 5020, address: int = 1, value: int = 123):
    try:
        ok = write_holding_register(host, port, address, value)
        COMMANDS_TOTAL.labels(kind="modbus_write_hr").inc()
        return {"ok": ok}
    except Exception as e:
        raise HTTPException(500, f"Modbus write_hr failed: {e}")
