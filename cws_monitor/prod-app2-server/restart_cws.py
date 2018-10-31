#!/usr/local/bin/python2.7      
#coding=utf-8

' a restart scription when cws halt'
__author__ = 'Alex Wang'             #标准文件模板
# verson 1.01 ,modify at 2018.6.12 

import subprocess
import socket
import smtplib  
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from email.mime.application import MIMEApplication
import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import time
from datetime import datetime,timedelta 
import re
import shlex


env = "prod"
# multi evn configurations 
cfg = {
    "qa" : {  
        "shell_path": "/data/cyy928/crond/",
        "cws_update_flag": "/data/cyy928/crond/cws_update_flag.txt"
    },
    "prod" : {
        "shell_path": "/data/cyy928/crontab/",
        "cws_update_flag": "/data/cyy928/crontab/cws_update_flag.txt"
    }
}

#各节点详细信息    
node = {
        "9000": {
                "name": "cws",
                "cws_path": "/data/cyy928/cws/",
                "log_file": "/data/cyy928/crontab/log/cws_9000_status.log"
                },
        "9001": {
                "name": "cws4job",
                "cws_path": "/data/cyy928/cws4job/",
                "log_file": "/data/cyy928/crontab/log/cws_9001_status.log"
                },            
        "9006": {
                "name": "financialGateway",
                "cws_path": "/data/cyy928/financialGateway/financial-gateway/",
                "log_file": "/data/cyy928/crontab/log/cws_9006_status.log"
                },  
        "7000": {
                "name": "ledger-service",
                "cws_path": "/data/cyy928/ledgerServers/ledger-service/",
                "log_file": "/data/cyy928/crontab/log/cws_7000_status.log"
                },             
        "9050": {
                "name": "dataSyncService",
                "cws_path": "/data/cyy928/dataSyncService/",
                "log_file": "/data/cyy928/crontab/log/cws_9050_status.log"
                },
        "9090": {
                "name": "cws2",
                "cws_path": "/data/cyy928/cws-server/cws2/",
                "log_file": "/data/cyy928/crontab/log/cws_9090_status.log"
                },
        "9093": {
                "name": "cws3",
                "cws_path": "/data/cyy928/cws3/",
                "log_file": "/data/cyy928/crontab/log/cws_9093_status.log"
                } ,
        "9002": {
                "name": "stag",
                "cws_path": "/data/cyy928/stag/cws/",
                "log_file": "/data/cyy928/crond/log/cws_9002_status.log"
                }         
        }
        
#全局参数
ports = ['9000','9001','9006','9050','7000'] 
mark_end_time = datetime.now() 
'''参数设置， mark_start_time和mark_end_time这两个是为检查cws_update_flag.txt而设定的,
如果标志成deloying超过15分钟，那么说明不是正在部署中，而是部署人员忘记关闭开关标志'''        

# email configurations
hostname = socket.gethostname() 
sender = 'wxgzh@cyy928.com'  
sender_pw = 'Password1'
smtp_server = 'smtp.cyy928.com'
receivers = '044@cyy928.com, wxp205@cyy928.com'   #正式人员
#receivers = 'wxp205@cyy928.com'   #测试人员
receiver1 = 'wxp205@cyy928.com'   #低优先级别邮件组
attached_file = '/data/cyy928/logs/play_status.log' 


#发送邮件模块,目前在QQ和163邮箱环境测试成功
def  sendmail(subject,content,receivers,attached_flag):        
    #sender = 'wxgzh@cyy928.com'  
    receivers = receivers  
    subject = hostname+subject 
    smtpserver = smtp_server  
    username = sender  
    password = sender_pw
    attached_flag = int(attached_flag)
    content=content + "\n\r\n\rFrom " + hostname + " at " + str(datetime.now())	  
    #msg = MIMEText(context,'plain','utf-8')#中文需参数‘utf-8’，单字节字符不需要  
    msg = MIMEMultipart()
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = 'cws监控<wxgzh@cyy928.com>'
    msg['To'] = receivers
    puretext = MIMEText(content)
    msg.attach(puretext) 
    if attached_flag == 1:   #如果标识位为0，那么发送附件，否则不发送      
            play_status_file=open(attached_file,'rb')	
            part =MIMEApplication(play_status_file.read())
            part.add_header('Content-Disposition', 'attachment', filename="play_status.log")
            #如果附件名称需要更改，需要在这里调整，另外中文名称乱码问题未解决
            msg.attach(part)  
            play_status_file.close()
    smtp = smtplib.SMTP_SSL(smtpserver, 465)
    smtp.connect(smtpserver)  
    smtp.login(username, password)  
    smtp.sendmail(sender, receivers.split(','), msg.as_string())  
    smtp.quit() 
    return

