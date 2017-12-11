#!/bin/bash
# Script: /usr/local/cron/ssh_scan.sh
# Author cnscn <http://www.redlinux.org>
# Date: 2012-05-11
#此脚本由alex.wang学习并注释

export LC_ALL=UTC
#设定时区为UTC,这条命令好像会出错，注释掉也没有太大问题

#扫描10分钟内的登陆失败的IP
SCANNER=$( tm=$(date -d '10 minutes ago' +"%h %d %H") && \
             awk -v tm="$tm" ' $0 ~ tm &&  /Failed password/ && /ssh2/ { print $(NF-3) ; } ' /var/log/secure \
           | sort \
           | uniq -c \
           | awk '{print $1"="$2;}' \
        )
# date -d '10 minutes ago' +"%h %d %H" ，这条命令是查询10分钟之前，系统是那一天那一小时，例如会获得结果dec 11 11,那么就是12月11日11点这个小时
# awk -v tm="$tm" 赋值tm 为"$tm" ,我怀疑是将日期转化成字符串
#  $0 ~ tm   $0 表示整行 ， ~ 是匹配符 ,$0 ~ tm 表示将某一行匹配这个时间段的进行操作
#  /Failed password/ && /ssh2/  ，搜索出具备 Failed password 和  ssh2 这两个字符串的 文本
#  { print $(NF-3) ; } 表示 输出NF-3字段，  NF表示字段总数，也就是最后一个字段， NF-3就是倒数第四字段，也就是secure这个文件的IP字段
#  /var/log/secure  ，需要进行awk操作的文件名
#  sort |uniq -c   sort表示进行排序 ，uniq 就是去除重复的数据， uniq -c 就是对重复的数据计数，统计有多少个
#  awk '{print $1"="$2;}' 表示将筛选出来的数据，其中第一字段和第二字段中间添加”=“这个字符，我猜这种处理方法是将输出的数据变成一个字段，方便后期处理，不过我觉得不这么处理也应该可以
#  上面输出的结果类似这种  6=106.57.51.16
for i in $SCANNER
do
    #截取IP与数量
     IP=`echo $i|awk -F= '{print $2}'`
    NUM=`echo $i|awk -F= '{print $1}'`
	#   awk -F= '{print $2}' ， -F=表示分隔符是=,将$1和$2分隔开

    #数量大于8次，则使用iptables禁止IP
    if [ $NUM -gt 8 ]  
    then
        iptables -vnL | grep DROP | grep $IP &>/dev/null   #这条语句是看是否有被拒绝IP访问的规则，也就是这个IP是否已经被拒绝，如果没有，那么执行失败
        [ $? -eq 0 ] || /sbin/iptables -I INPUT -s $IP -j DROP   #$? -eq 0 ，如果上面那条语句执行失败，那么添加规则，drop
        echo "`date` $IP($NUM)" >> /var/log/scanner.log   #将相关信息写入scanner.log文件
    fi
done
#End of Script