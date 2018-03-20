cd $(dirname $0)

source /etc/profile 
SYSTEM_TIME=`date '+%Y-%m-%d %T'`

count=`ps -ef | grep "logstash" | grep -v grep | wc -l`
if [ $count -eq 0 ];then
echo $SYSTEM_TIME >> /data/cyy928/crond/check_logstash.log
echo "logstash is down" >> /data/cyy928/crond/check_logstash.log
nohup /data/cyy928/logstash/logstash-5.0.0/bin/logstash -f /data/cyy928/logstash/logstash-5.0.0/config/log.conf  &

fi
