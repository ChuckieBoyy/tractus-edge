# v2.5.3: ModbusTcpClient is in pymodbus.client.sync
from pymodbus.client.sync import ModbusTcpClient  

def read_coil(host="127.0.0.1", port=5020, address=1):
    c = ModbusTcpClient(host, port=port, timeout=2)
    if not c.connect():
        raise RuntimeError(f"Cannot connect to Modbus {host}:{port}")
    try:
        rr = c.read_coils(address, 1)
        if rr.isError():
            raise RuntimeError(rr)
        return bool(rr.bits[0])
    finally:
        c.close()

def write_coil(host="127.0.0.1", port=5020, address=1, value=True):
    c = ModbusTcpClient(host, port=port, timeout=2)
    if not c.connect():
        raise RuntimeError(f"Cannot connect to Modbus {host}:{port}")
    try:
        rq = c.write_coil(address, value)
        if rq.isError():
            raise RuntimeError(rq)
        return True
    finally:
        c.close()

def read_holding_register(host="127.0.0.1", port=5020, address=1):
    c = ModbusTcpClient(host, port=port, timeout=2)
    if not c.connect():
        raise RuntimeError(f"Cannot connect to Modbus {host}:{port}")
    try:
        rr = c.read_holding_registers(address, 1)
        if rr.isError():
            raise RuntimeError(rr)
        return int(rr.registers[0])
    finally:
        c.close()

def write_holding_register(host="127.0.0.1", port=5020, address=1, value=123):
    c = ModbusTcpClient(host, port=port, timeout=2)
    if not c.connect():
        raise RuntimeError(f"Cannot connect to Modbus {host}:{port}")
    try:
        rq = c.write_register(address, value)
        if rq.isError():
            raise RuntimeError(rq)
        return True
    finally:
        c.close()
