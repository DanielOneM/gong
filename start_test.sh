docker build --rm -t gongworker .
docker network create --subnet 172.25.0.0/16 testnet
docker run -d --net testnet --name rmq -p 15672:15672 rabbitmq:3-management
echo 'waiting for rmq startup'
sleep 30
docker run -d --net testnet --name remotejasmin -v /home/dread/CODE/gong/logs/fake:/var/log/jasmin -p 8990:8990 jookies/jasmin:latest
echo 'waiting for jasmin startup'
sleep 30
docker run -d --net testnet --name gong gongworker 
