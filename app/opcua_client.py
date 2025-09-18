from asyncua.sync import Client
from asyncua import ua

def opcua_read(url: str, node_id: str):
    with Client(url=url) as client:
        node = client.get_node(node_id)
        return node.read_value()

def opcua_write(url: str, node_id: str, value):
    with Client(url=url) as client:
        node = client.get_node(node_id)
        # Coerce to the server's expected data type (Int32/Double/etc.)
        vtype = node.get_data_type_as_variant_type()
        if vtype == ua.VariantType.Int32:
            value = int(value)
        elif vtype == ua.VariantType.Double:
            value = float(value)
        node.write_value(ua.Variant(value, vtype))
        return True
