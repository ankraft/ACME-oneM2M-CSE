[← README](../README.md) 

# Running

## Installation and Configuration

Please refer to the [Installation](Installation.md) and [Configuration](Configuration.md) documentation for
installing the CSE and setting up the CSE's configuration. 

## Running the CSE

You can start the CSE by simply running it from the command line:

	python3 -m acme

In this case the [configuration file](Configuration.md) *acme.ini* configuration file must be in the same directory. An [interactive
configuration process](Installation.md#first_setup) is started if the configuration file is not found.

In additions, you can provide additional command line arguments that will override the respective settings from the configuration file:

| Command Line Argument                             | Description                                                                                                                                                     |
|:--------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -h, --help                                        | Show a help message and exit.                                                                                                                                   |
| --http, --https                                   | Run the CSE with http or https server.<br />This overrides the [useTLS](Configuration.md#security) configuration setting.                                       |
| --config &lt;filename>                            | Specify a configuration file that is used instead of the default (*acme.ini*) one.                                                                              |
| --db-reset                                        | Reset and clear the database when starting the CSE.                                                                                                             |
| --db-storage {memory,disk,mongo}                 | Specify the DB\'s storage mode.<br />This overrides the [inMemory] and [mongo.enable] (Configuration.md#database) configuration setting.                                            |
| --db-host <mongo-host>                 			| Specify the MongoDB host.<br />This overrides the [database.mongo.host] configuration setting.                                            |
| --db-port <mongo-port>                 			| Specify the MongoDB host.<br />This overrides the [database.mongo.port] configuration setting.                                            |
| --headless                                        | Operate the CSE in headless mode. This disables almost all screen output and also the build-in console interface.                                               |
| --http-address &lt;server URL>                    | Specify the CSE\'s http server URL.<br />This overrides the [address](Configuration.md#http_server) configuration setting.                                      |
| --http-port &lt;http port>                        | Specify the CSE\'s http server port.<br />This overrides the [address](Configuration.md#http_port) configuration setting.                                       |
| --import-directory &lt;directory>                 | Specify the import directory.<br />This overrides the [resourcesPath](Configuration.md#general) configuration setting.                                          |
| --network-interface &lt;ip address                | Specify the network interface/IP address to bind to.<br />This overrides the [listenIF](Configuration.md#server_http) configuration setting.                    |
| --log-level {info, error, warn, debug, off}       | Set the log level, or turn logging off.<br />This overrides the [level](Configuration.md#logging) configuration setting.                                        |
| --mqtt, --no-mqtt                                 | Enable or disable the MQTT binding.<br />This overrides MQTT's [enable](Configuration.md#client_mqtt) configuration setting.                                    |
| --remote-cse, --no-remote-cse                     | Enable or disable remote CSE connections and checking.<br />This overrides the [enableRemoteCSE](Configuration.md#general) configuration setting.               |
| --statistics, --no-statistics                     | Enable or disable collecting CSE statistics.<br />This overrides the [enable](Configuration.md#statistics) configuration setting.                               |
| --textui                                          | Run the CSE's text UI after startup.                                                                                                                           |



### Debug Mode

Please see [Development - Debug Mode](Development.md#debug-mode) how to enable the debug mode to see further information in case you run into problems when trying to run the CSE.


## Stopping the CSE

The CSE can be stopped by pressing pressing the uppercase *Q* key or *CTRL-C* **once** on the command line. [^1]

[^1]: You can configure this behavior with the [\[cse.console\].confirmQuit](Configuration.md#console) configuration setting.

Please note, that the shutdown might take a moment (e.g. gracefully terminating background processes, writing database caches, sending notifications etc). 

**Being impatient and hitting *CTRL-C* twice might lead to data corruption.**



## Command Console

The CSE has a command console interface to execute build-in commands. 

See [Command Console](Console.md) for further details.



## Running a Notifications Server

If you want to work with subscriptions and notification then you might want to have a Notifications Server running first before starting the CSE. The Notification Server provided with the CSE in the [tools/notificationServer](../tools/notificationServer) directory provides a very simple implementation that receives and answers notification requests.

See the [Notification Server's README](../tools/notificationServer/README.md) file for further details.

[← README](../README.md) 
