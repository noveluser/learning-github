#!/usr/local/bin/python2.7 
#coding=utf-8

' 客诉周报'
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

        "logfile_path": "/data/cyy928/crontab/log/customer_complain_list.log",
        "attachfile": "/data/cyy928/crontab/export/customercreate_order_list.csv"
    },

    "prod" : {
        "db_name": "cyydb",
        "db_user": "cyyuser",
        "db_pass": "lkkRrrhO",
        "db_ip": "10.10.95.100",

        "logfile_path": "/data/cyy928/crontab/log/customer_complain_list.log",
        "attachfile": "/data/cyy928/crontab/export/customer_complain_list.csv"
    }
}


# email configurations
hostname = socket.gethostname() 
sender = 'wxgzh@cyy928.com'  
sender_pw = 'Password1'
smtp_server = 'smtp.cyy928.com'
receivers = '044@cyy928.com, wxp205@cyy928.com, hl421@cyy928.com, hpx441@cyy928.com, ryl479@cyy928.com,wg270@cyy928.com,ld203@cyy928.com,lfy161@cyy928.com,zyp232@cyy928.com'  #正式人员
#receivers = 'wxp205@cyy928.com'   #测试人员
attached_file = '/data/cyy928/crontab/export/customer_complain_list.csv'

# sql execute statement
execute_statement=" WITH rel_order AS ( SELECT DISTINCT req_id FROM car_service.service_request_activities WHERE ACTION IN ( 'TO_COMPLAINT', 'UPGRADE_COMPLAINT', 'CANCEL_COMPLAINT' ) AND created_dt >= (CURRENT_DATE - INTERVAL '7 days' ) :: TIMESTAMP AND created_dt < CURRENT_DATE :: TIMESTAMP ), rel_action AS ( SELECT req_id, SUM ( CASE ACTION WHEN 'TO_COMPLAINT' THEN 1 ELSE 0 END ) AS T, SUM ( CASE ACTION WHEN 'UPGRADE_COMPLAINT' THEN 1 ELSE 0 END ) AS u, SUM ( CASE ACTION WHEN 'CANCEL_COMPLAINT' THEN 1 ELSE 0 END ) AS C FROM ( SELECT DISTINCT req_id, ACTION FROM car_service.service_request_activities WHERE ACTION IN ( 'TO_COMPLAINT', 'UPGRADE_COMPLAINT', 'CANCEL_COMPLAINT' ) AND created_dt >= (CURRENT_DATE - INTERVAL '7 days' ) :: TIMESTAMP AND created_dt < (CURRENT_DATE ) :: TIMESTAMP ) dis_activi GROUP BY req_id ), grp_cl AS ( SELECT gs.name, sr. ID, sr.complaints_level FROM car_service.service_request_groups srg, rel_order ro, car_service.service_reqs sr, security_service.groups gs WHERE srg.request_id = ro.req_id AND sr. ID = ro.req_id AND group_id != 1003 AND  srg.group_id = gs. ID ) SELECT NAME, SUM (T) 意向投诉单量, SUM (u) 升级单量, SUM (C) 取消单量, SUM ( CASE WHEN complaints_level IS NOT NULL AND complaints_level NOT IN ('Z', 'U') THEN 1 ELSE 0 END ) 真实投诉发生量 FROM grp_cl, rel_action WHERE grp_cl. ID = rel_action.req_id GROUP BY NAME "


#定义日志输出格式
logging.basicConfig(level=logging.INFO,
        format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = cfg[env]["logfile_path"],
        filemode = 'a')

#发送邮件模块,目前在QQ和163邮箱环境测试成功
def sendmail(subject, content, receivers, attached_flag):
    smtpserver = smtp_server
    username = sender
    password = sender_pw
    attached_flag = int(attached_flag)
    content = content + "\n\r\n\rFrom " + hostname + " at " + str(datetime.now())
    msg = MIMEMultipart()
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = 'cws监控程序'
    msg['To'] = receivers
    puretext = MIMEText(content)
    msg.attach(puretext) 
    if attached_flag == 1:   #如果标识位为0，那么发送附件，否则不发送       
        AttachedFileName = 'weekly_customer_complain_report' + time.strftime('%Y%m%d',time.localtime(time.time())) + '.csv'         
        att = MIMEText(open(cfg[env]["attachfile"],'rb').read(), "base64", "utf-8")
        att["Content-Type"] = "application/octet-stream"
        att["Content-Disposition"] = 'attachment; filename=%s' % AttachedFileName.decode('utf-8').encode('gbk')
        msg.attach(att)
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
        w = csv.DictWriter(csvfile, ['调度中心','意向投诉单量','升级单量','取消量','真实投诉量'])
        w.writeheader()
        for row in rows:
           w.writerow({'调度中心':row[0],'意向投诉单量':row[1],'升级单量':row[2],'取消量':row[3],'真实投诉量':row[4]})
    return
  
def safe_output_rows(sql):
    a = 0
    while a < 5 :
        queuedOrders = fetchQueuedOrders(sql)
        if type(queuedOrders) == list :
            a = 100
        else:
            a += 1
            sendmail("【"  + env.upper()  + "】投诉单查询失败",str(queuedOrders),'wxp205@cyy928.com',0)
            time.sleep(10)
    return queuedOrders
    

if __name__ == '__main__':
    #queuedOrders = get_df_from_db(execute_statement)
    queuedOrders = safe_output_rows(execute_statement)
    if type(queuedOrders) == list :               
        generateCsvFile(cfg[env]["attachfile"], queuedOrders)
        sendmail("上周意向投诉单统计",
                 "详情请见附件", receivers, 1)          
    else :
        sendmail("【"  + env.upper()  + "】投诉单查询失败",str(queuedOrders),'wxp205@cyy928.com',0)






