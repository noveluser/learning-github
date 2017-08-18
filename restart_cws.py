#!/usr/local/bin/python2.7      
#coding=utf-8

' a restart scription when cws halt'
__author__ = 'Alex Wang'             #标准文件模板

import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import commands
import time
from datetime import datetime

def cws_restart(path):     #运行shell重启脚本
    status=commands.getstatusoutput(path+'stop_'+port+'.sh')
    #print status
    time.sleep(1)
    status=commands.getstatusoutput(path+'startup_'+port+'.sh')
    #print status
    return         #return是标准函数最后一句

def log(file,context):     #log记录函数
    current_time=datetime.now()
    f = open(file,"a+")
    f.write(str(current_time)+context+'\n')
    f.close()
    return


def sendmail():           #邮件函数，暂时用shell写，后面再换成python
    command_content='echo -e "`hostname` 已经自动重启，请确定服务状态，重启时间：这是一封自动邮件，请不要回复" | mail -s "`hostname`重启报告邮件"  wxp205@cyy928.com'
    commands.getstatusoutput(command_content)
    return

def check_restart(log_file,check_file,port):    #检查是否已经重启过的函数，如果已经重启过，则跳过重启函数
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
	 
def check_url(port):               #判断URL是否超时，
    log_file=path1+"cws_"+port+"_status.log"     #日志文件绝对路径
    check_file=path1+port+"_status.txt"       #设置重启标志的文件，如果重启，那么完成后写入重启标志1
    url="http://123.59.53.69:"+port+"/api/misc/db/test/334834"       #检测URL路径
    cws_status = 0
    try:
        url_status = requests.get(url,timeout=1.002)
        log(log_file,'服务器检测正常')
        print(url_status.status_code)
    except ReadTimeout:
        print('Timeout')
        cws_status = 1       #超时状态标志为1
 
    except ConnectionError:
        print('Connection error')
        log(log_file,context='Connection error.服务器检测不正常')

    except RequestException:
        print('Error')
        log(log_file,context='Error.服务器检测不正常')
    if cws_status == 1:           #如果超时，那么进入重启模块
        if __name__=='__main__':
            check_restart(log_file,check_file,port)
            t=datetime.now()
	    print(t,cws_status,log_file,check_file)
        sendmail()	
    return 

ports=['9000','9090']
path1="/data/cyy928/crond/"    #监控程序所在目录
n=1
#url="http://:120.132.50.181:9090/api/misc/db/test/334834"
#url="http://123.59.53.69:9000/api/misc/db/test/334834"       #检测URL路径


while n<10000:
    for port in ports:
	if __name__=='__main__':    
	    check_url(port)
    time.sleep(60)
    n=n+1
	
