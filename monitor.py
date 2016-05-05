#!/usr/bin/env python
# coding=utf-8
# code by 92ez.com

from pymongo import MongoClient
import subprocess
import datetime
import platform
import psutil
import json
import web
import sys
import os

urls = (
    "/","index",
    "/regist","doRegist",
    "/login","doLogin",
    "/manage","dataCenter",
    "/sysinfo","systemInfo",
    "/sysconfig","systemConfig",
    "/allinfo","getLinuxInfo",
    "/getCurrent","currentInfo"
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

#sysconfig
class systemConfig:
    def GET(self):
        return render.systemconfig()

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



if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit('You must run this script as root')

    app = web.application(urls,globals())
    app.run()
