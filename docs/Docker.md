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

You can adapt (ie. configure a new Docker Hub ID) the build script and *Dockerfile* in the [tools/Docker](../tools/Docker) directory. It might be a good idea, for example, to run the CSE in head-less mode (command line argument *--headless* or configuration setting *[console].headless*), which disables screen output.

The build script take the current scripts, attribute definitions etc from the *init* directory and includes them in the Docker image. The configuration file for the Docker image's *acme.ini* file is copied from file *acme.docker* from the *Docker* directory. Please make any necessary changes to that file before building the image.

### Build

Clone then, on project root

```sh
$ docker build --no-cache -t acme-cse -f tools/Docker/Dockerfile .
```

### Run

``` sh
$ docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -d  -p 9090:9090 --name acme-cse acme-cse
```

#### With MongoDB as storage

``` sh
$ docker run -e COLUMNS="`tput cols`" -e LINES="`tput lines`" -d  -p 9090:9090 --name acme-cse acme-cse --headless --db-storage=mongo --db-host=127.0.0.1 --db-port=27017
```

_For setting mongo credentials (username and password) along with other configurations, modify configuration file_ `/acme-cse/acme.ini`

``` sh
$ docker exec -it acme-cse bash
$ vi acme.ini
```

[← README](../README.md) 
