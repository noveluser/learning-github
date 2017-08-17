#!/usr/local/bin/python2.7
#coding=utf-8

' a restart scription when cws halt'
__author__ = 'Alex Wang'

import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import commands
import time
from datetime import datetime

def cws_restart(path):
    status=commands.getstatusoutput(path+'stop_9000.sh')
    #print status
    time.sleep(1)
    status=commands.getstatusoutput(path+'startup_9000.sh')
    #print status
    return

def log(file,context):
    f = open(file,"a+")
    f.write(str(t)+context+'\n')
    f.close()
    return


def sendmail():
    command_content='echo -e "`hostname` 已经自动重启，请确定服务状态，重启时间：这是一封自动邮件，请不要回复" | mail -s "`hostname`重启报告邮件"  wxp205@cyy928.com'
    commands.getstatusoutput(command_content)
    return

def check_restart(log_file,check_file):
     f = open(check_file,"r")
     flag=f.read()
     f.close()
     if int(flag) == 0:
         cws_restart(path1)
         f2 = open(check_file,"w")
         f2.write('2')
         f2.close()
         log(log_file,'服务器检测不正常，已重启')
     else:
         log(log_file,'服务器已经在1小时内重启过,无需再重启')
     return


path1="/data/cyy928/crond/"    #监控程序所在目录
log_file=path1+"cws_9000_status.log"
check_file=path1+"9000_status.txt"
#url="http://:120.132.50.181:9090/api/misc/db/test/334834"
url="http://123.59.53.69:9000/api/misc/db/test/334834"
t=datetime.now()

try:
    url_status = requests.get(url,timeout=1.002)
    log(log_file,'服务器检测正常')
    print(url_status.status_code)
    cws_status = 0
except ReadTimeout:
    print('Timeout')
    cws_status = 1
 
except ConnectionError:
    print('Connection error')
    log(log_file,context='Connection error.服务器检测不正常')

except RequestException:
    print('Error')
    log(log_file,context='Error.服务器检测不正常')

if cws_status == 1:
    if __name__=='__main__':
        check_restart(log_file,check_file)
    print(cws_status)
    sendmail()
