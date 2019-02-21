#!/usr/local/bin/python2.7 
#coding=utf-8

import os
import socket
import smtplib 
from email.mime.text import MIMEText  
from email.mime.multipart import MIMEMultipart
from email.header import Header  
from datetime import datetime

# email configurations
# hostname = socket.gethostname() 
# sender = 'wxgzh@cyy928.com'  
# sender_pw = 'Password1'
# smtp_server = 'smtp.cyy928.com'
# #receivers = '001@cyy928.com,044@cyy928.com, hl421@cyy928.com,xl440@cyy928.com,011@cyy928.com,hpx441@cyy928.com,ld203@cyy928.com,wg270@cyy928.com,lfy161@cyy928.com,wxp205@cyy928.com,zyp232@cyy928.com'  #正式人员
# receivers = 'wxp205@cyy928.com'   #测试人员
# attached_file = '/data/cyy928/crontab/export/好奇怪的附件.txt'

class MailSender(object):
    _from = None
    _attachments = []
    
    def __init__(self,smtpSvr,port):
        self.smtp = smtplib.SMTP_SSL()
        print("connecting..")
        self.smtp.connect(smtpSvr,port)
        print("connected!!!")
        
    def loging(self,user,pwd):
        self._from = user
        print("login...")
        self.smtp.login(user,pwd)
        
    def add_attachment(self,oldfilename):
        att = MIMEText(open(oldfilename,'rb').read(), "base64", "utf-8")
        AttachedFileName = os.path.basename(oldfilename)
        
        att["Content-Type"] = "application/octet-stream"
        att["Content-Disposition"] = 'attachment; filename=%s' % AttachedFileName.decode('utf-8').encode('gbk')
        self._attachments.append(att)
        
#         att = MIMEBase("application",'octet-stream')
#         att.set_payload(open(filename,'rb').read())
#         att.add_header('Content-Disposition','attachment',filename=('gbk','',filename))
#         encoders.encode_base64(att)
#         self._attachments.append(att)
        return


    
    def send(self,subject,content,to_addr):
        msg = MIMEMultipart('alternative')
        content1 = content + "\n\r\n\rFrom " + socket.gethostname() + " at " + str(datetime.now())
        #contents = MIMEText(content1, "html", _charset='utf-8')
        contents = MIMEText(content1)
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = self._from
        msg['To'] = to_addr
        for att in self._attachments:
            msg.attach(att)
        msg.attach(contents)
        try:
            self.smtp.sendmail(self._from,to_addr.split(','),msg.as_string())
            return True
        except Exception as e:
            print(str(e))
            return False
        
    def close(self):
        self.smtp.quit()
        print("logout")
        
    