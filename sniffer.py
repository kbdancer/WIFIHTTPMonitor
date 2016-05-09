#!/usr/bin/python
# coding=utf-8

from scapy.all import *
import sqlite3
import sys

def myprint(packet):
    thisRecord = "\n".join(packet.sprintf("{Raw:%Raw.load%}").split(r"\r\n"))
    lines = packet.sprintf("{Raw:%Raw.load%}").split(r"\r\n")

    for line in lines:
        print '-'*90+'\n'+line
    # try:
    #     cx = sqlite3.connect(sys.path[0]+"/wifihttp.db")
    #     cu.execute("create table users (id integer primary key,starttime varchar(20),mac varchar(20),clientname varchar(100),createtime TimeStamp NOT NULL DEFAULT (datetime('now','localtime')))")
    #     cx.execute("insert into catalog values (?,?,?,?)", t)
    #     cx.commit()
    # except Exception, e:
    #     print e

    return thisRecord

sniff(iface='at0',prn=myprint,lfilter=lambda p: "GET" in str(p) or "POST" in str(p),filter="tcp")
