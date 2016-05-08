#!/usr/bin/env python

import scapy.all as scapy

while 1:
    pkts = scapy.sniff(iface="at0",filter = "tcp",count=1)
    pkts[0].show()