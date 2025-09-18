# app/opcua_sim_server.py (quick dev server)
import asyncio
from asyncua import ua, Server

async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)
    objects = server.nodes.objects
    myobj = await objects.add_object(idx, "Demo")
    # One variable you can read/write
    myvar = await myobj.add_variable(ua.NodeId("Demo/SpeedRpm", idx), "SpeedRpm", 100)
    await myvar.set_writable()  # allow writes
    async with server:
        print("OPC UA demo server on opc.tcp://localhost:4840")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