#日志记录模块
def log(file,level,content1,content2=''):    
    current_time = datetime.now()
    f = open(file,"a+")
    f.write(str(current_time)+'  '+level+'  '+str(content1)+str(content2)+'\n')
    f.close()
    return

def execute_command(cmdstring, cwd=None, timeout=None, shell=False):
    """执行一个SHELL命令
        封装了subprocess的Popen方法, 支持超时判断，支持读取stdout和stderr
        参数:
        cwd: 运行命令时更改路径，如果被设定，子进程会直接先更改当前路径到cwd
        timeout: 超时时间，秒，支持小数，精度0.1秒
        shell: 是否通过shell运行
    Returns: return_code
    Raises: Exception: 执行超时
    """
    if shell:
        cmdstring_list = cmdstring
    else:
        cmdstring_list = shlex.split(cmdstring)
    if timeout:
        end_time = datetime.now() + timedelta(seconds=timeout)
    
    #没有指定标准输出和错误输出的管道，因此会打印到屏幕上；
    sub = subprocess.Popen(cmdstring_list, cwd=cwd, stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=shell,bufsize=4096)
    
    #subprocess.poll()方法：检查子进程是否结束了，如果结束了，设定并返回码，放在subprocess.returncode变量中 
    while sub.poll() is None:
        time.sleep(0.1)
        if timeout:
            if end_time <= datetime.now():
                raise Exception("Timeout：%s"%cmdstring)
        
    return str(sub.returncode)
        
