#!/usr/local/bin/python2.7 
#coding=utf-8

' 待审批及待支付订单列表'
__author__ = 'Alex Wang'             #标准文件模板

import socket
import smtplib 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication
import psycopg2
#import pandas as pd
import logging
from datetime import datetime
import csv
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

        "logfile_path": "/data/cyy928/crontab/log/unproved_order_list.log",
        "attachfile": "/data/cyy928/crontab/export/customercreate_order_list.csv"
    },

    "prod" : {
        "db_name": "cyy_ledgerdb",
        "db_user": "cyyuser",
        "db_pass": "lkkRrrhO",
        "db_ip": "10.10.84.234",

        "logfile_path": "/data/cyy928/crontab/log/unproved_order_list.log",
        "attachfile": "/data/cyy928/crontab/export/customercreate_order_list.csv"
    }
}


# email configurations
hostname = socket.gethostname() 
sender = 'wxgzh@cyy928.com'  
sender_pw = 'Password1'
smtp_server = 'smtp.cyy928.com'
receivers = '044@cyy928.com,xjb460@cyy928.com,ryl479@cyy928.com '  #正式人员
#receivers = 'wxp205@cyy928.com'   #测试人员
attached_file = '/data/cyy928/crontab/export/customercreate_order_list.csv'

# sql execute statement
execute_statement=" SELECT ( SELECT NAME FROM ledger_service.regions WHERE level = 1 AND ID = aoi.province_id ) area, SUM ( CASE examine_status WHEN 'UNPROVED' THEN 1 ELSE 0 END ) 待审批, SUM ( CASE examine_status WHEN 'UNPAID' THEN 1 ELSE 0 END ) 待支付 ,SUM ( CASE examine_status WHEN 'FAILURE' THEN 1 ELSE 0 END) 支付失败 FROM ledger_service.agencies_order_info aoi WHERE aoi.prob_balance_type = 'CASH' AND aoi.request_audit_status IN ('INNER_APPROVED','INNER_FALED') AND examine_status IN ('UNPROVED', 'UNPAID','FAILURE') AND province_id != 0 AND  createtime > to_date('2018-12-01', 'yyyy-mm-dd') AND createtime < CURRENT_DATE  :: TIMESTAMP  GROUP BY province_id,area "


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


def generateCsvFile(filename, rows):
    with open(filename, "w") as csvfile:
        w = csv.DictWriter(csvfile, ['服务商','自建订单总量','执行完成量','取消量','未完成量'])
        w.writeheader()
        for row in rows:
           w.writerow({'服务商':row[0],'自建订单总量':row[1],'执行完成量':row[2],'取消量':row[3],'未完成量':row[4]})
    return
  
def get_df_from_db(sql):
    conn = psycopg2.connect(database=cfg[env]["db_name"],user=cfg[env]["db_user"],password=cfg[env]["db_pass"],host=cfg[env]["db_ip"],port=5432)
    cursor = conn.cursor() 
    cursor.execute(sql)
    data = cursor.fetchall()
    columnDes = cursor.description #获取连接对象的描述信息
    columnNames = [columnDes[i][0] for i in range(len(columnDes))]
    #print(columnNames)
    df = pd.DataFrame([list(i) for i in data],columns=columnNames)        
    return df

def safe_output_rows(sql):
    a = 0
    while a < 5 :
        queuedOrders = fetchQueuedOrders(sql)
        if type(queuedOrders) == list :
            a = 100
        else:
            a += 1
            sendmail("【"  + env.upper()  + "】昨日非现金类客户自解统计查询失败",str(queuedOrders),'wxp205@cyy928.com',0)
            time.sleep(10)
    return queuedOrders

def merge_str(keys):
    #keys是SQL输出的查询结果，以list方式存储
    md_table = ""
    md_key =  {
        "area":"",
        "unproved":"",
        "unpaid":""
        "failure"
        } 
    num = 1  
    for row in keys:
        md_key["area"] = "【**" + row[0] + "**】"
        md_key["unproved"] = "待审批**" + str(row[1]) + "**单"   
        md_key["unpaid"] =  "待支付**" + str(row[2]) + "**单" 
        md_key["failure"] =  "支付失败**" + str(row[3]) + "**单" 
        add_table = str(num) + ". {0},{1},{2},{3}\n\n".format(md_key["area"],md_key["unproved"],md_key["unpaid"],md_key["failure"]) 
        md_table += add_table 
        content = "**待审批/待支付/支付失败现金单积压统计**\n\n------------    \n\n"
        num += 1 
    #str1 = "curl 'https://oapi.dingtalk.com/robot/send?access_token=e15004423e91ab55b79cf2aaea5397d42aa9bed127a1bdc18676de169660e33d' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content + md_table + " \" },\"at\":{ \"isAtAll\": false }}' "   #自建机器人
    str1 = "curl 'https://oapi.dingtalk.com/robot/send?access_token=716d50316a8b0bb52213b86d914d3b15cab4cd410f35b6bfa1bf1e64ec41d941' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content + md_table + " \" },\"at\":{ \"isAtAll\": false }}' "   #服务商跟进
    #str1 = "curl 'https://oapi.dingtalk.com/robot/send?access_token=81619e510b4537c73703db10bc783c0da2c2256fa24c8db7f8224dbad67115f9' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content + md_table + " \" },\"at\":{ \"isAtAll\": false }}' "   #车友援研发部
    #str1 = "curl 'https://oapi.dingtalk.com/robot/send?access_token=db336a98c76d77eec587aa24a213d6059b72cb60e31754b25bb6a0bbc3dee356' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content + md_table + " \" },\"at\":{ \"isAtAll\": false }}' "   #车友援运营处理中心
    return str1    

if __name__ == '__main__':
    #queuedOrders = get_df_from_db(execute_statement)
    queuedOrders = safe_output_rows(execute_statement)
    if type(queuedOrders) == list :               
#         generateCsvFile(cfg[env]["attachfile"], queuedOrders)
#         sendmail("【" + env.upper()  + "】服务商自建订单统计报表",
#                  "自建订单统计报表请见附件", receivers, 1)
        dingding_command =merge_str(queuedOrders)
        #print(dingding_command)
        subprocess.Popen(dingding_command,bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)           
    else :
        sendmail("【"  + env.upper()  + "】服务商自建订单查询失败",str(queuedOrders),receivers,0)






