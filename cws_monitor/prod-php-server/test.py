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


def  sendmail(warning,context,receivers,attached_flag):        
	sender = 'wxgzh@cyy928.com'  
	receivers = receivers  
	subject = hostname+warning  
	smtpserver = 'smtp.cyy928.com'  
	username = sender  
	password = 'Password1'
        attached_flag = int(attached_flag)
	context=hostname+"  "+str(datetime.now())+"  "+context
	  
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
	smtp = smtplib.SMTP_SSL(smtpserver, 465)
	smtp.connect(smtpserver)  
	smtp.login(username, password)  
	smtp.sendmail(sender, receivers.split(','), msg.as_string())  
	smtp.quit() 
        return

def kill_process(key):
    log_file=path1+"cws_"+port+"_status.log"     #日志文件绝对路径
    lines = os.popen('ps -ef|grep '+key) 
    for line in lines:       
        if line.find('grep '+key)!=-1: continue
        
        vars = line.split()
        pid = vars[1] #get pid
        proc = ''.join(vars[7:]) #get proc description
        
        out = os.system('kill '+pid)
        if out==0:
            log(log_file,'success! kill '+pid+'  ',proc)
        else:
            log(log_file,'failed! kill '+pid+'  ',proc)


def locate_cws_path(port):
    if port == '9003':
		cws_path="/data/cyy928/cwsserver/cws"  
    return cws_path

	
def cws_restart(path):     #运行shell重启脚本    
       	status=os.system(path+'stop_'+port+'.sh')
        kill_process('cwsserver')
    	time.sleep(1)
    	status=os.system(path+'startup_'+port+'.sh')
        time.sleep(5)
        status=os.system(path+'stop_'+port+'.sh')
    	time.sleep(1)
    	status=os.system(path+'startup_'+port+'.sh')

    	return         #return是标准函数最后一句


def log(file,context,respondtime):     #log记录函数
    current_time=datetime.now()
    f = open(file,"a+")
    f.write(str(current_time)+str(context)+respondtime+'\n')
    f.close()
    return

def search_keyword(file):
        t=file
	restart_status=False
	with open(t,'r') as f:
            active_count_result='0'
            lines = f.readlines()
            for x in lines:
                if x.startswith('Active count'):
                    #a.extend([x.strip().split()[0], lines.index(x),])
                    active_count_result = x.split(':')[1]       #还要考虑active搜索不到，文件为空的情况
                else :
 		    restart_status=True     #play_status.log文件找不到active count,状态文件未能输出，那么也重启
		if int(active_count_result) > 10:
                    restart_status=True     #active count结果大于180
	    	    #print ('active count is %s' % active_count_result)
   	    sendmail('PLAY STATUS检测结果','active count='+active_count_result,receiver1,0)
        return restart_status	


def check_restart(log_file,check_file,port):    #检查是否已经重启过的函数，如果已经重启过，则跳过重启函数
     f = open(check_file,"r")
     flag=f.read()
     f.close()
     
     try:
        start_time=time.time()*1000
        check_networkcard_status = requests.get("http://localhost:10001/nginx_status",timeout=5.002)
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,'网卡检测正常,反应时间为  ',duration_time )
     except ReadTimeout as f:
        print('readtime out')
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,f,'网卡反应时间 '+duration_time)
     except ConnectionError as f:
        print('Connection error')
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,f,'网卡反应时间 '+duration_time)

     except RequestException as f:
        print('Error')
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,f,'网卡反应时间 '+duration_time)

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
    api_url="http://127.0.0.1:"+port+"/api/dispatch/896260/persons?authToken=176ed33052b1fed902319090b27260baa2066cfe%239076&appID=d18b6732881d7e04e665e3eb761861db03b5f06c&secretKey=98da99443c76c483a48904ac70af7c42&agency-id=1"       #检测URL路径
    while count <3 : 
          try:
              start_time=time.time()*1000
	      url_status = requests.get(api_url,timeout=5.002)
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,'report服务检测正常,反应时间为  ',duration_time )
              #sendmail('test','test',receivers,1)
          except ReadTimeout as f:
      	      cws_status = cws_status+1
              print('readtime out')
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,f,'report readtimeout反应时间 '+duration_time)
              sendmail('重要！！！report服务有异常',str(f)+'\n'+'反应时间 '+duration_time,receiver1,0)
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
          time.sleep(20)
    restart_status=False
    #cws_status =2    #测试语句
    if cws_status == 2:           #如果连续超时，那么进入active检测模块
            cws_path=locate_cws_path(port)
            play_status='/data/package/play-1.4.2/play status --url http://127.0.0.1:'+port+' > /data/cyy928/logs/play_status.log'
            subprocess.Popen(play_status,bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,cwd=cws_path)
	    restart_status=search_keyword('/data/cyy928/logs/play_status.log')
    if restart_status :           #如果active count>180,那么进入重启模块
	    check_restart(log_file,check_file,port)
    t=datetime.now()
    print(t,cws_status,log_file,check_file)
        
    return
	
hostname =socket.gethostname() 
#ports=['9000']
ports=['9003']
path1="/data/cyy928/crontab/"    #监控程序所在目录
receiver1='wxp205@cyy928.com'
#receivers='wxp205@cyy928.com'
receivers='044@cyy928.com,wxp205@cyy928.com'

n = 1
while n <720 :
    for port in ports:
        if __name__=='__main__':    
	    check_url(port)
    n = n+1
    log(path1+'2.txt','命令输出结果',str(n))
    time.sleep(20)
