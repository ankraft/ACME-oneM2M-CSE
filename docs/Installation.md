[← README](../README.md) 

# Installation

## Prerequisites
In order to run the CSE the following prerequisites must be fulfilled:

### Python

ACME requires **Python 3.8** or newer. Install it with your favorite package manager.

You may consider to use a virtual environment manager like pyenv + virtualenv (see, for example, [this tutorial](https://realpython.com/python-virtual-environments-a-primer/)).

### Frameworks and Libraries

- **cbor2**: The [cbor2](https://github.com/agronholm/cbor2) package is used to parse and create CBOR serializations.
- **flask**: The CSE uses the [Flask](https://flask.palletsprojects.com/) web framework to service http(s) requests.
- **isodate**: The [isodate](https://github.com/gweis/isodate) package is used to parse and handle ISO 8601 time, date, and duration.
- **psutil**: The [psutil](https://pypi.org/project/psutil/) package is used to gather various system information for the CSE's hosting node resource.
This package might not be available for every hardware  or OS platform. In this case you should remove it from the install command below. You should also disable the **CSE-Node** application in the configuration file (see [Configurations for the CSE Node App](Configuration.md#cse_node)).
- **requests**: The CSE uses the [Requests](https://requests.readthedocs.io) HTTP Library to send requests vi http.
- **Rich**: The CSE uses the [Rich](https://github.com/willmcgugan/rich) text formatter library to format various terminal output.
- **tinydb 4.x** : To store resources the CSE uses the lightweight [TinyDB](https://github.com/msiemens/tinydb) document database.

Install these packages by running the following command:

	python3 -m pip install -r requirements.txt

or install all of them manually:  

	python3 -m pip install cbor2 flask isodate psutil requests rich tinydb


## Installation and Configuration

Install the ACME CSE by copy the whole distribution to a new directory. You also need to copy the configuration file [acme.ini.default](acme.ini.default) to a new file *acme.ini* and make adjustments to that new file.

	cp acme.ini.default acme.ini

Please have a look at the configuration file. All the CSE's settings are read from this file. 

There are a lot of individual things to configure here. Mostly, the defaults should be sufficient, but individual settings can be applied to each of the sections.

See [Configuration](Configuration.md) for further details on the configuration.

Also see the [Docker](Docker.md) instructions on how to build and run your own CSE Docker image.


## Third-Party Components
The following third-party components are used for the ACME CSE.

### Core CSE
- cbor2 [https://github.com/agronholm/cbor2](https://github.com/agronholm/cbor2), MIT License
- Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/), BSD 3-Clause License
- isodate: [https://github.com/gweis/isodate](https://github.com/gweis/isodate), BSD License
- PSUtil: [https://github.com/giampaolo/psutil](https://github.com/giampaolo/psutil), BSD 3-Clause License
- Requests: [https://requests.readthedocs.io/en/master/](https://requests.readthedocs.io/en/master/), Apache2 License
- Rich: [https://github.com/willmcgugan/rich](https://github.com/willmcgugan/rich), MIT License 
- TinyDB: [https://github.com/msiemens/tinydb](https://github.com/msiemens/tinydb), MIT License


### UI Components
- TreeJS: [https://github.com/m-thalmann/treejs](https://github.com/m-thalmann/treejs), MIT License
- Picnic CSS : [https://picnicss.com](https://picnicss.com), MIT License

[← README](../README.md) 
