[← README](../README.md) 

# Installation

### Python

ACME requires **Python 3.10** or newer. Install it with your favorite package manager.

>[!Caution]
> Python 3.12 is not fully supported yet. Please stick to 3.10.x or 3.11.x for the moment.

You may consider to use a virtual environment manager like pyenv + virtualenv (see, for example, [this tutorial](https://realpython.com/python-virtual-environments-a-primer/)).

<a name="first_setup"></a>
## Installation and First Setup

1. Install the ACME CSE by cloning the repository, or by copying the whole distribution to a new directory.

		git clone https://github.com/ankraft/ACME-oneM2M-CSE.git
		cd ACME-oneM2M-CSE

1. **Either** install the required packages by running the following command (recommended):

		python3 -m pip install -r requirements.txt

	**OR** install them individually:  

		python3 -m pip install cbor2 flask flask-cors InquirerPy isodate paho-mqtt plotext rdflib requests rich tinydb

1. Run the CSE for the first time.  
You can start the CSE by simply running it from the command line:

		python3 -m acme

	Please refer to the [Running](Running.md) documentation for more detailed instructions how to start and run the ACME CSE.

	If no configuration file is found then an interactive configuration process is started. The
configuration is saved to a configuration file. e.g. *acme.ini* by default.  
&nbsp;  
![](images/bootstrapConfig.gif)

1.  After terminating the CSE again you can edit that configuration file and add more settings if necessary.
	There are a lot of individual settings to configure here. Mostly, the defaults should be sufficient, but individual settings can be applied to each of the sections.  
	See the [Configuration](docs/Configuration.md) documentation for further details, and the defaults configuration file [acme.ini.default](../acme.ini.default).


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
- The [cbor2](https://github.com/agronholm/cbor2) package is used to parse and create CBOR serializations. MIT License
- The CSE uses the [Flask](https://flask.palletsprojects.com/) web framework to service http(s) requests. BSD 3-Clause License
- [flask-cors](https://github.com/corydolphin/flask-cors/) is a *Flask* extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
- [InquirerPy](https://github.com/kazhala/InquirerPy/) is a collection of common interactive command-line interfaces. MIT License
- The [isodate](https://github.com/gweis/isodate) package is used to parse and handle ISO 8601 time, date, and duration. BSD License
- The [paho-mqtt](https://www.eclipse.org/paho/) library provides a client class which enables applications to connect to an MQTT broker. Eclipse Public License 1.0 
- The [plotext](https://github.com/piccolomo/plotext) library offers functions to plot graphs in the text console. MIT License
- [rdflib](https://github.com/RDFLib/rdflib) is a Python library for working with RDF. BSD 3-Clause License.
- The CSE uses the [Requests](https://requests.readthedocs.io) HTTP Library to send requests vi http. Apache2 License
- The CSE uses the [Rich](https://github.com/willmcgugan/rich) text formatter library to format various terminal output. MIT License 
- [shapely](https://github.com/shapely/shapely) is a library for manipulation and analysis of geometric objects. BSD 3-Clause License 
- [Textual](https://github.com/textualize/textual) is a Rapid Application Development framework for to build textual user interfaces in Python. MIT License
- [waitress](https://github.com/Pylons/waitress) is a production-quality pure-Python WSGI server with very acceptable performance. ZPL 2.1 License
- To store resources the CSE uses the lightweight [TinyDB](https://github.com/msiemens/tinydb) document database. MIT License


### Web UI Components
- TreeJS: [https://github.com/m-thalmann/treejs](https://github.com/m-thalmann/treejs), MIT License
- Picnic CSS : [https://picnicss.com](https://picnicss.com), MIT License

[← README](../README.md) 
