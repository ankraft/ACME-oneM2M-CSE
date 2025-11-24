#
#	Makefile
#
#	To build the Docker image
#
#	Targets:
#		- build (default)
#		- publish
#		- run
#


DOCKERFILE = Dockerfile

DOCKERHUBID = ankraft
DOCKERTAG = acme-onem2m-cse
PLATFORM-amd64 = linux/amd64
PLATFORM-arm64 = linux/arm64

build: build-amd64


build-arm64:				## Build image for arm64 architecture 
	docker build --no-cache -t ${DOCKERTAG} -f ${DOCKERFILE} --platform ${PLATFORM-arm64} .
	docker tag ${DOCKERTAG} ${DOCKERHUBID}/${DOCKERTAG}


build-amd64:				## Build image for amd64 architecture (default)
	docker build --no-cache -t ${DOCKERTAG} -f ${DOCKERFILE} --platform ${PLATFORM-amd64} .
	docker tag ${DOCKERTAG} ${DOCKERHUBID}/${DOCKERTAG}


publish: build				## Push current image to DockerHub
	docker push ${DOCKERHUBID}/${DOCKERTAG}

run:					## Run the current image
	sh runDocker.sh


help:					## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make [command]\033[36m\033[0m\n\n  Commands:\n"} /^[$$()% a-zA-Z0-9_-]+:.*?##/ { printf "    \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

