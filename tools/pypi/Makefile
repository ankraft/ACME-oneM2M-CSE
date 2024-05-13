#
#	Makefile
#
#	To build the package and upload it to PyPi
#
#	Targets:
#		- build (default)
#		- publish
#		- clean
#		- install_local
#		- uninstall_local
#

SRCDIR = ../..
SOURCE = acme
PROJNAME = acmecse

PACKAGEDIR = ${SRCDIR}/${SOURCE}
PACKAGECOPY = ${SRCDIR}/${PROJNAME}
DISTDIR = ${SRCDIR}/dist


build: prepare _build finish

_build:
	cd ${SRCDIR} && python -m build -s
	cd ${SRCDIR} && python -m build 


publish: build
	twine upload `ls -t ${DISTDIR}/*.whl | head -1`


install_local:
	python -m pip install `ls -t ${DISTDIR}/*.whl | head -1`


uninstall_local:
	python -m pip uninstall `ls -t ${DISTDIR}/*.whl | head -1`


prepare:
	if [ ! -d ${PACKAGECOPY} ]; then \
		cp -r ${PACKAGEDIR} ${PACKAGECOPY}; \
	fi

finish:
	if [ -d ${PACKAGECOPY} ]; then \
		rm -r ${PACKAGECOPY}; \
	fi


clean: finish
	rm -r ${SRCDIR}/*.egg-info

# TODO remove dist ... directories


