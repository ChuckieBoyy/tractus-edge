# Project Roadmap

This document outlines the development roadmap for the Tractus Edge project, including a 4-week ramp-up plan, an 8-10 week proof-of-concept (POC) build, and a curated list of learning resources.

---

## 1) Ramp-up Plan (4 Weeks)

This plan is designed for a code-first, beginner-friendly ramp-up without requiring any physical hardware.

### Week 1 — “Hello, PLC world” (sim only)

**Goal:** Read and write values on OPC UA and Modbus-TCP simulators through your own tiny API.

*   **Set up simulators:**
    *   OPC UA demo server (e.g., open62541, Prosys).
    *   Modbus-TCP slave simulator (e.g., diagslave).
*   **Write the edge API (Python/FastAPI):**
    *   `GET /state?device={id}`
    *   `POST /command { device, capability, params, idempotencyKey }`
    *   Implement basic OPC UA `ReadTag`/`WriteTag` and Modbus `read`/`write` holding registers.
*   **Logging & Metrics:**
    *   Log caller, command JSON, exact tag/register touched, and device reply.
    *   Expose `/metrics` (Prometheus) for request count, error rate, and p50/p95 latency.
*   **Acceptance:** `curl` can flip a value on both simulators; `/metrics` shows traffic; logs show exact addresses written.

### Week 2 — Safety, Schema, and Offline

**Goal:** Behave like a real edge node: safe, auditable, and works if the WAN dies.

*   **Command Schema (v0):**
    *   Freeze fields: `id`, `deviceId`, `capability`, `params` (unit-safe), `deadline`, `riskLevel`, `idempotencyKey`, `preconditions`, `postconditions`.
    *   Validate every request against this schema.
*   **Idempotency + RBAC:**
    *   Store `idempotencyKey` in SQLite; duplicates return the first result.
    *   Simple RBAC: e.g., Operators can `Start`/`Stop`; Engineers can `SetSpeed`.
*   **Local Orchestration + Offline:**
    *   Add a tiny state machine (timeouts, retries, cancel).
    *   Add a local scheduler (cron-like) persisted in SQLite.
    *   Test offline capability: scheduled commands must still run.
*   **Acceptance:** Re-POSTing with the same key is a no-op; high-risk commands require confirmation; scheduled jobs execute with WAN off.

### Week 3 — Visual “moves” demo + Policy Guardrails

**Goal:** Show something moving on screen while maintaining industrial discipline.

*   **Robot/Conveyor Sim (Optional):**
    *   Spin up a ROS 2 + Gazebo sample.
    *   Adapt `Start`/`Stop`/`SetSpeed` to hit a ROS 2 topic/service.
*   **Policy Checks:**
    *   Integrate OPA (Open Policy Agent) or a simple rules layer.
    *   Examples: “No `SetSpeed` > 1.0 unless `role=Engineer`,” “Deny `Start` if zone lock is held.”
*   **Operator Mini-Console (2-D):**
    *   A tiny web page showing site topology, device list, queue, and incidents.
    *   Implement a “shadow mode” preview for high-risk commands.
*   **Acceptance:** Live demo shows a command making the sim move, with policy checks and audit/metrics updates; forbidden commands are cleanly denied.

### Week 4 — Hardening: LLM UI, Security, Chaos Drills

**Goal:** Wrap the UX and prove reliability.

*   **LLM as Parser (Optional):**
    *   A small function turns English → strict JSON (your schema).
    *   Validate the JSON before dispatch; the LLM is a UI helper only.
*   **Deadlines, Cancel, and Replay:**
    *   Add `deadline` to commands; implement cancellation.
    *   Create an “audit replay” page showing the full command lifecycle.
*   **Security Smoke Test:**
    *   (Optional) Run the API behind WireGuard; use mTLS between services.
    *   Ensure NTP/PTP time sync is active.
*   **Chaos Drills:**
    *   Duplicate, delay, and drop messages; confirm idempotency and timeouts behave as designed.
