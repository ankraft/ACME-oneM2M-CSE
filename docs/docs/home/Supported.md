# Supported Resource Types and Functionalities

This article lists the supported oneM2M resource types, functionalities, and additional runtime features of the ACME CSE.


## oneM2M Features

### oneM2M Specification Conformance

The CSE implementation successfully passes all the relevant oneM2M test cases for the supported resource types, attributes and behaviours.

### Release Versions

The ACME CSE supports oneM2M release 1 - 4 and the upcoming release 5 for the supported resource types and functionalities listed below. 

### CSE Types

The ACME CSE supports the following CSE types:

| CSE Type | Supported |
|:---------|:---------:|
| IN       |  &check;  |
| MN       |  &check;  |
| ASN      |  &check;  |


### Resource Types

The ACME CSE supports the following oneM2M resource types:

| Resource Type                   | Supported | Remarks                                                                                                                                                                                                             |
|:--------------------------------|:---------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Access Control Policy (ACP)     |  &check;  | Attribute-based access control is yet not supported                                                                                                                                                                 |
| Action (ACTR)                   |  &check;  | No support for the `input` attribute.                                                                                                                                                                               |
| Application Entity (AE)         |  &check;  | &lt;authorizationDecision>, &lt;authorizationPolicy> and &lt;authorizationInformation> are not supported yet.                                                                                                       |
| Container (CNT)                 |  &check;  |                                                                                                                                                                                                                     |
| ContentInstance (CIN)           |  &check;  |                                                                                                                                                                                                                     |
| CrossResourceSubscription (CRS) |  &check;  |                                                                                                                                                                                                                     |
| CSEBase (CB)                    |  &check;  |                                                                                                                                                                                                                     |
| Dependency (DEPR)               |  &check;  |                                                                                                                                                                                                                     |
| FlexContainer & Specializations |  &check;  | Any specialization is supported and validated. See [Attribute Policies](../development/AttributePolicies.md) for further details.<br />Supported specializations include: TS-0023 R4, GenericInterworking, AllJoyn. |
| FlexContainerInstance           |  &check;  | Experimental. This is an implementation of the draft FlexContainerInstance specification.                                                                                                                           |
| Group (GRP)                     |  &check;  | The support includes requests via the *fopt* (fanOutPoint) virtual resource. Groups may contain remote resources.                                                                                                   |
| LocationPolicy (LCP)            |  &check;  | Only *device based* location policy is supported. The LCP's *cnt* stores geo-coordinates and geo-fencing results.                                                                                                   |
| Management Objects              |  &check;  | See also the list of supported [management objects](#mgmtobjs).                                                                                                                                                     |
| Node (NOD)                      |  &check;  |                                                                                                                                                                                                                     |
| Polling Channel (PCH)           |  &check;  | Support for Request and Notification long-polling via the *pcu* (pollingChannelURI) virtual child resource. *requestAggregation* functionality is supported, too.                                                   |
| Remote CSE (CSR)                |  &check;  | Announced resources are  supported. Transit request to resources on registered CSE's are supported.                                                                                                                 |
| Request (REQ)                   |  &check;  |                                                                                                                                                                                                                     |
| Schedule (SCH)                  |  &check;  | Support for CSE communication, nodes, subscriptions and crossResourceSubscriptions.                                                                                                                                 |
| SemanticDescriptor (SMD)        |  &check;  | Support for basic resource handling and semantic queries.                                                                                                                                                           |
| Subscription (SUB)              |  &check;  | Notifications via http(s) (direct url or an AE's Point-of-Access (POA)). BatchNotifications, attributes, statistics, operation Monitor.                                                                             |
| TimeSeries (TS)                 |  &check;  | Including missing data notifications.                                                                                                                                                                               |
| TimeSeriesInstance (TSI)        |  &check;  | *dataGenerationTime* attribute only supports absolute timestamps.                                                                                                                                                   |
| TimeSyncBeacon (TSB)            |  &check;  | Experimental. Implemented functionality might change according to specification changes.                                                                                                                            |

<a name="mgmtobjs"></a>

### Management Object Specializations

The following table presents the supported management object specifications.

| Management Objects       | Management Objects     |
|--------------------------|------------------------|
| AreaNwkDeviceInfo (ANDI) | Memory (MEM)           |
| AreaNwkInfo (ANI)        | MobileNetwork (MNWK)   |
| Battery (BAT)            | MyCertFileCred (NYCFC) |
| DataCollect (DATC)       | Reboot (REB)           |
| DeviceCapability (DVC)   | SIM (SIM)              |
| DeviceInfo (DVI)         | Software (SWR)         |
| EventLog (EVL)           | WifiClient (WIFIC)     |
| Firmware (FWR)           |                        |


### FlexContainer Specializations

ACME CSE supports all FlexContainerSpecializations of [oneM2M TS-0023](https://specifications.onem2m.org/ts-0023){target=_new}.



### Protocols Bindings

The following Protocol Bindings are supported:

| Protocol Binding | Supported | Remark                                                                                                                                        |
|:-----------------|:---------:|:----------------------------------------------------------------------------------------------------------------------------------------------|
| http             |  &check;  | incl. TLS (https) and CORS support. *basic* and *bearer* authentication. <br/>Experimental: Using PATCH to replace missing DELETE in http/1.0 |
| coap             |  &cross;  |                                                                                                                                               |
| mqtt             |  &check;  | incl. mqtts                                                                                                                                   |
| WebSocket        |  &check;  | incl. TLS (wss) support                                                                                                                       |

The supported bindings can be used together, and combined and mixed in any way.


### Serialization Types
The following serialization types are supported:

| Serialization Type | Supported | Remark                                                                                                         |
|:-------------------|:---------:|:---------------------------------------------------------------------------------------------------------------|
| JSON               |  &check;  | In addition to normal JSON syntax, C-style comments ("//...", "#..." and "/\* ... \*/") are supported as well. |
| CBOR               |  &check;  |                                                                                                                |
| XML                |  &cross;  |                                                                                                                |

The supported serializations can be used together, e.g. between different or even with the same entity.


### Result Content Types

The following result contents are implemented for standard oneM2M requests and discovery:

| Discovery Type                         | RCN |
|:---------------------------------------|:---:|
| nothing                                | 0   |
| attributes                             | 1   |
| hierarchical address                   | 2   |
| hierarchical address + attributes      | 3   |
| attributes + child-resources           | 4   |
| attributes + child-resource-references | 5   |
| child-resource-references              | 6   |
| original-resource                      | 7   |
| child-resources                        | 8   |
| modified attributes                    | 9   |
| semantic content                       | 10  |
| discovery result references            | 11  |


### oneM2M Service Functions

The following oneM2M service functions are supported:

| Functionality                 | Supported | Remark                                                                                                                                     |
|:------------------------------|:---------:|:-------------------------------------------------------------------------------------------------------------------------------------------|
| AE registration               |  &check;  |                                                                                                                                            |
| Blocking requests             |  &check;  |                                                                                                                                            |
| Delayed request execution     |  &check;  | Through the *Operation Execution Timestamp* request attribute.                                                                             |
| Discovery                     |  &check;  |                                                                                                                                            |
| Geo-query                     |  &check;  |                                                                                                                                            |
| Location                      |  &check;  | Only *device based, and no *network based* location policies are supported.                                                                |
| Long polling                  |  &check;  | Long polling for request unreachable AEs and CSEs through &lt;pollingChannel>.                                                             |
| Non-blocking requests         |  &check;  | Non-blocking synchronous and asynchronous, and flex-blocking, incl. *Result Persistence*.                                                  |
| Notifications                 |  &check;  | E.g. for subscriptions and non-blocking requests.                                                                                          |
| Partial Retrieve              |  &check;  | Support for partial retrieve of individual resource attributes.                                                                            |
| Remote CSE registration       |  &check;  |                                                                                                                                            |
| Request expiration            |  &check;  | The *Request Expiration Timestamp* request attribute                                                                                       |
| Request forwarding            |  &check;  | Forwarding requests from one CSE to another.                                                                                               |
| Request parameter validations |  &check;  |                                                                                                                                            |
| Resource addressing           |  &check;  | *CSE-Relative*, *SP-Relative* and *Absolute* as well as hybrid addressing are supported.                                                   |
| Resource announcements        |  &check;  | Under the CSEBaseAnnc resource (R4 feature). Bi-directional update sync.                                                                   |
| Resource expiration           |  &check;  |                                                                                                                                            |
| Resource validations          |  &check;  |                                                                                                                                            |
| Result expiration             |  &check;  | The *Result Expiration Timestamp* request attribute. Result timeouts for non-blocking requests depend on the resource expiration interval. |
| Semantics                     |  &check;  | Basic support for semantic descriptors and semantic queries and discovery.                                                                 |
| Standard oneM2M requests      |  &check;  | CREATE, RETRIEVE, UPDATE, DELETE, NOTIFY                                                                                                   |
| Subscriptions                 |  &check;  | Incl. batch notification, and resource type and attribute filtering.                                                                       |
| Time Synchronization          |  &check;  |                                                                                                                                            |
| TimeSeries data handling      |  &check;  | Incl. missing data detection, monitoring and notifications.                                                                                |


###  Notification Event Types

The following notification event types for Subscriptions are supported:

| Notification Event Types | Supported |
|:-------------------------|:---------:|
| resourceUpdate           |  &check;  |
| resourceUpdate           |  &check;  |
| createDirectChild        |  &check;  |
| deleteDirectChild        |  &check;  |
| retrieveCNTNoChild       |  &cross;  |
| triggerReceivedForAE     |  &cross;  |
| blockingUpdate           |  &check;  |
| missingData              |  &check;  |



## Additional CSE Runtime Features

<a name="runtime"></a>
### Runtime Environments
The ACME CSE runs at least on the following runtime environments:

| Runtime Environment | Remark                                                                                |
|:--------------------|:--------------------------------------------------------------------------------------|
| Generic Linux       | Including [Raspberry Pi OS (32bit)](../howtos/RaspberryPi.md) on Raspberry Pi 3 and 4. |
| Mac OS              | Intel and Apple silicon.                                                              |
| MS Windows          |                                                                                       |
| Jupyter Notebooks   | ACME CSE can be run headless inside a Jupyter Notebook.                               |

| Functionality         | Remark                                                                                                                       |
|:----------------------|:-----------------------------------------------------------------------------------------------------------------------------|
| HTTP CORS             | Support for *Cross-Origin Resource Sharing* to support http(s) redirects.                                                    |
| HTTP Authorization    | Basic support for *basic* and *bearer* (token) authorization.                                                                |
| HTTP WSGI             | Support for the Python *Web Server Gateway Interface* to improve integration with a reverse proxy or API gateway, ie. Nginx. |
| Text Console          | Control and manage the CSE, inspect resources, run scripts in a text console.                                                |
| Test UI               | Text-based UI to inspect resources and requests, configurations, stats, and more                                             |
| Testing: Upper Tester | Basic support for the Upper Tester protocol defined in TS-0019, and additional command execution support.                    |
| Request Recording     | Record requests to and from the CSE to learn and debug requests over Mca and Mcc.                                            |
| Script Interpreter    | Lisp-based scripting support to extent functionalities, implement simple AEs, prototypes, test, ...                          |
| Web UI                |                                                                                                                              |


### Database Bindings

The following database bindings are supported:

| Database Binding  | Remark                               |
|:------------------|:-------------------------------------|
| PostgreSQL        |                                      |
| TinyDB in-memory  | Fast and simple in-memory database.  |
| TinyDB file-based | Fast and simple file-based database. |



### Experimental CSE Features
These features are prove-of-concept implementations of new and currently discussed oneM2M features. They are not yet part of the oneM2M standard.

| Functionality                            | Remark                                                                                     |
|:-----------------------------------------|:-------------------------------------------------------------------------------------------|
| Enhanced CSR functionality               | Support of new *eventEvaluationMode* to react in missing events                            |
| Subscription References                  | Support for subscription references for resource instead of direct subscriptions.          |
| Advanced Queries                         | Experimental implementation of a new query language to support enhanced query capabilities |
| Simplified Time Synchronization          | Experimental implementation of a simplified time synchronization mechanism.                |
| Support for DELETE requests for http/1.0 | Using PATCH requests to emulate DELETE requests for http/1.0 clients.                      |

