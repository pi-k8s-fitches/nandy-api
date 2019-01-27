ARG BASE
FROM ${BASE}

RUN apk add git

COPY entry.sh /usr/bin/entry.sh

RUN mkdir -p /opt/pi-k8s

WORKDIR /opt/pi-k8s

ADD requirements.txt .

RUN pip install -r requirements.txt

ADD nandy-data nandy-data
WORKDIR /opt/pi-k8s/nandy-data
RUN python setup.py install
WORKDIR /opt/pi-k8s

ADD openapi openapi
ADD bin bin
ADD lib lib
ADD test test

ENV PYTHONPATH "/opt/pi-k8s/lib:${PYTHONPATH}"

CMD "/opt/pi-k8s/bin/api.py"
