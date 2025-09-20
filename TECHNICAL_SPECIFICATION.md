# TECHNICAL_SPECIFICATION.md

This document provides a detailed technical reference, including API contracts, data models, and operational runbooks for the Tractus Edge POC.

## 1. API Contracts

### Health & Version

*   `GET /healthz`
    *   **Description:** Standard health check endpoint.
    *   **Response (200 OK):** `{"status":"ok"}`
*   `GET /version`
    *   **Description:** Returns the current service name and version from the `.env` config.
    *   **Response (200 OK):** `{"service":"tractus-edge","version":"0.1.0"}`

### Direct OPC UA Endpoints

*   `GET /opcua/read`
    *   **Query Params:** `url`, `node_id`
    *   **Response (200 OK):** `{"node_id": "...", "value": ...}`
*   `POST /opcua/write`
    *   **Request Body:** `{"url": "...", "node_id": "...", "value": ...}`
    *   **Response (200 OK):** `{"ok": true, "value": ...}`
    *   **Note:** The `value` is automatically coerced to the node's `VariantType`.

### Direct Modbus TCP Endpoints

*   `GET /modbus/read_coil`, `GET /modbus/read_hr`
    *   **Query Params:** `host`, `port`, `address`
    *   **Response (200 OK):** `{"address": ..., "value": ...}`
*   `POST /modbus/write_coil`, `POST /modbus/write_hr`
    *   **Query Params:** `host`, `port`, `address`, `value`
    *   **Response (200 OK):** `{"ok": true}`

### Generic Command Endpoints

*   `POST /commands/validate`
    *   **Description:** Validates a `CommandBase` payload without executing it.
    *   **Response (200 OK):** `{"ok": true, "command": {<normalized_payload>}}`
*   `POST /commands/execute`
    *   **Description:** Executes a command with idempotency checks.
    *   **Idempotency Behavior:**
        *   **New Key:** Reserves key, executes, completes key, returns result.
        *   **Duplicate Key (`completed`):** Returns the cached result.
        *   **Duplicate Key (`failed`):** Returns a `400 Bad Request` with the previous error.
        *   **Duplicate Key (`accepted`):** Returns a `409 Conflict` as the command is in-flight.
    *   **Response (200 OK):** `{"ok": true, "commandId": "...", "result": {...}}`

---

## 2. Data Models & Database

### Pydantic `CommandBase` Schema

This is the core data model for all commands, defined in `app/schemas.py`.

```python
class CommandBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    deviceId: str
    capability: str = Field(pattern=r"^[a-z0-9_.-]+@v\d+$")
    params: Dict[str, Any]
    deadline: Optional[AwareDatetime] = None
    idempotencyKey: Optional[str] = Field(None, min_length=8, max_length=128)
    riskLevel: RiskLevel = "low"
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### SQLite `idempotency` Table

The schema for the idempotency table, defined in `app/idempotency.py`.

```sql
CREATE TABLE IF NOT EXISTS idempotency (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  idempotency_key TEXT NOT NULL UNIQUE,
  device_id       TEXT NOT NULL,
  capability      TEXT NOT NULL,
  created_at      TEXT NOT NULL,  -- ISO-8601 UTC
  status          TEXT NOT NULL,  -- accepted | completed | failed
  result_json     TEXT            -- Cached response for duplicates
);
```

---

## 3. Runbook: Local Development

### Environment Setup

1.  **Create `.env` file:**
    ```
    SERVICE_NAME=tractus-edge
    SERVICE_VERSION=0.1.0
    LOG_LEVEL=INFO
    LIB_LOG_LEVEL=WARNING
    ```
2.  **Install Dependencies (PowerShell):**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

### Running the System

1.  **Start Simulators** (in two separate terminals):
    ```powershell
    # Terminal 1: OPC UA
    python app\opcua_sim_server.py

    # Terminal 2: Modbus
    python app\modbus_sim_server.py
    ```
2.  **Run the API** (in a third terminal):
    ```powershell
    python -m uvicorn app.main:app --reload
    ```

### Testing with `curl`

*   **OPC UA Write:**
    ```bash
    curl -X POST "http://127.0.0.1:8000/opcua/write" -H "Content-Type: application/json" -d '{"value": 1600}'
    ```
*   **Modbus Write:**
    ```bash
    curl -X POST "http://127.0.0.1:8000/modbus/write_hr?address=1&value=456"
    ```
*   **Idempotent Command:**
    ```bash
    # First call executes
    curl -X POST "http://127.0.0.1:8000/commands/execute" -H "Content-Type: application/json" -d @cmd.json

    # Second call returns the cached result
    curl -X POST "http://127.0.0.1:8000/commands/execute" -H "Content-Type: application/json" -d @cmd.json
    ```

---

## 4. Extending the System

### Adding a New Capability

1.  **Implement the Logic:** Add a new helper function in the relevant client (e.g., `opcua_read_array` in `opcua_client.py`).
2.  **Update the Executor:** Add a new `elif` branch in `_execute_capability` in `main.py` to map the new capability string (e.g., `"opcua.read_array@v1"`) to your new function.
3.  **Add a Schema (Optional):** For complex parameters, create a new Pydantic model in `schemas.py` for validation.
4.  **Instrument:** Increment the `COMMANDS_TOTAL` Prometheus counter with the new `kind`.
