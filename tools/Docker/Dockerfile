FROM python:3.10-slim

RUN apt-get update && apt-get -y update
RUN apt-get install vim-tiny -y

RUN mkdir acme-cse
COPY tools/Docker/acme.docker acme-cse/acme.ini
COPY acme/ acme-cse/acme/
COPY init/ acme-cse/init/
COPY requirements.txt acme-cse/requirements.txt

# RUN curl -LJO https://bootstrap.pypa.io/get-pip.py
WORKDIR acme-cse/
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "-m", "acme", "--config", "acme.ini" ]
CMD ["--headless"]
