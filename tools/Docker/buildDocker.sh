#!/bin/sh
DOCKERHUBID=ankraft

cd ../..
docker build --no-cache -t acme-onem2m-cse -f tools/Docker/Dockerfile .
docker tag acme-onem2m-cse $DOCKERHUBID/acme-onem2m-cse
docker push $DOCKERHUBID/acme-onem2m-cse
