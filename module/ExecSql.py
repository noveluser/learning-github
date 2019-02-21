#!/usr/local/bin/python2.7 
#coding=utf-8

import psycopg2
import logging

file = '/data/cyy928/crontab/log/psql.log'

#定义日志输出格式
logging.basicConfig(level=logging.INFO,
        format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filename = file,
        filemode = 'a')

class ExecSql(object): 
    def __init__(self,database,user,password,host):
        self.db=database
        self.user=user
        self.pwd=password
        self.host=host        
        self._conn = self.GetConnect()
        if(self._conn):
            self._cur = self._conn.cursor()
            
    
    #连接数据库
    def GetConnect(self):
        conn = False
        try:
            conn = psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.pwd,
                database =self.db
            )
        except Exception as err:
            print("连接数据库失败, %s" % err)
        else:
            return conn
            
    #执行查询
    def ExecQuery(self,sql):
        res = ""
        try:
            self._cur.execute(sql)
            res = self._cur.fetchall()
            logging.info('数据查询成功:%s' % res)
        except Exception as err:
            logging.error('数据查询失败:%s' % err)
            return err
        else:
            return res
        

    #执行非查询类语句
    def ExecNonQuery(self, sql):
        flag = False
        try:
            self._cur.execute(sql)
            self._conn.commit()
            flag = True
            logging.info('数据修改成功:%r' % flag)
        except Exception as err:
            flag = False
            self._conn.rollback()
            logging.error('数据修改失败:%s' % err)
        else:
            return flag
     
    #关闭数据库连接
    def Close(self):
        if(self._conn):
            try:
                if(type(self._cur)=='object'):
                    self._cur.close()
                if(type(self._conn)=='object'):
                    self._conn.close()
            except:
                raise("关闭异常, %s,%s" % (type(self._cur), type(self._conn)))