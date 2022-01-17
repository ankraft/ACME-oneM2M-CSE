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
- **InquirerPy**: [InquirerPy](https://github.com/kazhala/InquirerPy/) ist a collection of common interactive command-line user interfaces.
- **isodate**: The [isodate](https://github.com/gweis/isodate) package is used to parse and handle ISO 8601 time, date, and duration.
- **paho-mqtt**	: The [paho-mqtt](https://www.eclipse.org/paho/) library provides a client class which enables applications to connect to an MQTT broker.
- **requests**: The CSE uses the [Requests](https://requests.readthedocs.io) HTTP Library to send requests vi http.
- **Rich**: The CSE uses the [Rich](https://github.com/willmcgugan/rich) text formatter library to format various terminal output.
- **tinydb 4.x** : To store resources the CSE uses the lightweight [TinyDB](https://github.com/msiemens/tinydb) document database.

**Either** install these packages by running the following command (recommended):

	python3 -m pip install -r requirements.txt

**or** install them individually:  

	python3 -m pip install cbor2 flask InquirerPy isodate paho-mqtt requests rich tinydb

## Installation and Quick Configuration

1. Install the ACME CSE by cloning the repository, or by copying the whole distribution to a new directory.

		git clone https://github.com/ankraft/ACME-oneM2M-CSE.git
		cd ACME-oneM2M-CSE

1. Copy the configuration file [acme.ini.default](../acme.ini.default) to a new file *acme.ini* so that you can make adjustments to the configuration. Also, the ACME detects a file by this name and reads the configuration from it.

		cp acme.ini.default acme.ini

1.  Edit the configuration file *acme.ini*. The CSE's settings are read from this file.  
	There are a lot of individual things to configure here. Mostly, the defaults should be sufficient, but individual settings can be applied to each of the sections.  
	The next section describes the quick configuration procedure that is sufficient for most cases.

### Quick Configuration

The format of the configuration file follows the Windows INI file format with sections, keywords and values. 
A configuration file may include comments, where lines are starting with the characters "#"" or ";"" .

At the top of the configuration file *acme.ini* are templates for a section named *basic.config*. Uncomment one of these sections for the basic values
for either an IN (infra-structure node), MN (middle node), or ASN (application service node) configuration, and make changes to the following individual
configuration settings, if necessary. Running an IN-CSE might be the most common choice to start with.

- **cseType**  
The CSE type. Allowed values are: IN, MN, ASN .
- **cseID**  
The CSE-ID. This is just the ID, without a leading "/" character.
- **cseName**  
The name of the CSE. This is also the CSEBase's resource name.
- **adminID**  
The name of the admin originator for the CSE.
- **dataDirectory**  
The root directory for the data, init, log and cert directories. The built-in macro "${baseDirectory}" provides the path 
to the installation directory of the *acme* module itself.
- **networkInterface**  
The network interface to listen to. Use 0.0.0.0 for all interfaces.
- **cseHost**  
The IP address or hostname under which the CSE is reachable.
- **httpPort**  
The port for the CSE's HTTP server to listen for incoming requests.
- **logLevel**  
The level for log messages. Allowed values are: *debug*, *info*, *warning*, *error*, *off* .
- **databaseInMemory**  
Specify whether the CSE's database is stored in memory. Be aware that setting this configuration 
to "true" means that the database content is removed when the CSE terminates.

This quick configuration will configure a CSE that is reachable via http and that uses JSON as the default serialization.

The following additional configuration settings are only needed for MN-CSE and ASN-CSE installations, and in case the CSE should
register to another CSE. They provide the necessary information about the registrar CSE (ie. the rempote CSE that the CSE will register to).

- **registrarCseHost**  
The IP address of the registrar CSE.
- **registrarCsePort**  
The TCP port of the registrar CSE.
- **registrarCseID**  
The CSE-ID of the registrar CSE.
- **registrarCseName**  
The resource name of the registrar CSE's CSEBase.

Please see [Configuration](Configuration.md) for further details on the configuration, e.g. how to enable MQTT or to change other
CSE parameters.


### Examples

The following is an example for basic configuration for a IN-CSE.

	[basic.config]
	cseType=IN
	cseID=id-in
	cseName=cse-in
	adminID=CAdmin
	dataDirectory=${baseDirectory}
	networkInterface=0.0.0.0
	cseHost=127.0.0.1
	httpPort=8080
	logLevel=debug
	databaseInMemory=False

The following is an example for an MN-CSE. It will register to an IN-CSE that runs on the same host (ie. the address for the registrar CSE's is *127.0.0.1*, but uses a different port).

	[basic.config]
	cseType=MN
	cseID=id-mn
	cseName=cse-mn
	adminID=CAdmin
	dataDirectory=${baseDirectory}
	networkInterface=0.0.0.0
	cseHost=127.0.0.1
	httpPort=8081
	logLevel=debug
	databaseInMemory=False

	registrarCseHost=127.0.0.1
	registrarCsePort=8080
	registrarCseID=id-in
	registrarCseName=cse-in

## Running the CSE

Please refer to the [Running](Running.md) documentation for instructions how to start and run the ACME CSE next.

---
## Certificates and Support for https

To enable https you have to set various settings [\[server.http.security\] - HTTP Security Settings](Configuration.md#security_http), and provide a certificate and a key file. 
One way to generate those files is the [openssl](https://www.openssl.org) tool that may already be installed on your OS. The following example shows how to 
generate a self-signed certificate:

	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -nodes -days 1000

This will generate the self-signed certificate and private key without password protection (*-nodes*), and stores them in the files *cert.pem* and *key.pem* respectively. 
*openssl* will prompt you with questions for *Country Name* etc, but you can just hit *Enter* and accept the defaults. The *-days* parameter affects the certificate's
expiration date.

Please also consult the *openssl* manual for further instructions. 

After you generated these files you can move them to a separate directory (for example you may create a new directory named *cert* in ACME's installation directory) and set the *caCertificateFile* and *caPrivateKeyFile* configuration parameters accordingly.

---

## Third-Party Components
The following third-party components are used by the ACME CSE.

### Core CSE
- cbor2 [https://github.com/agronholm/cbor2](https://github.com/agronholm/cbor2), MIT License
- Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/), BSD 3-Clause License
- InquirerPy: [https://github.com/kazhala/InquirerPy](https://github.com/kazhala/InquirerPy), MIT License
- isodate: [https://github.com/gweis/isodate](https://github.com/gweis/isodate), BSD License
- paho-mqtt: [https://www.eclipse.org/paho/](https://www.eclipse.org/paho/), Eclipse Public License 1.0 
- Requests: [https://requests.readthedocs.io/en/master/](https://requests.readthedocs.io/en/master/), Apache2 License
- Rich: [https://github.com/willmcgugan/rich](https://github.com/willmcgugan/rich), MIT License 
- TinyDB: [https://github.com/msiemens/tinydb](https://github.com/msiemens/tinydb), MIT License


### Web UI Components
- TreeJS: [https://github.com/m-thalmann/treejs](https://github.com/m-thalmann/treejs), MIT License
- Picnic CSS : [https://picnicss.com](https://picnicss.com), MIT License

[← README](../README.md) 
