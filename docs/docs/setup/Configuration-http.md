# Configuration - HTTP Binding Settings

The CSE supports HTTP binding for communication with clients and other CSEs. The HTTP binding is always enabled and its settings are configured in the configuration file under the section `[http]` and its subsections.

##	General Settings

**Section: `[http]`**

These are the general settings for the HTTP binding.

| Setting                   | Description                                                                                                                                                                                                                                                                                                    | Default                                                                                                                                                               | Configuration Name             |
|:--------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------|
| port                      | Port to listen to.                                                                                                                                                                                                                                                                                             | [${basic.config:httpPort}](../setup/Configuration-basic.md#basic-configuration)                                                                                       | http.port                      |
| listenIF                  | Interface to listen to. Use 0.0.0.0 for "all" interfaces.                                                                                                                                                                                                                                                      | [${basic.config:networkInterface}](../setup/Configuration-basic.md#basic-configuration)                                                                               | http.listenIF                  |
| address                   | Own address. Should be a local/public reachable address.                                                                                                                                                                                                                                                       | http://[${basic.config:cseHost}](../setup/Configuration-basic.md#basic-configuration):[${basic.config:httpPort}](../setup/Configuration-basic.md#basic-configuration) | http.address                   |
| root                      | CSE Server root. Never provide a trailing `/`.                                                                                                                                                                                                                                                                 | empty string                                                                                                                                                          | http.root                      |
| enableRemoteConfiguration | Enable an endpoint for get and set certain configuration values via a REST interface.<br />**ATTENTION: Enabling this feature exposes configuration values, IDs and passwords, and is a security risk.**                                                                                                       | False                                                                                                                                                                 | http.enableRemoteConfiguration |
| enableStructureEndpoint   | Enable an endpoint for getting a structured overview about a CSE's resource tree and deployment infrastructure (remote CSE's).<br />**ATTENTION: Enabling this feature exposes various potentially sensitive information.**<br/>See also the \[console].hideResources setting to hide resources from the tree. | False                                                                                                                                                                 | http.enableStructureEndpoint   |
| enableUpperTesterEndpoint | Enable an endpoint for supporting Upper Tester commands to the CSE. This is to support certain testing and certification systems. See oneM2M's TS-0019 for further details.<br/>**ATTENTION: Enabling this feature may lead to a total loss of data.**                                                         | False                                                                                                                                                                 | http.enableUpperTesterEndpoint |
| allowPatchForDelete       | Allow the http PATCH method to be used as a replacement for the DELETE method. This is useful for constraint devices that only support http/1.0, which doesn't specify the DELETE method.                                                                                                                      | False                                                                                                                                                                 | http.allowPatchForDelete       |
| timeout                   | Timeout when sending http requests and waiting for responses.                                                                                                                                                                                                                                                  | 10 seconds                                                                                                                                                            | http.timeout                   |


## Security

**Section: `[http.security]`**

These are the security settings for the HTTP binding.

| Setting           | Description                                                                                                                                                                                                                  | Default                                                                                                                   | Configuration Name              |
|:------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------|:--------------------------------|
| useTLS            | Enable TLS for communications.<br />This can be overridden by the command line arguments [--http and --https](Running.md).<br />See oneM2M TS-0003 Clause 8.2.1 "Overview on Security Association Establishment Frameworks". | False                                                                                                                     | http.security.useTLS            |
| tlsVersion        | TLS version to be used in connections. <br />Allowed versions: `TLS1.1`, `TLS1.2`, `auto` . Use `auto` to allow client-server certificate version negotiation.                                                               | auto                                                                                                                      | http.security.tlsVersion        |
| verifyCertificate | Verify certificates in requests. Set to *False* when using self-signed certificates.                                                                                                                                         | False                                                                                                                     | http.security.verifyCertificate |
| caCertificateFile | Path and filename of the certificate file.                                                                                                                                                                                   | empty string                                                                                                              | http.security.caCertificateFile |
| caPrivateKeyFile  | Path and filename of the private key file.                                                                                                                                                                                   | empty string                                                                                                              | http.security.caPrivateKeyFile  |
| enableBasicAuth   | Enable basic authentication for the HTTP binding.                                                                                                                                                                            | False                                                                                                                     | http.security.enableBasicAuth   |
| enableTokenAuth   | Enable token authentication for the HTTP binding.                                                                                                                                                                            | False                                                                                                                     | http.security.enableTokenAuth   |
| basicAuthFile     | Path and filename of the http basic authentication file. The file must contain lines with the format "username:password". Comments are lines starting with a # character.                                                    | [${basic.config:baseDirectory}](../setup/Configuration-basic.md#basic-configuration)/certs/http_basic_auth.txt | http.security.basicAuthFile     |
| tokenAuthFile     | Path and filename of the http bearer token authentication file. The file must contain lines with the format "token". Comments are lines starting with a # character.                                                         | [${basic.config:baseDirectory}](../setup/Configuration-basic.md#basic-configuration)/certs/http_token_auth.txt | http.security.tokenAuthFile     |



## CORS

**Section: `[http.cors]`**

These are the CORS (Cross-Origin Resource Sharing) settings for the HTTP binding.

| Setting   | Description                                                                                             | Default                                                | Configuration Name  |
|:----------|:--------------------------------------------------------------------------------------------------------|:-------------------------------------------------------|:--------------------|
| enable    | Enable CORS support for the HTTP binding.                                                               | False                                                  | http.cors.enable    |
| resources | A comma separated list of allowed resource paths. The list elements could be regular expressions.<br /> | "/*" , ie. all resources under the HTTP server's root. | http.cors.resources |


## WSGI 

**Section: `[http.wsgi]`**

These are the settings for the WSGI (Web Server Gateway Interface) support.

| Setting         | Description                                                                                                                                | Default | Configuration Name        |
|:----------------|:-------------------------------------------------------------------------------------------------------------------------------------------|:--------|:--------------------------|
| enable          | Enable WSGI support for the HTTP binding.                                                                                                  | False   | http.wsgi.enable          |
| threadPoolSize  | The number of threads used to process requests. This number should be of similar size as the *connectionLimit* setting.                    | 100     | http.wsgi.threadPoolSize  |
| connectionLimit | The number of possible parallel connections that can be accepted by the WSGI server. Note: One connection uses one system file descriptor. | 100     | http.wsgi.connectionLimit |
