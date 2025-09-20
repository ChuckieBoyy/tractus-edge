# app/modbus_client.py
import logging
from pymodbus.client.sync import ModbusTcpClient  # v2.5.3 import

log = logging.getLogger("modbus")

def _client(host, port):
    c = ModbusTcpClient(host, port=port, timeout=2)
    if not c.connect():
        raise RuntimeError(f"Cannot connect to Modbus {host}:{port}")
    return c

def read_coil(host="127.0.0.1", port=5020, address=1):
    c = _client(host, port)
    try:
        rr = c.read_coils(address, 1)
        if rr.isError():
            raise RuntimeError(rr)
        val = bool(rr.bits[0])
        log.info("modbus.read_coil host=%s port=%s addr=%s val=%s", host, port, address, val)
        return val
    finally:
        c.close()

def write_coil(host="127.0.0.1", port=5020, address=1, value=True):
    c = _client(host, port)
    try:
        rq = c.write_coil(address, value)
        if rq.isError():
            raise RuntimeError(rq)
        log.info("modbus.write_coil host=%s port=%s addr=%s val=%s", host, port, address, value)
        return True
    finally:
        c.close()

def read_holding_register(host="127.0.0.1", port=5020, address=1):
    c = _client(host, port)
    try:
        rr = c.read_holding_registers(address, 1)
        if rr.isError():
            raise RuntimeError(rr)
        val = int(rr.registers[0])
        log.info("modbus.read_hr host=%s port=%s addr=%s val=%s", host, port, address, val)
        return val
    finally:
        c.close()

def write_holding_register(host="127.0.0.1", port=5020, address=1, value=123):
    c = _client(host, port)
    try:
        rq = c.write_register(address, value)
        if rq.isError():
            raise RuntimeError(rq)
        log.info("modbus.write_hr host=%s port=%s addr=%s val=%s", host, port, address, value)
        return True
    finally:
        c.close()
