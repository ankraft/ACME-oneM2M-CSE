# ![](acme/webui/web/img/acme_sm.png) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 2024.03

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

- Added WebSocket Binding support.  
  Though fully functional, there are two experimental features added to the implementation. See the [article](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/143) that explains these features and how to use them.
- Added support for *SIM* and *MobileNetwork* ManagementObject specializations.
- Added support for Python 3.12.

### Improvements
- Improved Text UI.
  - Auto-refresh for diagrams.
  - Diagrams now support containers that contain boolean-kind values.
  - Added Service menu for resources.
    - Export a resource and its child resources as curl commands.
    - Export the instance resources of &lt;container> and &lt;timeSeries> container to CSV files.
- Improved scripting support with new functions.


### What to expect in the next release

See the [announcement](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/142) in the [discussions](https://github.com/ankraft/ACME-oneM2M-CSE/discussions).

## Acknowledgements

Many People have contributed to this project and helped to make it what it is today with their ideas, suggestions, and code. Please see the [Acknowledgements](docs/Contributing.md#acknowledgements) for the list of contributors.


## License

BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.

