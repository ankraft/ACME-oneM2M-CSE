[← README](../../README.md) 

# Notification Server

This is a simple base implementation of a Notification Server to handle notifications from a CSE. Verification requests are always acknowledged, and notifications are just printed to the console.

The server normally listens on port 9999. This can be changed by specifying another value to the *port* variable at the beginning of the file or the command line argumnet *--port* (see below).

## Running

### Start as basic HTTP notification server
Start the server by running the command:

	python3 notificationServer.py

In this case the starts and listens on the default port (9999) for incoming connections.

### Start with MQTT support



## Command Line Arguments

In additions, you can provide additional command line arguments:

| Command Line Argument                      | Description                                                          |
|--------------------------------------------|----------------------------------------------------------------------|
| -h, --help                                 | Show a help message and exit.                                        |
| --port &lt;port>                           | Specify the server port (default: 9999).                             |
| --http, --https                            | Run as http (default) or as https server.                            |
| --certfile &lt;certfile>                   | Specify the certificate file (mandatory for https).                  |
| --keyfile &lt;>keyfile>                    | Specify the key file (mandatory for https).                          |
| --mqtt                                     | Additionally enable MQTT for notifications                           |
| --mqtt-address &lt;>host>                  | MQTT broker address (default: localhost)                             |
| --mqtt-port &lt;>port>                     | MQTT broker port (default: 1883)                                     |
| --mqtt-topic &lt;>topic> [&lt;>topic> ...] | MQTT topic list to subscribe to (default: ['/oneM2M/req/id-in/+/#']) |
| --mqtt-username &lt;>username>             | MQTT username (default: None)                                        |
| --mqtt-password &lt;>password>             | MQTT password (default: None)                                        |
| --mqtt-logging                             | MQTT enable logging (default: disabled)                              |
| --fail-verification                        | Fail all verification requests with "no privileges" (default: False) |


### Example: NotificationServer with MQTT
The following command starts the NotificationServer with MQTT support enabled. It would connect to an MQTT broker with username and password authentication, 
and would listen to the topics "/oneM2M/req/id-in/+/#" and "/oneM2M/req/id-mn/+/#". In addition logging extra information about the MQTT communication to the console
is enabled.

	python3 notificationServer.py --mqtt --mqtt-address mqttAddress --mqtt-username mqttUser --mqtt-password mqttPassword --mqtt-topic /oneM2M/req/id-in/+/# /oneM2M/req/id-mn/+/# --mqtt-logging

[← README](../../README.md) 
