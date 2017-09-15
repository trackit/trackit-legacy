#! /bin/bash

docker build -t trackitio_api:dev_427 .
docker stop trackitio_api_1 && docker rm trackitio_api_1
docker run -d --name=trackitio_api_1 --link trackitio_es1_1:es1 --link trackitio_mysql_1:mysql --link trackitio_redis_1:redis --link trackitio_telegraf_1:telegraf -v /tracktio/log:/root/log -v /home/giubil/trackit_io/api/files/api:/root/api trackitio_api:dev_427
