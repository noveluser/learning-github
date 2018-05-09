#pid=$(ps -df | pgrep -f python2.7)  #获取实例pid
#echo "kill process $pid" &> /dev/null
#kill -9 $pid
#rm  -rf /tmp/cws.lock
echo "0" > /data/cyy928/crontab/9001_status.txt
echo "0" > /data/cyy928/crontab/9002_status.txt
echo "0" > /data/cyy928/crontab/9003_status.txt
echo "0" > /data/cyy928/crontab/9004_status.txt
