#!/usr/bin/env python
# coding=utf-8
# code by 92ez.com

from pymongo import MongoClient
import subprocess
import datetime
import platform
import psutil
import signal
import json
import time
import web
import sys
import os

DN = open(os.devnull, 'w')

urls = (
    "/","dataCenter",
    "/regist","doRegist",
    "/login","doLogin",
    "/manage","dataCenter",
    "/sysinfo","systemInfo",
    "/allinfo","getLinuxInfo",
    "/getCurrent","currentInfo",
    "/getInterface","netIface",
    "/createAp","createAP",
    "/rmMon","rmMon"
)

#static
render = web.template.render('templates',cache=False)

#init program
class index:
    def GET(self):
        return render.index()

#login
class doLogin:
    def POST(self):
        loginUser = web.input().get("username")
        loginPass = web.input().get("password")

        if len(loginUser) < 5:
            return json.dumps({"code":-1,"msg":"用户名不能小于5位"})
            sys.exit()
        if len(loginPass) < 5:
            return json.dumps({"code":-1,"msg":"密码不能小于5位"})
            sys.exit()
        try:
            client = MongoClient('localhost', 27017)
            db = client.wifirecord
            db.authenticate("admin","admin")

            allcollections = db.collection_names(include_system_collections=False)
            print "[log]["+ str(datetime.datetime.now()) +"] :Find collections list :" + str(allcollections)

            collection = db.users

            if collection.find_one({"username":loginUser,"password":loginPass}) == None:
                return json.dumps({"code":-1,"msg":"用户名或密码错误"})
            else:
                return json.dumps({"code":0})
        except Exception,e:
            print "[e]["+ str(datetime.datetime.now()) +"] : Exception:" + str(e)
            return json.dumps({"code":-1,"msg":"数据库连接失败"})

#main
class dataCenter:
    def GET(self):
        return render.data()

#sysinfo
class systemInfo:
    def GET(self):
        return render.systeminfo()

class getLinuxInfo:
    def POST(self):
        hostname = platform.uname()[1]
        release = platform.uname()[2]
        version = platform.linux_distribution()
        machine = platform.uname()[4]
        processor = platform.architecture()[0]

        logiccore = psutil.cpu_count()
        phycore = psutil.cpu_count(logical=False)
        phymem = psutil.virtual_memory()[0]/1024.0/1024.0
        starttime = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        disktotal = psutil.disk_usage('/')[0]/1024.0/1024.0/1024.0
        diskused = psutil.disk_usage('/')[1]/1024.0/1024.0/1024.0
        diskfree = psutil.disk_usage('/')[2]/1024.0/1024.0/1024.0

        thisPid = os.getpid()

        return json.dumps(
            {
                "code":0,
                "system":{
                    "hostname":hostname,
                    "release":release,
                    "version":version,
                    "machine":machine,
                    "processor":processor,
                    "starttime":starttime
                },
                "hard":{
                    "logiccore":logiccore,
                    "phycore":phycore,
                    "phymem":phymem,
                    "disktotal":disktotal,
                    "diskused":diskused,
                    "diskfree":diskfree
                },
                "os":{
                    "thisPid":thisPid
                }
            }
        )

class currentInfo:
    def POST(self):
        cpuused = psutil.cpu_percent(interval=None, percpu=False)
        memused = psutil.virtual_memory()[2]
        diskused = psutil.disk_usage('/')[3]
        pidcount = len(psutil.pids())

        uptimeshell = subprocess.Popen(['uptime'],stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        uptimeshell.wait()
        uptime = uptimeshell.communicate()

        return json.dumps(
            {
                "code":0,
                "current":{
                    "cpuused":cpuused,
                    "memused":memused,
                    "diskused":diskused,
                    "pidcount":pidcount,
                    "uptime":uptime
                }
            }
        )

class netIface:
    def POST(self):

        iface_res = os.popen("ip link").read()
        interfaces = []
        macs = []
        for line in iface_res.split('\n'):
            if "default qlen" in line:
                interfaces.append(line.split()[1].split(':')[0])
            if "link/" in line:
                macs.append(line.split()[1])

        ips = []
        for thisIface in interfaces:
            tempres = os.popen("ifconfig "+thisIface).read()
            tempip = '无'
            for line in tempres.split('\n'):
                if "netmask" in line:
                    tempip = line.split()[1]
            ips.append(tempip)

        router = os.popen("/sbin/ip route").read()
        active = []
        for line in router.split('\n'):
            if 'default via' in line:
                line = line.split()
                active.append(line[4])

        istatus = []
        for iface in interfaces:
            tempstatus = ''
            if iface in active:
                tempstatus = "连接"
            elif 'mon' in iface:
                tempstatus = "监听"
            elif 'lo' in iface:
                tempstatus = "回环"
            elif 'at' in iface:
                tempstatus = "转发"
            else:
                tempstatus = "断开"

            istatus.append({"name":iface,"status":tempstatus,"mac":macs[interfaces.index(iface)],"ip":ips[interfaces.index(iface)]})

        wirelessiface = []
        proc = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=DN)
        wiface = proc.communicate()[0].split('\n')
        for line in wiface:
            if "IEEE 8" in line:
                if 'mon' in line: continue
                wirelessiface.append(line.split()[0])

        return json.dumps({"code":0,"interfaces":istatus,"wireless":wirelessiface})

