# ![](acme/webui/web/img/acme_sm.png) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 0.11.0

[![oneM2M](https://img.shields.io/badge/oneM2M-f00)](https://www.onem2m.org) [![Python](https://img.shields.io/badge/Python-3.8-blue)](https://www.python.org) [![Maintenance](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/ankraft/ACME-oneM2M-CSE/graphs/commit-activity) [![License](https://img.shields.io/badge/License-BSD%203--Clause-green)](LICENSE) [![MyPy](https://img.shields.io/badge/MyPy-covered-green)](LICENSE)  
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/acmeCSE.svg?style=social&label=%40acmeCSE)](https://twitter.com/acmeCSE)



## Introduction

This CSE implements a subset of the oneM2M standard specializations (see [http://www.onem2m.org](http://www.onem2m.org)). The intention is to provide an easy to install, extensible, and easy to use and maintain CSE for educational purposes. Also see the discussion on [Limitations](docs/Supported.md#limitations).


![](docs/images/title.png)

## Documentation
Please consult the following pages for further instructions.

- [Installation](docs/Installation.md)
- [Configuration](docs/Configuration.md)
- [Running](docs/Running.md)
	- [Console](docs/Console.md)
	- [Docker](docs/Docker.md)
	- [Notification Server](tools/notificationServer/README.md)
- [Web & Rest UI](docs/WebUI.md)
- [Importing Resources](docs/Importing.md)
- [Operation](docs/Operation.md)
- [ACMEScript](docs/ACMEScript.md)
	- [Commands](docs/ACMEScript-commands.md)
	- [Macros](docs/ACMEScript-macros.md)
	- [Meta Tags](docs/ACMEScript-metatags.md)
- [Supported Resource Types and Functionalities](docs/Supported.md)
	- [Limitations](docs/Supported.md#limitations)
- [Roadmap](docs/Roadmap.md)
- [Development](docs/Development.md)
- [Contributing](docs/Contributing.md)
	- [Acknowledgements](docs/Contributing.md#acknowledgements)
- [FAQ](docs/FAQ.md)

## Changes

Please see the [Changelog](CHANGELOG.md) for the detailed list of changes.

### Highlights in this release

- &lt;crossResourceSubscription> and &lt;semanticDescriptor> resource types support.
- Support for semantic queries and semantic discovers.
- [wifilient] and [dataCollect] management object specializations support.
- Support for *blocking UPDATE* notification event type.
- Various improvements: Support for *expirationCounter* and notification statistics (&lt;subscription> and &lt;crossResourceSubscription>).
- Added CORS (Cross-Origin Resource Sharing) support for http binding.
- Various new commands and macros for scripting interpreter and the console.
- Improved definition of enumeration values for validation.
- Changed subscription notification handling to asynchronous.
- Improved request timeouts, especially for the http binding.
- Improved internal handling of requests sent by the CSE itself.
- And, as usual, many improvements, bug fixes, and performance improvements.

## Acknowledgements

Please see [Acknowledgements](docs/Contributing.md#acknowledgements).


## License
BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.

