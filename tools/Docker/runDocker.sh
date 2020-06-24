#!/bin/sh
DOCKERHUBID=ankraft

docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -p 8080:8080 --rm --name acme-onem2m-cse $DOCKERHUBID/acme-onem2m-cse
