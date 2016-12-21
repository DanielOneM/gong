# start from base
FROM python:2.7-onbuild
MAINTAINER Daniel Enache <daniel.enache@onem.com>

# expose port
EXPOSE 2775

# start app
CMD python gong/worker/worker.py -n test -p 2775 --rabbit_host 172.25.0.2
