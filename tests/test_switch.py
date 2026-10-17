import unittest

from vswitch import (
    BROADCAST,
    MacTable,
    format_mac,
    is_group,
    parse_frame,
)

MAC_A = bytes.fromhex("02000000000a")
MAC_B = bytes.fromhex("02000000000b")


def make_frame(dst, src, ethertype=0x0800, payload=b"hi"):
    return dst + src + ethertype.to_bytes(2, "big") + payload


class TestFrames(unittest.TestCase):
    def test_parse_frame(self):
        frame = make_frame(MAC_B, MAC_A, 0x0806)
        self.assertEqual(parse_frame(frame), (MAC_B, MAC_A, 0x0806))

    def test_short_frame_raises(self):
        with self.assertRaises(ValueError):
            parse_frame(b"\x00" * 13)

    def test_format_mac(self):
        self.assertEqual(format_mac(MAC_A), "02:00:00:00:00:0a")

    def test_is_group(self):
        self.assertTrue(is_group(BROADCAST))
        self.assertTrue(is_group(bytes.fromhex("01005e000001")))
        self.assertFalse(is_group(MAC_A))


class TestMacTable(unittest.TestCase):
    def test_learn_and_lookup(self):
        table = MacTable()
        table.learn(MAC_A, "port1")
        self.assertEqual(table.lookup(MAC_A), "port1")

    def test_unknown_returns_none(self):
        self.assertIsNone(MacTable().lookup(MAC_B))

    def test_group_source_not_learned(self):
        table = MacTable()
        table.learn(BROADCAST, "port1")
        self.assertIsNone(table.lookup(BROADCAST))

    def test_mac_moves_to_new_port(self):
        table = MacTable()
        table.learn(MAC_A, "port1")
        table.learn(MAC_A, "port2")
        self.assertEqual(table.lookup(MAC_A), "port2")

    def test_entry_expires(self):
        table = MacTable(max_age=10)
        table.learn(MAC_A, "port1", now=0)
        self.assertEqual(table.lookup(MAC_A, now=5), "port1")
        self.assertIsNone(table.lookup(MAC_A, now=11))

    def test_ports_are_unique(self):
        table = MacTable()
        table.learn(MAC_A, "port1")
        table.learn(MAC_B, "port1")
        self.assertEqual(table.ports(), {"port1"})


if __name__ == "__main__":
    unittest.main()
