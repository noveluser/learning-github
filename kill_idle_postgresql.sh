#!/bin/sh
source /etc/profile
export PGPASSWORD=lkkRrrhO
time=$(date +"%Y%m%d %T")
echo "$time"  >> /data/shellscript/terminal.log
psql -U cyyuser cyydb -h 127.0.0.1 -c "select pg_terminate_backend(pid) from pg_stat_activity where state like 'idle in%' and current_timestamp - query_start > interval '60 seconds';" >> /data/shellscript/terminal.log