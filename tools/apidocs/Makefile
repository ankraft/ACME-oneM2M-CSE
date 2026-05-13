#

#	Makefile
#
#	To build the API documentation
#
#	Targets:
#		- build (default)
#		- pydoctor - generate API documentation using PyDoctor
#		- open - open the generated API documentation in a web browser
#		- open-missing - open the undoccedSummary.html file in a web browser
#		- dash - generate a .docset for Dash documentation
#		- dash-install - install and open the generated .docset in Dash
#		- clean - clean up generated files
#

ROOTDIR= ../..
DOCDIR = ${ROOTDIR}/docs
APIDOCS = ${DOCDIR}/apidocs
MKDOCSDIR = ${ROOTDIR}/../ACME-oneM2M-CSE-mkdocs
TITLE = ACME oneM2M CSE
DASHDOCSET = ${DOCDIR}

build: pydoctor

pydoctor:				## Build API documentation (default)
	find ${ROOTDIR} -type d -name __pycache__ -exec rm -rf {}  + 2>/dev/null || true
	pydoctor

open:					## Open API documentation in the default web browser
	open ${APIDOCS}/index.html

open-missing:				## Open a list of undocumented items in the default web browser
	open ${APIDOCS}/undoccedSummary.html

dash:					## Generate a docset for Dash documentation
	doc2dash "${APIDOCS}" -f -n "${TITLE}" -d "${DASHDOCSET}" -I index.html

dash-install:				## Install and open the generated docset in Dash
	open "${DASHDOCSET}/${TITLE}.docset"


publish: 				## Publish the API docs to the documentation website
	-cd ${MKDOCSDIR} && \
	git checkout gh-pages && \
	git pull && \
	mkdir api
	cp -r ${APIDOCS}/* ${MKDOCSDIR}/api
	-cd ${MKDOCSDIR} && \
	git add api && \
	git commit -uno -m "adding api docs" && \
	git push 
	-cd ${MKDOCSDIR} && \
	git checkout main



clean:					## Remove generated files
	-rm -r ${APIDOCS}
	-rm -r "${DASHDOCSET}.docset"


help:					## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make [command]\033[36m\033[0m\n\n  Commands:\n"} /^[$$()% a-zA-Z0-9_-]+:.*?##/ { printf "    \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

