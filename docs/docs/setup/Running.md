# Running

This article describes how to start and stop the CSE, and how to use the command console interface.

## Running the CSE

You can start the CSE by simply running it from the command line. This is the simplest way to start the ACME CSE.

=== "Package installation"

		acmecse

=== "Manual Installation"

		python3 -m acme

The current working directory is used as the base directory for the CSE and the *acme.ini* [configuration file](Configuration.md) must be in the same directory. An [interactive configuration process](Installation.md#automatic-configuration) is started if the configuration file is not found.


### Different Configuration File

The CSE can also be started with a different configuration file:

=== "Package Installation"

		acmecse --config <filename>

=== "Manual Installation"

		python3 -m acme --config <filename>

The current working directory is still the base directory for the CSE and the configuration file is still expected to be located in this directory.

### Different Base Directory

The CSE can also be started with a different base directory:

=== "Package Installation"

		acmecse -dir <directory>

=== "Manual Installation"

		python3 -m acme -dir <directory>

This will use the specified directory as the root directory for runtime data such as *data*, *logs*, and *temporary* files. The configuration file *acme.ini*is expected to be in the specified directory, or it will be created there if it does not exist.

### Secondary *init* Directory

A base directory may also host a secondary *init* directory that is used for importing further resources such as attribute definitions and scripts. Resources in this directory are automatically imported when the CSE starts, and processed after the resources in the primary *init* directory have been imported and processed.


## Command Line Arguments

The ACME CSE provides a number of command line arguments that will override the respective settings from the configuration file. They can be used to change certain CSE behaviours without changing the configuration file.

<mark>TODO correct links</mark>

| Command Line Argument                                    | Description                                                                                                                                       |
|:---------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------|
| -h, --help                                               | Show a help message and exit.                                                                                                                     |
| --config &lt;filename>                                   | Specify a configuration file that is used instead of the default (*acme.ini*) one.                                                                |
| --base-directory &lt;directory>,<br/>-dir &lt;directory> | Specify the root directory for runtime data such as data, logs, and temporary files.                                                              |
| --db-directory &lt;directory>                            | Specify the directory where the CSE's data base files are stored.                                                                                 |
| --db-reset                                               | Reset and clear the database when starting the CSE.                                                                                               |
| --db-type {memory, tinydb, postgresql}                   | Specify the DB's storage type.<br />This overrides the [database.type](../setup/Configuration-database.md) configuration setting.                         |
| --headless                                               | Operate the CSE in headless mode. This disables almost all screen output and also the build-in console interface.                                 |
| --http, --https                                          | Run the CSE with http or https server.<br />This overrides the [useTLS](../setup/Configuration-http.md#security) configuration setting.                         |
| --http-wsgi                                              | Run CSE with http WSGI support.<br />This overrides the [http.wsgi.enable](../setup/Configuration-http.md#wsgi) configuration setting.                                               |
| --http-address &lt;server URL>                           | Specify the CSE's http server URL.<br />This overrides the [address](../setup/Configuration-http.md#general-settings) configuration setting.                        |
| --http-port &lt;http port>                               | Specify the CSE's http server port.<br />This overrides the [address](../setup/Configuration-http.md#general-settings) configuration setting.                         |
| --init-directory &lt;directory>                          | Specify the import directory.<br />This overrides the [resourcesPath](../setup/Configuration-basic.md) configuration setting.                            |
| --network-interface &lt;ip address                       | Specify the network interface/IP address to bind to.<br />This overrides the [listenIF](../setup/Configuration-http.md#general-settings) configuration setting.      |
| --log-level {info, error, warn, debug, off}              | Set the log level, or turn logging off.<br />This overrides the [level](Configuration.md#logging) configuration setting.                          |
| --mqtt, --no-mqtt                                        | Enable or disable the MQTT binding.<br />This overrides the [mqtt.enable](Configuration.md#client_mqtt) configuration setting.                    |
| --remote-cse, --no-remote-cse                            | Enable or disable remote CSE connections and checking.<br />This overrides the [enableRemoteCSE](Configuration.md#general) configuration setting. |
| --statistics, --no-statistics                            | Enable or disable collecting CSE statistics.<br />This overrides the [enable](Configuration.md#statistics) configuration setting.                 |
| --textui                                                 | Run the CSE's text UI after startup.                                                                                                              |
| --ws, --no-ws                                            | Enable or disable the WebSocket binding.<br />This overrides the [websocket.enable](Configuration.md#websocket) configuration setting.            |


<mark>TODO: To Development</mark>


## Debug Mode

Please see [Development - Debug Mode](Development.md#debug-mode) how to enable the debug mode to see further information in case you run into problems when trying to run the CSE.


## Stopping the CSE

The CSE can be stopped by pressing pressing the uppercase *Q* key or *CTRL-C* **once** on the command line. [^1]

[^1]: You can configure this behavior with the [\[cse.console\].confirmQuit](Configuration.md#console) configuration setting.

Please note, that the shutdown might take a moment (e.g. gracefully terminating background processes, writing database caches, sending notifications etc). 

**Being impatient and hitting *CTRL-C* twice might lead to data corruption.**


<mark>TODO: To Development</mark>


## Running a Notifications Server

If you want to work with subscriptions and notification then you might want to have a Notifications Server running first before starting the CSE. The Notification Server provided with the CSE in the [tools/notificationServer](../tools/notificationServer) directory provides a very simple implementation that receives and answers notification requests.

See the [Notification Server's README](../tools/notificationServer/README.md) file for further details.
