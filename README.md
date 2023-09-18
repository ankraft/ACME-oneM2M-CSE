# ![](acme/webui/web/img/acme_sm.png) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 2023.DEV

[![oneM2M](https://img.shields.io/badge/oneM2M-f00)](https://www.onem2m.org) [![Python](https://img.shields.io/badge/Python-3.8-blue)](https://www.python.org) [![Maintenance](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/ankraft/ACME-oneM2M-CSE/graphs/commit-activity) [![License](https://img.shields.io/badge/License-BSD%203--Clause-green)](LICENSE) [![MyPy](https://img.shields.io/badge/MyPy-covered-green)](LICENSE)  
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

Please see the [Changelog](CHANGELOG.md) and this [discussion](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/110) for the detailed list of changes.

### Highlights in this release

- Support for the \<action> and \<dependency> resource types
- Support for partial retrieve
- New text UI for the console interface
- Request recording to show the oneM2M communication flow, and to help with debugging  
- Starting support draft and experimental oneM2M Release 5 features

### Improvements
- Big overall speed improvements for database operations ( > 10-100+ times for big resource trees).
**Unfortunately this means an incompatible change in the DB schemas**
- Improved resource validation (complex and enumeration types)

### <font color="red">Breaking Changes</font>
- The script interpreter is changed to a lisp-based language in this release. Be aware that scripts in the old format need be converted manually.
- The DB schemas are updated due to the necessary changes for the speed improvements.
- Renamed some configuration settings and section titles (see [discussion](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/110)).

### What to expect in the next release

See the [announcement](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/120) in the [discussions](https://github.com/ankraft/ACME-oneM2M-CSE/discussions).

## Acknowledgements

Many People have contributed to this project and helped to make it what it is today with their ideas, suggestions, and code. Please see the [Acknowledgements](docs/Contributing.md#acknowledgements) for the list of contributors.


## License

BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.

