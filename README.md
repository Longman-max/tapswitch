# tapswitch

A virtual Ethernet switch over UDP, built from scratch to learn how layer 2 works.

## Status
Phase 3: a TAP device that prints every frame the kernel sends (Linux, root).

## Run the tests
    python -m unittest discover -s tests -v

## What I'm learning
- Why a switch learns from the source MAC
- Why unknown destinations get flooded
- Why TAP and not TUN

## Try it (Phase 2)
Terminal 1: `python vswitch.py`

Then, in other terminals (each listens for 15 seconds):

    python fake_client.py 10003 02:00:00:00:00:0c
    python fake_client.py 10002 02:00:00:00:00:0b 02:00:00:00:00:0a "hi A"
    python fake_client.py 10001 02:00:00:00:00:0a 02:00:00:00:00:0b "hi B"

## Try it (Phase 3)
Terminal 1: `sudo python3 vport.py`

Terminal 2:

    sudo ip addr add 10.1.1.101/24 dev tapswitch0
    sudo ip link set tapswitch0 up
    ping 10.1.1.102

You should see ARP broadcasts appear in terminal 1.
