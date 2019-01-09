#!/usr/local/bin/python2.7      
#coding=utf-8

'''
Created on 2018.12.7
通过Play status监控rewrite job执行状态
@author: wangle
'''
import subprocess
import re
import time
from datetime import datetime,timedelta
import logging
import socket
import smtplib 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication


#参数设置
'''参数说明 
   env是环境变量
'''
# multi env configurations 
env = 'prod'
cfg = {
    "qa" : {  
        "node_path": "/data/cyy928/qa/cws1/",
        "port": "9000",
        "logfile": "/data/cyy928/crontab/log/monitor_rewrite.log"
    },
    "stag" : {  
        "node_path": "/data/cyy928/stag/cws/",
        "port": "9002",
        "logfile": "/data/cyy928/crontab/log/monitor_rewrite.log"
    },
    "prod" : {
        "node_path": "/data/cyy928/dataSyncService/",
        "port": "9050",
        "logfile": "/data/cyy928/crontab/log/monitor_rewrite.log"
    }
}

# email configurations
hostname = socket.gethostname() 
sender = 'wxgzh@cyy928.com'  
sender_pw = 'Password1'
smtp_server = 'smtp.cyy928.com'
#receivers = '044@cyy928.com, wxp205@cyy928.com, wms228@cyy928.com, ljw394@cyy928.com,xjb460@cyy928.com,zls138@cyy928.com '  #正式人员
receivers = 'wxp205@cyy928.com,zls138@cyy928.com'   #测试人员
attached_file = '/data/cyy928/crontab/export/order_list.csv'

    
#定义日志输出格式
logging.basicConfig(level=logging.INFO,
        format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = cfg[env]['logfile'],
        filemode = 'a')

#发送邮件模块,目前在QQ和163邮箱环境测试成功
def  sendmail(subject, content, receivers, attached_flag):
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
        open_file = open(attached_file,'rb')    
        part = MIMEApplication(open_file.read())
        part.add_header('Content-Disposition', 'attachment', filename="rewrite_orders.csv")
        #如果附件名称需要更改，需要在这里调整，另外中文名称乱码问题未解决
        msg.attach(part)  
        open_file.close()
    smtp = smtplib.SMTP_SSL(smtpserver, 465)     
    smtp.connect(smtpserver)  
    smtp.login(username, password)  
    smtp.sendmail(sender, receivers.split(','), msg.as_string())  
    smtp.quit() 

#截取需要筛选的日志段
def search_keyword(content,keyword1,keyword2):
    filter_log = ''
    p = re.compile(r"("+keyword1+".+?)"+keyword2+"",re.DOTALL)
    a = re.findall(p,content)
    #print(a)
    if a  :       
        for element in a:
            filter_log += element
    else :
        logging.info("获取play status状态失败:%s" % a)        
    return filter_log
 
#获得所需的job上次执行时间         
def get_job_runtime(content,keyword):
    p = re.compile(r"("+keyword+").+last run at (.+)\)\n")
    for match in p.finditer(content):
        str1,last_runtime = match.groups()
        d2 = datetime.strptime(last_runtime,"%m/%d/%Y %H:%M:%S")
        if d2 + timedelta(minutes=5) < datetime.now():
            logging.error("the job:%s is not activing" %keyword)
            return True
        logging.info("the job:%s is activing" %keyword)
    return False

