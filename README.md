# ![](webui/img/acme_sm.png) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 0.4.0


## Introduction

This CSE implements a subset of the oneM2M standard specializations (see [http://www.onem2m.org](http://www.onem2m.org)). The intention is to provide an easy to install, extensible, and easy to use and maintain CSE for educational purposes. Also see the discussion on [Limitations](docs/Supported.md#limitations).

The CSE implementation successfully passes the oneM2M release 1 test cases.


![](docs/images/webui.png)

## Documentation
Please consult the following pages for further instructions.

- [Installation](docs/Installation.md)
- [Configuration](docs/Configuration.md)
- [Running](docs/Running.md)
	- [Docker](docs/Docker.md)
- [Web & Rest UI](docs/WebUI.md)
- [Importing Resources](docs/Importing.md)
- [Operation](docs/Operation.md)
	- [Applications and Nodes](docs/ApplicationsNodes.md)
- [Supported Resource Types and Functionalities](docs/Supported.md)
	- [Limitations](docs/Supported.md#limitations)
- [Development](docs/Development.md)

## Changes

Please see the [Changelog](CHANGELOG.md) for the latest changes.

## License
BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.


## Roadmap & Backlog
- CSE: support non-blocking requests
- CSE: Support the PollingChannel resource type
- CSE: Announcements
- CSE: Timeseries
- UI: Support for resource specific actions (e.g. latest, oldest)
- UI: Graph for Container reosurces
- Importer: Automatically import/update resources when the CSE is running
- App development: support more specializations
