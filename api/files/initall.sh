#!/bin/sh

cd /root/api/
/root/api/trackitio initall
while [ $? != 0 ]
do
    echo "Initall crashed, try again in 10s..."
    sleep 10
    /root/api/trackitio initall
done
/root/api/trackitio flushcache

while [ 42 ]
do
    echo "Initall successfully ended! Waiting for new deployment..."
    sleep 10
done
