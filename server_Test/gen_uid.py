#!/bin/env python
# coding: utf-8

import sys
import time

class UIDGenerator:
    def __init__(self):
        self.mac_str = self.get_mac()
        self.seq = 0

    def get_uid(self):
        mac_bytes = self._get_mac_bytes()
        time_bytes = self._get_time_bytes()
        cur_seq = self._next_seq()
        uid = mac_bytes | time_bytes | cur_seq
        return uid

    def get_mac(self):
        from uuid import getnode as mac
        mac_int = mac()
        mac_str = ':'.join(("%012X" % mac_int)[i:i+2] for i in range(0, 12, 2))
        return mac_str

    def _next_seq(self):
        self.seq = (self.seq + 1) % 256
        return self.seq

    def _get_mac_bytes(self):
        mac_byte_list = self.mac_str.split(":")
        mac_bytes = 0
        bit_offset = 56
        for mac_byte in mac_byte_list[2:]:
            mac_bytes = mac_bytes | (int(mac_byte, 16) << bit_offset)
            bit_offset -= 8
        #print "mac bytes: %x" % mac_bytes
        return mac_bytes

    def _get_time_bytes(self):
        now_ts = int(time.time())
        now_ts = now_ts & ~(0xFF << 24)
        now_ts = now_ts << 8
        #print "time bytes: %x" % now_ts
        return now_ts

def main():
    if (len(sys.argv) != 2):
        print "Usage: %s <MAC ADDRESS>" % sys.argv[0]
        return 1

    mac_str = sys.argv[1]
    uid_gen = UIDGenerator(mac_str)

    uid = uid_gen.get_uid();
    print "uid: %x" % uid

    print "-" * 20

    uid = uid_gen.get_uid();
    print "uid: %x" % uid

if __name__ == "__main__":
    main()
