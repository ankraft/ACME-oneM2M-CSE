# Howto build a PyPi distribution

This document describes how to build a PyPi distribution of the CSE.

## Prerequisites

- build environment

	pip install build

- twine

	pip install twine

## Building the distribution


### Build

Run the following command in the *tools/pypi* directory

	make

### Manual Build

Run the following command in the root directory of the CSE:

	python -m build -s
	python -m build

This will create a source distribution and a wheel distribution in the `dist` directory.

## Uploading the distribution

To upload the distribution to PyPi, you need to have a PyPi account and the `twine` package installed.

Run the following command:

	twine upload dist/<filename>


