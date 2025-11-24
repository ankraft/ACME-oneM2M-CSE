FROM python:3.11

RUN apt-get update && apt-get -y update

RUN pip3 install acmecse

RUN mkdir data
COPY acme.ini data/acme.ini
ADD runACME.sh runACME.sh


# Expose default port for the bindings: http, mqtt, coap
EXPOSE 8080/tcp
EXPOSE 8180/tcp
EXPOSE 5683/udp

# Use this command to run the CSE in headless mode
# CMD ["acmecse", "-dir", "/data", "--headless" ]

# Use this command to run the CSE in headless mode and support restarting the CSE
# without exiting the container
CMD ["/bin/sh", "runACME.sh" ]

