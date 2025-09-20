# app/opcua_client.py
import logging
from asyncua.sync import Client
from asyncua import ua

log = logging.getLogger("opcua")

def opcua_read(url: str, node_id: str):
    with Client(url=url) as client:
        node = client.get_node(node_id)
        val = node.read_value()
        log.info("opcua.read ok url=%s node=%s val=%s", url, node_id, val)
        return val

def opcua_write(url: str, node_id: str, value):
    with Client(url=url) as client:
        node = client.get_node(node_id)
        vtype = node.get_data_type_as_variant_type()  # Int32/Double/etc.
        # cast to expected type (prevents BadTypeMismatch)
        if vtype == ua.VariantType.Int32:
            value = int(value)
        elif vtype == ua.VariantType.Double:
            value = float(value)

        node.write_value(ua.Variant(value, vtype))
        new_val = node.read_value()     # <-- read-back confirmation
        log.info("opcua.write ok url=%s node=%s set=%s now=%s (%s)",
                 url, node_id, value, new_val, vtype.name)
        return new_val
