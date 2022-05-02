[← README](../README.md) 

# Configuration

[Configuration Sections](#sections)  
[Advanced Usage](#advanced)  


Configuration of CSE parameters is done through a configuration file. This file contains all configurable and customizable
settings for the CSE. It is optional, and settings in this file overwrite the CSE's default values. 

It follows the Windows INI file format with sections, keywords and values. A configuration file may include comments, 
prefixed with the characters "#"" or ";"" .

Also, some settings can be applied via the command line when starting the CSE. These command line arguments overwrite the
settings in the configuration file.


## The Configuration File

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
referece settings from the same or from other sections. The syntax to denote a value from a section is ```${section:option}```.

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

[\[cse\] - General CSE Settings](#general)  
[\[cse.security\] - General Security Settings](#security)  
[\[cse.operation\] - CSE Operations Settings](#operation)  
[\[server.http\] - HTTP Server Settings](#server_http)  
[\[server.http.security\] - HTTP Security Settings](#security_http)  
[\[client.mqtt\] - MQTT Client Settings](#client_mqtt)  
[\[client.mqtt.security\] - MQTT Security Settings](#security_mqtt)  
[\[database\] - Database Settings](#database)  
[\[logging\] - Logging Settings](#logging)  
[\[cse.registration\] - Settings for Self-Registrations](#cse_registration)  
[\[cse.registrar\] - Settings for Remote CSE Access](#registrar)  
[\[cse.announcements\] - Settings for Resource Announcements](#announcements)  
[\[cse.statistics\] - Statistic Settings](#statistics)  
[\[cse.resource.acp\] - Resource defaults: Access Control Policies](#resource_acp)  
[\[cse.resource.cnt\] - Resource Defaults: Container](#resource_cnt)  
[\[cse.resource.req\] - Resource Defaults: Request](#resource_req)  
[\[cse.resource.sub\] - Resource Defaults: Subscription](#resource_sub)  
[\[cse.resource.ts\] - Resource Defaults: TimeSeries](#resource_ts)  
[\[cse.resource.tsb\] - Resource Defaults: TimeSyncBeacon](#resource_tsb)  
[\[cse.console\] - Console Settings](#console)  
[\[cse.scripting\] - Scripting Settings](#scripting)  
[\[cse.webui\] - Web UI Settings](#webui)  
	

### Additional Settings
[\[server.http.mappings\] - ID Mappings](#id_mappings)  


<a name="general"></a>
### [cse] - General CSE Settings

| Keyword                  | Description                                                                                                                                            | Configuration Name           |
|:-------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------|
| type                     | The CSE type. Allowed values: IN, MN, ASN.<br/>Default: IN                                                                                             | cse.type                     |
| serviceProviderID        | The CSE's service provider ID.<br/>Default: acme                                                                                                       | cse.spid                     |
| cseID                    | The CSE ID. Can be overwritten in imported CSE definition. A CSE-ID must start with a /.<br/>Default: id-in                                            | cse.csi                      |
| resourceID               | The CSE's resource ID. This should be the *cseid* without the leading "/". Can be overwritten in imported CSE definition.<br/>Default: id-in           | cse.ri                       |
| resourceName             | The CSE's resource name or CSE-Name. Can be overwritten in imported CSE definition.<br>Default: cse-in                                                 | cse.rn                       |
| resourcesPath            | Directory of default resources to import.<br/>See also command line argument [–import-directory](Running.md).<br/>Default: ./init                      | cse.resourcesPath            |
| expirationDelta          | Expiration time before resources are removed in seconds.<br/> Default: 60*60*24*365 = 31536000 seconds = 1 year                                        | cse.expirationDelta          |
| maxExpirationDelta       | Maximum expirationTime allowed for resources in seconds.<br/>Default: 5 years = 157680000 seconds                                                      | cse.maxExpirationDelta       |
| requestExpirationDelta   | Expiration time for requests sent by the CSE in seconds<br/>Default: 10.0 seconds                                                                      | cse.requestExpirationDelta   |
| originator               | Admin originator for the CSE.<br/>Default: CAdmin                                                                                                      | cse.originator               |
| enableRemoteCSE          | Enable remote CSE registration and checking.<br/>See also command line arguments [–remote-cse and –no-remote-cse](Running.md).<br/>Default: true       | cse.enableRemoteCSE          |
| sortDiscoveredResources  | Enable alphabetical sorting of discovery results.<br/>Default: true                                                                                    | cse.sortDiscoveredResources  |
| checkExpirationsInterval | Interval to check for expired resources. 0 means "no checking".<br/>Default: 60 seconds                                                                | cse.checkExpirationsInterval |
| flexBlockingPreference   | Indicate the preference for flexBlocking response types. Allowed values: "blocking", "nonblocking".<br />Default: blocking                             | cse.flexBlockingPreference   |
| supportedReleaseVersions | A comma-separated list of supported release versions. This list can contain a single or multiple values.<br />Default: 2a,3,4                          | cse.supportedReleaseVersions |
| releaseVersion           | The release version indicator for requests. Allowed values: 2a, 3, 4.<br />Default: 3                                                                  | cse.releaseVersion           |
| defaultSerialization     | Indicate the serialization format if none was given in a request and cannot be determined otherwise.<br/>Allowed values: json, cbor.<br/>Default: json | cse.defaultSerialization     |


<a name="security"></a>
### [cse.security] - General Security Settings

| Keyword         | Description                                                                               | Configuration Name           |
|:----------------|:------------------------------------------------------------------------------------------|:-----------------------------|
| enableACPChecks | Enable access control checks.<br/> Default: true                                          | cse.security.enableACPChecks |
| fullAccessAdmin | Always grant the admin originator full access (bypass access checks).<br /> Default: True | cse.security.fullAccessAdmin |


<a name="operation"></a>
### [cse.operation] - CSE Operations Settings

| Keyword                | Description                                                                                                                                                                                                                                     | Configuration Name                   |
|:-----------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------|
| jobBalanceTarget       | Thread Pool Management: Target balance between paused and running jobs (n paused for 1 running threads).<br/>Default: 3.0                                                                                                                       | cse.operation.jobBalanceTarget       |
| jobBalanceLatency      | Thread Pool Management: Number of get / create requests for a new thread before performing a balance check. A latency of 0 disables the thread pool balancing.<br/>Default: 1000                                                                | cse.operation.jobBalanceLatency      |
| jobBalanceReduceFactor | Thread Pool Management: The Factor to reduce the paused jobs (number of paused / balanceReduceFactor) in a balance check.<br/>Example: a factor of 2.0 reduces the number of paused threads by half in a single balance check.<br/>Default: 2.0 | cse.operation.jobBalanceReduceFactor |


<a name="server_http"></a>
###	[server.http] - HTTP Server Settings

| Keyword                   | Description                                                                                                                                                                                                                                                                                                                             | Configuration Name             |
|:--------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------|
| port                      | Port to listen to.<br/>Default: 8080                                                                                                                                                                                                                                                                                                    | http.port                      |
| listenIF                  | Interface to listen to. Use 0.0.0.0 for "all" interfaces.<br/>Default:127.0.0.1                                                                                                                                                                                                                                                         | http.listenIF                  |
| address                   | Own address. Should be a local/public reachable address.<br/> Default: http://127.0.0.1:8080                                                                                                                                                                                                                                            | http.address                   |
| root                      | CSE Server root. Never provide a trailing /.<br/>Default: empty string                                                                                                                                                                                                                                                                  | http.root                      |
| enableRemoteConfiguration | Enable an endpoint for get and set certain configuration values via a REST interface.<br />**ATTENTION: Enabling this feature exposes configuration values, IDs and passwords, and is a security risk.**<br/> Default: false                                                                                                            | http.enableRemoteConfiguration |
| enableStructureEndpoint   | Enable an endpoint for getting a structured overview about a CSE's resource tree and deployment infrastructure (remote CSE's).<br />**ATTENTION: Enabling this feature exposes various potentially sensitive information.**<br/>See also the \[cse.console].hideResources setting to hide resources from the tree.<br /> Default: false | http.enableStructureEndpoint   |
| enableResetEndpoint       | Enable an endpoint for resetting the CSE (remove all resources and import the init directory again)<br />**ATTENTION: Enabling this feature may lead to a total loss of data**.<br/>Default: false                                                                                                                                      | http.enableResetEndpoint       |
| enableUpperTesterEndpoint | Enable an endpoint for supporting Upper Tester commands to the CSE. This is to support certain testing and certification systems. See oneM2M's TS-0019 for further details.<br/>**ATTENTION: Enabling this feature may lead to a total loss of data.**<br/>Default: false                                                               | http.enableUpperTesterEndpoint |
| allowPatchForDelete       | Allow the http PATCH method to be used as a replacement for the DELETE method. This is useful for constraint devices that only support http/1.0, which doesn't specify the DELETE method.<br />Default: False                                                                                                                           | http.allowPatchForDelete       |


<a name="security_http"></a>
### [server.http.security] - HTTP Security Settings

| Keyword           | Description                                                                                                                                                                                                                                      | Configuration Name              |
|:------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------|
| useTLS            | Enable TLS for communications.<br />This can be overridden by the command line arguments [--http and --https](Running.md).<br />See oneM2M TS-0003 Clause 8.2.1 "Overview on Security Association Establishment Frameworks".<br />Default: False | http.security.useTLS            |
| tlsVersion        | TLS version to be used in connections. <br />Allowed versions: TLS1.1, TLS1.2, auto . Use "auto" to allow client-server certificate version negotiation.<br />Default: auto                                                                      | http.security.tlsVersion        |
| verifyCertificate | Verify certificates in requests. Set to *False* when using self-signed certificates.<br />Default: False                                                                                                                                         | http.security.verifyCertificate |
| caCertificateFile | Path and filename of the certificate file.<br />Default: None                                                                                                                                                                                    | http.security.caCertificateFile |
| caPrivateKeyFile  | Path and filename of the private key file.<br />Default: None                                                                                                                                                                                    | http.security.caPrivateKeyFile  |


<a name="client_mqtt"></a>
###	[client.mqtt] - MQTT Client Settings

| Keyword     | Description                                                                               | Configuration Name |
|:------------|:------------------------------------------------------------------------------------------|:-------------------|
| enable      | Enable the MQTT binding.<br />Default: False                                              | mqtt.enable        |
| address     | he hostname of the MQTT broker.<br />Default; 127.0.0.1                                   | mqtt.address       |
| port        | Set the port for the MQTT broker.<br />Default: 1883, or 8883 for TLS                     | mqtt.port          |
| listenIF    | Interface to listen to. Use 0.0.0.0 for "all" interfaces.<br/>Default:127.0.0.1           | mqtt.listenIF      |
| keepalive   | Value for the MQTT connection's keep-alive parameter in seconds.<br />Default: 60 seconds | mqtt.keepalive     |
| topicPrefix | Optional prefix for topics.<br />Default: empty string                                    | mqtt.topicPrefix   |
| timeout     | Timeout when sending MQTT requests and waiting for responses.<br />Default: 5.0 seconds   | mqtt.timeout       |


<a name="security_mqtt"></a>
### [client.mqtt.security] - MQTT Security Settings		

| Keyword              | Description                                                                                                                                                                                                                     | Configuration Name                 |
|:---------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------|
| username             | The username for MQTT broker authentication if required by the broker.<br/>Default: None                                                                                                                                        | mqtt.security.username             |
| password             | The password for MQTT broker authentication.<br/>Default: None                                                                                                                                                                  | mqtt.security.password             |
| useTLS               | Enable TLS for communications with the MQTT broker.<br />Default: False                                                                                                                                                         | mqtt.security.useTLS               |
| verifyCertificate    | Verify certificates in requests. Set to False when using self-signed certificates..<br />Default: False                                                                                                                         | mqtt.security.verifyCertificate    |
| caCertificateFile    | Path and filename of the certificate file.<br />Default: None                                                                                                                                                                   | mqtt.security.caCertificateFile    |
| allowedCredentialIDs | List of credential-IDs that can be used to register an AE via MQTT. If this list is empty then all credential IDs are allowed.<br />This is a comma-separated list. Wildcards (* and ?) are supported.<br />Default: empty list | mqtt.security.allowedCredentialIDs |


<a name="database"></a>
###	[database] - Database Settings

| Keyword        | Description                                                                                                                                                          | Configuration Name |
|:---------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------|
| path           | Directory for the database files.<br/>Default: ./data                                                                                                                | db.path            |
| inMemory       | Operate the database in in-memory mode. Attention: No data is stored persistently.<br/>See also command line argument [--db-storage](Running.md).<br/>Default: false | db.inMemory        |
| cacheSize      | Cache size in bytes, or 0 to disable caching.<br/>Default: 0                                                                                                         | db.cacheSize       |
| resetOnStartup | Reset the databases at startup.<br/>See also command line argument [--db-reset](Running.md).<br/>Default: false                                                      | db.resetOnStartup  |


<a name="logging"></a>
###	[logging] - Logging Settings

| Keyword               | Description                                                                                                                                                 | Configuration Name            |
|:----------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------|
| enableFileLogging     | Enable logging to file.<br/>Default: false                                                                                                                  | logging.enableFileLogging     |
| enableScreenLogging   | Enable logging to the screen.<br/>Default: true                                                                                                             | logging.enableScreenLogging   |
| path                  | Pathname for log files.<br />Default: ./logs                                                                                                                | logging.path                  |
| level                 | Loglevel. Allowed values: debug, info, warning, error, off.<br/>See also command line argument [–log-level](Running.md).<br/> Default: debug                | logging.level                 |
| count                 | Number of files for log rotation.<br/>Default: 10                                                                                                           | logging.count                 |
| size                  | Size per log file.<br/>Default: 100.000 bytes                                                                                                               | logging.size                  |
| stackTraceOnError     | Print a stack trace when logging an 'error' level message.<br />Default: True                                                                               | logging.stackTraceOnError     |
| enableBindingsLogging | Enable logging of low-level HTTP & MQTT client events.<br />Default: False                                                                                  | logging.enableBindingsLogging |
| queueSize             | Number of log entries that can be added to the asynchronous queue before blocking. A queue size of 0 means disabling the queue.<br />Default: F5000 entries | logging.queueSize             |


<a name="cse_registration"></a>
###	[cse.registration] - Settings for Self-Registrations

| Keyword               | Description                                                                                                                                                                     | Configuration Name                     |
|:----------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------------------------------------|
| allowedAEOriginators  | List of AE originators that can register. This is a comma-separated list of originators. Wildcards (* and ?) are supported.<br />Default: C\*, S\*                              | cse.registration.allowedAEOriginators  |
| allowedCSROriginators | List of CSR originators that can register. This is a comma-separated list of originators. Wildcards (* and ?) are supported.<br />Note: No leading "/"<br />Default: empty list | cse.registration.allowedCSROriginators |
| checkLiveliness       | Check the liveliness if the registrations to the registrar CSE and also from the registree CSEs.<br /> Default: True                                                            | cse.registration.checkLiveliness       |


<a name="registrar"></a>
### [cse.registrar] - Settings for Registrar Registrar CSE Access 

| Keyword              | Description                                                                                                                                          | Configuration Name                 |
|:---------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------|
| address              | URL of the Registrar CSE.<br/>Default: no default                                                                                                    | cse.registrar.address              |
| root                 | Registrar CSE root path. Never provide a trailing /.<br/>Default: empty string                                                                       | cse.registrar.root                 |
| cseID                | CSE-ID of the Registrar CSE. A CSE-ID must start with a /.<br/>Default: no default                                                                   | cse.registrar.csi                  |
| resourceName         | The Registrar CSE's resource name. <br>Default: no default                                                                                           | cse.registrar.rn                   |
| serialization        | Specify the serialization type that must be used for the registration to the registrar CSE.<br />Allowed values: json, cbor<br />Default: json       | cse.registrar.serialization        |
| checkInterval        | Wait n seconds between tries to to connect to the reRegistrarmote CSE and to check validity of Registrar CSE connections in seconds.<br/>Default: 30 | cse.registrar.checkInterval        |
| excludeCSRAttributes | List of resources that are excluded when creating a registrar CSR.<br />Default: empty list                                                          | cse.registrar.excludeCSRAttributes |


<a name="announcements"></a>
### [cse.announcements] - Settings for Resource Announcements 

| Keyword       | Description                                                                                      | Configuration Name              |
|:--------------|:-------------------------------------------------------------------------------------------------|:--------------------------------|
| checkInterval | Wait n seconds between tries to to announce resources to registered remote CSE.<br />Default: 10 | cse.announcements.checkInterval |



<a name="statistics"></a>
###	[cse.statistics] - Statistic Settings

| Keyword       | Description                                                              | Configuration Name           |
|:--------------|:-------------------------------------------------------------------------|:-----------------------------|
| enable        | Enable or disable collecting CSE statistics.<br />Default: True          | cse.statistics.enable        |
| writeInterval | Interval for saving statistics data to disk in seconds.<br />Default: 60 | cse.statistics.writeInterval |


<a name="resource_acp"></a>
###	[cse.resource.acp] - Resource Defaults: ACP

| Keyword        | Description                                                           | Configuration Name |
|:---------------|:----------------------------------------------------------------------|:-------------------|
| permission     | Default permission when creating an ACP resource.<br />Default: 63    | cse.acp.pv.acop    |
| selfPermission | Default selfPermission when creating an ACP resource.<br/>Default: 51 | cse.acp.pvs.acop   |


<a name="resource_cnt"></a>
### [cse.resource.cnt] - Resource Defaults: Container

| Keyword      | Description                                            | Configuration Name   |
|:-------------|:-------------------------------------------------------|:---------------------|
| enableLimits | Enable/disable the default limits.<br/> Default: False | cse.cnt.enableLimits |
| mni          | Default for maxNrOfInstances.<br/> Default: 10         | cse.cnt.mni          |
| mbs          | Default for maxByteSize.<br/>Default: 10.000 bytes     | cse.cnt.mbs          |


<a name="resource_req"></a>
### [cse.resource.req] - Resource Defaults: Request

| Keyword               | Description                                                                               | Configuration Name |
|:----------------------|:------------------------------------------------------------------------------------------|:-------------------|
| minimumExpirationTime | A \<request> resource's minimum expiration time in seconds. Must be >0.<br />Default: 60  | cse.req.minet      |
| maximumExpirationTime | A \<request> resource's maximum expiration time in seconds. Must be >0.<br />Default: 180 | cse.req.maxet      |


<a name="resource_sub"></a>
### [cse.resource.sub] - Resource Defaults: Subscription

| Keyword             | Description                                                                           | Configuration Name |
|:--------------------|:--------------------------------------------------------------------------------------|:-------------------|
| batchNotifyDuration | Default for the batchNotify/duration in seconds. Must be >0.<br />Default: 60 seconds | cse.sub.dur        |


<a name="resource_ts"></a>
### [cse.resource.ts] - Resource Defaults: TimeSeries

| Keyword      | Description                                            | Configuration Name  |
|:-------------|:-------------------------------------------------------|:--------------------|
| enableLimits | Enable/disable the default limits.<br/> Default: False | cse.ts.enableLimits |
| mni          | Default for maxNrOfInstances.<br/> Default: 10         | cse.ts.mni          |
| mbs          | Default for maxByteSize.<br/>Default: 10.000 bytes     | cse.ts.mbs          |
| mdn          | Default for missingDataMaxNr.<br />Default: 10         | cse.ts.mdn          |


<a name="resource_tsb"></a>
### [cse.resource.tsb] - Resource Defaults: TimeSyncBeacon

| Keyword | Description                                                                                                                                                                               | Configuration Name |
|:--------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------|
| bcni    | Default timeSyncBeacon interval. This is the duration between to beacon notifications sent by the CSE to an AE or CSE.T he format must be an ISO8601 duration.<br/>Default: PT1H = 1 hour | cse.tsb.bcni       |
| bcnt    | Default timeSyncBeacon threshold. When this time threshold is passed then a beacon notifications is sent to an AE or CSE.<br/>Default: 10.0 seconds                                       | cse.ts.bcnt        |


<a name="console"></a>
###	[cse.console] - Console Settings

| Keyword                     | Description                                                                                                                                                                                   | Configuration Name                      |
|:----------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------|
| refreshInterval             | Interval for continuously refreshing information displays. Must be > 0.0<br/>Default: 2.0 seconds                                                                                             | cse.console.refreshInterval             |
| hideResources               | Hide certain resources from display in the console. This is a list of resource identifiers. Wildcards are allowed.<br/>Default: Empty list                                                    | cse.console.hideResources               |
| treeMode                    | Set the mode how resources and their content are presented in the console's and structure endpoint's tree view.<br/>Allowed values: normal, compact, content, contentOnly<br/>Default: normal | cse.console.treeMode                    |
| treeIncludeVirtualResources | Show virtual resources in the console's and structure endpoint's tree view..<br/>Default: False                                                                                               | cse.console.treeIncludeVirtualResources |
| confirmQuit                 | Quitting the console needs to be confirmed.<br />This may not work under Windows, so it is switched off by default.<br />Default: False                                                       | cse.console.confirmQuit                 |
| theme                       | Set the color theme for the console. Allowed values are "dark" and "light".<br />Default: dark                                                                                                | cse.console.theme                       |


<a name="scripting"></a>
###	[cse.scripting] - Scripting Settings

| Keyword                | Description                                                                                                                                                    | Configuration Name                   |
|:-----------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------|
| scriptDirectories      | Add one or multiple directory paths to look for scripts, in addition to the ones in the "init" directory. Must be a comma-separated list.<br/>Default: not set | cse.scripting.scriptDirectories      |
| verbose                | Enable debug output during script execution, such as the current executed line.<br/>Default: False                                                             | cse.scripting.verbose                |
| fileMonitoringInterval | Set the interval to check for new files in the script (init) directory.<br/>0 means disable monitoring. Must be >= 0.0.<br/>Default: 2.0 seconds               | cse.scripting.fileMonitoringInterval |


<a name="webui"></a>
###	[cse.webui] - Web UI Settings

| Keyword | Description                                  | Configuration Name |
|:--------|:---------------------------------------------|:-------------------|
| enable  | Enable the web UI.<br/>Default: true         | cse.webui.enable   |
| root    | Root path of the web UI.<br/>Default: /webui | cse.webui.root     |


<a name="id_mappings"></a>
###	[server.http.mappings] - ID Mappings

This section defines mappings for URI paths to IDs in the CSE. Mappings
can be used to provide a more convenient way to access the CSE's resources via http.
Each setting in the configuration file  specifies a mapping, where the key
specifies a new path and the value specified the mapping to a request
(including optional arguments).

The http server redirects a request to a path element that matches one of 
specified keys to the respective request mapping (using the http status code 307).

Please note, that the "root" path in [server.http](#server_http) prefixes both the new
path and the respecting mapping. Also note, that the request still needs to have the necessary
headers set in the request.

The following snippet only presents some example for ID mappings.

```ini
[server.http.mappings]
/access/v1/devices=/cse-mn?ty=14&fu=1&fo=2&rcn=8
/access/v1/apps=/id-mn?ty=2&fu=1&fo=2&rcn=8
/access/v1/devices/battery=/id-mn?ty=14&mgd=1006&fu=1&fo=2&rcn=8
```

<a name="advanced"></a>
## Advanced Usage

### Using Settings During Imports

Configuration values can be referenced by their respective configuration name and used when [importing resources](Importing.md#accessing-configuration-settings).

The following configuration names are supported in addition to those defined in the sections below. They are set by the CSE at runtime.

| Configuration name | Description                              |
|:-------------------|:-----------------------------------------|
| configfile         | Path and name of the configuration file. |
| packageDirectory   | Path to the acme package directory.      |


[← README](../README.md) 
