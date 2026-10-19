"""Temporary test helper: pretend to be a VPort.

Usage: python fake_client.py <udp_port> <my_mac> [dst_mac] [message]

Sends one frame to the switch (broadcast if no dst_mac is given), then
prints any frames the switch sends back for 15 seconds.
"""

import socket
import sys
import time

SWITCH = ("127.0.0.1", 9999)
LISTEN_SECONDS = 15
BROADCAST = "ff:ff:ff:ff:ff:ff"


def mac_bytes(text: str) -> bytes:
    return bytes.fromhex(text.replace(":", ""))


def mac_text(mac: bytes) -> str:
    return ":".join(f"{b:02x}" for b in mac)


def main() -> None:
    my_port = int(sys.argv[1])
    my_mac = mac_bytes(sys.argv[2])
    dst = mac_bytes(sys.argv[3]) if len(sys.argv) > 3 else mac_bytes(BROADCAST)
    message = sys.argv[4] if len(sys.argv) > 4 else "hello"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", my_port))

    frame = dst + my_mac + (0x88B5).to_bytes(2, "big") + message.encode()
    sock.sendto(frame, SWITCH)
    print(f"[{my_port}] sent {mac_text(my_mac)} -> {mac_text(dst)}: {message!r}")

    deadline = time.monotonic() + LISTEN_SECONDS
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        sock.settimeout(remaining)
        try:
            data, _ = sock.recvfrom(2048)
        except socket.timeout:
            break
        print(
            f"[{my_port}] GOT {mac_text(data[6:12])} -> {mac_text(data[0:6])}: "
            f"{data[14:].decode(errors='replace')!r}"
        )


if __name__ == "__main__":
    main()
