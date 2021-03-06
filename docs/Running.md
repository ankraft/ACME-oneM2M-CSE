[← README](../README.md) 

# Running


## Running the CSE

You can start the CSE by simply running it from a command line:

	python3 acme.py

In this case the configuration file *acme.ini* must be in the same directory.

In additions, you can provide additional command line arguments that will override the respective settings from the configuration file:

| Command Line Argument                             | Description                                                                                                                                                     |
|:--------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -h, --help                                        | Show a help message and exit.                                                                                                                                   |
| --http, --https                                   | Run the CSE with http or https server.<br />This overrides the [useTLS](Configuration.md#security) configuration setting.                                       |
| --apps, --noapps                                  | Enable or disable the build-in applications.<br />This overrides the [enableApplications](Configuration.md#general) configuration setting.                      |
| --config \<filename>                              | Specify a configuration file that is used instead of the default (*acme.ini*) one.                                                                              |
| --db-reset                                        | Reset and clear the database when starting the CSE.                                                                                                             |
| --db-storage {memory,disk}                        | Specify the DB´s storage mode.<br />This overrides the [inMemory](Configuration.md#database) configuration setting.                                             |
| --headless                                        | Operate the CSE in headless mode. This disables almost all screen output and also the build-in console interface.                                               |
| --http-address \<server URL>                      | Specify the CSE\'s http server URL.<br />This overrides the [address](Configuration.md#http_server) configuration setting.                                      |
| --import-directory \<directory>                   | Specify the import directory.<br />This overrides the [resourcesPath](Configuration.md#general) configuration setting.                                          |
| --network-interface \<ip address>                 | Specify the network interface/IP address to bind to.<br />This overrides the [listenIF](Configuration.md#server_http) configuration setting.                    |
| --log-level {info, error, warn, debug, off}       | Set the log level, or turn logging off.<br />This overrides the [level](Configuration.md#logging) configuration setting.                                        |
| --remote-configuration, --no-remote-configuration | Enable or disable http remote configuration endpoint.<br />This overrides the [enableRemoteConfiguration](Configuration.md##server_http) configuration setting. |
| --remote-cse, --no-remote-cse                     | Enable or disable remote CSE connections and checking.<br />This overrides the [enableRemoteCSE](Configuration.md#general) configuration setting.               |
| --statistics, --no-statistics                     | Enable or disable collecting CSE statics.<br />This overrides the [enable](Configuration.md#statistics) configuration setting.                                  |
| --validation, --no-validation                     | Enable or disable attribute and argument validations.<br />This overrides the [enableValidation](Configuration.md#general) configuration setting.               |

### Certificates and Support for https

To enable https you have to set various settings [ [cse.security] configuration section](Configuration.md#security), and provide a certificate and a key file. 
One way to generate those files is the [openssl](https://www.openssl.org) tool that may already be installed on your OS. The following example shows how to 
generate a self-signed certificate:

	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -nodes -days 1000

This will generate the self-signed certificate and private key without password protection (*-nodes*), and stores them in the files *cert.pem* and *key.pem* respectively. 
openssl will prompt you with questions for *Country Name* etc, but you can just hit *Enter* and accept the defaults. The *-days* parameter affects the certificate's
expiration date.

Please also consult the *openssl* manual for further instructions. 

After you generated these files you can move them to a separate directory (for example you may create a new directory named *cert* in ACME's installation directory) and set the *caCertificateFile* and *caPrivateKeyFile* configuration parameters accordingly.


## Stopping the CSE

The CSE can be stopped by pressing pressing the uppercase *Q* key or *CTRL-C* **once** on the command line. 

Please note, that the shutdown might take a moment (e.g. gracefully terminating background processes, writing database caches, sending notifications etc). 

**Being impatient and hitting *CTRL-C* twice might lead to data corruption.**


## Command Console

The CSE has a simple command console interface to execute build-in commands. Currently these commands are available:

 - h, ?  - This help
 - Q, ^C - Shutdown CSE
 - c     - Show configuration
 - D     - Delete resource
 - i     - Inspect resource
 - l     - Toggle logging on/off
 - r     - Show CSE registrations
 - s     - Show statistics
 - t     - Show resource tree
 - w     - Show worker threads status

 The following screenshot shows, for example, a CSE's resource tree:

![](images/console_tree.png)


## Running a Notifications Server

If you want to work with subscriptions and notification then you might want to have a Notifications Server running first before starting the CSE. The Notification Server provided with the CSE in the [tools/notificationServer](../tools/notificationServer) directory provides a very simple implementation that receives and answers notification requests.

See the [Notification Server's README](../tools/notificationServer/README.md) file for further details.

[← README](../README.md) 
