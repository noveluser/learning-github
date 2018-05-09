#!/usr/bin/python
#coding=utf-8

import psycopg2
import time
from datetime import datetime

conn = psycopg2.connect(database="cyy_insurdb", user="cyyuser",password="kkz9c7H2", host="10.10.1.210")
print "connect success"


def log(file,context):     #log记录函数
    current_time=datetime.now()
    f = open(file,"wb+")
    f.write(str(current_time)+str(context)+'\n')
    f.close()
    return

def  compa():
       cur = conn.cursor()
       result=cur.execute("SELECT count(1) from car_service.insurance_orders where created_dt > current_timestamp - interval '5 min';")
       print result

       conn.commit()
       conn.close()
       return


           


compa()
