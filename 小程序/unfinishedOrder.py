#!/usr/local/bin/python2.7 
#coding=utf-8

' 未完成订单统计'
__author__ = 'Alex Wang'             #标准文件模板

import socket
import smtplib 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
import psycopg2
import codecs
import logging
from datetime import datetime
import csv
import subprocess


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
execute_statement1 = " with order_info as ( select sr.id , case when sr.flags = 1 then 1 else 0 end on_off from car_service.service_reqs sr where sr.created_dt >= (CURRENT_DATE + INTERVAL '-1 days') :: TIMESTAMP and sr.created_dt < CURRENT_DATE :: TIMESTAMP and ( sr.is_deleted = FALSE OR sr.is_deleted IS NULL ) AND sr.TYPE = 'SR' AND sr.service_id NOT IN (14,15) AND sr.status NOT IN ('CANCELED','COMPLETED') AND sr.appointment_time IS NULL ), group_info as ( select g.id,g.name 调度中心 , sum(case on_off when 1 then 1 else 0 end) 线下 , sum(case on_off when 0 then 1 else 0 end) 线上 from order_info sr INNER JOIN car_service.service_request_groups srg on sr.id = srg.request_id INNER JOIN security_service.groups g on g.id = srg.group_id where g.id != 1003 group by g.id,g.name ) select 调度中心, 线下,线上  from group_info where NOT (线下 = 0 and 线上= 10) ; "
execute_statement2 = "with order_info as ( select sr.id , case when sr.flags = 1 then 1 else 0 end on_off , sr.created_dt , srhd.processed_dt , srhd.completed_dt , sr.status , (select name from agency_service.persons where user_id = srhd.last_audit_person_id ) 最后审核人 , (select name from agency_service.persons where user_id = sr.current_dispatch_uid ) 调度员 , (select count(1) from order_service.ping_plus_plus_charges where paid = true and request_id = sr.id ) 是否未支付 , case when sr.source_agency_id in (2552,1094) then 1 else 0 end 是否自费订单 from car_service.service_reqs sr INNER join car_service.service_request_handle_details srhd ON sr.id = srhd.request_id where sr.created_dt >= current_date - INTERVAL '1 d' and sr.created_dt < current_date and ( sr.is_deleted = FALSE OR sr.is_deleted IS NULL ) AND sr.TYPE = 'SR' AND sr.service_id NOT IN (14,15) AND sr.status IN ('COMPLETED') AND sr.appointment_time IS NULL AND sr.flags = 1 ), group_stats as ( select g.id,g.name 调度中心 , sum(case when COALESCE(sr.processed_dt,sr.created_dt) < sr.created_dt + interval '00:08:00' then 1 else 0 end ) 到达现场异常 , sum(case when COALESCE(sr.completed_dt,sr.created_dt) < COALESCE(sr.processed_dt,sr.created_dt) + interval '00:05:00' then 1 else 0 end ) 执行完成异常 , sum( case when 是否自费订单 = 1 and 是否未支付 = 0 then 1 else 0 end ) 未支付已完成自费订单量 from order_info sr INNER JOIN car_service.service_request_groups srg on sr.id = srg.request_id INNER JOIN security_service.groups g on g.id = srg.group_id where g.id != 1003 group by g.id,g.name ) select * from group_stats;"
#异常订单统计


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
        AttachedFileName = '异常订单统计.csv'       
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
        rows = cursor.fetchall()
        logging.info("数据查询成功:%s" % rows)
        #print(rows[0][0])
    except Exception,e:
        logging.error('数据查询失败:%s' % e) 
        sendmail("【"  + env.upper()  + "】查询失败",str(e),receivers,0)
        rows = []       
    finally:
        cursor.close()
        conn.close()
    return rows

def get_phone_list(keys):
    msg1 = msg2 = ''
    keys =['18926050885','18128863251','17782868126','18926050929','18982128930']
    #四名调度经理的钉钉电话
    for row in keys:
        #phone = row[1]
        phone = row
        msg1 += "@" + phone + " "
        msg2 += phone + ","
    #print("%s  %s" %(msg1,msg2))
    return msg1,msg2

