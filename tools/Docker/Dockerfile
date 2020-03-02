FROM python:3.8

RUN apt-get update && apt-get -y update

RUN pip3 install tinydb
RUN pip3 install flask
RUN pip3 install psutil
RUN pip3 install requests

RUN mkdir acme-cse
COPY acme.py acme-cse/
COPY acme.ini acme-cse/
COPY acme/ acme-cse/acme/
COPY apps/ acme-cse/apps/
COPY init/ acme-cse/init/
COPY webui/ acme-cse/webui/
WORKDIR acme-cse/

CMD ["python3", "acme.py"]
