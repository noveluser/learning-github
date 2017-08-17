# -*- coding: utf-8 -*-
#!/usr/bin/env python

' a restart scription when cws halt'
__author__ = 'Alex Wang'

import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import commands
import time
from datetime import datetime

def cws_restart():
    status=commands.getstatusoutput('/data/wang/stop.sh')
    #print status
    time.sleep(1)
    status=commands.getstatusoutput('/data/wang/startup.sh')
    #print status
    return

def log(t,context):
    f = open(log_file,"a+")
    f.write(str(t)+context+'\n')
    f.close()
    return


def sendmail():
    command_content='echo -e "`hostname` 已经自动重启，请确定服务状态，重启时间：这是一封自动邮件，请不要回复" | mail -s "`hostname`重启报告邮件"  wxp205@cyy928.com'
    commands.getstatusoutput(command_content)
    return

def check_restart():
     f = open(check_file,"r")
     flag=f.read()
     f.close()
     if int(flag) == 0:
         cws_restart()
         f2 = open(check_file,"w")
         f2.write('2')
         f2.close()
         log(t,'服务器检测不正常，已重启')
     else:
         log(t,'服务器已经在1小时内重启过,无需再重启')
     return



log_file="/data/wang/9000_status.txt"
check_file="/data/wang/cws_9000_status.txt"
#url="http://:120.132.50.181:9090/api/misc/db/test/334834"
url="http://123.59.53.69:9000/api/misc/db/test/334834"
t=datetime.now()

try:
    url_status = requests.get(url,timeout=0.002)
    log(t,'服务器检测正常')
    print(url_status.status_code)

except ReadTimeout:
    print('Timeout')
    if __name__=='__main__':
        check_restart()
    sendmail()
 
except ConnectionError:
    print('Connection error')
    log(t,context='Connection error.服务器检测不正常')

except RequestException:
    print('Error')
    log(t,context='Error.服务器检测不正常')

