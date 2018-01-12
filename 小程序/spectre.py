#!/usr/bin/python
#coding=utf-8

import psycopg2
import time
from datetime import datetime

conn = psycopg2.connect(database="cyy28c", user="cyyuser",password="123456", host="192.168.1.197")
print "connect success"


def log(file,context):     #log记录函数
    current_time=datetime.now()
    f = open(file,"wb+")
    f.write(str(current_time)+str(context)+'\n')
    f.close()
    return

def  compa():
       cur = conn.cursor()
       cur.execute('''CREATE TABLE COMPANY1
       (ID INT PRIMARY KEY     NOT NULL,
        NAME           TEXT    NOT NULL,
         AGE            INT     NOT NULL,
          ADDRESS        CHAR(50),
           SALARY         REAL);''')
       print "Table created successfully"

       conn.commit()
       conn.close()
       return

def  compaInsert():
       conn = psycopg2.connect(database="cyy12", user="cyyuser",password="123456", host="192.168.1.197")
       cur = conn.cursor()

       cur.execute("INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) \
       VALUES (1, 'Paul', 32, 'California', 20000.00 )");

       cur.execute("INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) \
       VALUES (2, 'Allen', 25, 'Texas', 15000.00 )");

       cur.execute("INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) \
       VALUES (3, 'Teddy', 23, 'Norway', 20000.00 )");

       cur.execute("INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) \
       VALUES (4, 'Mark', 25, 'Rich-Mond ', 65000.00 )");

       conn.commit()
       print "Records created successfully";
       conn.close() 
       return

def  companySelect():
       conn = psycopg2.connect(database="cyy12", user="cyyuser",password="123456", host="192.168.1.197")
       cur = conn.cursor()
       cur.execute("SELECT id, name, address, salary  from COMPANY")
       rows = cur.fetchall()
       for row in rows:
              #result  ='$'.join(row)
              result  = "ID = "+str(row[0])
              result  += "NAME = "+row[1]
              result  += "ADDRESS = "+row[2]
              result  += "SALARY = "+ str(row[3])+ "\n"

              print result+"           ";
              #连接执行完要记得关了 
              #conn.close() 
      


def  companySelect2():
       conn = psycopg2.connect(database="cyy12", user="cyyuser",password="123456", host="192.168.1.197")
       cur = conn.cursor()

        # cur.execute("SELECT id, name, address, salary  from COMPANY")


       newsql ="""SELECT  procpid,  start,  now() - start AS lap, current_query FROM 
       (SELECT   backendid,  pg_stat_get_backend_pid(S.backendid) AS procpid,  pg_stat_get_backend_activity_start(S.backendid) AS start, 
       pg_stat_get_backend_activity(S.backendid) AS current_query FROM (SELECT pg_stat_get_backend_idset() AS backendid) AS S ) AS S ,
       pg_stat_activity pa  WHERE current_query <> '<IDLE>' and  procpid<> pg_backend_pid() and pa.pid=s.procpid and pa.state<>'idle'  ORDER BY lap DESC;"""
      
       #print newsql
       #查看PostgreSQL正在执行的SQL   
       cur.execute(newsql) 

       rows = cur.fetchall()
       #print rows
       for row in rows:
          #result  ='$'.join(row)
          result  = "   pid = "+str(row[0])
          result  += "  starttime = "+str(row[1])
          result  += "  laptime = "+str(row[2])
          result  += "  sql = "+ str(row[3])+ "\n"

          print "\n"+result
          #print "\n"+result+"          Operation done successfully";
          #连接执行完要记得关了 
          #conn.close() 
          print  conn
           


#compaInsert()
n = 1
while n <1000 :
        companySelect2()
        n=n+1
        print n
        time.sleep(1)