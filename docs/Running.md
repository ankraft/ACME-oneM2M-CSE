[← README](../README.md) 

# Running


## Running the CSE

You can start the CSE by simply running it from a command line:

	python3 acme.py

In this case the configuration file *acme.ini* must be in the same directory.

In additions, you can provide additional command line arguments that will override the respective settings from the configuration file:

| Command Line Argument | Description |
|----|----|
| -h, --help | Show a help message and exit. |
| --apps, --noapps | Enable or disable the build-in applications. This overrides the settings in the configuration file. |
| --config CONFIGFILE | Specify a configuration file that is used instead of the default (*acme.ini*) one. |
| --db-reset | Reset and clear the database when starting the CSE. |
| --db-storage {memory,disk} | Specify the DB´s storage mode. |
| --log-level {info, error, warn, debug, off} | Set the log level, or turn logging off. |
| --import-directory IMPORTDIRECTORY | Specify the import directory. |
| --remote-cse, --no-remote-cse | Enable or disable remote CSE connections and checking. |
| --statistics, --no-statistics | Enable or disable collecting CSE statics |
| --validation, --no-validation | Enable or disable sattributes and arguments validation. |


## Stopping the CSE

The CSE can be stopped by pressing *CTRL-C* **once** on the command line. 

Please note, that the shutdown might take a moment (e.g. gracefully terminating background processes, writing database caches, sending notifications etc). 

**Being impatient and hitting *CTRL-C* twice might lead to data corruption.**


## Running a Notifications Server

If you want to work with subscriptions and notification then you might want to have a Notifications Server running first before starting the CSE. The Notification Server provided with the CSE in the [tools/notificationServer](../tools/notificationServer) directory provides a very simple implementation that receives and answers notification requests.

See the [Notification Server's README](../tools/notificationServer/README.md) file for further details.

[← README](../README.md) 
