#!/usr/local/bin/python2.7 
#coding=utf-8

' check db activition'
__author__ = 'Alex Wang'             #标准文件模板

import socket
import smtplib 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication
import psycopg2
import time
from datetime import datetime

def  sendmail(warning,context,receivers,attached_flag):        #发送邮件模块
	sender = 'wxgzh@cyy928.com'  
	receivers = receivers  
	subject = warning  
	smtpserver = 'smtp.cyy928.com'  
	username = sender  
	password = 'Password1'
        attached_flag = int(attached_flag)
	context=context+" From "+hostname+" at "+str(datetime.now())
	  
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


def log(file,context):     #log记录函数
    current_time=datetime.now()
    f = open(file,"a+")
    f.write(str(current_time)+"  "+str(context)+'\n')
    f.close()
    return
    


def  check_db_activity():
   conn = psycopg2.connect(database="cyy_insurdb", user="cyyuser",password="lkkRrrhO", host="10.10.38.29")
   #conn = psycopg2.connect(database="cyy_insurdb", user="cyyuser",password="kkz9c7H2", host="10.10.1.210")
   cur = conn.cursor()
   cur.execute("SELECT count(1) FROM car_service.insurance_orders WHERE created_dt <= CURRENT_TIMESTAMP - INTERVAL '5 min' AND process_status = 'QUEUED';")
   rows = cur.fetchone()
   result=rows[0]
   log(log_file,'expire order:'+str(result))
   #print result
   conn.close()
   return result
   
def  expire_order():
   conn = psycopg2.connect(database="cyy_insurdb", user="cyyuser",password="lkkRrrhO", host="10.10.38.29")
   #conn = psycopg2.connect(database="cyy_insurdb", user="cyyuser",password="kkz9c7H2", host="10.10.1.210")
   cur = conn.cursor()
   cur.execute("SELECT * FROM car_service.insurance_orders WHERE created_dt <= CURRENT_TIMESTAMP - INTERVAL '5 min' AND process_status = 'QUEUED';")
   rows = cur.fetchall()
   for each in rows:
       rows[each]=str(rows[each])
       print rows[each]
   result=''.join(rows)
   # for each in rows:
      # result=''
      # result += str(each)
   log(log_file,result)
   #print result
   conn.close()
   return result

hostname =socket.gethostname() 
log_file='/data/cyy928/crontab/monitor_db_insurdb.log'
#receivers='044@cyy928.com,wxp205@cyy928.com,wxm228@cyy928.com'
receivers='wxp205@cyy928.com,wxm228@cyy928.com'
n = 1
total_sendtime=0
last_checktime=time.time()
while n < 4 :
    check_result=check_db_activity()
    if check_result > 0:
      expire_order_detail=expire_order()
      current_checktime=time.time()
      duration_checktime=current_checktime-last_checktime 
      last_checktime=current_checktime      
      if duration_checktime <120 :
          total_sendtime=total_sendtime+1          
      else :
          total_sendtime=0      
      total_sendtime=10   #测试语句
      if total_sendtime ==0 :
           #print "ok"
           sendmail("【保险公司网关】订单解析异常","warning  "+str(check_result)+'个过期订单未处理'+'\n'+expire_order_detail,receivers,0)
      elif total_sendtime ==1 :
           sendmail("【保险公司网关】订单解析异常","the second warning  "+str(check_result)+'个过期订单未处理'+'\n'+expire_order_detail,receivers,0)
      elif total_sendtime ==2 :
           sendmail("【保险公司网关】订单解析异常","！！！the final warning  "+str(check_result)+"个过期订单未处理"+'\n'+expire_order_detail,receivers,0)     
      else :
          log(log_file,'send too many mails in a short time')
      #print duration_checktime
      #print total_sendtime

    n = n+1
    time.sleep(60)