#检查进程是否存活 
def check_port_activity(key):
    #lines = os.popen('ps -ef|grep ' + key  )
    lines = subprocess.Popen(key,bufsize=1024,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    vars1 = 'blank'
    for line in lines.stdout: 
        #if line.find('grep '+key)!=-1: continue
        vars1 = line.split()
        logging.info("端口值：%r" %vars1)
        #result = vars[1] #get pid
    return vars1

#节点重启模块
def cws_restart():     #运行shell重启脚本 
    '''  
            整个重启流程分为检测故障节点PID，执行stop脚本，端口检测，kill进程，执行start脚本
            ，端口检测，超时检测几部分。先确定PID,执行stop,再检测端口是否存活，一旦
            还存活那么执行kill模块，执行start脚本，检测端口是否存活，如果不存活那么重复
            stop--start过程，如果存活，则重启完成，未通过则
            重复stop-start过程
    '''
    filename = cfg[env]["node_path"] + 'server.pid'
    num = 0
    while num < 3:    #设定最多重启三次，三次后还有问题就只能人工干预
        with open(filename,'r') as f:
            pid = f.read()
        logging.info('开始执行stop脚本')
        ps = subprocess.Popen(cfg[env]['node_path']+'stop.sh',bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,cwd=cfg[env]["node_path"])
        logging.info(ps.stdout.read())
        time.sleep(1)
        check_port = 'netstat -tulnp | grep '+ cfg[env]['port'] 
        stop_result = check_port_activity(check_port)               
        if stop_result != 'blank':    #如果进程不存在,变量获取的就是初始值blank
            logging.error("stop脚本执行不成功，执行kill" )
            output1 = subprocess.Popen('kill -9  '+pid,bufsize=1024,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            subprocess.Popen('rm -rf ' + filename ,bufsize=1024,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            logging.error("kill执行结果：%r,如果值为空就是成功" %output1.stdout.read())
        else :
            logging.info("stop脚本执行成功，一切顺利" )
        logging.info("开始执行startup脚本")
        subprocess.Popen(cfg[env]['node_path']+'startup.sh',bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,cwd=cfg[env]["node_path"])
        time.sleep(18)
        startup_result = check_port_activity(check_port) 
        logging.info("端口检测值："+startup_result[3][-4:])
        if startup_result[3][-4:] != cfg[env]['port']:    #如果进程不存在
            logging.error("start脚本执行失败，端口未发现" )
            logging.error(startup_result)
#                 sendmail("立刻行动！！","进程未启动，请尽快人工干预！！！",
#                          'kilner1@163.com',0)
            num = num + 1
            continue
        else :    
            logging.info("start脚本执行成功,端口已经启动，一切顺利" )
            num = 100   #启动成功，结束循环                                          
    return  True       #return是标准函数最后一句 


if __name__ == '__main__':
    #play_status = '/data/package/play-1.4.2/play status --url http://127.0.0.1:'  +cfg[env]["port"]    
    keyword1 = 'Scheduled jobs \(4\):'
    keyword2 = 'Waiting jobs:'
    keyword3 = 'ImagesDataSyncJob'
    keyword4 = 'CommonDataSyncJob'
    times = 0
    get_status_flag = 0   #play status是否获取日志的标志
    #while times < 1 :
    while True:
        play_status = '/data/package/play-1.4.2/play status --url http://127.0.0.1:' + cfg[env]['port']
        ps =  subprocess.Popen(play_status,bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,cwd=cfg[env]['node_path'])
        output_lines = ps.stdout.read()
        filter_log = search_keyword(output_lines,keyword1,keyword2)
        if filter_log == []:
            get_status_flag += 1
        else :
            get_status_flag = 0
        if get_status_flag > 2:
            sendmail("【" + env.upper()  + "回写节点故障】","回写节点故障，需要重启", receivers, 0)
            #print("测试 %d" %get_status_flag)
        if_outtime_picture = get_job_runtime(filter_log,keyword3)
        if if_outtime_picture:
            sendmail("【" + env.upper()  + "照片回写job故障】","照片回写job5分钟未活动", receivers, 0)
            #cws_restart()
        if_outtime_common = get_job_runtime(filter_log,keyword4) 
        if if_outtime_common:
            sendmail("【" + env.upper()  + "数据回写job故障】","数据回写job5分钟未活动", receivers, 0)
            #cws_restart()  
        time.sleep(300)
#         times = times + 1
#         print(times)


      
