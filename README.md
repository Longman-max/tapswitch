# tapswitch

A virtual Ethernet switch over UDP, built from scratch to learn how layer 2 works.

## Status
Phase 1: frame parsing and MAC table.

## Run the tests
    python -m unittest discover -s tests -v

## What I'm learning
- Why a switch learns from the source MAC
- Why unknown destinations get flooded
- Why TAP and not TUN
