#/usr/bin/python
# encoding=utf-8
import urllib2,urllib
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
import json,math,os,MySQLdb,hashlib,time
from base64 import b64decode,b64encode
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

conn = MySQLdb.connect("localhost","pingantest","E9Zhdt7svv5","guns",charset='utf8')
cur=conn.cursor()

coupon={"appkey":"61000143","secr":"e55f7b0f-a1a3-4dce-a7a6-51ebf226fe14","pubkey":"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCEwMTJ/QkR+nLiUF+vcX/GcDJGrOhPSQPB5KxdngZqN+1w9GbRkyWUPgJPcUBONGMrRbJFylFrYYX5p5fWcSEAjJF7jRUckxMdJNHQ4YCGh3AO1/PAHypDsKdgaybMXSowhnhRutMrJn3DTYGAZ/BJX9SkblTpK141n66717w0mwIDAQAB"}
nocoupon={"appkey":"61000146","secr":"9e461435-1ee3-4668-9877-b02a4d3f257a","pubkey":"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCDSQzMo/xchfkVEryWOjYmHmS9Y23vWfLG4wr3/r5fwUctkr4hS7imv6ZrxCtSR5/wJoD2vV5UOB2sLc7x5LU2YRWfqjTwMp6sclF9n3UfaAy8cVTT2QqwemJTTw9Wns4lnrrQHEOFQNfIKdWNKWVgICQCfHBhZ1OhkKp30oOqrwIDAQAB"}

# online
coupon={"appkey":"61000179","secr":"05d6700c-2dc2-4ba8-b30a-0dd13f8adaa0","pubkey":"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDE2AMU7Gh5tVz5QazUpNXSZ1+shk3tqZ+dgEMH3gthQp5nAnLv4W2aOaz4uWzW9CKSotKUPxU5YbcWUp3jxvEDLcuRmaEZaxU/emhunv91C2DCNeQSqVlDzjT23RIlbS5rKmQ/AeN9xFKCbM3QhKS3brWh8VxcLKj94kEtR/LT2QIDAQAB"}
nocoupon={"appkey":"61000181","secr":"03b92c06-7e22-43f2-9fee-a02a6b7b3dab","pubkey":"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCEP57g+QKxthc+H2GQnjoL/ik+vyYf7XVdrO7wuUda/V6Jy2CCpQXQHr1vilkLxmlU+O7eimHad6IunXNw99XhvcgoISdcQxHYYzovuJBEoIKTbu0CdFB+RtKLLKG8KGu0x9UEZhUTDmKYTqY/l6loiCsxJ/KenGx2knPmND+liwIDAQAB"}

host="open.d.api.edaijia.cn"


def sig(params,use_coupon=False):
	siginfo=(coupon if use_coupon else nocoupon)
	params['appkey']=siginfo["appkey"]

	params["from"]='test'
	params["ver"]='3'
	params["timestamp"]=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
	keys=params.keys()
	orgstr=''
	for key in sorted(keys):
		orgstr+=str(key)+str(params[key])

	orgstr+=siginfo["secr"]
	sig=hashlib.md5(orgstr).hexdigest()
	params['sig']=sig
	return params
def get(path,params,host=host):
	url="http://%s/%s?%s"%(host,path,urllib.urlencode(params,"utf-8"))
	res=urllib2.urlopen(url).read()
	print url,res
	return res

def getToken(phone,use_coupon=False):
	siginfo=(coupon if use_coupon else nocoupon)
	rsab64key=siginfo["pubkey"]

	params={"phone":str(phone),"randomkey":"xxxxxxxxxxxxxxxx","os":"android","udid":"1"}

	params=sig(params,use_coupon)
	rsakey=RSA.importKey(b64decode(rsab64key))
	cipher = Cipher_pkcs1_v1_5.new(rsakey)
	org=[]
	for param in params:
		org.append("%s=%s"%(param,params[param]))
	org='&'.join(org)
	step1=cipher.encrypt(org[:117])
	step2=cipher.encrypt(org[117:])
	cipher_text = b64encode(step1+step2)
	res=json.loads(get("customer/getAuthenToken",{"appkey":siginfo["appkey"],"data":cipher_text}))
	# print res
	res=AES.new(params["randomkey"], AES.MODE_ECB, params["randomkey"]).decrypt(b64decode(res["data"]))
	return res.replace("\n","").replace("token=","")
	# print cipher_text

