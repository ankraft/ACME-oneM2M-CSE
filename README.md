# ![](acme/webui/web/img/acme_sm.png) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 2024.05.01

[![oneM2M](https://img.shields.io/badge/oneM2M-f00)](https://www.onem2m.org) [![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org) [![Maintenance](https://img.shields.io/badge/Maintained-Yes-green.svg)](https://github.com/ankraft/ACME-oneM2M-CSE/graphs/commit-activity) [![License](https://img.shields.io/badge/License-BSD%203--Clause-green)](LICENSE) [![MyPy](https://img.shields.io/badge/MyPy-covered-green)](LICENSE)  
[![Mastodon](https://img.shields.io/badge/-@acmeCSE@mstdn.social-FFF?label=mastodon&logo=mastodon&style=social)](https://mstdn.social/@acmeCSE)  
[![Discord](https://img.shields.io/badge/-ACME%20oneM2M%20CSE-FFF?label=discord&logo=discord&style=social)](https://discord.gg/6ryMHQC2Uj)


![](docs/images/title.png)

## Overview

This oneM2M compliant CSE implements a subset of the oneM2M standard (see [http://www.onem2m.org](http://www.onem2m.org)). The intention is to provide an easy to install, extensible, and easy to use and maintainable CSE for educational purposes.

See [https://acmecse.net](https://acmecse.net) for more exhaustive information.

## Changes

Please see the [Changelog](CHANGELOG.md) and this [discussion](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/152) for a detailed list of changes.

### Highlights in this release
- The CSE can now be installed via pip: `pip install acmecse`
- ACME CSE got its own domain: [https://acmecse.net](https://acmecse.net)
- The working directory for the CSE can now be changed.
  
### Improvements
- Lots of small improvements and bug fixes.

### Breaking Changes
- Moved the *init* directory to the acme module.
- Moved the *acme.ini.default* file to the new *init* directory location.

### What to expect in the next release

See the [announcement](https://github.com/ankraft/ACME-oneM2M-CSE/discussions/157) in the [discussions](https://github.com/ankraft/ACME-oneM2M-CSE/discussions).

## Acknowledgements

Many People have contributed to this project and helped to make it what it is today with their ideas, suggestions, and code. Please see the [Acknowledgements](docs/Contributing.md#acknowledgements) for the list of contributors.


## Join the Discussions on Discord

Join the ACME CSE community on [Discord ](https://discord.gg/6ryMHQC2Uj) to discuss the project, ask questions, and get help.

## License

BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.

