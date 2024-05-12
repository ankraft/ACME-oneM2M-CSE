# Configuration - Basic Settings

The CSE is configured using the configuration file `acme.ini`. This file contains all necessary settings for the CSE to run. 
These settings are used throughout the configuration settings using [interpolation](Configuration-introduction.md#settings-interpolation).

When creating the configuration file, it is recommended to use the [interactive procedure](../setup/Installation.md#guided-configuration) to generate a file with basic configuration settings. [^1]

[^1]:You can add further configurations if necessary by copying sections and settings from [acme.ini.default](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init/acme.ini.default){target=_new}.


## Basic Configuration

**Section: `[basic.config]`**

These are the general settings for the CSE.
Some settings are mandatory, others are optional. This depends on the type of CSE to run.

| Setting          | Description                                                                                                                                                                                         | Optional |
|:-----------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| cseType          | The type of CSE to run.<br/>Allowed values: `IN`, `MN`, `ASN`                                                                                                                                       | No       |
| cseID            | The CSE-ID of the CSE. This is a unique identifier for the CSE.                                                                                                                                     | No       |
| cseName          | The name of the CSE.                                                                                                                                                                                | No       |
| adminID          | The CSE-ID of the CSE's admin.                                                                                                                                                                      | No       |
| networkInterface | The network interface to use.                                                                                                                                                                       | No       |
| cseHost          | The IP address of the CSE.<br/>The default is [${hostIPAddress}](../setup/Configuration-introduction.md#command-line-arguments).                                                                    | No       |
| httpPort         | The port for the HTTP server.<br/>This value depends on the *cseType*.                                                                                                                              | No       |
| registrarCseID   | The CSE-ID of the registrar CSE.<br/>This setting is mandatory for *cseType* = *MN* and *ASN*.                                                                                                      | Yes      |
| registrarCseName | The name of the registrar CSE.<br/>This setting is mandatory for *cseType* = *MN* and *ASN*.                                                                                                        | Yes      |
| registrarCseHost | The IP address of the registrar CSE.<br/>This setting is mandatory for *cseType* = *MN* and *ASN*.<br/>The default is [${hostIPAddress}](../setup/Configuration-introduction.md#built-in-settings). | Yes      |
| registrarCsePort | The port of the registrar CSE.<br/>This setting is mandatory for *cseType* = *MN* and *ASN*.                                                                                                        | Yes      |
| databaseType     | The type of database to use.<br/>Allowed values: `memory`, `tinydb`, `postgresql`                                                                                                                   | No       |
| logLevel         | The log level for the CSE.<br/>Allowed values: `debug`, `info`, `warning`, `error`, `off`                                                                                                           | Yes      |
| consoleTheme     | The theme for the console and text UI.<br/>Allowed values: `light`, `dark`                                                                                                                          | Yes      |

In addition to the settings in the table above, the [built-in configuration settings](../setup/Configuration-introduction.md#built-in-settings) 
and [envirnoment variables](../setup/Configuration-introduction.md#environment-variables) can be used in the configuration.

