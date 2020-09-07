[← README](../../README.md) 

# Notification Server

This is a simple base implementation of a Notification Server to handle notifications from a CSE. Verification requests are always acknowledged, and notifications are just printed to the console.

The server normally listens on port 9999. This can be changed by specifying another value to the *port* variable at the beginning of the file or the command line argumnet *--port* (see below).

Start the server by running the command:

	python3 notificationServer.py

In this case the starts and listens on the default port (9999) for incoming connections.

## Command Line Arguments

In additions, you can provide additional command line arguments:

| Command Line Argument | Description |
|----|----|
| -h, --help | Show a help message and exit. |
| --port PORT | Specify the server port (default: 9999). |
| --http, --https | Run as http (default) or as https server. | 
| --certfile CERTFILE | Specify the certificate file (mandatory for https). |
| --keyfile KEYFILE | Specify the key file (mandatory for https). |


[← README](../../README.md) 
