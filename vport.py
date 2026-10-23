"""tapswitch - the client (VPort).

Phase 3: open a TAP device and print every Ethernet frame the kernel sends.
Phase 4 will relay these frames to the switch over UDP.

Needs Linux and root:  sudo python3 vport.py
"""

import fcntl
import os
import struct
import sys

from vswitch import format_mac, parse_frame

TUNSETIFF = 0x400454CA  # ioctl request: "set up this tun/tap interface"
IFF_TAP = 0x0002        # TAP mode: frames, not IP packets
IFF_NO_PI = 0x1000      # no extra header, just the raw frame

ETHERTYPES = {0x0800: "IPv4", 0x0806: "ARP", 0x86DD: "IPv6"}


def open_tap(name: str = "tapswitch0"):
    """Create a TAP interface. Returns (file descriptor, real name)."""
    fd = os.open("/dev/net/tun", os.O_RDWR)
    request = struct.pack("16sH", name.encode(), IFF_TAP | IFF_NO_PI)
    reply = fcntl.ioctl(fd, TUNSETIFF, request)
    real_name = reply[:16].split(b"\x00")[0].decode()
    return fd, real_name


def main() -> None:
    fd, name = open_tap(sys.argv[1] if len(sys.argv) > 1 else "tapswitch0")
    print(f"TAP device {name} is up. Configure it in another terminal:")
    print(f"  sudo ip addr add 10.1.1.101/24 dev {name}")
    print(f"  sudo ip link set {name} up")
    print("Then try: ping 10.1.1.102   (Ctrl+C here to stop)")

    try:
        while True:
            frame = os.read(fd, 2048)
            try:
                dst, src, ethertype = parse_frame(frame)
            except ValueError as err:
                print(f"short frame: {err}")
                continue
            kind = ETHERTYPES.get(ethertype, f"0x{ethertype:04x}")
            print(f"{format_mac(src)} -> {format_mac(dst)}  {kind}  {len(frame)} bytes")
    except KeyboardInterrupt:
        print("\nstopping")


if __name__ == "__main__":
    main()
