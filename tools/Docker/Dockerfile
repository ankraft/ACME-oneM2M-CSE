FROM python:3.11

RUN apt-get update && apt-get -y update

RUN pip3 install acmecse

RUN mkdir data
COPY acme.ini data/acme.ini
EXPOSE 8080

CMD ["acmecse", "-dir", "/data"]
