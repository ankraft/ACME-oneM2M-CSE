# Installation

## Pre-Requisites

ACME requires **Python 3.10** or newer. Install it with your favorite package manager or as part of a virtual environment.

<mark>TODO copy article</mark>
You may consider to use a virtual environment manager like pyenv + virtualenv (see [this HowTo](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/137) or [this tutorial](https://realpython.com/python-virtual-environments-a-primer/){target=_new}).


## Installation and First Setup

### Installation

There are two ways to install the ACME CSE: using *pip* or by doing a manual installation.

=== "Using pip (Package Installation)"

	Run *pip* to install the ACME CSE from the Python Package Index (PyPI):

	```bash title="Install ACME CSE"
	python -m pip install acmecse
	```

	This will install the latest version of the ACME CSE and all required dependencies. 

	You can also upgrade to the latest version by running:

	```bash title="Upgrade ACME CSE"
	python -m pip install --upgrade acmecse
	```

=== "Manual Installation"

	1. Install the ACME CSE by cloning the repository, or by downloading the [latest](https://github.com/ankraft/ACME-oneM2M-CSE/releases/latest){target=_new} release package, unpacking it, and copying the whole distribution to a new directory.  

		```bash title="Clone the Repository"
		git clone https://github.com/ankraft/ACME-oneM2M-CSE.git
		cd ACME-oneM2M-CSE
		```

	1. It is recommend to install the required packages by running the following command:

		```bash title="Install Required Packages"
		python3 -m pip install -r requirements.txt
		```

		You may also install the packages manually, but make sure to install the exact versions as specified in the *requirements.txt* file.

		An alternative is to let ACME handle the installation automatically when running it for the first time (see below).


### Guided Configuration

The ACME CSE can be configured by an interactive process when it is started for the first time. This process will create a configuration file that can be edited later.

1. Run the CSE for the first time.  
You can start the CSE by simply running it from the command line:

	=== "For Package Installation "

		Run the following command from the command line from **within any directory that uses the Python environment where you installed the package**:

		```bash title="Start ACME CSE"
		acmecse
		```

	=== "For Manual Installation"

		Run the following command from the command line from **within the directory where you installed the CSE**:

		```bash title="Start ACME CSE as a module"
		python3 -m acme
		```

	Please refer to the [Running](Running.md) documentation for more detailed instructions how to start and run the ACME CSE.

    If you have not installed the required packages during the installation ACME will ask you to install them now. This can be done by ACME automatically, or you can do it manually (see above).

	If no configuration file is found in the *base directory* then an interactive configuration process is started. The configuration is saved to a configuration file. e.g. *acme.ini* by default. 

	The *base directory* by default is the directory where the CSE is started from. This directory can be changed by the *--base-directory* (or *-dir*) command line argument to a different directory. 

	<figure>
	![ACME CSE Guided Configuration](../images/bootstrapConfig.gif)
	<figcaption>ACME CSE Guided Configuration</figcaption>
	</figure>

	After the configuration is saved, the CSE is started. with this configuration.

1.  After terminating the CSE again you can edit that configuration file and add more settings if necessary.
	There are a lot of individual settings to configure here. Mostly, the defaults should be sufficient, but individual settings can be applied to each of the sections.  
	See the [Configuration](docs/Configuration.md) documentation for further details, and the defaults configuration file [acme.ini.default](../acme/init/acme.ini.default).

<mark>TODO handle following</mark>

---
## Certificates and Support for https

To enable https you have to set various settings [\[server.http.security\] - HTTP Security Settings](Configuration.md#security_http), and provide a certificate and a key file. 
One way to generate those files is the [openssl](https://www.openssl.org){target=_new} tool that may already be installed on your OS. The following example shows how to 
generate a self-signed certificate:

	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -nodes -days 1000

This will generate the self-signed certificate and private key without password protection (*-nodes*), and stores them in the files *cert.pem* and *key.pem* respectively. 
*openssl* will prompt you with questions for *Country Name* etc, but you can just hit *Enter* and accept the defaults. The *-days* parameter affects the certificate's
expiration date.

Please also consult the *openssl* manual for further instructions. 

After you generated these files you can move them to a separate directory (for example you may create a new directory named *cert* in ACME's installation directory) and set the *caCertificateFile* and *caPrivateKeyFile* configuration parameters in the *acme.ini* configuration file under the *\[server.http.security\]* section accordingly.

---

<mark>TODO move</mark>

## Third-Party Components
The following third-party components are used by the ACME CSE.

### Core CSE
- The [cbor2](https://github.com/agronholm/cbor2){target=_new} package is used to parse and create CBOR serializations. MIT License.
- The CSE uses the [Flask](https://flask.palletsprojects.com/){target=_new} web framework to service http(s) requests. BSD 3-Clause License.
- [flask-cors](https://github.com/corydolphin/flask-cors/){target=_new} is a *Flask* extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
- [InquirerPy](https://github.com/kazhala/InquirerPy/){target=_new} is a collection of common interactive command-line interfaces. MIT License.
- The [isodate](https://github.com/gweis/isodate){target=_new} package is used to parse and handle ISO 8601 time, date, and duration. BSD License.
- The [paho-mqtt](https://www.eclipse.org/paho/){target=_new} library provides a client class which enables applications to connect to an MQTT broker. Eclipse Public License 1.0 .
- The [plotext](https://github.com/piccolomo/plotext){target=_new} library offers functions to plot graphs in the text console. MIT License.
- [Psycopg](https://www.psycopg.org){target=_new} is a PostgreSQL adapter for the Python programming language. GNU Lesser General Public License.
- [rdflib](https://github.com/RDFLib/rdflib){target=_new} is a Python library for working with RDF. BSD 3-Clause License.
- The CSE uses the [Requests](https://requests.readthedocs.io){target=_new} HTTP Library to send requests vi http. Apache2 License
- The CSE uses the [Rich](https://github.com/willmcgugan/rich){target=_new} text formatter library to format various terminal output. MIT License. 
- [shapely](https://github.com/shapely/shapely){target=_new} is a library for manipulation and analysis of geometric objects. BSD 3-Clause License. 
- [Textual](https://github.com/textualize/textual){target=_new} is a Rapid Application Development framework for to build textual user interfaces in Python. MIT License.
- [waitress](https://github.com/Pylons/waitress){target=_new} is a production-quality pure-Python WSGI server with very acceptable performance. ZPL 2.1 License.
- To store resources the CSE uses the lightweight [TinyDB](https://github.com/msiemens/tinydb){target=_new} document database. MIT License.


### Web UI Components
- TreeJS: [https://github.com/m-thalmann/treejs](https://github.com/m-thalmann/treejs){target=_new}, MIT License.
- Picnic CSS : [https://picnicss.com](https://picnicss.com){target=_new}, MIT License.
