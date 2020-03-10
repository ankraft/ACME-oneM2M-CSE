#!/bin/sh
cd ../..
docker build -t acme-onem2m-cse -f tools/Docker/Dockerfile .
docker tag acme-onem2m-cse ankraft/acme-onem2m-cse
docker push ankraft/acme-onem2m-cse
