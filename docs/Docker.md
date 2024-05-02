[← README](../README.md) 

# Docker

## Downloading and Running From a Docker Image

A Docker image with reasonable defaults is available on Docker Hub: [https://hub.docker.com/repository/docker/ankraft/acme-onem2m-cse](https://hub.docker.com/repository/docker/ankraft/acme-onem2m-cse) .

You can download and run it with the following shell command:

```sh
docker run -it -p 8080:8080 --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

To adjust the output to the current terminal width run the image with the following command:

```sh
docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it -p 8080:8080 --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

## Build Your Own Docker Image

You can adapt (ie. configure a new Docker Hub ID) the build script and *Dockerfile* in the [tools/Docker](../tools/Docker) directory. It might be a good idea, for example, to run the CSE in head-less mode (command line argument *--headless* or configuration setting *[console].headless*), which disables screen output.

The build script takes all the current scripts, attribute definitions etc. from the ACME module's *init* directory and includes them in the Docker image. The configuration file for the Docker image's *acme.ini* file is copied from file *acme.docker* from the *Docker* directory. Please make any necessary changes to that file before building the image.

## Using a Mapped Base Directory

The Docker image uses the *data* directory as the base directory for the CSE's runtime data. This directory can be mapped to a volume on the host system. For example, to use a local data directory as the base directory, run the following command:

```sh
docker run -it -p 8080:8080 -v /path/to/data:/data --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

This is useful for persisting data across container restarts and to provide a different configuration file that is then used instead of the default *acme.ini* file.


## Environment Variables in Configuration Settings

ACME supports the use of environment variables in the configuration settings. This is useful when running the CSE in a Docker container, where the configuration settings can be set via environment variables. 

One example is to provide the Docker host's IP address to the CSE as the *cseHost* configuration settings.

The setting for *cseHost* in the *acme.ini* file should should be changed to the following:

```ini
[basic.config]
...
cseHost=${DOCKER_HOST_IP}
...
```

The value for this setting can be provided by setting the environment variable *DOCKER_HOST_IP* to the Docker host's IP address:

```sh
docker run -it -p 8080:8080 -v /path/to/data:/data -e DOCKER_HOST_IP=`ifconfig en0 | awk '$1 == "inet" {print $2}'` -rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

Values for other setting, such as credentials, can be provided in the same way.


[← README](../README.md) 