*   **Acceptance:** p95 API→actuation latency < 150 ms (sim); duplicate commands don’t double-execute; high-risk flows require dual-confirm; audit replay is clear.

---

## 2) POC Build Plan (8-10 Weeks)

This plan outlines the build for a full Proof-of-Concept (POC) for Tractus v0.1, including AI features.

### Objective & Scope

Build an edge-first, vendor-neutral Operations API that controls OPC UA and Modbus-TCP simulators, runs offline, and integrates AI for a copilot, anomaly detection, and optimization.

### Success Criteria

*   End-to-end command execution on both sims with p95 < 150 ms latency.
*   Offline proof: scheduled jobs execute during a WAN outage.
*   Idempotency: no double-execution with repeated keys.
*   Safety: high-risk actions require dual-confirm; policies deny unsafe commands.
*   Full audit replay is available.
*   AI: Copilot outputs valid JSON ≥95% of the time; anomaly engine detects drifts and suggests guarded fixes; optimizer improves a KPI vs. baseline.

### Timeline

*   **Weeks 0–2:** Foundation (repos, command schema, simulators, basic edge API).
*   **Weeks 2–4:** Southbound + Idempotency + Metrics + Audit.
*   **Weeks 4–6:** Orchestrator + Scheduler + RBAC + OPA + Offline; Ops Console v1.
*   **Weeks 6–8:** AI Phase 1–2 (NL Copilot + Anomaly v1).
*   **Weeks 8–10:** AI Phase 3 (Optimizer v1), WMS adapter, polish, pilot prep.

### Minimal Architecture

*   **Edge Node:** Command Bridge (REST/gRPC), Connectors (OPC UA, Modbus), Orchestrator, Policy (OPA), Metrics (Prometheus), Time/Security (NTP, mTLS).
*   **Control Plane:** API Gateway, GraphQL Read Service, Registry (Postgres), Historian (TimescaleDB), Object Store (MinIO), Ops Console.

---

## 3) Learning Resources (Ramp-up with Links)

### Week 1 Resources

*   **FastAPI:** [Official Docs](https://fastapi.tiangolo.com/)
*   **OPC UA (Python):** [python-opcua Docs](https://python-opcua.readthedocs.io/)
*   **OPC UA Simulators:** [open62541](https://open62541.org/), [Prosys Simulation Server](https://www.prosysopc.com/products/opc-ua-simulation-server/)
*   **Modbus (Python):** [pymodbus Docs](https://pymodbus.readthedocs.io/)
*   **Modbus Simulator:** [diagslave](http://www.modbusdriver.com/diagslave.html)
*   **Prometheus (Python):** [Client Docs](https://prometheus.github.io/client_python/)

### Week 2 Resources

*   **Pydantic v2:** [Official Docs](https://docs.pydantic.dev/latest/)
*   **Idempotency Keys:** [Stripe's Docs](https://stripe.com/docs/api/idempotent_requests)
*   **Scheduling:** [APScheduler Docs](https://apscheduler.readthedocs.io/)
*   **SQLite:** [Python sqlite3 Docs](https://docs.python.org/3/library/sqlite3.html)

### Week 3 Resources

*   **ROS 2:** [Official Docs](https://docs.ros.org/en/jazzy/index.html)
*   **Gazebo + ROS 2:** [Integration Docs](https://gazebosim.org/docs/latest/ros_integration)
*   **Open Policy Agent (OPA):** [Official Docs](https://www.openpolicyagent.org/docs/latest/)

### Week 4 Resources

*   **Structured Outputs (LLM):** [OpenAI Docs](https://platform.openai.com/docs/guides/function-calling)
*   **WireGuard:** [Official Docs](https://www.wireguard.com/)
*   **mTLS:** [smallstep Guide](https://smallstep.com/hello-mtls/doc/intro)
*   **Chaos Testing:** [tc netem](https://man7.org/linux/man-pages/man8/tc-netem.8.html), [Toxiproxy](https://github.com/Shopify/toxiproxy)
