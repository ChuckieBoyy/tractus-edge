# MEMORY.md

This document serves as a "living memory" for the Tractus Edge project, intended to help any developer (or AI agent) get up to speed quickly.

## 1) Current Status (End of Week 1)

*   ✅ **Simulators:** OPC UA & Modbus sims are working locally and can be started with `python app/<sim_name>.py`.
*   ✅ **FastAPI App:** The core application is running with endpoints for health checks (`/healthz`), metrics (`/metrics/`), and direct device interaction.
*   ✅ **Command Endpoints:** The generic command endpoints (`/commands/validate` and `/commands/execute`) are implemented.
*   ✅ **OPC UA Client:** The client uses a pooled connection for low-latency calls (sub-10ms) and is integrated into the main app lifecycle.
*   ✅ **Prometheus Metrics:** The app exposes key metrics, including request latency, request totals, and command counters.
*   ✅ **SQLite Idempotency:** The `reserve`/`complete`/`lookup` pattern is implemented to prevent duplicate command execution.
*   ✅ **Configuration:** The application is configured via a `.env` file for service name, version, and log levels.

## 2) File Tree (Repo Root)

```
.
├─ .venv/                     # Local virtualenv (ignored by Git)
├─ app/
│  ├─ __init__.py
│  ├─ main.py                 # FastAPI app, metrics, endpoints, command executor, UA client lifecycle
│  ├─ modbus_client.py        # Modbus/TCP helpers (pymodbus 2.5.3)
│  ├─ modbus_sim_server.py    # Local Modbus demo server
│  ├─ opcua_client.py         # OPC UA helpers with type-safe writes & pooled client
│  ├─ opcua_sim_server.py     # Local OPC UA demo server (ns=…;s=Demo/SpeedRpm)
│  ├─ schemas.py              # Pydantic models (CommandBase)
│  └─ idempotency.py          # SQLite-based idempotency logic
├─ .env                       # Runtime configuration
├─ .gitignore                 # Standard Python gitignore
├─ ARCHITECTURE.md            # System architecture design
├─ MEMORY.md                  # This file
├─ ROADMAP.md                 # Project ramp-up and POC plan
├─ TECHNICAL_SPECIFICATION.md # Detailed API contracts and runbooks
├─ requirements.txt           # Pinned Python libraries
├─ commands.txt               # Handy local curl snippets for testing
├─ cmd.json                   # Example command payload
└─ state.sqlite               # Local SQLite DB for idempotency
```

## 3) Key Decisions & Rationale

*   **OPC UA Pooled Client**: A client is connected at startup and reused for all calls. This drops p95 latency from ~2s (for connect-per-call) to ~5–10ms, which is critical for a responsive system.
*   **SQLite for Idempotency**: Using a local SQLite database provides reliable duplicate suppression without requiring external services like Redis or a full-blown database, making the edge node self-contained and resilient.
*   **Prometheus Metrics**: Integrated from day one to ensure the system is observable. We track not just API metrics but also domain-specific counters (e.g., `commands_total{kind="opcua_write"}`).
*   **pymodbus v2.5.3**: Pinned to this version to align with stable, well-documented synchronous APIs (`.client.sync`, `.server.sync`) and avoid breaking changes in v3.
*   **Fixed NodeId & Int32 in OPC UA Sim**: This simplifies development and demos by ensuring the client and server are always aligned on the data type, avoiding common `BadTypeMismatch` errors.

## 4) How to Resume After a Break

1.  **Activate Virtual Environment:**
    *   PowerShell: `.\.venv\Scripts\Activate`
    *   Bash: `source .venv/Scripts/activate`
2.  **Start Simulators** (in two separate terminals):
    *   `python app/opcua_sim_server.py`
    *   `python app/modbus_sim_server.py`
3.  **Run the API** (in a third terminal):
    *   `uvicorn app.main:app --reload`
4.  **Run Sanity Checks:**
    *   `curl -sS http://127.0.0.1:8000/healthz`
    *   `curl -sS "http://127.0.0.1:8000/opcua/read"`
    *   `curl -sS -X POST "http://127.0.0.1:8000/opcua/write" -H "Content-Type: application/json" -d '{"value":1500}'`
5.  **Check Metrics:**
    *   `curl -sSL http://127.0.0.1:8000/metrics/`

## 5) Notes for AI Collaborators

*   **AI is a client, not the core.** Never write code that allows an AI layer to directly access device I/O. The AI's role is to produce strict, valid JSON that is sent to the Edge Node's API. The Edge Node is the single source of truth for validation, policy, and execution.
*   **Extend via capabilities.** To add a new action, define a new capability string (`name@vN`) and add a corresponding handler in `_execute_capability`.
*   **Respect data types.** Always use the `_coerce_to_variant` helper for OPC UA writes to match the target node's data type.
*   **Instrument new commands.** When adding a new capability, increment the `COMMANDS_TOTAL` Prometheus counter with the appropriate `kind` label.
