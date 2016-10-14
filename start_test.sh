docker build --rm -t gongworker .
docker network create testnet
docker run -d --net testnet --name rmq -p 15672:15672 rabbitmq:3-management
docker run -d --net testnet --name remotejasmin -v /home/dread/CODE/gong/logs/fake:/var/log/jasmin -p 8990:8990 jookies/jasmin:latest
docker run -d --net testnet --name gong gongworker 
