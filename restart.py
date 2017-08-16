#coding=utf-8
import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
import time
from datetime import datetime

file_path="/data/wang/9000_status.txt"
#url="http://:120.132.50.181:9090/api/misc/db/test/334834"
url="http://123.59.53.69:9000/api/misc/db/test/334834"
t=datetime.now()
print(t)

try:
    url_status = requests.get(url,timeout=0.002)
    f = open(file_path,"a+")
    f.write(str(t))
    f.write('服务器第一次检测正常'+'\n')
    f.close()
    print(url_status.status_code)
except ReadTimeout:
    print('Timeout')
    f = open(file_path,"a+")
    f.write(str(t)+'服务器第一次检测不正常'+'\n')
    f.close()
except ConnectionError:
    print('Connection error')
except RequestException:
    print('Error')

