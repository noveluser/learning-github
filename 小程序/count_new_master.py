#!/usr/local/bin/python2.7 
#coding=utf-8

' 新增服务商/师傅统计'
__author__ = 'Alex Wang'             #标准文件模板

import socket
import smtplib 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication
import psycopg2
import logging
from datetime import datetime
import subprocess
import time


env = "prod"
# multi env configurations 
cfg = {
    "qa" : {
        "db_name": "cyydb_20181213",
        "db_user": "cyyuser",
        "db_pass": "kkz9c7H2",
        "db_ip": "10.10.1.210",

        "logfile_path": "/data/cyy928/crontab/log/monitor_service_order_list.log",
        "attachfile": "/data/cyy928/crontab/export/customercreate_order_list.csv"
    },

    "prod" : {
        "db_name": "cyydb",
        "db_user": "cyyuser",
        "db_pass": "lkkRrrhO",
        "db_ip": "10.10.95.100",

        "logfile_path": "/data/cyy928/crontab/log/monitor_service_order_list.log",
        "attachfile": "/data/cyy928/crontab/export/customercreate_order_list.csv"
    }
}


# email configurations
hostname = socket.gethostname() 
sender = 'wxgzh@cyy928.com'  
sender_pw = 'Password1'
smtp_server = 'smtp.cyy928.com'
#receivers = '044@cyy928.com,xjb460@cyy928.com,ryl479@cyy928.com '  #正式人员
receivers = 'wxp205@cyy928.com'   #测试人员
attached_file = '/data/cyy928/crontab/export/customercreate_order_list.csv'

# sql execute statement

execute_statement1=" SELECT asa.name \"当日新增服务商\",'(' || asp.name || ' 录入)' \"录入\" FROM agency_service.agencies asa INNER JOIN agency_service.persons asp on cast(asa.created_by as int8) = asp.user_id WHERE is_contractee != TRUE AND asa.created_dt >= (CURRENT_DATE - INTERVAL '1 days')::TIMESTAMP AND asa.created_dt < (CURRENT_DATE )::TIMESTAMP AND asp.is_admin = TRUE AND asp.agency_id = 1; "
execute_statement2=" SELECT asa.name , sum(case when asp.is_admin is true then 0 else 1 end) ,sum(case when asp.is_admin is true then 1 else 0 end) FROM agency_service.agencies asa INNER JOIN agency_service.persons asp on asa.id = asp.agency_id WHERE is_contractee != TRUE AND asp.created_dt >= (CURRENT_DATE - INTERVAL '1 days')::TIMESTAMP AND asp.created_dt < (CURRENT_DATE )::TIMESTAMP AND asp.agency_id != 1 GROUP BY asp.agency_id,asa.name ; "


#定义日志输出格式
logging.basicConfig(level=logging.INFO,
        format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = cfg[env]["logfile_path"],
        filemode = 'a')

#发送邮件模块,目前在QQ和163邮箱环境测试成功
def  sendmail(subject, content, receivers, attached_flag):
	smtpserver = smtp_server
	username = sender
	password = sender_pw
        attached_flag = int(attached_flag)
	content = content + "\n\r\n\rFrom " + hostname + " at " + str(datetime.now())
	  
	#msg = MIMEText(context,'plain','utf-8')#中文需参数‘utf-8’，单字节字符不需要  
	msg = MIMEMultipart()
	msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = 'cws监控程序'
        msg['To'] = receivers
	puretext = MIMEText(content)
	msg.attach(puretext) 
        if attached_flag == 1:   #如果标识位为0，那么发送附件，否则不发送      
        	open_file = open(cfg[env]["attachfile"],'rb')	
		part = MIMEApplication(open_file.read())
		part.add_header('Content-Disposition', 'attachment', filename="customercreate_order_list.csv")
       #如果附件名称需要更改，需要在这里调整，另外中文名称乱码问题未解决
		msg.attach(part)  
		open_file.close()

	#smtp = smtplib.SMTP()
	smtp = smtplib.SMTP_SSL(smtpserver, 465) 	
	smtp.connect(smtpserver)  
	smtp.login(username, password)  
	smtp.sendmail(sender, receivers.split(','), msg.as_string())  
	smtp.quit() 
    

