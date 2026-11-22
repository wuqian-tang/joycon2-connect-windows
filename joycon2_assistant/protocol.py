"""Small, dependency-free pieces of the Joy-Con 2 advertisement protocol."""
from __future__ import annotations


def identify_advertisement(data: bytes) -> tuple[str, bool] | None:
    # bleak removes the 0x0553 company identifier before exposing this value.
    if len(data) < 16 or not data.startswith(bytes.fromhex('0100037e05')):
        return None
    side = {0x2067: 'left', 0x2066: 'right'}.get(int.from_bytes(data[5:7], 'little'))
    if side is None:
        return None
    return side, not any(data[10:16])
