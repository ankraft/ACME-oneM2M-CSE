FROM python:3.11

RUN apt-get update && apt-get -y update

RUN pip3 install acmecse

RUN mkdir data
COPY acme.ini data/acme.ini


# Expose default port for the bindings: http, mqtt, coap
EXPOSE 8080/tcp
EXPOSE 8180/tcp
EXPOSE 5683/udp

CMD ["acmecse", "-dir", "/data", "--headless" ]
