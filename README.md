# ![](acme/webui/web/img/acme_sm.png) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 0.9.0

[![oneM2M](https://img.shields.io/badge/oneM2M-f00)](https://www.onem2m.org) [![Python](https://img.shields.io/badge/Python-3.8-blue)](https://www.python.org) [![Maintenance](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/ankraft/ACME-oneM2M-CSE/graphs/commit-activity) [![License](https://img.shields.io/badge/License-BSD%203--Clause-green)](LICENSE) [![MyPy](https://img.shields.io/badge/MyPy-covered-green)](LICENSE)  
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/acmeCSE.svg?style=social&label=%40acmeCSE)](https://twitter.com/acmeCSE)



## Introduction

This CSE implements a subset of the oneM2M standard specializations (see [http://www.onem2m.org](http://www.onem2m.org)). The intention is to provide an easy to install, extensible, and easy to use and maintain CSE for educational purposes. Also see the discussion on [Limitations](docs/Supported.md#limitations).


![](docs/images/webui.png)

## Documentation
Please consult the following pages for further instructions.

- [Installation](docs/Installation.md)
- [Configuration](docs/Configuration.md)
- [Running](docs/Running.md)
	- [Docker](docs/Docker.md)
	- [Notification Server](tools/notificationServer/README.md)
- [Web & Rest UI](docs/WebUI.md)
- [Importing Resources](docs/Importing.md)
- [Operation](docs/Operation.md)
- [Supported Resource Types and Functionalities](docs/Supported.md)
	- [Limitations](docs/Supported.md#limitations)
- [Roadmap](docs/Roadmap.md)
- [Development](docs/Development.md)
- [Contributing](docs/Contributing.md)
- [FAQ](docs/FAQ.md)

## Changes

Please see the [Changelog](CHANGELOG.md) for the detailed list of changes.

### Important 1: Example AEs removed
This release removes the example  AEs from the project. They will become available in another project in the future. This make the distribution a bit smaller and removes the problematic dependency to the *psutil* package, which is not available on all platforms.

### Important 2: Changed the start method (again)
Due to the project restructuring the CSE is now started with the command ```python3 -m acme```.

### Highlights in this release

- Long-necessary refactoring of the project source structure.
- Simplified initial configuration.
- MQTT Binding support.
- PollingChannel support.
- Improved evaluation of target URIs for notifications, forward URIs etc.
- New console commands (Continuous updating tree view, resource export etc).
- Support for delayed operation execution.
- Lot's of small improvements, bug fixes, and optimizations

## Acknowledgements

Thank you for contributed code, patches, testing, bug fixes, time, and more!

![reinaortega](https://github.com/reinaortega.png?size=24) [Miguel Angel Reina Ortega](https://github.com/reinaortega)  
![YannGarcia](https://github.com/YannGarcia.png?size=24) [Yann Garcia](https://github.com/YannGarcia)  
<img src="https://github.com/massimov.png" width="24"> [Massimo Vanetti](https://github.com/massimov)  


## License
BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.

