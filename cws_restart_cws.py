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
	sender = 'flywangle@163.com'  
	receivers = receivers  
	subject = hostname+warning  
	smtpserver = 'smtp.163.com'  
	username = sender  
	password = 'stone1'
        attached_flag = int(attached_flag)
	context=hostname+"  "+str(datetime.now())+"  "+context
	  
	#msg = MIMEText(context,'plain','utf-8')#中文需参数‘utf-8’，单字节字符不需要  
	msg = MIMEMultipart()
	msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = 'wangle<flywangle@163.com>'
        msg['To'] = receivers
	puretext = MIMEText(context)
	msg.attach(puretext) 
        if attached_flag == 1:   #如果标识位为0，那么发送附件，否则不发送      
        	play_status_file=open('/data/cyy928/logs/play_status.log','rb')	
		part =MIMEApplication(play_status_file.read())
		part.add_header('Content-Disposition', 'attachment', filename="play_status.log")
		msg.attach(part)  
		play_status_file.close()
	smtp = smtplib.SMTP()  
	smtp.connect(smtpserver)  
	smtp.login(username, password)  
	smtp.sendmail(sender, receivers.split(','), msg.as_string())  
	smtp.quit() 
        return

def command_run(command,timeout,path):
    proc = subprocess.Popen(command,bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,cwd=path)
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and proc.poll() == None:
        time.sleep(poll_seconds)
    if proc.poll() == None:
        if float(sys.version[:3]) >= 2.6:
            proc.terminate()

    stdout,stderr = proc.communicate()

    return stdout,stderr,proc.returncode

	
def cws_restart(path):     #运行shell重启脚本    
        if port == '9000':
		cws_path="/data/cyy928/cws1"
		print cws_path
	if port == '9090':
		cws_path="/data/cyy928/cws2"
		print cws_path
	if port == '9093':
		cws_path="/data/cyy928/cws3"
		print cws_path   
    	play_status='/data/package/play-1.4.2/play status --url http://127.0.0.1:'+port+' > /data/cyy928/logs/play_status.log'
	command_status=command_run(play_status,10,cws_path)
	log(path+'cws_'+port+'_status.log',str(command_status),'命令输出结果')
	status=os.system(path+'stop_'+port+'.sh')
    	time.sleep(1)
    	status=os.system(path+'startup_'+port+'.sh')
    	# status=commands.getstatusoutput(path+'startup_'+port+'.sh')
    	#print status
    	return         #return是标准函数最后一句

def log(file,context,respondtime):     #log记录函数
    current_time=datetime.now()
    f = open(file,"a+")
    f.write(str(current_time)+str(context)+respondtime+'\n')
    f.close()
    return
	

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
    cws_status1 = 0      # 初始值为0表示正常，为1表示有异常，如果两个都为1，表明版本更新，不重启
    db_url="http://127.0.0.1:"+port+"/api/misc/db/test/334834"       #检测URL路径
    #url="http://127.0.0.1:"+port+"/api/dispatch/238848/persons?authToken=176ed33052b1fed902319090b27260baa2066cfe%239076&appID=d18b6732881d7e04e665e3eb761861db03b5f06c&secretKey=98da99443c76c483a48904ac70af7c42&agency-id=1"       #检测URL路径
    
    start_time=time.time()*1000
    try:
        url_status = requests.get(db_url,timeout=4.002)
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,'服务器检测正常,反应时间为  ',duration_time )
        #sendmail('test','test',receivers,1)
    except ReadTimeout as f:
        print('readtime out')
        cws_status1 = 1       #超时状态标志为1
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,f,'readtimeout反应时间 '+duration_time)
        sendmail('服务器有异常',str(f)+'\n'+'反应时间 '+duration_time,receiver1,0)
    except ConnectionError as f:
	cws_status1 = 1
        print('Connection error')
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,f,'connectError反应时间 '+duration_time)
        sendmail('服务器有异常',str(f),receiver1,0)
    except RequestException as f:
        print('Error')
        end_time=time.time()*1000
        duration_time=str(end_time-start_time)
        log(log_file,f,'Exception反应时间 '+duration_time)
        sendmail('服务器有异常',str(f),receiver1,0)

    count=1
    cws_status2 = 0
    while count <3 :
    
          api_url="http://127.0.0.1:"+port+"/api/dispatch/238848/persons?authToken=176ed33052b1fed902319090b27260baa2066cfe%239076&appID=d18b6732881d7e04e665e3eb761861db03b5f06c&secretKey=98da99443c76c483a48904ac70af7c42&agency-id=1"       #检测URL路径
          start_time=time.time()*1000
          try:
              url_status = requests.get(api_url,timeout=5.002)
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,'API服务检测正常,反应时间为  ',duration_time )
              #sendmail('test','test',receivers,1)
          except ReadTimeout as f:
      	      cws_status2 = cws_status2+1
              print('readtime out')
              end_time=time.time()*1000
              duration_time=str(end_time-start_time)
              log(log_file,f,'API readtimeout反应时间 '+duration_time)
              sendmail('API服务有异常',str(f)+'\n'+'反应时间 '+duration_time,receivers,0)
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
    cws_status=cws_status2
    if cws_status == 2:           #如果连续超时，那么进入重启模块
        if __name__=='__main__':
            check_restart(log_file,check_file,port)
        t=datetime.now()
	print(t,cws_status,log_file,check_file)
        
    return
	
hostname =socket.gethostname() 
ports=['9000','9090','9093']
path1="/data/cyy928/crontab/"    #监控程序所在目录
receiver1='wxp205@cyy928.com'
receivers='044@cyy928.com,wxp205@cyy928.com,pc338@cyy928.com'
#url="http://:120.132.50.181:9090/api/misc/db/test/334834"
#url="http://123.59.53.69:9000/api/misc/db/test/334834"       #检测URL路径
n = 1
while n <1430 :
    for port in ports:
        if __name__=='__main__':    
	    check_url(port)
    n = n+1
