# Configuration - CSE Settings

The CSE settings are used to configure the CSE's general behavior, security settings, and statistics collection. 

## General Settings

**Section: `[cse]`**

These settings are used to configure basic settings and the general behavior of the CSE.

| Setting                                | Description                                                                                                                                                                                              | Default                                          | Configuration Name                         |
|:---------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------|:-------------------------------------------|
| asyncSubscriptionNotifications         | Enable or disable asynchronous notification for normal runtime subscription notifications.                                                                                                               | true                                             | cse.asyncSubscriptionNotifications         |
| checkExpirationsInterval               | Interval to check for expired resources. 0 means "no checking".                                                                                                                                          | 60 seconds                                       | cse.checkExpirationsInterval               |
| cseID                                  | The CSE ID. A CSE-ID must start with a /.                                                                                                                                                                | id-in                                            | cse.cseID                                  |
| defaultSerialization                   | Indicate the serialization format if none was given in a request and cannot be determined otherwise.<br/>Allowed values: json, cbor.                                                                     | json                                             | cse.defaultSerialization                   |
| enableRemoteCSE                        | Enable remote CSE registration and checking.<br/>See also command line arguments [–-remote-cse and -–no-remote-cse](../setup/Running.md#command-line-arguments).                                         | true                                             | cse.enableRemoteCSE                        |
| enableResourceExpiration               | Enable resource expiration. If disabled resources will not be expired when the "expirationTimestamp" is reached.                                                                                         | true                                             | cse.enableResourceExpiration               |
| enableSubscriptionVerificationRequests | Enable or disable verification requests when creating a new subscription.                                                                                                                                | true                                             | cse.enableSubscriptionVerificationRequests |
| flexBlockingPreference                 | Indicate the preference for flexBlocking response types. Allowed values: "blocking", "nonblocking".                                                                                                      | blocking                                         | cse.flexBlockingPreference                 |
| maxExpirationDelta                     | Default and maximum expirationTime allowed for resources in seconds.                                                                                                                                     | 60\*60\*24\*365\*5 = 157680000 seconds = 5 years | cse.maxExpirationDelta                     |
| originator                             | Admin originator for the CSE.                                                                                                                                                                            | CAdmin                                           | cse.originator                             |
| poa                                    | Set the CSE's point-of-access. This is a comma-separated list of URLs.                                                                                                                                   | The configured HTTP server's address.            | cse.poa                                    |
| releaseVersion                         | The release version indicator for requests. Allowed values: see setting of *supportedReleaseVersions*.                                                                                                   | 4                                                | cse.releaseVersion                         |
| requestExpirationDelta                 | Expiration time for requests sent by the CSE in seconds.                                                                                                                                                 | 10.0 seconds                                     | cse.requestExpirationDelta                 |
| resourceID                             | The \<CSEBase> resource's resource ID. This should be the same value as *cseID* without the leading "/".                                                                                                 | id-in                                            | cse.resourceID                             |
| resourceName                           | The CSE's resource name or CSE-Name.                                                                                                                                                                     | cse-in                                           | cse.resourceName                           |
| resourcesPath                          | Directory of the CSE's *init* directory that hosts resources, policies, and other settings to import.<br/>See also command line argument [–-init-directory](../setup/Running.md#command-line-arguments). | [${basic.config:initDirectory}](../setup/Configuration-introduction.md#settings-interpolation)                    | cse.resourcesPath                          |
| sendToFromInResponses                  | Indicate whether the optional "to" and "from" parameters shall be sent in responses.                                                                                                                     | true                                             | cse.sendToFromInResponses                  |
| serviceProviderID                      | The CSE's service provider ID.                                                                                                                                                                           | acme.example.com                                 | cse.serviceProviderID                      |
| sortDiscoveredResources                | Enable alphabetical sorting of discovery results.                                                                                                                                                        | true                                             | cse.sortDiscoveredResources                |
| supportedReleaseVersions               | A comma-separated list of supported release versions. This list can contain a single or multiple values.                                                                                                 | 2a,3,4,5                                         | cse.supportedReleaseVersions               |
| type                                   | The CSE type. Allowed values: IN, MN, ASN.                                                                                                                                                               | IN                                               | cse.type                                   |


## Resource Announcements

**Section: `[cse.announcements]`**

These settings are used to configure the behavior of resource announcements. They control mainly internal CSE behaviour and are not directly related to the oneM2M standard.

| Setting                        | Description                                                                                                                 | Default    | Configuration Name                               |
|:-------------------------------|:----------------------------------------------------------------------------------------------------------------------------|:-----------|:-------------------------------------------------|
| checkInterval                  | Wait n seconds between tries to announce resources to registered remote CSE.                                                | 10 seconds | cse.announcements.checkInterval                  |
| allowAnnouncementsToHostingCSE | Allow resource announcements to the own hosting CSE.                                                                        | True       | cse.announcements.allowAnnouncementsToHostingCSE |
| delayAfterRegistration         | Specify a short delay in seconds before starting announcing resources after a remote CSE has registered at the hosting CSE. | 3 seconds  | cse.announcements.delayAfterRegistration         |


## Operation - Jobs

**Section: `[cse.operation.jobs]`**

These settings are used to configure the CSE's job and thread management.
Jobs are used to handle asynchronous tasks like resource expiration, resource announcements, and other tasks.

| Setting             | Description                                                                                                                                                                                                                    | Default | Configuration Name                     |
|:--------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------|:---------------------------------------|
| balanceTarget       | Thread Pool Management: Target balance between paused and running jobs (n paused for 1 running threads).                                                                                                                       | 3.0     | cse.operation.jobs.balanceTarget       |
| balanceLatency      | Thread Pool Management: Number of get / create requests for a new thread before performing a balance check. A latency of 0 disables the thread pool balancing.                                                                 | 1000    | cse.operation.jobs.balanceLatency      |
| balanceReduceFactor | Thread Pool Management: The factor to reduce the paused jobs (number of paused / balanceReduceFactor) in a balance check.<br/>Example: a factor of 2.0 reduces the number of paused threads by half in a single balance check. | 2.0     | cse.operation.jobs.balanceReduceFactor |


## Operation - Requests

**Section: `[cse.operation.requests]`**


These settings are used to configure the CSE's internal request recording.

| Setting | Description                                                                                                                                                                                               | Default | Configuration Name            |
|:--------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|:------------------------------|
| enable  | Enable request recording.                                                                                                                                                                                 | False   | cse.operation.requests.enable |
| size    | Maximum number of requests to be stored. Oldest requests will be deleted when this threshold is reached. Note, that a large number of requests might take a moment to be displayed in the console or UIs. | 250     | cse.operation.requests.size   |


## CSE Registration 

**Section: `[cse.registration]`**

These settings are used to configure the CSE's internal registration behaviour, but also set the allowed originators for AE and CSR registrations.

| Setting               | Description                                                                                                                                                                          | Default    | Configuration Name                     |
|:----------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------|:---------------------------------------|
| allowedAEOriginators  | List of AE originators that can register. This is a comma-separated list of originators. Wildcards (* and ?) are supported.                                                          | C\*, S\*   | cse.registration.allowedAEOriginators  |
| allowedCSROriginators | List of CSR originators that can register. This is a comma-separated list of originators. Wildcards (* and ?) are supported.<br />**Note**: CSE-IDs must **not** have a leading "/". | empty list | cse.registration.allowedCSROriginators |
| checkLiveliness       | Check the liveliness of the registrations to the registrar CSE and also from the registree CSEs.                                                                                     | True       | cse.registration.checkLiveliness       |


## Registrar CSE Access 

**Section: `[cse.registrar]`**

These settings are used to configure the address and access to its Registrar CSE.

| Setting              | Description                                                                                                                                                                                                   | Default      | Configuration Name                 |
|:---------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------|:-----------------------------------|
| address              | URL of the Registrar CSE.                                                                                                                                                                                     | no default   | cse.registrar.address              |
| root                 | Registrar CSE root path. Never provide a trailing /.                                                                                                                                                          | empty string | cse.registrar.root                 |
| cseID                | CSE-ID of the Registrar CSE. A CSE-ID must start with a /.                                                                                                                                                    | no default   | cse.registrar.cseID                |
| resourceName         | The Registrar CSE's resource name.                                                                                                                                                                            | no default   | cse.registrar.resourceName         |
| serialization        | Specify the serialization type that must be used for the registration to the registrar CSE.<br />Allowed values: json, cbor                                                                                   | json         | cse.registrar.serialization        |
| checkInterval        | This setting specifies the pause in seconds between tries to connect to the configured registrar CSE. This value is also used to check the connectivity to the registrar CSE after a successful registration. | 30 seconds   | cse.registrar.checkInterval        |
| excludeCSRAttributes | Comma separated list of attributes that are excluded when creating a registrar CSR.                                                                                                                           | empty list   | cse.registrar.excludeCSRAttributes |


## General Security

**Section: `[cse.security]`**

These settings are used to configure the CSE's security settings.

| Setting         | Description                                                           | Default | Configuration Name           |
|:----------------|:----------------------------------------------------------------------|:--------|:-----------------------------|
| enableACPChecks | Enable access control checks.                                         | True    | cse.security.enableACPChecks |
| fullAccessAdmin | Always grant the admin originator full access (bypass access checks). | True    | cse.security.fullAccessAdmin |


## Statistics

**Section: `[cse.statistics]`**

These settings are used to configure the CSE's internal statistics collection and reporting.

| Setting       | Description                                                                                             | Default    | Configuration Name           |
|:--------------|:--------------------------------------------------------------------------------------------------------|:-----------|:-----------------------------|
| enable        | This setting enables or disables the CSE's statistics collection and reporting.                         | True       | cse.statistics.enable        |
| writeInterval | This setting specifies the pause, in seconds, between writing the collected statistics to the database. | 60 seconds | cse.statistics.writeInterval |

