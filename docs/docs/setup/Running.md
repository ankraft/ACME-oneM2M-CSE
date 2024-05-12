# Running

This article describes how to start and stop the CSE, and how to use the command console interface.

## Running the CSE

You can start the CSE by simply running it from the command line. This is the simplest way to start the ACME CSE.

=== "Package installation"

	```bash title="Start ACME CSE"
	acmecse
	```

=== "Manual Installation"

	```bash title="Start ACME CSE as a module"
	python3 -m acme
	```

The current working directory is used as the base directory for the CSE and the *acme.ini* [configuration file](../setup/Configuration-introduction.md#the-configuration-file) must be in the same directory. An [interactive configuration process](Installation.md#guided-configuration) is started if the configuration file is not found.


### Different Configuration File

The CSE can also be started with a different configuration file:

=== "Package Installation"

	```bash title="Start ACME CSE with a different configuration file"
	acmecse --config <filename>
	```

=== "Manual Installation"

	```bash title="Start ACME CSE with a different configuration file"
	python3 -m acme --config <filename>
	```

The current working directory is still the base directory for the CSE and the configuration file is still expected to be located in this directory.

### Different Base Directory

The CSE can also be started with a different base directory:

=== "Package Installation"

	```bash title="Start ACME CSE with a different base directory"
	acmecse -dir <directory>
	```

=== "Manual Installation"

	```bash title="Start ACME CSE with a different base directory"
	python3 -m acme -dir <directory>
	```

This will use the specified directory as the root directory for runtime data such as *data*, *logs*, and *temporary* files. The configuration file *acme.ini*is expected to be in the specified directory, or it will be created there if it does not exist.

### Secondary *init* Directory

A base directory may also host a secondary *init* directory that is used for importing further resources such as attribute definitions and scripts. Resources in this directory are automatically imported when the CSE starts, and processed after the resources in the primary *init* directory have been imported and processed.


## Command Line Arguments

The ACME CSE provides a number of command line arguments that will override the respective settings from the configuration file. They can be used to change certain CSE behaviours without changing the configuration file.

| Command Line Argument                                    | Description                                                                                                                                                             |
|:---------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -h, --help                                               | Show a help message and exit.                                                                                                                                           |
| --config &lt;filename>                                   | Specify a configuration file that is used instead of the default (*acme.ini*) one.                                                                                      |
| --base-directory &lt;directory>,<br/>-dir &lt;directory> | Specify the root directory for runtime data such as data, logs, and temporary files.                                                                                    |
| --db-directory &lt;directory>                            | Specify the directory where the CSE's data base files are stored.                                                                                                       |
| --db-reset                                               | Reset and clear the database when starting the CSE.                                                                                                                     |
| --db-type {memory, tinydb, postgresql}                   | Specify the DB's storage type.<br />This overrides the [database.type](../setup/Configuration-database.md#general-settings) configuration setting.                      |
| --headless                                               | Operate the CSE in headless mode. This disables almost all screen output and also the build-in console interface.                                                       |
| --http, --https                                          | Run the CSE with http or https server.<br />This overrides the [useTLS](../setup/Configuration-http.md#security) configuration setting.                                 |
| --http-wsgi                                              | Run CSE with http WSGI support.<br />This overrides the [http.wsgi.enable](../setup/Configuration-http.md#wsgi) configuration setting.                                  |
| --http-address &lt;server URL>                           | Specify the CSE's http server URL.<br />This overrides the [address](../setup/Configuration-http.md#general-settings) configuration setting.                            |
| --http-port &lt;http port>                               | Specify the CSE's http server port.<br />This overrides the [address](../setup/Configuration-http.md#general-settings) configuration setting.                           |
| --init-directory &lt;directory>                          | Specify the import directory.<br />This overrides the [resourcesPath](../setup/Configuration-cse.md#general-settings) configuration setting.                            |
| --network-interface &lt;ip address                       | Specify the network interface/IP address to bind to.<br />This overrides the [listenIF](../setup/Configuration-http.md#general-settings) configuration setting.         |
| --log-level {info, error, warn, debug, off}              | Set the log level, or turn logging off.<br />This overrides the [level](../setup/Configuration-logging.md#general-settings) configuration setting.               |
| --mqtt, --no-mqtt                                        | Enable or disable the MQTT binding.<br />This overrides the [mqtt.enable](../setup/Configuration-mqtt.md#general-settings) configuration setting.                       |
| --remote-cse, --no-remote-cse                            | Enable or disable remote CSE connections and checking.<br />This overrides the [enableRemoteCSE](../setup/Configuration-cse.md#general-settings) configuration setting. |
| --statistics, --no-statistics                            | Enable or disable collecting CSE statistics.<br />This overrides the [enable](../setup/Configuration-cse.md#statistics) configuration setting.                                       |
| --textui                                                 | Run the CSE's text UI after startup.                                                                                                                                    |
| --ws, --no-ws                                            | Enable or disable the WebSocket binding.<br />This overrides the [websocket.enable](../setup//Configuration-ws.md#general-settings) configuration setting.                                  |



## Stopping the CSE

The CSE can be stopped by pressing pressing the uppercase *Q* key or *CTRL-C* **once** on the command line.[^1]

[^1]: You can configure this behavior with the [\[cse.console\].confirmQuit](../setup/Configuration-uis.md#console) configuration setting.

Please note, that the shutdown might take a moment (e.g. gracefully terminating background processes, writing database caches, sending notifications etc). 

!!! warning
	Being impatient and hitting *CTRL-C* twice might lead to data corruption.