def orderDetail(token,oid,use_coupon=False):
	params={"orderId":oid,"token":token,"needAll":"1"}
	params=sig(params,use_coupon)

	return get("order/detail",params)
def orderList(token):
	params={"token":token,"pageSize":10,"pageNo":1}
	# params={"token":token}
	return get("order/history/list",params)


def impInfo(phone,bookingId,use_coupon=False):
	siginfo=(coupon if use_coupon else nocoupon)
	params={"bookingId":bookingId,"phone":phone,"channel":siginfo["appkey"],"needCancelOrder":"1"}
	params=sig(params,use_coupon)
	return get("order/impInfo",params)

def getDrivers(token,use_coupon=False):
	params={"pollingCount":"1","gpsType":"baidu","token":token}
	params=sig(params,use_coupon)
	return get("customer/info/drivers",params)

def updateBonusAndProcess(status,orderId,couponId):
		processMsg="进行中"
		if status==1:
			if couponId!=None :
				cur.execute("update guns.coupon_type set usedcount=usedCount+1 where id in (select couponTypeId from guns.coupon where couponId='%s' and `status`=1)limit 1"%couponId)
				cur.execute("update guns.coupon set `status`=3 where couponId='%s' and `status`=1"%couponId)
			processMsg="已完成"

		elif status==2:
			if couponId!=None :
				cur.execute("update guns.coupon set `status`=0,useTime=0 where couponId='%s' and `status`=1"%couponId)
				cur.execute("update guns.order_info set couponId=null where orderId='%s' limit 1"%orderId)
			processMsg="已取消"
		if processMsg!="":
			cur.execute("insert ignore into guns.order_process(orderId,recordTime,description) values('%s','%s','%s')"%(orderId,time.time(),processMsg))
		conn.commit()

cur.execute("select id,orderId,edjbookingId,customerPhone,status,couponId,source from guns.order_info where (`status`=0  or (`status`=2 and not isnull(couponId))) and orderTime>unix_timestamp()-864000 order by customerPhone desc;")
# cur.execute("select id,orderId,edjbookingId,customerPhone,status,couponId,source from guns.order_info where orderTime>unix_timestamp()-864000 order by customerPhone desc;")
# processing finnished canceled
orderStatus=[set([101,201,301,302,303,304]),set([500,501,600]),set([401,402,403,404,405,406,502,503,504,505,506,509,508,509])]

tokens={}
for order in cur.fetchall():
	orgid=order[0]
	orderId=order[1]
	bookingId=order[2]
	phone=order[3]
	couponId=order[5]
	source=order[6]
	try:
	# if True:
		use_coupon=(source==coupon["appkey"])
		res=json.loads(impInfo(phone,bookingId,use_coupon))
		print res
		if len(res["data"]['drivers'])!=0:
			status=0
			order=res["data"]["drivers"][0]["orders"][0]
			print ">>>:",int(order['orderStateCode']) , int(order['orderStateCode']) in orderStatus[2]
			if int(order['orderStateCode']) in orderStatus[1]:
				status=1

			elif int(order['orderStateCode']) in orderStatus[2]:
				status=2
			updateBonusAndProcess(status,orderId,couponId)
			sql="update guns.order_info set `status`=%s , edjOrderid='%s' where id=%s limit 1"%(status,order["orderId"],orgid)
			cur.execute(sql)
			conn.commit()
	except Exception as e:
		print e
