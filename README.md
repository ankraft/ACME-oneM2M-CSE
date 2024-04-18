# ![](acme/webui/web/img/acme_sm.png) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 2024.04

[![oneM2M](https://img.shields.io/badge/oneM2M-f00)](https://www.onem2m.org) [![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org) [![Maintenance](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/ankraft/ACME-oneM2M-CSE/graphs/commit-activity) [![License](https://img.shields.io/badge/License-BSD%203--Clause-green)](LICENSE) [![MyPy](https://img.shields.io/badge/MyPy-covered-green)](LICENSE)  
[![Mastodon](https://img.shields.io/badge/-@acmeCSE@mstdn.social-FFF?label=mastodon&logo=mastodon&style=social)](https://mstdn.social/@acmeCSE)
## Introduction

This oneM2M compliant CSE implements a subset of the oneM2M standard (see [http://www.onem2m.org](http://www.onem2m.org)). The intention is to provide an easy to install, extensible, and easy to use and maintainable CSE for educational purposes.

![](docs/images/title.png)

## Documentation

- [Installation](docs/Installation.md)
- [Configuration](docs/Configuration.md)
- [Running](docs/Running.md)
	- [Console](docs/Console.md)
	- [Text UI](docs/TextUI.md)
	- [Docker](docs/Docker.md)
	- [Notification Server](tools/notificationServer/README.md)
    - [Web & Rest UI](docs/WebUI.md)
- [CSE Startup, Importing Resources and Other Settings](docs/Importing.md)
- [Operation](docs/Operation.md)
- [ACMEScript](docs/ACMEScript.md)
	- [Functions](docs/ACMEScript-functions.md)
	- [Meta Tags](docs/ACMEScript-metatags.md)
- [Supported Resource Types and Functionalities](docs/Supported.md)
	- [Limitations](docs/Supported.md#limitations)
- [Roadmap](docs/Roadmap.md)
- [Development](docs/Development.md)
- [Contributing](docs/Contributing.md)
	- [Acknowledgements](docs/Contributing.md#acknowledgements)
- [FAQ](docs/FAQ.md)

## Changes

Please see the [Changelog](CHANGELOG.md) and this [discussion](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/131) for the detailed list of changes.

### Highlights in this release

- Added postgreSQL support. Instead of the default TinyDB, you can now use a PostgreSQL database backend to store the resources and runtime data.
  
### Improvements

### Breaking Changes
- Due to the new database support, the configuration file has changed. Please see the [Configuration](docs/Configuration.md) documentation for further details.



### What to expect in the next release

See the [announcement](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/142) in the [discussions](https://github.com/ankraft/ACME-oneM2M-CSE/discussions).

## Acknowledgements

Many People have contributed to this project and helped to make it what it is today with their ideas, suggestions, and code. Please see the [Acknowledgements](docs/Contributing.md#acknowledgements) for the list of contributors.


## Join the Discussions on Discord

Join the ACME CSE community on [Discord ](https://discord.gg/C7Qx33Xw) to discuss the project, ask questions, and get help.


## License

BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.

