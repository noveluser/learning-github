#!/usr/local/bin/python2.7      
#coding=utf-8

' a restart scription when cws halt'
__author__ = 'Alex Wang'             #标准文件模板

import os
import subprocess
import socket
import smtplib  
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication
import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import time
from datetime import datetime


def  sendmail(warning,context,receivers,attached_flag):        #发送邮件模块
	sender = 'wxgzh@cyy928.com'  
	receivers = receivers  
	subject = hostname+" "+warning  
	smtpserver = 'smtp.cyy928.com'  
	username = sender  
	password = 'Password1'
        attached_flag = int(attached_flag)
        context="From "+hostname+" at "+str(datetime.now())+" "+context

	#msg = MIMEText(context,'plain','utf-8')#中文需参数‘utf-8’，单字节字符不需要  
	msg = MIMEMultipart()
	msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = 'cws监控<wxgzh@cyy928.com>'
        msg['To'] = receivers
	puretext = MIMEText(context)
	msg.attach(puretext) 
        if attached_flag == 1:   #如果标识位为0，那么发送附件，否则不发送      
        	play_status_file=open('/data/cyy928/logs/play_status.log','rb')	
		part =MIMEApplication(play_status_file.read())
		part.add_header('Content-Disposition', 'attachment', filename="play_status.log")
		msg.attach(part)  
		play_status_file.close()
	#smtp = smtplib.SMTP()
	smtp = smtplib.SMTP_SSL(smtpserver, 465) 	
	smtp.connect(smtpserver)  
	smtp.login(username, password)  
	smtp.sendmail(sender, receivers.split(','), msg.as_string())  
	smtp.quit() 
        return


def locate_cws_path(port):                    #定位cws节点的路径
    # if port == '9000':
		# cws_path="/data/cyy928/cws1"
    if port == '9001':
		cws_path="/data/cyy928/cwsserver/cws1"
    if port == '9002':
		cws_path="/data/cyy928/cwsserver/cws2"  
    return cws_path

	
def cws_restart(path):     #运行shell重启脚本    
    	status=os.system(path+'startup_'+port+'.sh')
    	return         #return是标准函数最后一句


def log(file,context,respondtime):     #log记录函数
    current_time=datetime.now()
    f = open(file,"a+")
    f.write(str(current_time)+" "+str(context)+" "+respondtime+'\n')
    f.close()
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
         log(log_file,'服务器检测不正常','已重启')
 	 sendmail('服务器重启','重启',receivers,1)
	 #time.sleep(10)
	 subprocess.Popen('echo '' > play_status.log ',bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,cwd='/data/cyy928/logs/')
         log(log_file,'已重置play_status数据','clear play_status')
     else:
         log(log_file,'服务器已经在1小时内重启过,','无需再重启')
     return
	 
def check_url(port):               #判断URL是否超时，
    log_file=path1+"cws_"+port+"_status.log"     #日志文件绝对路径
    check_file=path1+port+"_status.txt"       #设置重启标志的文件，如果重启，那么完成后写入重启标志1
    count=1
    cws_status = 0
    api_url="http://127.0.0.1:"+port+"/api/dispatch/238848/persons?authToken=176ed33052b1fed902319090b27260baa2066cfe%239076&appID=d18b6732881d7e04e665e3eb761861db03b5f06c&secretKey=98da99443c76c483a48904ac70af7c42&agency-id=1"       #检测URL路径
    while count <3 : 
          try:
              start_time=time.time()*1000
	      url_status = requests.get(api_url,timeout=5.002)
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,'API服务检测正常,反应时间为  ',duration_time+"毫秒" )
              #sendmail('test','test',receivers,1)
          except ReadTimeout as f:
      	      cws_status = cws_status+1
              print('readtime out')
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,f,'API readtimeout反应时间 '+duration_time)
              sendmail('API服务有异常',str(f)+'\n'+'反应时间 '+duration_time,receiver1,0)
          except ConnectionError as f:
              #cws_status2 = 1       #超时状态标志为1
              print('Connection error')
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,f,'APIconnectError反应时间 '+duration_time)
              sendmail('API服务器有异常',str(f),receiver1,0)
          except RequestException as f:
              print('Error')
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,f,'API Exception反应时间 '+duration_time)
              sendmail('API服务器有异常',str(f),receiver1,0)
          count=count+1
          time.sleep(10)
    restart_status=False
    #cws_status =2    #测试语句
    if cws_status == 2:           #如果连续超时，那么进入active检测模块
            cws_path=locate_cws_path(port)
	    play_status='/data/package/play-1.4.2/play status --url http://127.0.0.1:'+port+' > /data/cyy928/logs/play_status.log'
	    subprocess.Popen(play_status,bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,cwd=cws_path)
	    check_restart(log_file,check_file,port)
        
    return
	
hostname =socket.gethostname() 
#ports=['9090']
ports=['9001','9002']
path1="/data/cyy928/crontab/"    #监控程序所在目录
receiver1='wxp205@cyy928.com'
#receivers='wxp205@cyy928.com'
receivers='044@cyy928.com,wxp205@cyy928.com'

n = 1
while n < 720 :
    for port in ports:
        if __name__=='__main__':    
	    check_url(port)
    n = n+1
    time.sleep(20)