# cur.execute("select id,edjOrderId,customerPhone,status,source,orderId,couponId from guns.order_info where not isnull(edjOrderId) and `status`<>0 and orderTime>unix_timestamp()-864000 order by customerPhone desc;")
cur.execute("select id,edjOrderId,customerPhone,status,source,orderId,couponId from guns.order_info where not isnull(edjOrderId) and isnull(endAddr) and `status`<>0 and orderTime>unix_timestamp()-864000 order by customerPhone desc;")

for order in cur.fetchall():
	order_id=order[0]
	edjOrderId=order[1]
	customerPhone=order[2]
	status=int(order[3])
	source=order[4]
	orderId=order[5]
	couponId=order[6]
	if edjOrderId!=None:
		try:
			use_coupon=(source==coupon["appkey"])
			tokentype=("coupon" if use_coupon else "nocoupon")
			if customerPhone in tokens and tokentype in tokens[customerPhone]:
				token=tokens[customerPhone][tokentype]
			else:
				token=getToken(customerPhone,use_coupon)
				if not customerPhone in tokens:
					tokens[customerPhone]={}
				tokens[customerPhone][tokentype]=token
			res=orderDetail(token,edjOrderId,use_coupon)
			print res
			order_res=json.loads(res)
			if not "driver" in order_res["data"]:
				continue
			driverInfo=order_res['data']['driver']
			orderInfo=order_res['data']

			driver,driverPhone,driverSource,arriveDistance,mileage=driverInfo['name'],'-',"e代驾",'0',math.floor(int(driverInfo['distance'][0:-1])*0.001)
			endTime=orderInfo['endTime']
			startTime=orderInfo['startTime']
			print ">>",status,orderId,couponId
			updateBonusAndProcess(status,orderId,couponId)
			endAddr=orderInfo['locationEnd']
			bookingTime=time.mktime(time.strptime(orderInfo["bookingTime"],"%Y-%m-%d %H:%M:%S"))

			waitingTime=int(orderInfo['waitingTime'][:-2] if "waitingTime" in orderInfo else 0)

			mileageFee=orderInfo['kiloFee'][:-1]
			waitFee=int(orderInfo['waitingFee'] if 'waitingFee' in orderInfo else '0')
			subsidyFee=int(orderInfo['subsidy'][:-1] if 'subsidy' in orderInfo else '0')
			# customerComments
			surfee=1;
			price=0
			for i in orderInfo['collectionFee']:
				price+=int(i['value'][0:-1])
				if i['key']==u"保险费":
					surfee=int(i['value'][0:-1])
				elif waitFee==0 and i['key'][:3]==u"等候费":
					waitFee=int(i['value'][0:-1])
				else:
                	subsidyFee+=int(i['value'][0:-1])
                					# break
            subsidyFee-=int(mileageFee)
			if couponId!=None:
				prisql="SELECT price FROM guns.coupon_type where id in (select couponTypeId from guns.coupon where couponId in (select couponId from guns.order_info where orderId='%s'));"%orderId
				cur.execute(prisql)
				price=int(cur.fetchone()[0])
			else:
				price=0
			oinfsql="update guns.order_info set price=%s ,endAddr='%s' where orderId='%s';"%(price,endAddr,orderId)
			odinfsql="insert ignore into guns.order_driver(orderId,driver,driverPhone,driverSource,arriveDistance,mileage,endTime,startTime,arriveTime,waitTime) values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');"%(orderId,driver,driverPhone,driverSource,arriveDistance,mileage,endTime,startTime,bookingTime,waitingTime)
			feesql="insert ignore into guns.order_fee(orderId,price,mileageFee,waitFee,subsidyFee) values('%s','%s','%s','%s','%s');"%(orderId,price,int(mileageFee)+ (0 if int(mileageFee)==0 else surfee),waitFee,subsidyFee)

			cur.execute(oinfsql)
			cur.execute(odinfsql)
			cur.execute(feesql)
			conn.commit()
		except Exception as e:
			print ">>:",e




