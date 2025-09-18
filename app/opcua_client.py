# app/opcua_client.py
from asyncua.sync import Client

def opcua_read(url: str, node_id: str):
    with Client(url=url) as client:
        node = client.get_node(node_id)
        return node.read_value()

def opcua_write(url: str, node_id: str, value):
    with Client(url=url) as client:
        node = client.get_node(node_id)
        vtype = node.get_data_type_as_variant_type()
        node.write_value(value)
        return True
