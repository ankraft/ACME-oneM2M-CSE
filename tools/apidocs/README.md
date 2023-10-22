# Generate ACME API Documentation

This document provides instructions how to generate API documentation for
the ACME CSE implementation.


## Installation

Install the following packages via pip:

- To generate only the API documentation:

		pip3 install pydoctor

- To generate additionally a [Dash][1] docset:

		pip3 install doc2dash

## Generate the API Documentation and Docset

Run the following commands from within the *tools/apidocs* directory:

- To generate the API documentation in the sub-directory `apidocs`.

		pydoctor

	Configuration and command arguments are read from the *pydoctor.ini* configuration file in the same directory.

- To generate a [Dash][1] docset and automatically add it to Dash:

		doc2dash ../../docs/apidocs -a -f -n "ACME oneM2M CSE"




[1]: https://kapeli.com/dash

