FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev curl

COPY ./requirements.txt /requirements.txt
WORKDIR /
RUN pip3 install -r requirements.txt

COPY . /

CMD python3 server.py