#检查进程是否存活 
def check_port_activity(key):
    #lines = os.popen('ps -ef|grep ' + key  )
    lines = subprocess.Popen(key,bufsize=1024,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    vars = 'blank'
    for line in lines.stdout: 
        #if line.find('grep '+key)!=-1: continue
        vars = line.split()
        #result = vars[1] #get pid
    return vars

#终止进程
def kill_process(pid):
        #out = subprocess.Popen('kill -9  '+pid,bufsize=4096,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        out = execute_command('kill -9 '+pid, timeout=1, shell=True)
        if out == 0:
            log(node[port]["log_file"],'success!',' kill %s ' % pid)
        else:
            log(node[port]["log_file"],'fail!',' kill %s ' % pid)
        return out

#判断URL是否超时，
def check_timeout(url,timeout):                       
        try:
            f = '' 
            requests.get(url,timeout=timeout)
        except ReadTimeout as f:            
            return 'ReadTimeout',f
        except ConnectionError as f:
            return 'ConnectionError',f
        except RequestException as f:
            return 'RequestException',f
        except Exception as f:
			return 'Exception',f
        return 'ok', f  

                  
#cws重启模块	
def cws_restart():     #运行shell重启脚本 
        '''  
            整个重启流程分为检测故障节点PID，执行stop脚本，端口检测，kill进程，执行start脚本
            ，端口检测，超时检测几部分。先确定PID,执行stop,再检测端口是否存活，一旦
            还存活那么执行kill模块，执行start脚本，检测端口是否存活，如果不存活那么重复
            stop--start过程，如果存活，那么进行三次超时检测，通过则重启完成，未通过则
            重复stop-start过程
        '''
        keyword = node[port]["cws_path"][-10:]
        check_pid = 'ps -ef | grep ' + keyword+' -m 20 | grep -v grep'
        num = 0
        while num < 3:    #设定最多重启三次，三次后还有问题就只能人工干预

            pid = check_port_activity(check_pid)[1]   #[1]栏是进程号
            log(node[port]["log_file"],'info','开始执行stop脚本')
            #status=os.system(cfg[env]["shell_path"]+'stop_'+port+'.sh')
            status = execute_command(cfg[env]["shell_path"]+'stop_'+port+'.sh',node[port]["cws_path"],10)
            log(node[port]["log_file"],'info',"stop脚本执行状态为："+str(status ))
            time.sleep(1) 
            check_port = 'netstat -tulnp | grep '+ port
            #result = check_port_activity(port)
            stop_result = check_port_activity(check_port)              

            if stop_result != 'blank':    #如果进程不存在,变量获取的就是初始值blank

                log(node[port]["log_file"],'error',"stop脚本执行不成功，执行kill" )
                kill_process(pid)
                #kill_result = False
            else :
                log(node[port]["log_file"],'info',"stop脚本执行成功，一切顺利" )
                #kill_result = True  #终止退出
                
#            if kill_result != True:
#                sendmail("立刻行动！！","进程无法清除，请尽快人工干预！！！",
#                         'kilner1@163.com',0) 
#                continue   #其实如果kill不成功，其实上重复也没有必要了，必须人工干预
            log(node[port]["log_file"],'info',"开始执行startup脚本")
            #status=os.system(cfg[env]["shell_path"]+'startup_'+port+'.sh')
            #print execute_command('/data/cyy928/crond/startup_9002.sh',node[port]["cws_path"],10)
            status = execute_command(cfg[env]['shell_path']+'startup_'+port+'.sh',node[port]["cws_path"],10)
            log(node[port]["log_file"],'info',"start脚本执行状态为："+str(status ))
            time.sleep(15)
            startup_result = check_port_activity(check_port) 
            log(node[port]["log_file"],'info',"端口检测值："+startup_result[3][-4:])
            #startup_result = True  #test
            if startup_result[3][-4:] != port:    #如果进程不存在
                log(node[port]["log_file"],'error',"start脚本执行失败，端口未发现" )
                sendmail("立刻行动！！","进程未启动，请尽快人工干预！！！",
                         'kilner1@163.com',0)
                num = num + 1
                continue
            else :    
                log(node[port]["log_file"],'info',"start脚本执行成功,端口已经启动，一切顺利" )

            ok = 0
            i = 0
            while i < 4 :     #至少3次超时检查通过
                start_time = time.time()*1000             
                status,result = check_timeout(api_url,timeout=5.002)
                end_time = time.time()*1000
                duration_time = str(end_time-start_time)
                if status == 'ok' :
                   log(node[port]["log_file"],'info','API服务检测正常,反应时间为 ',duration_time )
                   ok = ok + 1
                else :
                   log(node[port]["log_file"],'error',result,'readtimeout反应时间 '+duration_time)
                time.sleep(6)
                if ok >= 2:    #如果超时检测通过2次，那么结束大循环，否则继续重启
                    num = 100   
                i = i + 1
            num = num + 1                                              
        return         #return是标准函数最后一句

#搜索文本中的关键词
def search_keyword(file):
    with open(file, "r") as f:
        content = f.read()
    keyword = ["Requests execution pool","Jobs execution pool"]
    result = 0  # 如果result一直为0，表明active count 一直小于 max
    for i in keyword :
        rx_sequence=re.compile(r"^("+i+".+?)\n~+\n(.+?\n)(.+?\n)",re.MULTILINE)
        '''
        这个正则表达式的意识是搜索以keyword关键词为首的字符串,("+i+".+?)\n思是任意无限个字符串
        后面以\n回车符结尾的,~+\n,这个'~'开始，\n结束的，(.+?\n)任意字符[包括字母，数字]
        开始，不限数量，\n结束的一行
        '''
        for match in rx_sequence.finditer(content):
            Request, Pool, Active = match.groups()
            #title = title.strip()
            max_count = int(Pool.split(':')[1])
            active_count = int(Active.split(':')[1])
            if active_count * 1.12 > max_count :
                print "连接数已经接近最大值"
                result = result + 1
            else :
                print "连接数量不多,资源充足" 
            log(node[port]["log_file"],'info',Request+Pool+Active )
    var_exists = 'Request' in locals()
    if var_exists == False:   #搜索的play_status.log文件不存在或者获取不成功，导致搜索不到关键词，那么一律重启
        result = 100
        log(node[port]["log_file"],'info',"play_status未能获取" )
    #result = 100 #暂时取消关键词判断功能
    return result	

#检查是否已经重启过的函数，如果已经重启过，则跳过重启函数
def check_restart(check_file):    
     with open(check_file,"r") as f:
         flag = f.read()    
     if int(flag) == 0:
         cws_restart()
         f2 = open(check_file,"w")
         f2.write('2')
         f2.close()
         sendmail('服务器重启',port+'重启',receivers,1)
         subprocess.Popen('echo '' > play_status.log ',bufsize=0,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          shell=True,cwd='/data/cyy928/logs/')
         log(node[port]["log_file"],'error','服务器检测不正常,已重启')
     else:
         log(node[port]["log_file"],'error','服务器已经在1小时内重启过',',无需再重启')
     return

#检查CWS节点是否僵死	 
def check_url(port):               #判断URL是否超时，
    #log_file=path1+"cws_"+port+"_status.log"     #日志文件绝对路径
    #check_file=path1+port+"_status.txt"       #设置重启标志的文件，如果重启，那么完成后写入重启标志1
    timeout_time = 0    
    
    for i in range(0,2):
                start_time=time.time()*1000             
                status,result = check_timeout(api_url,timeout=5.002)
                end_time=time.time()*1000
                duration_time = str(end_time-start_time)                
                if status == 'ok' :
                    log(node[port]["log_file"],'info','API服务检测情况：'+str(status),
                        ' 响应时间为: '+duration_time )
                elif status == 'ReadTimeout' :
                    timeout_time =timeout_time + 1
                    log(node[port]["log_file"],'error','readtimeout服务检测情况：'+str(result),
                        ' 响应时间为: '+duration_time )
                    #sendmail('服务有异常',str(result)+'\n'+'反应时间 '+duration_time,receiver1,0)
                elif status == 'ConnectionError' :
                    timeout_time =timeout_time + 1
                    log(node[port]["log_file"],'error','ConnectionError服务检测情况：'+str(result),
                        ' 响应时间为: '+duration_time )
                    sendmail('服务有异常',str(result)+'\n'+'反应时间 '+duration_time,receiver1,0)
                else :
                    #timeout_time =timeout_time + 1
                    log(node[port]["log_file"],'error','RequestException服务检测情况：'+str(result),
                        ' 响应时间为: '+duration_time )
                    sendmail('服务有异常',str(result)+'\n'+'反应时间 '+duration_time,receiver1,0)
                i = i + 1
                time.sleep(6)
                
    return timeout_time
	




while True :
    for port in ports: 
        with open(cfg[env]["cws_update_flag"],"r") as f:
            result = f.read().replace("\n", "")
            if result == 'deploying' :
                #print 'in progress of deploying'
                log(node[port]["log_file"],'info',"  节点正在部署中。。。")
                if mark_end_time < datetime.now() :
                  sendmail("标志文件15分钟内保持部署状态,请人工干预",'warning','kilner1@163.com',0) 
                  mark_end_time = datetime.now()+ timedelta(seconds=900)   #恢复原状，，减少告警邮件的发送
            else :
                #print "not deploying"
                if __name__=='__main__':
                    if port == '9006' or port == '7000':
                      api_url = "http://127.0.0.1:"+port+ "/version"
                    else :                     
                      api_url = "http://127.0.0.1:"+port+"/api/dispatch/896260/persons?authToken=176ed33052b1fed902319090b27260baa2066cfe%239076&appID=d18b6732881d7e04e665e3eb761861db03b5f06c&secretKey=98da99443c76c483a48904ac70af7c42&agency-id=1"       #检测URL路径
                    mark_start_time = datetime.now()
                    mark_end_time = mark_start_time + timedelta(seconds=900)                    
                    restart_status = 0     #重启默认标志为0，不重启
                    timeout_time = check_url(port)
                    #timeout_time =2    #测试语句
                    log(node[port]["log_file"],'debug','超时次数：'+str(timeout_time) )
                    if timeout_time >= 2:          #如果连续超时，那么进入active检测模块
                        play_status = '/data/package/play-1.4.2/play status --url http://127.0.0.1:' \
                                        +port+' > /data/cyy928/logs/play_status.log'
                        log(node[port]["log_file"],'info','附件语句执行前' )                
                        subprocess.Popen(play_status,bufsize=0,stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,shell=True,cwd=node[port]["cws_path"])
                        log(node[port]["log_file"],'info','附件语句执行后' )
                        time.sleep(1)   #保证上述语句执行完成，否正有时会出现获取不到数据的问题
                        restart_status = search_keyword(attached_file)  
                        if restart_status > 0:           #如果active count +20 >max ,那么进入重启模块
                            log(node[port]["log_file"],'debug','restart_status：'+str(restart_status) )
                            check_restart(cfg[env]["shell_path"]+port+'_status.txt') 

    time.sleep(20)
