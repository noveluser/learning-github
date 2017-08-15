#coding=utf-8
import requests
from requests.exceptions import ReadTimeout, ConnectionError, RequestException

file_path="/data/wang/9000_status.txt"
#url="http://:120.132.50.181:9090/api/misc/db/test/334834"
url="http://123.59.53.69:9000/api/misc/db/test/334834"

try:
    response = requests.get(url, timeout = 0.5)
    print(response.status_code)
except ReadTimeout:
    print('Timeout')
except ConnectionError:
    print('Connection error')
except RequestException:
    print('Error')
	
	

if response.status_code==200:
    f = open(file_path,'a')
    f.write('服务器第一次检测正常'+'\n')
    f.close()
    print(response.status_code)
else:
    f = open(file_path,'a')
    f.write('服务器第一次检测不正常'+'\n')
    f.close()
    print(response.status_code)
