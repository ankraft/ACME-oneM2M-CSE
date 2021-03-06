[← README](../README.md) 

# Docker

## Downloading and Running From a Docker Image

A Docker image with reasonable defaults is available on Docker Hub: [https://hub.docker.com/repository/docker/ankraft/acme-onem2m-cse](https://hub.docker.com/repository/docker/ankraft/acme-onem2m-cse) .

You can download and run it with the following shell command:

```bash
$ docker run -it -p 8080:8080 --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

To adjust the output to the current terminal width run the image with the following command:

```bash
docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it -p 8080:8080 --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

## Build Your Own Docker Image

You can adapt (ie. configure a new Docker Hub ID) the build script and *Dockerfile* in the [tools/Docker](../tools/Docker) directory. It might be a good idea, for example, to run the CSE in head-less mode (command line argument *--headless*), which disables screen output.

The build script takes the current scripts, configuration, initialization resources etc., builds a new Docker image, and uploads the image to the configured Docker Hub repository.

[← README](../README.md) 
