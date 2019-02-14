#!/usr/local/bin/python2.7 
#coding=utf-8
'''
Created on 2019年1月29日

@author: wangle
'''
import subprocess
import shlex
import logging
import time

#参数配置
command_path = '/data/cyy928/crontab/'
fileList = ["customer_order_list.py","count_new_master.py","find_nouse_provider.py","unprovedORunpaid_order_list.py","uncashOrder.py","unnormalOrderList.py","orderStatic.py"]
#fileList = ["unfinishedOrder.py","unfinishedOrder.py","unfinishedOrder.py","unfinishedOrder.py","unfinishedOrder.py"]

#定义日志输出格式
logging.basicConfig(level=logging.INFO,
        format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = '/data/cyy928/crontab/log/startatNine.log',
        filemode = 'a')

if __name__ == '__main__':
    for fileName in fileList:
        shell_cmd = command_path+fileName
        cmd = shlex.split(shell_cmd)
        result = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while result.poll() is None:
            line = result.stdout.readline()
            line = line.strip()
            if line:
                loggin.info('Subprogram output: [{}]'.format(line))
        if result.returncode == 0:
            logging.info('Subprogram %s success' %fileName )
        else:
            logging.info('Subprogram %s failed' %fileName)

