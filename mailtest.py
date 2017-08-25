#!/usr/local/bin/python2.7      
#coding=utf-8

' a mail test program'
__author__ = 'Alex Wang'  

import smtplib  
from email.mime.text import MIMEText  
from email.header import Header  

def  sendmail():  
	sender = 'kilner1@163.com'  
	receiver = 'wxp205@cyy928.com'  
	subject = 'python email test'  
	smtpserver = 'smtp.163.com'  
	username = 'kilner1@163.com'  
	password = 'stone1'  
	  
	msg = MIMEText('你好','text','utf-8')#中文需参数‘utf-8’，单字节字符不需要  
	msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = 'wangle<kilner1@163.com>'
        msg['To'] = 'wxp205@cyy928.com'
        #smtp = smtplib.SMTP(smtpserver,25)

        #smtp.set_debuglevel(1)  
	  
	smtp = smtplib.SMTP()  
	smtp.connect('smtp.163.com')  
	smtp.login(username, password)  
	smtp.sendmail(sender, receiver, msg.as_string())  
	smtp.quit()  
	return

if __name__=='__main__': 
    sendmail()

