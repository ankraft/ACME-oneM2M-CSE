#!/bin/sh
DOCKERHUBID=ankraft

# Get the Docker host's IP address. Used for testing notifications
# This command works for MacOS. Change the following line to your OS. Comment it when you don't want send notifications
hostIP=`ipconfig getifaddr en1`

# run ACME in Docker
if [ -n "$hostIP" ]; then
	docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it -p 8080:8080 --add-host="localhost:$hostIP" --rm --name acme-onem2m-cse $DOCKERHUBID/acme-onem2m-cse
else
	docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it -p 8080:8080  --rm --name acme-onem2m-cse $DOCKERHUBID/acme-onem2m-cse
fi

