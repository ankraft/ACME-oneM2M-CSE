[← README](../README.md) 

# Installation

### Python

ACME requires **Python 3.10** or newer. Install it with your favorite package manager or as part of a virtual environment.

You may consider to use a virtual environment manager like pyenv + virtualenv (see [this HowTo](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/137) or [this tutorial](https://realpython.com/python-virtual-environments-a-primer/)).

<a name="first_setup"></a>
## Installation and First Setup

### Using pip

Run *pip* to install the ACME CSE from the Python Package Index (PyPI):

	python -m pip install acmecse

This will install the latest version of the ACME CSE and all required dependencies. 

You can also upgrade to the latest version by running:

	python -m pip install --upgrade acmecse


### Manual Installation

1. Install the ACME CSE by cloning the repository, or by downloading the [latest](https://github.com/ankraft/ACME-oneM2M-CSE/releases/latest) release package, unpacking it, and copying the whole distribution to a new directory.

		git clone https://github.com/ankraft/ACME-oneM2M-CSE.git
		cd ACME-oneM2M-CSE

1. It is recommend to install the required packages by running the following command:

		python3 -m pip install -r requirements.txt

	You may also install the packages manually, but make sure to install the exact versions as specified in the *requirements.txt* file.

	An alternative is to let ACME handle the installation automatically when running it for the first time (see below).


### First Setup Procedure

1. Run the CSE for the first time.  
You can start the CSE by simply running it from the command line:

	**For package installation:**

		acmecse
	
	**For manual installation:**

		python3 -m acme

	Please refer to the [Running](Running.md) documentation for more detailed instructions how to start and run the ACME CSE.

    If you have not installed the required packages during the installation ACME will ask you to install them now. This can be done by ACME automatically, or you can do it manually (see above).

	If no configuration file is found in the *base directory* then an interactive configuration process is started. The configuration is saved to a configuration file. e.g. *acme.ini* by default. 

	The *base directory* by default is the directory where the CSE is started from. This directory can be changed by the *--base-directory* (or *-dir*) command line argument to a different directory. 

	![](images/bootstrapConfig.gif)

	After the configuration is saved, the CSE is started. with this configuration.

1.  After terminating the CSE again you can edit that configuration file and add more settings if necessary.
	There are a lot of individual settings to configure here. Mostly, the defaults should be sufficient, but individual settings can be applied to each of the sections.  
	See the [Configuration](docs/Configuration.md) documentation for further details, and the defaults configuration file [acme.ini.default](../acme/init/acme.ini.default).


---

## Database Setup

The ACME CSE uses a database to store resources and other runtime data. This section describes the default database and how to set up a connection to a PostgreSQL database.

### TinyDB and In-Memory

The default database is a simple but fast file-based database using the [TinyDB](https://github.com/msiemens/tinydb) library. By default, it requires no additional setup.

The database files are stored by default in the directory *{baseDirectory}/data* (which can be changed by a [configuration setting](Configuration.md#databasetinydb---tinydb-database-settings)). 

TinyDB also provides a memory-based database that might be useful for testing and development purposes, or if you want to start with a clean database each time you start the CSE.

### PostgreSQL

An alternative to the file-based database is to use a PostgreSQL database. This requires a running PostgreSQL server to which the CSE can connect. The [PostgreSQL connection settings](Configuration.md#databasepostgresql---postgresql-database-settings) are configured in the *acme.ini* configuration file.

The following steps describe how to set up a PostgreSQL database for the ACME CSE:

1. Optional: Install PostgreSQL on your system. You can download the installer from the [PostgreSQL website](https://www.postgresql.org/download/).
1. Create a new database and user for the CSE. It is recommended to use the CSE-ID as the database name and as the role name.  
For example, you can use the following commands to create a new database named *id-in* and a role named *id-in* with the password *acme*:

		psql -c "CREATE DATABASE \"id-in\";"
		psql -c "CREATE USER \"id-in\" WITH PASSWORD 'acme';"
		psql -c "GRANT ALL PRIVILEGES ON DATABASE \"id-in\" TO \"id-in\";"

1. If not done during the setup procedure above: Edit the *acme.ini* configuration file and the following settings under the *\[database.postgresql\]* section:

		[database.postgresql]
		password = acme

	All other settings are optional and can be left at their default values. The *database* and *role* settings are set to the CSE-ID by default. If you used different names for the database and role, you have to adjust these settings accordingly. Also the *host* and *port* settings are set to *localhost* and *5432* by default. If your PostgreSQL server is running on a different host or port, you have to adjust these settings as well.  
	You also need to enable the PostgreSQL database by setting the *databaseType* setting in the *\[basic.config\]* section to *postgresql*:

		[basic.config]
		databaseType=postgresql

1. Run the CSE.  
The database schema, tables and other structures are created automatically by the CSE when it starts and connects for the first time. 


#### Disabling PostgreSQL Support

Sometimes it may not be possible or desirable to use a PostgreSQL database, for example, when running the CSE on a system where PostgreSQL is not available or when you want to use the CSE in a simple test environment.

In this case, you can disable the PostgreSQL database by setting the *databaseType* setting in the *\[basic.config\]* section to *tinydb* or *memory*:

	[basic.config]
	databaseType=tinydb

In order to prevent the PostgreSQL Python modules (i.e. psycopg2) to be loaded you can also set the `ACME_NO_PGSQL` environment variable to any value before running the CSE:

	export ACME_NO_PGSQL=1

---
## Installation on a Raspberry Pi

The ACME CSE can be installed on a Raspberry Pi. See the HowTo [Install ACME on a Raspberry Pi](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/132) for further details.


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

After you generated these files you can move them to a separate directory (for example you may create a new directory named *cert* in ACME's installation directory) and set the *caCertificateFile* and *caPrivateKeyFile* configuration parameters in the *acme.ini* configuration file under the *\[server.http.security\]* section accordingly.

---

## Third-Party Components
The following third-party components are used by the ACME CSE.

### Core CSE
- The [cbor2](https://github.com/agronholm/cbor2) package is used to parse and create CBOR serializations. MIT License.
- The CSE uses the [Flask](https://flask.palletsprojects.com/) web framework to service http(s) requests. BSD 3-Clause License.
- [flask-cors](https://github.com/corydolphin/flask-cors/) is a *Flask* extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
- [InquirerPy](https://github.com/kazhala/InquirerPy/) is a collection of common interactive command-line interfaces. MIT License.
- The [isodate](https://github.com/gweis/isodate) package is used to parse and handle ISO 8601 time, date, and duration. BSD License.
- The [paho-mqtt](https://www.eclipse.org/paho/) library provides a client class which enables applications to connect to an MQTT broker. Eclipse Public License 1.0 .
- The [plotext](https://github.com/piccolomo/plotext) library offers functions to plot graphs in the text console. MIT License.
- [Psycopg](https://www.psycopg.org) is a PostgreSQL adapter for the Python programming language. GNU Lesser General Public License.
- [rdflib](https://github.com/RDFLib/rdflib) is a Python library for working with RDF. BSD 3-Clause License.
- The CSE uses the [Requests](https://requests.readthedocs.io) HTTP Library to send requests vi http. Apache2 License
- The CSE uses the [Rich](https://github.com/willmcgugan/rich) text formatter library to format various terminal output. MIT License. 
- [shapely](https://github.com/shapely/shapely) is a library for manipulation and analysis of geometric objects. BSD 3-Clause License. 
- [Textual](https://github.com/textualize/textual) is a Rapid Application Development framework for to build textual user interfaces in Python. MIT License.
- [waitress](https://github.com/Pylons/waitress) is a production-quality pure-Python WSGI server with very acceptable performance. ZPL 2.1 License.
- To store resources the CSE uses the lightweight [TinyDB](https://github.com/msiemens/tinydb) document database. MIT License.


### Web UI Components
- TreeJS: [https://github.com/m-thalmann/treejs](https://github.com/m-thalmann/treejs), MIT License.
- Picnic CSS : [https://picnicss.com](https://picnicss.com), MIT License.

[← README](../README.md) 
