# Docker

This section describes how to create and run a Docker image for the ACME CSE. 


## Running from DockerHub

A Docker image with reasonable defaults is available on Docker Hub: [https://hub.docker.com/repository/docker/ankraft/acme-onem2m-cse](https://hub.docker.com/repository/docker/ankraft/acme-onem2m-cse){target = _new} .

You can download and run it with the following shell command:

```sh title="Download Image and Run"
docker run -it -p 8080:8080 --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

To adjust the output to the current terminal width run the image with the following command:

```sh title="Run Container with Terminal Width"
docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -it -p 8080:8080 --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```


## Build Your Own Docker Image

You can adapt (ie. configure a new Docker Hub ID) the build script and *Dockerfile* in the [tools/Docker](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/tools/Docker){target=_new} directory. It might be a good idea, for example, to run the CSE in head-less mode (command line argument `--headless` or configuration setting *[console].headless*), which disables screen output.

The build script takes all the current scripts, attribute definitions etc. from the ACME module's *init* directory and includes them in the Docker image. The configuration file for the Docker image's *acme.ini* file is copied from file *acme.docker* from the *Docker* directory. Please make any necessary changes to that file before building the image.


## Running the CSE 

### Mapped Base Directory

The Docker image uses the *data* directory as the base directory for the CSE's runtime data. This directory can be mapped to a volume on the host system. For example, to use a local data directory as the base directory, run the following command:

```sh title="Run Container with Mapped Base Directory"
docker run -it -p 8080:8080 -v /path/to/data:/data --rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

This is useful for persisting data across container restarts and to provide a different configuration file that is then used instead of the default *acme.ini* file.


###  Environment Variables

ACME supports the use of environment variables in the configuration settings. This is useful when running the CSE in a Docker container, where the configuration settings can be set via [environment variables](../setup/Configuration-introduction.md#environment-variables). 

One example is to provide the Docker host's IP address to the CSE as the *cseHost* configuration settings.

The setting for *cseHost* in the *acme.ini* file should should be changed to the following:

```ini title="Use Environment Variable to set Host IP"
[basic.config]
...
cseHost=${DOCKER_HOST_IP}
...
```


The value for this setting can be provided by setting the environment variable *DOCKER_HOST_IP* to the Docker host's IP address:

```sh title="Run Container with Docker Host IP Environment Variable"
docker run -it -p 8080:8080 -v /path/to/data:/data -e DOCKER_HOST_IP=`ifconfig en0 | awk '$1 == "inet" {print $2}'` -rm --name acme-onem2m-cse ankraft/acme-onem2m-cse
```

Values for other setting, such as credentials, can be provided the same way.
