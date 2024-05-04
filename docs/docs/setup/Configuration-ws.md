# Configuration - WebSocket Binding Settings

The CSE supports WebSocket communication via the WebSocket binding. The WebSocket binding is disabled by default and must be enabled in the configuration file under `[websocket].enable`.

## General Settings

**Section: `[websocket]`**

These are the general WebSocket settings.

| Setting  | Description                                               | Default | Configuration Name |
|:---------|:----------------------------------------------------------|:--------|:-------------------|
| enable   | Enable the WebSocket binding.                             | False   | websocket.enable   |
| port     | Set the port for the WebSocket server.                    | 8180    | websocket.port     |
| listenIF | Interface to listen to. Use 0.0.0.0 for "all" interfaces. | 0.0.0.0 | websocket.listenIF |


## Security

**Section: `[websocket.security]`**

These are the security settings for the WebSocket binding.

| Setting           | Description                                                                                                                                                    | Default      | Configuration Name                   |
|:------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------|:-------------------------------------|
| useTLS            | Enable TLS for websocket communications.                                                                                                                       | False        | websocket.security.useTLS            |
| tlsVersion        | TLS version to be used in connections. <br />Allowed versions: `TLS1.1`, `TLS1.2`, `auto` . Use `auto` to allow client-server certificate version negotiation. | auto         | websocket.security.tlsVersion        |
| verifyCertificate | Verify certificates in requests. Set to False when using self-signed certificates.                                                                             | False        | websocket.security.verifyCertificate |
| caCertificateFile | Path and filename of the certificate file.                                                                                                                     | empty string | websocket.security.caCertificateFile |
| caPrivateKeyFile  | Path and filename of the private key file.                                                                                                                     | empty string | websocket.security.caPrivateKeyFile  |