class rmMon:
    def POST(self):
        rm_mon()
        time.sleep(2)
        return json.dumps({"code":0})

class createAP:
    def POST(self):
        key = web.input().get("key")
        ssid = web.input().get("ssid")
        inet = web.input().get("inet")
        ap = web.input().get("ap")
        channel = '6'

        # set iptables
        iptables(inet)
        # start monitor
        mon_iface = start_monitor(ap,channel)
        # start ap
        start_ap(mon_iface, channel, ssid)
        # dhcpconf
        ipprefix = getIpfix(inet)
        try:
            dhcpconf = dhcp_conf(ipprefix)
            dhcp(dhcpconf, ipprefix)
            # os.system(sys.path[0]+'/sniffer.py')
            return json.dumps({"code":0})
        except Exception,e:
            print e
            return json.dumps({"code":-1,"msg":"Failed!"})

def getIpfix(inet_face):
    tempres = os.popen("ifconfig "+inet_face).read()
    for line in tempres.split('\n'):
        if "netmask" in line:
            tempip = line.split()[1][:2]
    return tempip

def iptables(inet_iface):
    global forw
    os.system('iptables -X')
    os.system('iptables -F')
    os.system('iptables -t nat -F')
    os.system('iptables -t nat -X')
    os.system('iptables -t nat -A POSTROUTING -o %s -j MASQUERADE' % inet_iface)
    with open('/proc/sys/net/ipv4/ip_forward', 'r+') as ipf:
        forw = ipf.read()
        ipf.write('1\n')
        return forw

def cleanup(signal, frame):
    with open('/proc/sys/net/ipv4/ip_forward', 'r+') as forward:
        forward.write(forw)
    os.system('iptables -F')
    os.system('iptables -X')
    os.system('iptables -t nat -F')
    os.system('iptables -t nat -X')
    os.system('pkill airbase-ng')
    os.system('pkill dhcpd')
    rm_mon()

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

def start_ap(mon_iface, channel, essid):
    print '[*] Starting the fake access point...'
    try:
        subprocess.Popen(['airbase-ng', '-P', '-c', channel, '-e', essid, mon_iface], stdout=DN, stderr=DN)
        print '[*] Waiting for 7 seconds...'
        time.sleep(6)
    except KeyboardInterrupt:
        cleanup(None, None)
    subprocess.Popen(['ifconfig', 'at0', 'up', '10.0.0.1', 'netmask', '255.255.255.0'], stdout=DN, stderr=DN)
    subprocess.Popen(['ifconfig', 'at0', 'mtu', '1400'], stdout=DN, stderr=DN)

def dhcp(dhcpconf, ipprefix):
    os.system('echo > /var/lib/dhcp/dhcpd.leases')
    dhcp = subprocess.Popen(['dhcpd', '-cf', dhcpconf], stdout=subprocess.PIPE, stderr=DN)
    if ipprefix == '19' or ipprefix == '17':
        os.system('route add -net 10.0.0.0 netmask 255.255.255.0 gw 10.0.0.1')
    else:
        os.system('route add -net 172.16.0.0 netmask 255.255.255.0 gw 172.16.0.1')

def rm_mon():
    monitors = []
    proc = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in proc.communicate()[0].split('\n'):
        if len(line) == 0: continue
        if line[0] != ' ':
            iface = line[:line.find(' ')]
            if 'Mode:Monitor' in line:
                monitors.append(iface)

    for m in monitors:
        if 'mon' in m:
            subprocess.Popen(['airmon-ng', 'stop', m], stdout=DN, stderr=DN)
        else:
            subprocess.Popen(['ifconfig', m, 'down'], stdout=DN, stderr=DN)
            subprocess.Popen(['iw', 'dev', m, 'mode', 'managed'], stdout=DN, stderr=DN)
            subprocess.Popen(['ifconfig', m, 'up'], stdout=DN, stderr=DN)

if __name__ == "__main__":

    if os.geteuid() != 0:
        sys.exit('[Error!!!] You must run this script as root')

    ifirst = raw_input('[Warning] If you run this script first time? (y/n):')

    if ifirst == 'y':

        print '[Waiting] Install and update modules...'
        print '-'*82

        os.system('pip install -U web.py')
        os.system('pip install -U psutil')
        os.system('pip install -U pymongo')
        os.system('pip install -U scapy')
        os.system('apt-get install mongodb -y')
        os.system('service mongodb restart')
        os.system('apt-get -y install isc-dhcp-server')

        print '-'*82

    rm_mon()
    app = web.application(urls,globals())
    app.run()
