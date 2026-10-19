"""tapswitch - the switch (server side).

Phase 1: frame parsing and the MAC table.
Phase 2: the UDP loop that learns, forwards and floods.
"""

import socket
import sys
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


def handle(table: MacTable, dst: bytes, src: bytes, ingress, now: float = None):
    """Learn the sender, then decide where the frame goes.

    Returns (reason, set of ports to send to).
    """
    table.learn(src, ingress, now)

    if is_group(dst):
        return "broadcast flood", table.ports() - {ingress}

    port = table.lookup(dst, now)
    if port is None:
        return "unknown flood", table.ports() - {ingress}
    if port == ingress:
        return "filtered", set()
    return "forward", {port}


def serve(host: str = "127.0.0.1", port: int = 9999) -> None:
    table = MacTable()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((host, port))
        print(f"tapswitch listening on {host}:{port} (Ctrl+C to stop)")
        try:
            while True:
                frame, ingress = sock.recvfrom(2048)
                try:
                    dst, src, _ = parse_frame(frame)
                except ValueError as err:
                    print(f"drop {ingress[0]}:{ingress[1]}  {err}")
                    continue

                reason, targets = handle(table, dst, src, ingress)
                print(
                    f"rx {ingress[0]}:{ingress[1]}  "
                    f"{format_mac(src)} -> {format_mac(dst)}  "
                    f"{reason}  ({len(targets)} port(s))"
                )
                for target in targets:
                    try:
                        sock.sendto(frame, target)
                    except OSError as err:
                        print(f"send to {target} failed: {err}")
        except KeyboardInterrupt:
            print("\nstopping")


if __name__ == "__main__":
    serve(port=int(sys.argv[1]) if len(sys.argv) > 1 else 9999)
