# app/schemas.py
from __future__ import annotations
from pydantic import BaseModel, Field, AwareDatetime, field_validator
from typing import Literal, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone

# risk levels used by control plane / alerts
RiskLevel = Literal["low", "medium", "high"]

class CommandBase(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Server-generated or client-provided command id")
    deviceId: str = Field(..., min_length=1)
    capability: str = Field(..., pattern=r"^[a-z0-9_.-]+@v\d+$")  # e.g., 'opcua.write@v1'
    params: Dict[str, Any] = Field(..., description="Capability-specific parameters with units")
    deadline: Optional[AwareDatetime] = Field(None, description="ISO-8601 with timezone")
    idempotencyKey: Optional[str] = Field(None, min_length=8, max_length=128)
    riskLevel: RiskLevel = "low"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("deadline")
    @classmethod
    def ensure_tz(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v.tzinfo is None:
            raise ValueError("deadline must be timezone-aware")
        return v

# Strongly-typed params for common capabilities (optional helpers)
class OpcUaWriteParams(BaseModel):
    url: str = "opc.tcp://localhost:4840/freeopcua/server/"
    nodeId: str = "ns=2;s=Demo/SpeedRpm"
    value: int = 1500
    unit: str = "rpm"

class ModbusWriteHrParams(BaseModel):
    host: str = "127.0.0.1"
    port: int = 5020
    address: int = 1
    value: int = 456
    unit: str = "raw"

class ModbusWriteCoilParams(BaseModel):
    host: str = "127.0.0.1"
    port: int = 5020
    address: int = 1
    value: bool = True

