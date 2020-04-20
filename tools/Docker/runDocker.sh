#!/bin/sh
DOCKERHUBID=ankraft

docker run -p 8080:8080 --rm --name acme-onem2m-cse $DOCKERHUBID/acme-onem2m-cse
