#!/usr/local/bin/python2.7      
#coding=utf-8

# name IsOpen.py  
import os  
import socket  
import time  
 
  
  
def IsOpen(ip,port,flag):  
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
    try:  
        s.connect((ip,int(port)))  
        s.shutdown(2)  
        print '%d is open' % port  
        return True  
    except:  
        print '%d is down' % port    
        return False  
      
if __name__ == '__main__':  
    while(1>0):  
        flag=1  
        IsOpen('127.0.0.1',80)  
        time.sleep(60)  
        flag=IsOpen('127.0.0.1',9906)  
        print flag  
        if flag==False:  
            print '服务被关闭' % port
            time.sleep(1800) 