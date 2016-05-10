#!/usr/bin/env python
# coding=utf-8
# code by 92ez.com

import os

os.system('apt-get update && apt-get dist-upgrade -y')
os.system('apt-get install python-dev -y')
os.system('apt-get install rfkill -y')
os.system('apt-get -y install isc-dhcp-server')
os.system('wget wget https://bootstrap.pypa.io/get-pip.py')
os.system('python get-pip.py')
os.system('pip install -U web.py')
os.system('pip install -U psutil')
os.system('pip install -U scapy')