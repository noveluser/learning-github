#!/usr/local/bin/python2.7 
#coding=utf-8

' 异常订单列表'
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
import time


env = "prod"
# multi env configurations 
cfg = {
    "qa" : {
        "db_name": "cyydb_20181213",
        "db_user": "cyyuser",
        "db_pass": "kkz9c7H2",
        "db_ip": "10.10.1.210",

        "logfile_path": "/data/cyy928/crontab/log/unnormalOrderList.log",
        "attachfile": "/data/cyy928/crontab/export/customercreate_order_list.csv"
    },

    "prod" : {
        "db_name": "cyydb",
        "db_user": "cyyuser",
        "db_pass": "lkkRrrhO",
        "db_ip": "10.10.95.100",

        "logfile_path": "/data/cyy928/crontab/log/unnormalOrderList.log",
        "attachfile": "/data/cyy928/crontab/export/customer_complain_list.csv"
    }
}


# email configurations
hostname = socket.gethostname() 
sender = 'wxgzh@cyy928.com'  
sender_pw = 'Password1'
smtp_server = 'smtp.cyy928.com'
receivers = '001@cyy928.com,044@cyy928.com, hl421@cyy928.com,hpx441@cyy928.com,ld203@cyy928.com,wg270@cyy928.com,lfy161@cyy928.com,wxp205@cyy928.com,zyp232@cyy928.com'  #正式人员
#receivers = 'wxp205@cyy928.com,qj533@cyy928.com'   #测试人员
attached_file = '/data/cyy928/crontab/export/customer_complain_list.csv'

# sql execute statement
execute_statement=" with order_info as ( select sr.id , case when sr.flags = 1 then 1 else 0 end on_off , sr.created_dt , srhd.processed_dt , srhd.completed_dt , sr.status , sr.case_code , (select name from agency_service.persons where user_id = srhd.last_audit_person_id ) 最后审核人 , (select name from agency_service.persons where user_id = sr.current_dispatch_uid ) 调度员 , (select count(1) from order_service.ping_plus_plus_charges where paid = true and request_id = sr.id ) 是否未支付 , case when sr.source_agency_id in (2552,1094) then 1 else 0 end 是否自费订单 from car_service.service_reqs sr INNER join car_service.service_request_handle_details srhd ON sr.id = srhd.request_id where sr.created_dt >= current_date - INTERVAL '1 d' and sr.created_dt < current_date and ( sr.is_deleted = FALSE OR sr.is_deleted IS NULL ) AND sr.TYPE = 'SR' AND sr.service_id NOT IN (14,15) AND sr.status IN ('COMPLETED') AND sr.appointment_time IS NULL AND sr.flags = 1 AND ( COALESCE(srhd.processed_dt,sr.created_dt) < sr.created_dt + interval '00:08:00' OR COALESCE(srhd.completed_dt,sr.created_dt) < COALESCE(srhd.processed_dt,sr.created_dt) + interval '00:05:00') ), group_info as ( select g.name 调度中心 , sr.id 订单ID , sr.case_code 报案号 , case when sr.on_off = 1 then '线下' else '线上' end 派单方式 , to_char(sr.created_dt,'YYYY-MM-DD HH24:mi:ss') 创建时间 , to_char(sr.processed_dt,'YYYY-MM-DD HH24:mi:ss') 到场时间 , to_char(sr.completed_dt,'YYYY-MM-DD HH24:mi:ss') 完成时间 , sr.最后审核人 , sr.调度员 , case when sr.是否未支付 = 0 then '未支付' else '已支付' end 是否未支付 , case when sr.是否自费订单 = 0 then '非自费' else '自费' end 是否自费订单 from order_info sr INNER JOIN car_service.service_request_groups srg on sr.id = srg.request_id INNER JOIN security_service.groups g on g.id = srg.group_id where g.id != 1003 ) select * from group_info ; "


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
            
        AttachedFileName = 'issued_orders_list_' + time.strftime('%Y%m%d',time.localtime(time.time())) + '.csv'      
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
        sendmail("【"  + env.upper()  + "】查询失败",str(e),'wxp205@cyy928.com',0)
        rows = []       
    finally:
        cursor.close()
        conn.close()
    return rows


def generateCsvFile(filename, rows):
    with open(filename, "w") as csvfile:
        csvfile.write(codecs.BOM_UTF8)
        w = csv.writer(csvfile,dialect='excel')
        w.writerow(['调度中心','订单ID','报案号','派单方式','创建时间','到场时间','完成时间','最后审核人','调度员','是否未支付','是否自费订单'])
        for row in rows:
            w.writerow([row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10]])
    return

def safe_output_rows(sql):
    a = 0
    while a < 5 :
        queuedOrders = fetchQueuedOrders(sql)
        if type(queuedOrders) == list :
            a = 100
        else:
            a += 1
            sendmail("【"  + env.upper()  + "】异常订单统计查询失败",str(queuedOrders),'wxp205@cyy928.com',0)
            time.sleep(10)
    return queuedOrders     

if __name__ == '__main__':
    #queuedOrders = get_df_from_db(execute_statement)
    queuedOrders = safe_output_rows(execute_statement)
    if queuedOrders :               
        generateCsvFile(cfg[env]["attachfile"], queuedOrders)
        sendmail("异常订单列表",
                 "详情请见附件", receivers, 1)          
    else :
        logging.info("异常订单统计查询为0")






