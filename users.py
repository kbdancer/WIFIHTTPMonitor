#!/usr/bin/python
# coding=utf-8

import sqlite3
import datetime
import time
import json
import sys
import hashlib
import subprocess

def saveUsers():
    users = []
    proc = subprocess.Popen(['cat', '/var/lib/dhcp/dhcpd.leases'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pks = proc.communicate()[0].split('}\n')
    if len(pks[-1]) == 0: pks.pop()
    for p in pks:
        hostname = ''
        ipaddress = ''
        start_utc = ''
        mac = ''
        uid = ''
        pline = p.split('\n')
        for line in pline:
            if "client-hostname" in line:
                hostname = line.split()[1].replace('"','')[:-1]
            if "lease" in line and "{" in line:
                ipaddress = line.split()[1]
            if "starts" in line:
                start_utc = line.split()[2]+' '+line.split()[3][:-1]
            if "hardware" in line:
                mac = line.split()[2][:-1]
            if "uid" in line:
                uid = line.split()[1].replace('"','')[:-1]
        m2 = hashlib.md5()   
        m2.update(start_utc+mac+ipaddress+uid+hostname)
        users.append((start_utc,mac,ipaddress,uid,hostname,m2.hexdigest()))

    try:
        cx = sqlite3.connect(sys.path[0]+"/wifihttp.db")
        cu = cx.cursor() 
        # cx.execute("create table users (id integer primary key,start_utc varchar(20),mac varchar(20),ip varchar(20),uid varchar(50),clientname varchar(100),createtime TimeStamp NOT NULL DEFAULT (datetime('now','localtime')))")
        for u in users:
            print u
            cu.execute("select * from users where hash = '"+u[5]+"'")
            # if not cu.fetchone():
            #     cu.execute("insert into users (start,mac,ip,uid,client,hash) values (?,?,?,?,?,?)", u)
        cx.commit()
    except Exception, e:
        print e


if __name__ == '__main__':
    saveUsers()