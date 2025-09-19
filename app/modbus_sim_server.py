# v2.5.3: StartTcpServer lives in pymodbus.server.sync
from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext, ModbusSequentialDataBlock
from pymodbus.server.sync import StartTcpServer 

store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*100),
    co=ModbusSequentialDataBlock(0, [0]*100),
    hr=ModbusSequentialDataBlock(0, [0]*100),
    ir=ModbusSequentialDataBlock(0, [0]*100),
    zero_mode=True,   # <-- add this so addresses are 0-based (easier for tests)
)
context = ModbusServerContext(slaves=store, single=True)

if __name__ == "__main__":
    print("Modbus demo server on tcp://localhost:5020")
    StartTcpServer(context, address=("0.0.0.0", 5020))
