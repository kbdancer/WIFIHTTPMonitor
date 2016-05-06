#!/usr/bin/env python

from scapy.all import sniff

while 1:
	pkts = sniff(iface="at0",count=1)
	pkts[0].show()