def fetchQueuedOrders(sql):
    """
    连接数据库（从），并进行数据查询，如果连接失败，会把错误写入日志中，并返回false，如果sql执行失败，也会把错误写入日志中，并返回false，如果所有执行正常，则返回查询到的数据，这个数据是经过转换的，转成字典格式，方便模板调用，其中字典的key是数据表里的字段名
    """
    try:
        conn = psycopg2.connect(database=cfg[env]["db_name"],user=cfg[env]["db_user"],password=cfg[env]["db_pass"],host=cfg[env]["db_ip"],port=5432)
        cursor = conn.cursor()        
        cursor.execute(sql)
        #data = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]     #转换数据，字典格式
        rows = cursor.fetchall()
        logging.info("数据查询成功:%s" % rows)
        #print(rows[0][0])
    except Exception,e:
        logging.error('数据查询失败:%s' % e)        
        return e
    finally:
        cursor.close()
        conn.close()
    return rows

def safe_output_rows(sql):
    a = 0
    while a < 5 :
        queuedOrders = fetchQueuedOrders(sql)
        if type(queuedOrders) == list :
            a = 100
        else:
            a += 1
            sendmail("【"  + env.upper()  + "】昨日调度订单量查询失败",str(queuedOrders),'wxp205@cyy928.com',0)
            time.sleep(10)
    return queuedOrders

def merge_str2(keys):
    #keys是SQL输出的查询结果，以list方式存储
    md_table = ""
    md_key =  {
        "master":"",
        "master_number":"",
        "admin_number":""
        } 
    num = 1
    master_number = 0
    for row in keys:
        md_key["master"] = "**" + row[0] + "**"
        md_key["master_number"] = "师傅**" + str(row[1]) + "**人"
        md_key["admin_nmuber"] = "管理账号**" + str(row[2]) + "**人"        
        master_number += row[1]
        add_table = str(num) + ". {0} {1},{2}\n\n".format(md_key["master"],md_key["master_number"],md_key["admin_nmuber"]) 
        md_table += add_table         
        num += 1
    title = "---------------    \n\n昨日新增师傅**" + str(master_number) + "**人\n\n------------    \n\n" 
    str1 = title + md_table
    return str1  

def merge_str1(keys):
    #keys是SQL输出的查询结果，以list方式存储
    md_table = ""
    md_key =  {
        "provider":"",
        "recorder":""
        } 
    num = 1
    for row in keys:
        md_key["provider"] = "**" + row[0] + "**"
        md_key["recorder"] = row[1]        
        add_table = str(num) + ". {0}{1}\n\n".format(md_key["provider"],md_key["recorder"]) 
        md_table += add_table         
        num += 1
    title = "昨日新增服务商**" + str(len(keys)) +"**家\n\n------------    \n\n"
    str1 = title + md_table
    return str1      

if __name__ == '__main__':
    queuedOrders = safe_output_rows(execute_statement1)
    if type(queuedOrders) == list :              
        content1 =merge_str1(queuedOrders)
    else :
         sendmail("【"  + env.upper()  + "】服务商自建订单查询失败",str(queuedOrders),receivers,0)

    queuedOrders = safe_output_rows(execute_statement2)
    if type(queuedOrders) == list :              
        content2 =merge_str2(queuedOrders)
    else :
         sendmail("【"  + env.upper()  + "】服务商自建订单查询失败",str(queuedOrders),receivers,0)
    #dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=e15004423e91ab55b79cf2aaea5397d42aa9bed127a1bdc18676de169660e33d' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content1 + content2 + " \" },\"at\":{ \"isAtAll\": false }}' "   #自建机器人
    #dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=81619e510b4537c73703db10bc783c0da2c2256fa24c8db7f8224dbad67115f9' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content1 +content2 + " \" },\"at\":{ \"isAtAll\": false }}' "   #车友援研发部
    #dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=db336a98c76d77eec587aa24a213d6059b72cb60e31754b25bb6a0bbc3dee356' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content1 +content2 + " \" },\"at\":{ \"isAtAll\": false }}' "   #车友援运营处理中心
    dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=716d50316a8b0bb52213b86d914d3b15cab4cd410f35b6bfa1bf1e64ec41d941' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content1 +content2 + " \" },\"at\":{ \"isAtAll\": false }}' "   #服务商跟进
    subprocess.Popen(dingding_command,bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)           






