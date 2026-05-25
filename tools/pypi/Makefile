#
#	Makefile
#
#	To build the package and upload it to PyPi
#
# ATTENTION: Whether a normal or a development version of the package is built
# depends on the presence of the "-dev" tag in the "setup.py" file.
#

SRCDIR = ../..
SOURCE = acmecse

PACKAGEDIR = ${SRCDIR}/${SOURCE}
DISTDIR = ${SRCDIR}/dist

.PHONY: all


build: _build 				## (default) Build the package only


publish: build 				## Build and publish the package
	twine upload `ls -t ${DISTDIR}/*.whl | head -1`


install_local:				## Install the local wheel
	python -m pip install `ls -t ${DISTDIR}/*.whl | head -1`


uninstall_local:			## Uninstall the local wheel
	python -m pip uninstall `ls -t ${DISTDIR}/*.whl | head -1`

clean: _finish				## Remove all generated info files
	rm -r ${SRCDIR}/*.egg-info


help:					## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make [command]\033[36m\033[0m\n\n  Commands:\n"} /^[$$()% a-zA-Z0-9_-]+:.*?##/ { printf "    \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)



_build:
	cd ${SRCDIR} && python -m build -s
	cd ${SRCDIR} && python -m build -w

# TODO remove dist ... directories


$(VERBOSE).SILENT:
