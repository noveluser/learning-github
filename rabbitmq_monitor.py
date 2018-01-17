#!/usr/bin/python 
#coding=utf-8

' a rabbitmq-server monitor scription'
__author__ = 'Alex Wang'             #标准文件模板

import os
import socket
import smtplib  
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication
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



	
def mq_restart():     #运行shell重启脚本    
   
    	#os.system('service rabbitmq-server restart')
	log(log_file,'服务器检测不正常','已重启')
	return         #return是标准函数最后一句

def log(file,context,respondtime):     #log记录函数
    current_time=datetime.now()
    f = open(file,"a+")
    f.write(str(current_time)+str(context)+respondtime+'\n')
    f.close()
    return

def IsOpen(ip,port):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.connect((ip,int(port)))
        s.shutdown(2)
        print '%d is open' % port
	log(log_file,'MQ服务检测正常 ','正常')
        return True
    except:
        print '%d is down' % port
	return False
	


	
hostname =socket.gethostname() 
port=5673
path1="/data/package/crontab/"    #监控程序所在目录
receiver1='wxp205@cyy928.com'
receivers='044@cyy928.com,wxp205@cyy928.com,pc338@cyy928.com'
log_file=path1+"mq_status.log"
#url="http://:120.132.50.181:9090/api/misc/db/test/334834"
#url="http://123.59.53.69:9000/api/misc/db/test/334834"       #检测URL路径
if __name__=='__main__':
    n=1
    while(n<2):
        flag=1
        IsOpen('127.0.0.1',port)
        time.sleep(1)
        flag=IsOpen('127.0.0.1',port)
        print flag
        if flag==False:
            #print '服务被关闭' % port
            mq_restart()
	    sendmail('MQ服务器有异常',' 已重启 ',receiver1,0)
        n=n+1

