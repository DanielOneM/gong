# start from base
FROM ubuntu:14.04
MAINTAINER Daniel Enache <daniel.enache@onem.com>

# install system-wide deps for python and node
RUN apt-get -yqq update
RUN apt-get -yqq install python-pip python-dev

# copy our application code
ADD gong /opt/gong
WORKDIR /opt/gong

# fetch app specific deps
RUN pip install -r requirements.txt

# expose port
EXPOSE 5000

# start app
CMD [ "python", "/opt/gong/gong-worker.py -n test -p 2775 --rabbit_port 5672" ]
