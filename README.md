# WIFIHTTPMonitor
用来监测通过wifi连接的TCP流量，解析HTTP请求并展示的web平台
### 注意
此程序在 kali linux 下测试通过，由于非root环境下的各种未知权限问题暂时未解决，故脚本必须在root权限下运行
### 用途
此程序开发针对树莓派使用，所以下面会对树莓派的环境配置作详细说明，但此程序并不仅限于树莓派，笔记本电脑同样可以运行，相对来说比树莓派兼容性更强，
### 环境配置（树莓派 kali 2016.1）
安装全新的系统之后需要按照以下顺序进行配置（或者运行 setup.py自动安装）

1.修改默认的软件源为国内源

####阿里云kali源
<pre>
deb http://mirrors.aliyun.com/kali kali-rolling main non-free contrib
deb-src http://mirrors.aliyun.com/kali kali-rolling main non-free contrib
deb http://mirrors.aliyun.com/kali-security kali-rolling/updates main contrib non-free
deb-src http://mirrors.aliyun.com/kali-security kali-rolling/updates main contrib non-free
</pre>
#####中科大kali源
<pre>
deb http://mirrors.ustc.edu.cn/kali kali-rolling main non-free contrib
deb-src http://mirrors.ustc.edu.cn/kali kali-rolling main non-free contrib
deb http://mirrors.ustc.edu.cn/kali-security kali-current/updates main contrib non-free
deb-src http://mirrors.ustc.edu.cn/kali-security kali-current/updates main contrib non-free
</pre>
2.全面更新系统并重启
<pre>apt-get update && apt-get dist-upgrade -y</pre>

3.安装 python-dev 和 gcc
<pre>apt-get install python-dev -y && apt-get install gcc -y</pre>

4.安装pip
<pre>wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py</pre>

5.安装scpay
<pre>pip install -U scapy</pre>

6.安装web.py
<pre>pip install -U web.py</pre>

7.安装psutil
<pre>pip install -U psutil</pre>

8.安装 isc-dhcp-server
<pre>apt-get install isc-dhcp-server</pre>

9.安装 rfkill
<pre>apt-get install rfkill</pre>

### 如何使用
下载并解压程序包 ，cd 切换到脚本所在目录（重要，一定要在脚本所在目录执行），执行python monitor.py 即可（树莓派上可直接 nohup python monitor.py 运行在后台，关闭shell窗口无影响），如需更换端口 请在命令后面加上端口号，默认8080端口

 浏览器输入localhost:8080即可进入管理界面
 
 创建AP之前请点击清理环境重置网卡和防火墙状态，否则容易出错
 
 清理环境后输入ssid和密码（为空则为不加密），加密方式只支持WEP加密，故密码必须为10位或以上数字
 
 点击创建AP会自动创建AP并开始嗅探流量，每次创建AP之前建议清理一次环境，避免出错

#### 反馈
时间仓促，很多细节可能没有考虑到，单纯实现了功能，测试也只是进行了初步的测试，遇到问题请将问题整理发送至邮箱 ttyusb@126.com

#### 注意
经过测试发现此程序并不能在树莓派3B上运行，查找相关资料并找到原因为arcrack-ng并不支持树莓派3的板载无线网卡（BCM 43430），所以建议还是买一块USB无线网卡比较保险，推荐RT8187
