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


build:
	docker build --no-cache -t ${DOCKERTAG} -f ${DOCKERFILE} .
	docker tag ${DOCKERTAG} ${DOCKERHUBID}/${DOCKERTAG}

publish: build
	docker push ${DOCKERHUBID}/${DOCKERTAG}

run:
	sh runDocker.sh





