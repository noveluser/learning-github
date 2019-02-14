#!/usr/local/bin/python2.7 
#coding=utf-8

' 每日订单数据统计'
__author__ = 'Alex Wang'             #标准文件模板

import socket
import smtplib 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication
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
receivers = '001@cyy928.com,044@cyy928.com, hl421@cyy928.com,xl440@cyy928.com,011@cyy928.com,hpx441@cyy928.com,ld203@cyy928.com,wg270@cyy928.com,lfy161@cyy928.com,wxp205@cyy928.com'  #正式人员
#receivers = 'wxp205@cyy928.com'   #测试人员
attached_file = '/data/cyy928/crontab/export/customer_complain_list.csv'

# sql execute statement
execute_statement=" WITH agency_name AS( SELECT id , name agency_name , CASE WHEN name LIKE '中国平安%' THEN 1 WHEN name LIKE '中华联合%' THEN 4 WHEN name LIKE '%车主自费%' THEN 3 ELSE 2 END agency_group FROM agency_service.agencies WHERE type = 'INSURANCE' AND status = 'ENABLED' AND id IN ( SELECT DISTINCT source_agency_id FROM car_service.service_reqs WHERE created_dt < current_date AND created_dt > LEAST(current_date - INTERVAL '2 d' , date_trunc( 'month', current_date - INTERVAL '1 d')) AND created_by_agency = 1 AND ( is_deleted = FALSE OR is_deleted IS NULL ) AND TYPE = 'SR' ) AND name not LIKE '测试%' ), the_month_order_cnt AS ( SELECT source_agency_id , count(1) cnt FROM car_service.service_reqs req WHERE created_dt < current_date AND created_dt > date_trunc( 'month', current_date - INTERVAL '1 d') AND created_by_agency = 1 AND ( req.is_deleted = FALSE OR req.is_deleted IS NULL) AND req. TYPE = 'SR' GROUP BY source_agency_id ), the_today_order_cnt AS ( SELECT source_agency_id , count(1) cnt , sum( CASE WHEN service_id in (3,4,5,19,23,24,25,34) THEN 1 ELSE 0 END ) luxiu , sum( CASE WHEN service_id in (1,6,7,26,27,28) THEN 1 ELSE 0 END ) tuoche , sum( CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END ) wancheng , sum( CASE WHEN status = 'CANCELED' THEN 1 ELSE 0 END ) quxiao , sum( CASE WHEN status = 'CANCELED' AND redispatch_id is not null THEN 1 ELSE 0 END ) chongpai_quxiao , sum( CASE WHEN is_issue_tASk is TRUE THEN 1 ELSE 0 END ) yichang , sum( CASE WHEN complaints_level is not null AND complaints_level NOT in ('Z','U') THEN 1 ELSE 0 END ) tousu FROM car_service.service_reqs req WHERE created_dt < current_date AND created_dt > current_date - INTERVAL '1 d' AND created_by_agency = 1 AND (req.is_deleted = FALSE OR req.is_deleted IS NULL ) AND req. TYPE = 'SR' GROUP BY source_agency_id ), the_yesterday_order_cnt AS ( SELECT source_agency_id , count(1) cnt FROM car_service.service_reqs req WHERE created_dt < current_date - INTERVAL '1 d' AND created_dt > current_date - INTERVAL '2 d' AND created_by_agency = 1 AND ( req.is_deleted = FALSE OR req.is_deleted IS NULL ) AND req. TYPE = 'SR' GROUP BY source_agency_id ), pinan AS ( SELECT (CASE WHEN agency_name != '中国平安财产险股份有限公司广东分公司-事故救援' THEN REPLACE(REPLACE( REPLACE( REPLACE(agency_name, '中国平安财产保险股份有限公司',''),'中国平安保险公司',''),'分公司',''),'中心支公司','') ELSE agency_name END ) 发包方 , COALESCE(mc.cnt,0) 本月累计订单总量 , COALESCE(tc.cnt,0) 日订单总量 , COALESCE(tc.luxiu,0) 日路修量 , COALESCE(tc.tuoche,0) 日拖车量 , COALESCE(tc.wancheng,0) 日完成量 , COALESCE(tc.quxiao,0) 日取消量 , COALESCE(tc.chongpai_quxiao,0) 日重派取消量 , COALESCE(tc.yichang,0) 异常订单 , COALESCE(tc.tousu,0) 投诉订单 , (COALESCE(tc.cnt,0) - COALESCE(yc.cnt,0)) 日订单环比增量 FROM agency_name an LEFT JOIN the_month_order_cnt mc on an.id = mc.source_agency_id LEFT JOIN the_today_order_cnt tc on an.id = tc.source_agency_id LEFT JOIN the_yesterday_order_cnt yc on an.id = yc.source_agency_id WHERE agency_group = 1 ORDER BY mc.cnt DESC ), pinan_all AS ( SELECT '平安机构'::VARCHAR AS agency_name , SUM(COALESCE(mc.cnt,0)) 本月累计订单总量 , SUM(COALESCE(tc.cnt,0)) 日订单总量 , SUM(COALESCE(tc.luxiu,0)) 日路修量 , SUM(COALESCE(tc.tuoche,0)) 日拖车量 , SUM(COALESCE(tc.wancheng,0)) 日完成量 , SUM(COALESCE(tc.quxiao,0)) 日取消量 , SUM(COALESCE(tc.chongpai_quxiao,0)) 日重派取消量 , SUM(COALESCE(tc.yichang,0)) 异常订单 , SUM(COALESCE(tc.tousu,0)) 投诉订单 , SUM((COALESCE(tc.cnt,0) - COALESCE(yc.cnt,0))) 日订单环比增量 FROM agency_name an LEFT JOIN the_month_order_cnt mc on an.id = mc.source_agency_id LEFT JOIN the_today_order_cnt tc on an.id = tc.source_agency_id LEFT JOIN the_yesterday_order_cnt yc on an.id = yc.source_agency_id WHERE agency_group = 1 ), zhonghua AS ( SELECT agency_name , COALESCE(mc.cnt,0) 本月累计订单总量 , COALESCE(tc.cnt,0) 日订单总量 , COALESCE(tc.luxiu,0) 日路修量 , COALESCE(tc.tuoche,0) 日拖车量 , COALESCE(tc.wancheng,0) 日完成量 , COALESCE(tc.quxiao,0) 日取消量 , COALESCE(tc.chongpai_quxiao,0) 日重派取消量 , COALESCE(tc.yichang,0) 异常订单 , COALESCE(tc.tousu,0) 投诉订单 , (COALESCE(tc.cnt,0) - COALESCE(yc.cnt,0)) 日订单环比增量 FROM agency_name an LEFT JOIN the_month_order_cnt mc on an.id = mc.source_agency_id LEFT JOIN the_today_order_cnt tc on an.id = tc.source_agency_id LEFT JOIN the_yesterday_order_cnt yc on an.id = yc.source_agency_id WHERE agency_group = 4 ORDER BY mc.cnt DESC ), other_own AS ( SELECT agency_name , COALESCE(mc.cnt,0) 本月累计订单总量 , COALESCE(tc.cnt,0) 日订单总量 , COALESCE(tc.luxiu,0) 日路修量 , COALESCE(tc.tuoche,0) 日拖车量 , COALESCE(tc.wancheng,0) 日完成量 , COALESCE(tc.quxiao,0) 日取消量 , COALESCE(tc.chongpai_quxiao,0) 日重派取消量 , COALESCE(tc.yichang,0) 异常订单 , COALESCE(tc.tousu,0) 投诉订单 , (COALESCE(tc.cnt,0) - COALESCE(yc.cnt,0)) 日订单环比增量 FROM agency_name an LEFT JOIN the_month_order_cnt mc on an.id = mc.source_agency_id LEFT JOIN the_today_order_cnt tc on an.id = tc.source_agency_id LEFT JOIN the_yesterday_order_cnt yc on an.id = yc.source_agency_id WHERE agency_group IN (2,3) ORDER BY agency_group ), all_data AS ( SELECT '合计'::VARCHAR AS agency_name , SUM(COALESCE(mc.cnt,0)) 本月累计订单总量 , SUM(COALESCE(tc.cnt,0)) 日订单总量 , SUM(COALESCE(tc.luxiu,0)) 日路修量 , SUM(COALESCE(tc.tuoche,0)) 日拖车量 , SUM(COALESCE(tc.wancheng,0)) 日完成量 , SUM(COALESCE(tc.quxiao,0)) 日取消量 , SUM(COALESCE(tc.chongpai_quxiao,0)) 日重派取消量 , SUM(COALESCE(tc.yichang,0)) 异常订单 , SUM(COALESCE(tc.tousu,0)) 投诉订单 , SUM((COALESCE(tc.cnt,0) - COALESCE(yc.cnt,0))) 日订单环比增量 FROM agency_name an LEFT JOIN the_month_order_cnt mc on an.id = mc.source_agency_id LEFT JOIN the_today_order_cnt tc on an.id = tc.source_agency_id LEFT JOIN the_yesterday_order_cnt yc on an.id = yc.source_agency_id ) SELECT * FROM pinan UNION ALL SELECT * FROM pinan_all UNION ALL SELECT * FROM other_own UNION ALL SELECT * FROM zhonghua UNION ALL SELECT * FROM all_data ; "


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
		part.add_header('Content-Disposition', 'attachment', filename="DailyEmployerStatistics.csv")
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


