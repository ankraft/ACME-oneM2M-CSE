FROM python:3.8

RUN apt-get update && apt-get -y update

RUN pip3 install cbor2
RUN pip3 install flask
RUN pip3 install isodate
RUN pip3 install psutil
RUN pip3 install requests
RUN pip3 install rich
RUN pip3 install tinydb

RUN mkdir acme-cse
COPY acme.py acme-cse/
COPY acme.ini acme-cse/
COPY acme/ acme-cse/acme/
COPY apps/ acme-cse/apps/
COPY init/ acme-cse/init/
COPY webui/ acme-cse/webui/
WORKDIR acme-cse/

#CMD ["python3", "acme.py", "--headless"]
CMD ["python3", "acme.py"]
