[← README](../README.md) 

# Configuration

[Configuration Sections](#sections)  
[Advanced Usage](#advanced)  


Configuration of CSE parameters is done through a configuration file. This file contains all configurable and customizable
settings for the CSE. It is optional, and settings in this file overwrite the CSE's default values. 

It follows the Windows INI file format with sections, setting and values. A configuration file may include comments, 
prefixed with the characters "#"" or ";"" .

Also, some settings can be applied via the command line when starting the CSE. These command line arguments overwrite the
settings in the configuration file.


## The Default Configuration File

**Changes should only be done to a copy of the default configuration file.**

A default configuration file is provided with the file [acme.ini.default](../acme.ini.default). Don't make changes to this file, 
but rather copy it to a new file named *acme.ini*, which is the default configuration file name. You can use another filename, 
but must then specify it with the *--config* command line argument when running the 
(see [Running the CSE](Running.md#running-the-cse)).

It is sufficient to only add the settings to the configuration file that need to be different from the default settings.
All other settings are read from the default config file *acme.ini.default*.

If the specified or the default *acme.ini* could not be found then an interactive procedure is started to generate a file
with basic configuration settings. You can add further configurations if necessary by copying sections and settings from *acme.ini.default*.

### Interpolating Configuration Settings

In addition to assigning individual values for configurations settings you can use
[settings interpolation](https://docs.python.org/3/library/configparser.html#interpolation-of-values) which allows you to
reference settings from the same or from other sections. The syntax to denote a value from a section is ```${section:option}```.

### Built-in Configuration Macros

#### ${basic.config:baseDirectory}

A built-in configuration setting that points to the base-directory of the CSE installation can be 
referenced by the interpolation ```${basic.config:baseDirectory}```.

Example:

```ini
[cse]
resourcesPath=${basic.config:baseDirectory}/init
```


<a name="sections"></a>
## Configuration Sections

The following tables provide detailed descriptions of all the possible CSE configuration settings.

[&#91;cse&#93; - General CSE Settings](#general)  
[&#91;cse.announcements&#93; - Settings for Resource Announcements](#announcements)  
[&#91;cse.operation.jobs&#93; - CSE Operations Settings - Jobs](#operation_jobs)  
[&#91;cse.operation.requests&#93; - CSE Operations Settings - Requests](#operation_requests)  
[&#91;cse.registration&#93; - Settings for Self-Registrations](#cse_registration)  
[&#91;cse.registrar&#93; - Settings for Remote CSE Access](#registrar)  
[&#91;cse.security&#93; - General Security Settings](#security)  
[&#91;cse.statistics&#93; - Statistic Settings](#statistics)  
[&#91;console&#93; - Console Settings](#console)  
[&#91;database&#93; - Database Settings](#database)  
[&#91;http&#93; - HTTP Server Settings](#http)  
[&#91;http.security&#93; - HTTP Security Settings](#security_http)  
[&#91;http.cors&#93; - HTTP CORS (Cross-Origin Resource Sharing) Settings](#http_cors)  
[&#91;http.wsgi&#93; - HTTP WSGI (Web Server Gateway Interface) Settings](#http_wsgi)  
[&#91;logging&#93; - Logging Settings](#logging)  
[&#91;mqtt&#93; - MQTT Client Settings](#client_mqtt)  
[&#91;mqtt.security&#93; - MQTT Security Settings](#security_mqtt)  
[&#91;resource.acp&#93; - Resource defaults: Access Control Policies](#resource_acp)  
[&#91;resource.actr&#93; - Resource defaults: Action](#resource_actr)  
[&#91;resource.cnt&#93; - Resource Defaults: Container](#resource_cnt)  
[&#91;resource.grp&#93; - Resource Defaults: Group](#resource_grp)  
[&#91;resource.lcp&#93; - Resource Defaults: LocationPolicy](#resource_lcp)  
[&#91;resource.req&#93; - Resource Defaults: Request](#resource_req)  
[&#91;resource.sub&#93; - Resource Defaults: Subscription](#resource_sub)  
[&#91;resource.ts&#93; - Resource Defaults: TimeSeries](#resource_ts)  
[&#91;resource.tsb&#93; - Resource Defaults: TimeSyncBeacon](#resource_tsb)  
[&#91;scripting&#93; - Scripting Settings](#scripting)  
[&#91;textui&#93; - Text UI Settings](#textui)  
[&#91;webui&#93; - Web UI Settings](#webui)  
	

<a name="general"></a>

### [cse] - General CSE Settings

| Setting                                | Description                                                                                                                                                                | Configuration Name                         |
|:---------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------|
| asyncSubscriptionNotifications         | Enable or disable asynchronous notification for normal runtime subscription notifications.<br/>Default: true                                                               | cse.asyncSubscriptionNotifications         |
| checkExpirationsInterval               | Interval to check for expired resources. 0 means "no checking".<br/>Default: 60 seconds                                                                                    | cse.checkExpirationsInterval               |
| cseID                                  | The CSE ID. A CSE-ID must start with a /.<br/>Default: id-in                                                                                                               | cse.cseID                                  |
| defaultSerialization                   | Indicate the serialization format if none was given in a request and cannot be determined otherwise.<br/>Allowed values: json, cbor.<br/>Default: json                     | cse.defaultSerialization                   |
| enableRemoteCSE                        | Enable remote CSE registration and checking.<br/>See also command line arguments [–-remote-cse and -–no-remote-cse](Running.md).<br/>Default: true                         | cse.enableRemoteCSE                        |
| enableResourceExpiration               | Enable resource expiration. If disabled resources will not be expired when the "expirationTimestamp" is reached.<br/>Default: true                                         | cse.enableResourceExpiration               |
| enableSubscriptionVerificationRequests | Enable or disable verification requests when creating a new subscription.<br/>Default: true                                                                                | cse.enableSubscriptionVerificationRequests |
| flexBlockingPreference                 | Indicate the preference for flexBlocking response types. Allowed values: "blocking", "nonblocking".<br />Default: blocking                                                 | cse.flexBlockingPreference                 |
| maxExpirationDelta                     | Default and maximum expirationTime allowed for resources in seconds.<br/>Default: 60*60*24*365*5 = 157680000 seconds = 5 years                                             | cse.maxExpirationDelta                     |
| originator                             | Admin originator for the CSE.<br/>Default: CAdmin                                                                                                                          | cse.originator                             |
| releaseVersion                         | The release version indicator for requests. Allowed values: see setting of *supportedReleaseVersions*.<br />Default: 4                                                     | cse.releaseVersion                         |
| requestExpirationDelta                 | Expiration time for requests sent by the CSE in seconds<br/>Default: 10.0 seconds                                                                                          | cse.requestExpirationDelta                 |
| resourceID                             | The \<CSEBase> resource's resource ID. This should be the same value as *cseID* without the leading "/". Can be overwritten in imported CSE definition.<br/>Default: id-in | cse.resourceID                             |
| resourceName                           | The CSE's resource name or CSE-Name. Can be overwritten in imported CSE definition.<br>Default: cse-in                                                                     | cse.resourceName                           |
| resourcesPath                          | Directory of default resources to import.<br/>See also command line argument [–-import-directory](Running.md).<br/>Default: ./init                                         | cse.resourcesPath                          |
| sendToFromInResponses                  | Indicate whether the optional "to" and "from" parameters shall be sent in responses.<br/>Default: true                                                                     | cse.sendToFromInResponses                  |
| serviceProviderID                      | The CSE's service provider ID.<br/>Default: acme.example.com                                                                                                               | cse.serviceProviderID                      |
| sortDiscoveredResources                | Enable alphabetical sorting of discovery results.<br/>Default: true                                                                                                        | cse.sortDiscoveredResources                |
| supportedReleaseVersions               | A comma-separated list of supported release versions. This list can contain a single or multiple values.<br />Default: 2a,3,4,5                                            | cse.supportedReleaseVersions               |
| type                                   | The CSE type. Allowed values: IN, MN, ASN.<br/>Default: IN                                                                                                                 | cse.type                                   |

[top](#sections)

---

<a name="security"></a>

### [cse.security] - General Security Settings

| Setting         | Description                                                                               | Configuration Name           |
|:----------------|:------------------------------------------------------------------------------------------|:-----------------------------|
| enableACPChecks | Enable access control checks.<br/> Default: true                                          | cse.security.enableACPChecks |
| fullAccessAdmin | Always grant the admin originator full access (bypass access checks).<br /> Default: True | cse.security.fullAccessAdmin |

[top](#sections)

---

<a name="operation_jobs"></a>

### [cse.operation.jobs] - CSE Operations Settings - Jobs

| Setting             | Description                                                                                                                                                                                                                                     | Configuration Name                     |
|:--------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------|
| balanceTarget       | Thread Pool Management: Target balance between paused and running jobs (n paused for 1 running threads).<br/>Default: 3.0                                                                                                                       | cse.operation.jobs.balanceTarget       |
| balanceLatency      | Thread Pool Management: Number of get / create requests for a new thread before performing a balance check. A latency of 0 disables the thread pool balancing.<br/>Default: 1000                                                                | cse.operation.jobs.balanceLatency      |
| balanceReduceFactor | Thread Pool Management: The factor to reduce the paused jobs (number of paused / balanceReduceFactor) in a balance check.<br/>Example: a factor of 2.0 reduces the number of paused threads by half in a single balance check.<br/>Default: 2.0 | cse.operation.jobs.balanceReduceFactor |

[top](#sections)


---

<a name="operation_requests"></a>

### [cse.operation.requests] - CSE Operations Settings - Requests

| Setting | Description                                                                                                                                                                                                                | Configuration Name            |
|:--------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------|
| enable  | Enable request recording.<br/>Default: False                                                                                                                                                                               | cse.operation.requests.enable |
| size    | Maximum number of requests to be stored. Oldest requests will be deleted when this threshold is reached. Note, that a large number of requests might take a moment to be displayed in the console or UIs.<br/>Default: 250 | cse.operation.requests.size   |

[top](#sections)

---

<a name="http"></a>

###	[http] - HTTP Server Settings

| Setting                   | Description                                                                                                                                                                                                                                                                                                                             | Configuration Name             |
|:--------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------|
| port                      | Port to listen to.<br/>Default: 8080                                                                                                                                                                                                                                                                                                    | http.port                      |
| listenIF                  | Interface to listen to. Use 0.0.0.0 for "all" interfaces.<br/>Default:0.0.0.0                                                                                                                                                                                                                                                         | http.listenIF                  |
| address                   | Own address. Should be a local/public reachable address.<br/> Default: http://127.0.0.1:8080                                                                                                                                                                                                                                            | http.address                   |
| root                      | CSE Server root. Never provide a trailing /.<br/>Default: empty string                                                                                                                                                                                                                                                                  | http.root                      |
| enableRemoteConfiguration | Enable an endpoint for get and set certain configuration values via a REST interface.<br />**ATTENTION: Enabling this feature exposes configuration values, IDs and passwords, and is a security risk.**<br/> Default: false                                                                                                            | http.enableRemoteConfiguration |
| enableStructureEndpoint   | Enable an endpoint for getting a structured overview about a CSE's resource tree and deployment infrastructure (remote CSE's).<br />**ATTENTION: Enabling this feature exposes various potentially sensitive information.**<br/>See also the \[console].hideResources setting to hide resources from the tree.<br /> Default: false | http.enableStructureEndpoint   |
| enableUpperTesterEndpoint | Enable an endpoint for supporting Upper Tester commands to the CSE. This is to support certain testing and certification systems. See oneM2M's TS-0019 for further details.<br/>**ATTENTION: Enabling this feature may lead to a total loss of data.**<br/>Default: false                                                               | http.enableUpperTesterEndpoint |
| allowPatchForDelete       | Allow the http PATCH method to be used as a replacement for the DELETE method. This is useful for constraint devices that only support http/1.0, which doesn't specify the DELETE method.<br />Default: False                                                                                                                           | http.allowPatchForDelete       |
| timeout                   | Timeout when sending http requests and waiting for responses.<br />Default: 10.0 seconds                                                                                                                                                                                                                                                | http.timeout                   |

[top](#sections)

---

<a name="security_http"></a>

### [http.security] - HTTP Security Settings

| Setting           | Description                                                                                                                                                                                                                                      | Configuration Name              |
|:------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------|
| useTLS            | Enable TLS for communications.<br />This can be overridden by the command line arguments [--http and --https](Running.md).<br />See oneM2M TS-0003 Clause 8.2.1 "Overview on Security Association Establishment Frameworks".<br />Default: False | http.security.useTLS            |
| tlsVersion        | TLS version to be used in connections. <br />Allowed versions: TLS1.1, TLS1.2, auto . Use "auto" to allow client-server certificate version negotiation.<br />Default: auto                                                                      | http.security.tlsVersion        |
| verifyCertificate | Verify certificates in requests. Set to *False* when using self-signed certificates.<br />Default: False                                                                                                                                         | http.security.verifyCertificate |
| caCertificateFile | Path and filename of the certificate file.<br />Default: None                                                                                                                                                                                    | http.security.caCertificateFile |
| caPrivateKeyFile  | Path and filename of the private key file.<br />Default: None                                                                                                                                                                                    | http.security.caPrivateKeyFile  |
| enableBasicAuth   | Enable basic authentication for the HTTP binding.<br />Default: false                                                                                                                                                                            | http.security.enableBasicAuth   |
| enableTokenAuth   | Enable token authentication for the HTTP binding.<br />Default: false                                                                                                                                                                            | http.security.enableTokenAuth   |
| basicAuthFile     | Path and filename of the http basic authentication file. The file must contain lines with the format "username:password". Comments are lines starting with a #.<br />Default: certs/http_basic_auth.txt                                          | http.security.basicAuthFile     |
| tokenAuthFile     | Path and filename of the http bearer token authentication file. The file must contain lines with the format "token". Comments are lines starting with a #.<br />Default: certs/http_token_auth.txt                                               | http.security.tokenAuthFile     |

[top](#sections)

---

<a name="http_cors"></a>

### [http.cors] - HTTP CORS (Cross-Origin Resource Sharing) Settings

| Setting   | Description                                                                                                                                               | Configuration Name  |
|:----------|:----------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------|
| enable    | Enable CORS support for the HTTP binding.<br />Default: false                                                                                             | http.cors.enable    |
| resources | A comma separated list of allowed resource paths. The list elements could be regular expressions.<br />Default: "/*" , ie. all resources under the HTTP server's root | http.cors.resources |

[top](#sections)

---
<a name="http_wsgi"></a>

### [http.wsgi] - HTTP WSGI (Web Server Gateway Interface) Settings

| Setting         | Description                                                                                                                                                  | Configuration Name        |
|:----------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------|
| enable          | Enable WSGI support for the HTTP binding.<br />Default: false                                                                                                | http.wsgi.enable          |
| threadPoolSize  | The number of threads used to process requests. This number should be of similar size as the *connectionLimit* setting.<br />Default: 100                    | http.wsgi.threadPoolSize  |
| connectionLimit | The number of possible parallel connections that can be accepted by the WSGI server. Note: One connection uses one system file descriptor.<br />Default: 100 | http.wsgi.connectionLimit |



[top](#sections)

---
<a name="client_mqtt"></a>

###	[mqtt] - MQTT Client Settings

| Setting     | Description                                                                               | Configuration Name |
|:------------|:------------------------------------------------------------------------------------------|:-------------------|
| enable      | Enable the MQTT binding.<br />Default: False                                              | mqtt.enable        |
| address     | The hostname of the MQTT broker.<br />Default; 127.0.0.1                                  | mqtt.address       |
| port        | Set the port for the MQTT broker.<br />Default: 1883, or 8883 for TLS                     | mqtt.port          |
| listenIF    | Interface to listen to. Use 0.0.0.0 for "all" interfaces.<br/>Default:0.0.0.0             | mqtt.listenIF      |
| keepalive   | Value for the MQTT connection's keep-alive parameter in seconds.<br />Default: 60 seconds | mqtt.keepalive     |
| topicPrefix | Optional prefix for topics.<br />Default: empty string                                    | mqtt.topicPrefix   |
| timeout     | Timeout when sending MQTT requests and waiting for responses.<br />Default: 10.0 seconds  | mqtt.timeout       |

[top](#sections)

---

<a name="security_mqtt"></a>

### [mqtt.security] - MQTT Security Settings		

| Setting              | Description                                                                                                                                                                                                                     | Configuration Name                 |
|:---------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------|
| username             | The username for MQTT broker authentication if required by the broker.<br/>Default: None                                                                                                                                        | mqtt.security.username             |
| password             | The password for MQTT broker authentication.<br/>Default: None                                                                                                                                                                  | mqtt.security.password             |
| useTLS               | Enable TLS for communications with the MQTT broker.<br />Default: False                                                                                                                                                         | mqtt.security.useTLS               |
| verifyCertificate    | Verify certificates in requests. Set to False when using self-signed certificates..<br />Default: False                                                                                                                         | mqtt.security.verifyCertificate    |
| caCertificateFile    | Path and filename of the certificate file.<br />Default: None                                                                                                                                                                   | mqtt.security.caCertificateFile    |
| allowedCredentialIDs | List of credential-IDs that can be used to register an AE via MQTT. If this list is empty then all credential IDs are allowed.<br />This is a comma-separated list. Wildcards (* and ?) are supported.<br />Default: empty list | mqtt.security.allowedCredentialIDs |

[top](#sections)

---

<a name="database"></a>

###	[database] - Database Settings

| Setting        | Description                                                                                                                                                          | Configuration Name      |
|:---------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------|
| path           | Directory for the database files.<br/>Default: ./data                                                                                                                | database.path           |
| inMemory       | Operate the database in in-memory mode. Attention: No data is stored persistently.<br/>See also command line argument [--db-storage](Running.md).<br/>Default: false | database.inMemory       |
| cacheSize      | Cache size in bytes, or 0 to disable caching.<br/>Default: 0                                                                                                         | database.cacheSize      |
| resetOnStartup | Reset the databases at startup.<br/>See also command line argument [--db-reset](Running.md).<br/>Default: false                                                      | database.resetOnStartup |
| writeDelay     | Delay in seconds before new data is written to disk to avoid trashing. Must be full seconds-<br/>Default: 1 second                                                   | database.writeDelay     |

[top](#sections)

---

<a name="logging"></a>

###	[logging] - Logging Settings

| Setting               | Description                                                                                                                                                 | Configuration Name            |
|:----------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------|
| enableFileLogging     | Enable logging to file.<br/>Default: false                                                                                                                  | logging.enableFileLogging     |
| enableScreenLogging   | Enable logging to the screen.<br/>Default: true                                                                                                             | logging.enableScreenLogging   |
| path                  | Pathname for log files.<br />Default: ./logs                                                                                                                | logging.path                  |
| level                 | Loglevel. Allowed values: debug, info, warning, error, off.<br/>See also command line argument [–log-level](Running.md).<br/> Default: debug                | logging.level                 |
| count                 | Number of files for log rotation.<br/>Default: 10                                                                                                           | logging.count                 |
| size                  | Size per log file.<br/>Default: 100.000 bytes                                                                                                               | logging.size                  |
| maxLogMessageLength   | Maximum length of a log message. Longer messages will be truncated. A value of 0 means no truncation.<br />Default: 1000 characters                         | logging.maxLogMessageLength   |
| stackTraceOnError     | Print a stack trace when logging an 'error' level message.<br />Default: True                                                                               | logging.stackTraceOnError     |
| enableBindingsLogging | Enable logging of low-level HTTP & MQTT client events.<br />Default: False                                                                                  | logging.enableBindingsLogging |
| queueSize             | Number of log entries that can be added to the asynchronous queue before blocking. A queue size of 0 means disabling the queue.<br />Default: F5000 entries | logging.queueSize             |
| filter                | List of component names to exclude from logging.<br />Default: werkzeug,markdown_it                                                                         | logging.filter                |

[top](#sections)

---

<a name="cse_registration"></a>

###	[cse.registration] - Settings for Self-Registrations

| Setting               | Description                                                                                                                                                                     | Configuration Name                     |
|:----------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------|
| allowedAEOriginators  | List of AE originators that can register. This is a comma-separated list of originators. Wildcards (* and ?) are supported.<br />Default: C\*, S\*                              | cse.registration.allowedAEOriginators  |
| allowedCSROriginators | List of CSR originators that can register. This is a comma-separated list of originators. Wildcards (* and ?) are supported.<br />Note: No leading "/"<br />Default: empty list | cse.registration.allowedCSROriginators |
| checkLiveliness       | Check the liveliness of the registrations to the registrar CSE and also from the registree CSEs.<br /> Default: True                                                            | cse.registration.checkLiveliness       |

[top](#sections)

---

<a name="registrar"></a>

### [cse.registrar] - Settings for Registrar Registrar CSE Access 

| Setting              | Description                                                                                                                                                                                                                    | Configuration Name                 |
|:---------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------|
| address              | URL of the Registrar CSE.<br/>Default: no default                                                                                                                                                                              | cse.registrar.address              |
| root                 | Registrar CSE root path. Never provide a trailing /.<br/>Default: empty string                                                                                                                                                 | cse.registrar.root                 |
| cseID                | CSE-ID of the Registrar CSE. A CSE-ID must start with a /.<br/>Default: no default                                                                                                                                             | cse.registrar.cseID                |
| resourceName         | The Registrar CSE's resource name. <br>Default: no default                                                                                                                                                                     | cse.registrar.resourceName         |
| serialization        | Specify the serialization type that must be used for the registration to the registrar CSE.<br />Allowed values: json, cbor<br />Default: json                                                                                 | cse.registrar.serialization        |
| checkInterval        | This setting specifies the pause in seconds between tries to connect to the configured registrar CSE. This value is also used to check the connectivity to the registrar CSE after a successful registration..<br/>Default: 30 | cse.registrar.checkInterval        |
| excludeCSRAttributes | List of attributes that are excluded when creating a registrar CSR.<br />Default: empty list                                                                                                                                    | cse.registrar.excludeCSRAttributes |

[top](#sections)

---

<a name="announcements"></a>

### [cse.announcements] - Settings for Resource Announcements 

| Setting                        | Description                                                                                                                                          | Configuration Name                               |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------|
| checkInterval                  | Wait n seconds between tries to announce resources to registered remote CSE.<br />Default: 10                                                        | cse.announcements.checkInterval                  |
| allowAnnouncementsToHostingCSE | Allow resource announcements to the own hosting CSE.<br />Default: True                                                                              | cse.announcements.allowAnnouncementsToHostingCSE |
| delayAfterRegistration         | Specify a short delay in seconds before starting announcing resources after a remote CSE has registered at the hosting CSE.<br />Default: 3 seconds. | cse.announcements.delayAfterRegistration         |

[top](#sections)

---

<a name="statistics"></a>

###	[cse.statistics] - Statistic Settings

| Setting       | Description                                                                                                              | Configuration Name           |
|:--------------|:-------------------------------------------------------------------------------------------------------------------------|:-----------------------------|
| enable        | This setting enables or disables the CSE's statistics collection and reporting.<br />Default: True                       | cse.statistics.enable        |
| writeInterval | This setting specifies the pause, in seconds, between writing the collected statistics to the database.<br />Default: 60 | cse.statistics.writeInterval |

[top](#sections)

---

<a name="resource_acp"></a>

###	[resource.acp] - Resource Defaults: ACP

| Setting        | Description                                                           | Configuration Name            |
|:---------------|:----------------------------------------------------------------------|:------------------------------|
| selfPermission | Default selfPermission when creating an ACP resource.<br/>Default: 51 | resource.acp.selfPermission   |

[top](#sections)

---

<a name="resource_actr"></a>

###	[resource.actr] - Resource Defaults: Action

| Setting       | Description                                                                                                                              | Configuration Name          |
|:--------------|:-----------------------------------------------------------------------------------------------------------------------------------------|:----------------------------|
| ecpContinuous | Default for the *evalControlParam* attribute, when the *evalMode* is "continuous". The unit is number.<br />Default: 1000                | resource.actr.ecpContinuous |
| ecpPeriodic   | Default for the *evalControlParam* attribute, when the *evalMode* is "periodic". The unit is milliseconds.<br />Default: 10000 ms = 10 s | resource.actr.ecpPeriodic   |

[top](#sections)

---

<a name="resource_cnt"></a>

### [resource.cnt] - Resource Defaults: Container

| Setting      | Description                                            | Configuration Name        |
|:-------------|:-------------------------------------------------------|:--------------------------|
| enableLimits | Enable/disable the default limits.<br/> Default: False | resource.cnt.enableLimits |
| mni          | Default for maxNrOfInstances.<br/> Default: 10         | resource.cnt.mni          |
| mbs          | Default for maxByteSize.<br/>Default: 10.000 bytes     | resource.cnt.mbs          |

[top](#sections)

---

<a name="resource_grp"></a>

### [resource.grp] - Resource Defaults: Group

| Setting              | Description                                                                                                                                                         | Configuration Name                |
|:---------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------|
| resultExpirationTime | Set the time for aggregating the results of a group request before interrupting. The format is the time in ms. A value of 0 ms means no timeout.</br >Default: 0 ms | resource.grp.resultExpirationTime |

[top](#sections)

---

<a name="resource_lcp"></a>

### [resource.lcp] - Resource Defaults: 

| Setting | Description                                                                           | Configuration Name |
|:--------|:--------------------------------------------------------------------------------------|:-------------------|
| mni     | Default for maxNrOfInstances for the LocationPolicy's container.<br/> Default: 10     | resource.lcp.mni   |
| mbs     | Default for maxByteSize for the LocationPolicy's container.<br/>Default: 10.000 bytes | resource.lcp.mbs   |

[top](#sections)

---

<a name="resource_req"></a>

### [resource.req] - Resource Defaults: Request

| Setting        | Description                                                                       | Configuration Name |
|:---------------|:----------------------------------------------------------------------------------|:-------------------|
| expirationTime | A \<request> resource's  expiration time in seconds. Must be >0.<br />Default: 60 | resource.req.et    |

[top](#sections)

---

<a name="resource_sub"></a>

### [resource.sub] - Resource Defaults: Subscription

| Setting             | Description                                                                           | Configuration Name                 |
|:--------------------|:--------------------------------------------------------------------------------------|:-----------------------------------|
| batchNotifyDuration | Default for the batchNotify/duration in seconds. Must be >0.<br />Default: 60 seconds | resource.sub.batchNotifyDuration   |

[top](#sections)

---

<a name="resource_ts"></a>

### [resource.ts] - Resource Defaults: TimeSeries

| Setting      | Description                                            | Configuration Name       |
|:-------------|:-------------------------------------------------------|:-------------------------|
| enableLimits | Enable/disable the default limits.<br/> Default: False | resource.ts.enableLimits |
| mni          | Default for maxNrOfInstances.<br/> Default: 10         | resource.ts.mni          |
| mbs          | Default for maxByteSize.<br/>Default: 10.000 bytes     | resource.ts.mbs          |
| mdn          | Default for missingDataMaxNr.<br />Default: 10         | resource.ts.mdn          |

[top](#sections)

---

<a name="resource_tsb"></a>

### [resource.tsb] - Resource Defaults: TimeSyncBeacon

| Setting | Description                                                                                                                                                                               | Configuration Name |
|:--------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------|
| bcni    | Default timeSyncBeacon interval. This is the duration between to beacon notifications sent by the CSE to an AE or CSE.T he format must be an ISO8601 duration.<br/>Default: PT1H = 1 hour | resource.tsb.bcni  |
| bcnt    | Default timeSyncBeacon threshold. When this time threshold is passed then a beacon notifications is sent to an AE or CSE.<br/>Default: 10.0 seconds                                       | resource.ts.bcnt   |

[top](#sections)

---

<a name="console"></a>

###	[console] - Console Settings

| Setting                     | Description                                                                                                                                                                                   | Configuration Name                  |
|:----------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------|
| confirmQuit                 | Quitting the console needs to be confirmed.<br />This may not work under Windows, so it is switched off by default.<br />Default: False                                                       | console.confirmQuit                 |
| headless                    | Run the CSE in headless mode, i.e. without a console and without screen logging.<br />Default: False                                                                                          | console.headless                    |
| hideResources               | Hide certain resources from display in the console. This is a list of resource identifiers. Wildcards are allowed.<br/>Default: Empty list                                                    | console.hideResources               |
| refreshInterval             | Interval for continuously refreshing information displays. Must be > 0.0<br/>Default: 2.0 seconds                                                                                             | console.refreshInterval             |
| theme                       | Set the color theme for the console. Allowed values are "dark" and "light".<br />Default: dark                                                                                                | console.theme                       |
| treeIncludeVirtualResources | Show virtual resources in the console's and structure endpoint's tree view..<br/>Default: False                                                                                               | console.treeIncludeVirtualResources |
| treeMode                    | Set the mode how resources and their content are presented in the console's and structure endpoint's tree view.<br/>Allowed values: normal, compact, content, contentOnly<br/>Default: normal | console.treeMode                    |

[top](#sections)

---

<a name="textui"></a>

###	[textui] - Text UI Settings

| Setting         | Description                                                                                                           | Configuration Name     |
|:----------------|:----------------------------------------------------------------------------------------------------------------------|:-----------------------|
| startWithTUI    | Show the text UI after startup.<br />See also command line argument [–-textui](Running.md).<br />Default: False       | textui.startWithTUI    |
| theme           | Set the color theme for the text UI. Allowed values are "dark" and "light".<br />Default: same as [console].theme     | textui.theme           |
| refreshInterval | Interval for refreshing various views in the text UI.<br />Default: 2.0                                               | textui.refreshInterval |

[top](#sections)


---

<a name="scripting"></a>

###	[scripting] - Scripting Settings

| Setting                | Description                                                                                                                                                    | Configuration Name               |
|:-----------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------|
| scriptDirectories      | Add one or multiple directory paths to look for scripts, in addition to the ones in the "init" directory. Must be a comma-separated list.<br/>Default: not set | scripting.scriptDirectories      |
| verbose                | Enable debug output during script execution, such as the current executed line.<br/>Default: False                                                             | scripting.verbose                |
| fileMonitoringInterval | Set the interval to check for new files in the script (init) directory.<br/>0 means disable monitoring. Must be >= 0.0.<br/>Default: 2.0 seconds               | scripting.fileMonitoringInterval |
| maxRuntime             | Set the timeout for script execution in seconds. 0.0 seconds means no timeout.<br/>Must be >= 0.0.<br/>Default: 60.0 seconds                                   | scripting.maxRuntime |

[top](#sections)

---

<a name="webui"></a>

###	[webui] - Web UI Settings

| Setting | Description                                  | Configuration Name |
|:--------|:---------------------------------------------|:-------------------|
| root    | Root path of the web UI.<br/>Default: /webui | webui.root         |

[top](#sections)

---

<a name="advanced"></a>

## Advanced Usage

### Using Settings During Imports

Configuration values can be referenced by their respective configuration name and used when [importing resources](Importing.md#accessing-configuration-settings).

The following configuration names are supported in addition to those defined in the sections below. They are set by the CSE at runtime.

| Configuration name | Description                              |
|:-------------------|:-----------------------------------------|
| configfile         | Name of the configuration file.          |
| packageDirectory   | Path to the ACME package directory.      |

[top](#sections)

---

[← README](../README.md) 
