#!/usr/bin/python
#!coding=utf-8
import os
import time
import sys
import smtplib
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
 

 
n=1
while n<2:
    Pro_status = os.popen('netstat -tulnp | grep nginx','r').readlines()
    print Pro_status
    print type(Pro_status)
    strl = ''.join(Pro_status)
    print strl
    print type(strl)
    port = strl.split()[3].split(':')[-1]
    print port
    print type(port)
    now_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    print type(now_time)
    try:
        if Pro_status == []:
            #os.system('service nginx start')
            new_Pro_status = os.popen('netstat -tulnp | grep nginx','r').readlines()
            str1 = ''.join(new_Pro_status)
            port = str1.split()[3].split(':')[-1]
            if port != '80':
                print 'nginx start fail ...'
            else:
                print 'nginx start success ...'
                #sendsimplemail(warning = "This is a warning!!!")
        else:
            print now_time , 'nginx 进程正常运行中 ... '
        time.sleep(10)
    except KeyboardInterrupt:
        sys.exit('\n')