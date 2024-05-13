# ![](https://github.com/ankraft/ACME-oneM2M-CSE/blob/4e6b4878ffc1a1295f443a243f21d269bf745fd0/acme/webui/web/img/acme_sm.png?raw=true) 

# ACME oneM2M CSE
An open source CSE Middleware for Education.

![](https://github.com/ankraft/ACME-oneM2M-CSE/blob/4e6b4878ffc1a1295f443a243f21d269bf745fd0/docs/images/title.png?raw=true)
## Introduction

This oneM2M compliant CSE implements a subset of the oneM2M standard (see [http://www.onem2m.org](http://www.onem2m.org)). The intention is to provide an easy to install, extensible, and easy to use and maintainable CSE for educational purposes.


## Installing
Install with pip or your favorite PyPI package manager.

	python -m pip install acmecse

## Running

Run the following to run the ACME CSE with the current directory as the runtime directory:

	python -m acmecse

To specify a different runtime directory, use the `-dir` option:

	python -m acmecse -dir /path/to/runtime

A configuration file and necessary directories will be created in the runtime directory if they do not exist.

## Documentation

See [https://acmecse.net](https://acmecse.net) for more exhaustive information.

## License

BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.

