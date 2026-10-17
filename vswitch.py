"""tapswitch - the switch (server side).

Phase 1: frame parsing and the MAC table. No networking yet.
"""

import time

ETH_HEADER_LEN = 14
BROADCAST = b"\xff" * 6


def format_mac(mac: bytes) -> str:
    """b'\\x02\\x00\\x00\\x00\\x00\\x0a' -> '02:00:00:00:00:0a'"""
    return ":".join(f"{b:02x}" for b in mac)


def is_group(mac: bytes) -> bool:
    """True for broadcast and multicast addresses."""
    return bool(mac[0] & 1)


def parse_frame(frame: bytes):
    """Return (destination MAC, source MAC, EtherType) of a frame."""
    if len(frame) < ETH_HEADER_LEN:
        raise ValueError(f"frame too short: {len(frame)} bytes")
    dst = frame[0:6]
    src = frame[6:12]
    ethertype = int.from_bytes(frame[12:14], "big")
    return dst, src, ethertype


class MacTable:
    """Remembers which port each MAC address lives behind."""

    def __init__(self, max_age: float = 300):
        self.max_age = max_age
        self._entries = {}  # mac -> (port, last_seen)

    def learn(self, mac: bytes, port, now: float = None) -> None:
        if is_group(mac):
            return  # a group address is never a real sender
        if now is None:
            now = time.monotonic()
        self._entries[mac] = (port, now)

    def lookup(self, mac: bytes, now: float = None):
        entry = self._entries.get(mac)
        if entry is None:
            return None
        port, last_seen = entry
        if now is None:
            now = time.monotonic()
        if now - last_seen > self.max_age:
            del self._entries[mac]
            return None
        return port

    def ports(self) -> set:
        return {port for port, _ in self._entries.values()}
