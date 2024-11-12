import gzip
import json
from typing import Any

from .primitives import Empty


def json_clean(obj: Any) -> dict:
    try:
        from jupyter_client.jsonutil import json_clean
    except ImportError:
        from ipykernel.jsonutil import json_clean
    return json_clean(obj)


def json_default(obj: Any) -> str | int | list | float | None:
    if isinstance(obj, Empty):
        return None
    try:
        from jupyter_client.jsonutil import json_default as jupyter_json_default
    except ImportError:
        from jupyter_client.jsonutil import date_default as jupyter_json_default

    if hasattr(obj, "__json__"):
        obj = obj.__json__()

    return jupyter_json_default(obj)


def json_packer(obj: Any) -> bytes:
    try:
        return json.dumps(
            obj,
            default=json_default,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf8", errors="surrogateescape")
    except (TypeError, ValueError):
        # Fallback to trying to clean the json before serializing
        packed = json.dumps(
            json_clean(obj),
            default=json_default,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf8", errors="surrogateescape")

        return packed


def dict_to_bytes(obj: dict, compresslevel: int = 9) -> bytes:
    res = gzip.compress(json.dumps(obj).encode(), compresslevel=compresslevel)
    return res


def dict_from_bytes(data_b: bytes) -> dict:
    return json.loads(gzip.decompress(data_b))
