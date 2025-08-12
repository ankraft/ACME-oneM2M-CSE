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

DOCDIR = ../../docs
APIDOCS = ${DOCDIR}/apidocs
TITLE = ACME oneM2M CSE
DASHDOCSET = ${DOCDIR}

build: pydoctor

pydoctor:
	pydoctor

open:
	open ${APIDOCS}/index.html

open-missing:
	open ${APIDOCS}/undoccedSummary.html

dash:
	doc2dash "${APIDOCS}" -f -n "${TITLE}" -d "${DASHDOCSET}" -I index.html

dash-install:
	open "${DASHDOCSET}/${TITLE}.docset"

clean:
	rm -r ${APIDOCS}
	rm -r "${DASHDOCSET}.docset"


