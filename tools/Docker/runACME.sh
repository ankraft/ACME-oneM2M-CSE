#!/bin/sh
# This script is used to run the ACME CSE in a Docker container.
# It will keep running the CSE in a loop until it exits with a code of 82,
# which indicates that the CSE is restarting. 

while true; do
    acmecse -dir /data --headless

	# If the exit code is 82, it means the CSE is restarting.
	# In this case, we will not exit the loop and will restart the CSE.
	if [ $? -ne 82 ]; then
        break
    fi

	echo "Restarting ACME CSE..."
done



