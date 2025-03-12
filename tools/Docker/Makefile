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


build-arm64:
	docker build --no-cache -t ${DOCKERTAG} -f ${DOCKERFILE} --platform ${PLATFORM-arm64} .
	docker tag ${DOCKERTAG} ${DOCKERHUBID}/${DOCKERTAG}


build-amd64:
	docker build --no-cache -t ${DOCKERTAG} -f ${DOCKERFILE} --platform ${PLATFORM-amd64} .
	docker tag ${DOCKERTAG} ${DOCKERHUBID}/${DOCKERTAG}


publish: build
	docker push ${DOCKERHUBID}/${DOCKERTAG}

run:
	sh runDocker.sh





