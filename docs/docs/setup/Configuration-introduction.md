# Configuration - Introduction

The CSE is highly configurable and can be adapted to different environments and requirements. This document describes the configuration settings and how to change them.

## Introduction

Configuration of CSE parameters is done through a configuration file. This file contains all configurable and customizable
settings for the CSE. Configurations are mostly optional, and settings in this file overwrite the CSE's default values.

The configuration file follows the Windows INI file format with sections, setting and values. A configuration file may include comments, prefixed with the characters `#` or `;` .

### Command Line Arguments

Also, some settings can be applied via the command line when starting the CSE. These command line arguments overwrite the
settings in the configuration file.

## The Configuration File

!!! warning
	Changes should only be done to a copy of the default configuration file.

A default configuration file is provided with the file [acme.ini.default](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init/acme.ini.default){target=_new}. Don't make changes to this file, but rather copy relevant configuration setting to a new file named *acme.ini*, which is the default configuration file name. You can use another filename, but must then specify it with the `--config` command line argument when running the (see [Running the CSE](../setup/Running.md#running-the-cse)).

It is sufficient to only add the settings to the configuration file that are different from the default settings. All other settings are read from the default config file *acme.ini.default*.

If the configuration file *acme.ini* could not be found at the specified location then an interactive procedure is started to generate a file with basic configuration settings. You can add further configurations if necessary by copying sections and settings from *acme.ini.default*.

!!!	info
	It is highly recommended to use this interactive procedure to create the configuration file. This ensures that all necessary settings are present and that the file is correctly formatted.


## Settings Interpolation

In addition to assigning individual or fixed values for configurations settings you can use [settings interpolation](https://docs.python.org/3/library/configparser.html#interpolation-of-values){target=_new} which allows you to reference settings from the same or from other sections. The syntax to denote a value from a section is ```${section:option}```.

### Built-in Settings

There are some built-in configuration settings that can be used in the configuration file. These settings are provided by the CSE and can be used to reference directories or other values.


**${basic.config:baseDirectory}**  
**${baseDirectory}**
:	Two built-in configuration settings that point to the base-directory of the CSE's data directory. These settings contain  either the current working directory or the directory that is specified with the command line argument `--base-directory` or `-dir`.  
	Both settings are equivalent and can be used interchangeably.


**${configfile}**
:	Configuration setting that contains the name of the configuration file in the *baseDirectory*.


**${hostIPAddress}**
:	Built-in configuration setting that contains the current IP address of the CSE host.


**${basic.config:initDirectory}**  
**${initDirectory}**
:	Two built-in configuration settings that point to acme's main *init* directory.  
	Both settings are equivalent and can be used interchangeably.

	```ini title="Use built-in settings"
	[cse]
	resourcesPath=${basic.config:initDirectory}
	```

**${basic.config:moduleDirectory}**  
**${moduleDirectory}**
:	Two built-in configuration settings that point to acme's module directory.
	Both settings are equivalent and can be used interchangeably.


### Environment Variables

You can also use environment variables in the configuration file. The syntax is also `${VARIABLE_NAME}`.

Environment variables can be used in the configuration file to provide sensitive information like passwords or API keys. 

Another useful application is to provide the IP address of a Docker host to the CSE. This can be done, for example, by setting the environment variable `DOCKER_HOST_IP` and using it in the configuration file.

```ini title="Use Environment Variable to set Host IP"
[basic.config]
cseHost=${DOCKER_HOST_IP}
```