def merge_str1(keys,item):
    #keys是SQL输出的查询结果，以list方式存储
    md_table = ""
    md_key =  {
        "1":"",
        "2":"",
        "3":""
        } 
    num = 1  
    for row in keys:          
        md_key["1"] = "【**" + row[0] + "**】"
        md_key["2"] = "未完成订单线上**" + str(row[1]) + "**单"   
        md_key["3"] =  "未完成订单线下**" + str(row[2]) + "**单" 
        add_table = str(num) + ". {0} {1},{2}\n\n".format(md_key["1"],md_key["2"],md_key["3"]) 
        md_table += add_table         
        num += 1 
    str2 = "**" + item + "**" 
    content = str2 + "\n\n------------    \n\n" + md_table
    return content   

def merge_str2(keys,item):
    #keys是SQL输出的查询结果，以list方式存储
    md_table = ""
    md_key =  {
        "1":"",
        "2":"",
        "3":"",
        "4":""
        } 
    num = 1  
    for row in keys:          
        md_key["1"] = "【**" + row[1] + "**】"
        md_key["2"] = "到达现场异常**" + str(row[2]) + "**单"  
        md_key["3"] = "执行完成异常**" + str(row[3]) + "**单"  
        md_key["4"] =  "未支付已完成自费订单**" + str(row[4]) + "**单" 
        add_table = str(num) + ". {0} {1},{2},{3}\n\n".format(md_key["1"],md_key["2"],md_key["3"],md_key["4"]) 
        md_table += add_table         
        num += 1 
    str2 = "**" + item + "**" 
    content = "------------    \n\n" + str2 + "\n\n------------    \n\n" + md_table
    return content   

if __name__ == '__main__':
    result1 = fetchQueuedOrders(execute_statement1)
    result2 = fetchQueuedOrders(execute_statement2)
    msg1 , msg2= get_phone_list('')
    if result1 : 
        item = "昨日未完成订单统计"                      
        content1 =merge_str1(result1,item)      
    else :
        logging.info("昨日未完成订单统计查询为0或查询失败") 
        content1 = []       
    if result2 :  
        item = "昨日可能存在作弊行为的订单统计"                     
        content2 =merge_str2(result2,item)      
    else :
        logging.info("昨日异常订单统计查询为0或查询失败")
        content2 = []        
    #dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=e15004423e91ab55b79cf2aaea5397d42aa9bed127a1bdc18676de169660e33d' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \""  + content1 + content2 + msg1 + " \" },\"at\":{\"atMobiles\": [" + msg2 + "],  \"isAtAll\": false }}' "   #自建机器人     
    dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=81619e510b4537c73703db10bc783c0da2c2256fa24c8db7f8224dbad67115f9' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content1 + content2 + msg1 + " \" },\"at\":{\"atMobiles\": [" + msg2 + "],  \"isAtAll\": false }}' "   #车友援研发
    #dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=db336a98c76d77eec587aa24a213d6059b72cb60e31754b25bb6a0bbc3dee356' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content1 + content2 + msg1 + " \" },\"at\":{\"atMobiles\": [" + msg2 + "],  \"isAtAll\": false }}' "   #车友援运营处理中心
    #dingding_command = "curl 'https://oapi.dingtalk.com/robot/send?access_token=716d50316a8b0bb52213b86d914d3b15cab4cd410f35b6bfa1bf1e64ec41d941' -H 'Content-Type: application/json' -d '{ \"msgtype\": \"markdown\", \"markdown\": {\"title\":\"消息通知\",\"text\": \"" + content1 + content2 + msg1 + " \" },\"at\":{\"atMobiles\": [" + msg2 + "],  \"isAtAll\": false }}' "   #服务商跟进 
    #print(dingding_command)   
    subprocess.Popen(dingding_command,bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True) 






