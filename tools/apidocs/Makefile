#
#	Makefile
#
#	To build the API documentation
#
#	Targets:
#		- build (default)
#		- open
#		- open-missing
#		- clean
#

DOCDIR = ../../docs/apidocs

build: 
	pydoctor

open:
	open ${DOCDIR}/index.html

open-missing:
	open ${DOCDIR}/undoccedSummary.html

clean:
	rm -r ${DOCDIR}


