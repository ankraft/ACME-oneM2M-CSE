FROM python:3.8

RUN apt-get update && apt-get -y update

RUN pip3 install cbor2
RUN pip3 install flask
RUN pip3 install isodate
RUN pip3 install paho-mqtt
RUN pip3 install requests
RUN pip3 install rich
RUN pip3 install tinydb

RUN mkdir acme-cse
COPY tools/Docker/acme.docker acme-cse/acme.ini
COPY acme/ acme-cse/acme/
COPY apps/ acme-cse/apps/
COPY init/ acme-cse/init/
WORKDIR acme-cse/

CMD ["python3", "acme"]