# def generateCsvFile(filename, rows):    
#     with open(filename, "w") as csvfile:
#         w = csv.DictWriter(csvfile, ['调度中心','意向投诉单量','升级单量','取消量','真实投诉量'])
#         w.writeheader()
#         for row in rows:
#            w.writerow({'调度中心':row[0],'意向投诉单量':row[1],'升级单量':row[2],'取消量':row[3],'真实投诉量':row[4]})
#     return

def generateCsvFile(filename, rows):    
    with open(filename, "wb") as csvfile:
        csvfile.write(codecs.BOM_UTF8)
        w = csv.writer(csvfile,dialect='excel')
        w.writerow(['发包方','本月累计订单总量','日订单总量','日路修量','日拖车量','日完成量','日取消量','日重派取消量','异常订单','投诉订单','日订单环比增量'])
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
            sendmail("【"  + env.upper()  + "】昨日发包方查询失败",str(queuedOrders),'wxp205@cyy928.com',0)
            time.sleep(10)
    return queuedOrders 
    

if __name__ == '__main__':
    #queuedOrders = get_df_from_db(execute_statement)
    queuedOrders = safe_output_rows(execute_statement)
    if type(queuedOrders) == list :               
        generateCsvFile(cfg[env]["attachfile"], queuedOrders)
        sendmail("昨日发包方统计",
                 "详情请见附件", receivers, 1)          
    else :
        sendmail("【"  + env.upper()  + "】昨日发包方查询失败",str(queuedOrders),'wxp205@cyy928.com',0)






