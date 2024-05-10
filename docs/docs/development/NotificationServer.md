# Notification Server

The Notification that is provided in the directory [tools/notificationServer](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/tools/notificationServer){target=_new} is a simple implementation of a Notification Server that can be used to receive notifications from a CSE. 

Verification requests are always acknowledged, and notifications are just printed to the console.

The server normally listens on port `9999`. This can be changed by specifying another value to the *port* variable at the beginning of the file or the command line argumnet *--port* (see below).

## Running

### Start as basic HTTP notification server
Start the server by running the command from the `tools/notificationServer` directory:

```bash title="Start the Notification Server"
python3 notificationServer.py
```

In this case the starts and listens on the default port `9999` for incoming connections.


### Start with MQTT support

The Notification Server can be started with MQTT support. In this case the server connects to an MQTT broker and listens to the topics specified in the command line arguments.


```bash title="Start the Notification Server"
python3 notificationServer.py --mqtt --mqtt-address mqtt.example.com
```

The following command starts the NotificationServer with MQTT support enabled. The server would connect to an MQTT broker with username and password authentication,  and would listen to the topics "/oneM2M/req/id-in/+/#" and "/oneM2M/req/id-mn/+/#". In addition logging extra information about the MQTT communication to the console
is enabled.

```bash title="More Sophisticated MQTT Example"
python3 notificationServer.py --mqtt --mqtt-address mqttAddress --mqtt-username mqttUser --mqtt-password mqttPassword --mqtt-useTLS --mqtt-caFile caFile --mqtt-certfile certFile -- mqtt-keyfile keyFile --mqtt-topic /oneM2M/req/id-in/+/# /oneM2M/req/id-mn/+/# --mqtt-logging
```


## Command Line Arguments

The Notification Server can be started with the following command line arguments:

| Command Line Argument                      | Description                                                          |
|--------------------------------------------|----------------------------------------------------------------------|
| -h, --help                                 | Show a help message and exit.                                        |
| --port &lt;port>                           | Specify the server port (default: 9999).                             |
| --http, --https                            | Run as http (default) or as https server.                            |
| --certfile &lt;certfile>                   | Specify the certificate file (mandatory for https).                  |
| --keyfile &lt;keyfile>                     | Specify the key file (mandatory for https).                          |
| --mqtt                                     | Additionally enable MQTT for notifications                           |
| --mqtt-address &lt;host>                   | MQTT broker address (default: localhost)                             |
| --mqtt-port &lt;port>                      | MQTT broker port (default: 1883)                                     |
| --mqtt-topic &lt;topic> [&lt;topic> ...]   | MQTT topic list to subscribe to (default: ['/oneM2M/req/id-in/+/#']) |
| --mqtt-username &lt;username>              | MQTT username (default: None)                                        |
| --mqtt-password &lt;password>              | MQTT password (default: None)                                        |
| --mqtt-logging                             | MQTT enable logging (default: disabled)                              |
| --mqtt-useTLS								 | MQTT enable TLS (default: disabled)									|
| --mqtt-caFile	&lt;cafile>				 	 | Specify the CA certificate file (mandatory for MQTTS)				|
| --mqtt-certfile &lt;certfile>				 | Specify the certificate file (mandatory for MQTTS)					|
| --mqtt-keyfile &lt;keyfile>				 | Specify the key file (mandatory for MQTTS)							|
| --fail-verification                        | Fail all verification requests with "no privileges" (default: False) |
| --delay-response [&lt;delay>]              | Delay response by n seconds (default: 60s)                           |
