# app/opcua_client.py
import logging
import threading
from typing import Optional

from asyncua.sync import Client
from asyncua import ua

log = logging.getLogger("opcua")
_UA_LOCK = threading.Lock()  # serialize shared-client access

def _coerce_to_variant(node, value):
    """Match the node's data type and build a UA Variant to avoid BadTypeMismatch."""
    vtype = node.get_data_type_as_variant_type()  # Int32 / Double / etc.
    if vtype == ua.VariantType.Int32:
        value = int(value)
    elif vtype == ua.VariantType.Double:
        value = float(value)
    # add more types as needed
    return ua.Variant(value, vtype), vtype

def _pooled_call(client: Client, fn):
    """Run an operation on the pooled client with a simple reconnect-once fallback."""
    with _UA_LOCK:
        try:
            return fn()
        except Exception as e:
            # reconnect once and retry (useful if the sim restarted)
            try:
                log.warning("opcua pooled call failed (%s); reconnecting once", e)
                client.disconnect()
            except Exception:
                pass
            client.connect()
            return fn()

def opcua_read(url: str, node_id: str, client: Optional[Client] = None):
    """Read a node value. If 'client' is provided, uses the pooled fast path."""
    if client is None:
        # classic one-shot (slower)
        with Client(url=url) as c:
            node = c.get_node(node_id)
            val = node.read_value()
            log.info("opcua.read ok url=%s node=%s val=%s", url, node_id, val)
            return val

    # pooled fast path
    def _do():
        node = client.get_node(node_id)
        val = node.read_value()
        log.info("opcua.read ok url=%s node=%s val=%s (pooled)", url, node_id, val)
        return val

    return _pooled_call(client, _do)

def opcua_write(url: str, node_id: str, value, client: Optional[Client] = None):
    """Write a node (type-safe) and read back the value. Supports pooled client."""
    if client is None:
        with Client(url=url) as c:
            node = c.get_node(node_id)
            variant, vtype = _coerce_to_variant(node, value)
            node.write_value(variant)
            new_val = node.read_value()
            log.info("opcua.write ok url=%s node=%s set=%s now=%s (%s)",
                     url, node_id, value, new_val, vtype.name)
            return new_val

    # pooled fast path
    def _do():
        node = client.get_node(node_id)
        variant, vtype = _coerce_to_variant(node, value)
        node.write_value(variant)
        new_val = node.read_value()
        log.info("opcua.write ok url=%s node=%s set=%s now=%s (%s, pooled)",
                 url, node_id, value, new_val, vtype.name)
        return new_val

    return _pooled_call(client, _do)
