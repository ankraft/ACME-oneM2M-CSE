[← README](../README.md) 

# Supported Resource Types and Functionalities

## oneM2M Specification Conformance

The CSE implementation successfully passes most of the oneM2M Release 1 test cases (353 out of 361), and all relevant test cases from Release 2, 3 and 4.


## Release Versions

The ACME CSE supports oneM2M release 2a, 3, and 4 for the supported resource types and functionalities listed below. 

## CSE Types

The ACME CSE supports the following CSE types:

| CSE Type | Supported |
|:---------|:---------:|
| IN       |  &check;  |
| MN       |  &check;  |
| ASN      |  &check;  |


## Resources

The ACME CSE supports the following oneM2M resource types:

| Resource Type                   | Supported | Remarks & Limitations                                                                                                                                                                                             |
|:--------------------------------|:---------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Access Control Policy (ACP)     |  &check;  |                                                                                                                                                                                                                   |
| Application Entity (AE)         |  &check;  |                                                                                                                                                                                                                   |
| Container (CNT)                 |  &check;  |                                                                                                                                                                                                                   |
| ContentInstance (CIN)           |  &check;  |                                                                                                                                                                                                                   |
| CSEBase (CB)                    |  &check;  |                                                                                                                                                                                                                   |
| FlexContainer & Specializations |  &check;  | Any specialization is supported and validated. See [Importing Attribute Policies](Importing.md#attributes) for further details.<br />Supported specializations include: TS-0023 R4, GenericInterworking, AllJoyn. |
| FlexContainerInstance           |  &check;  | Experimental. This is an implementation of the draft FlexContainerInstance specification.                                                                                                                         |
| Group (GRP)                     |  &check;  | The support includes requests via the *fopt* (fanOutPoint) virtual resource. Groups may contain remote resources.                                                                                                 |
| Management Objects              |  &check;  | See also the list of supported [management objects](#mgmtobjs).                                                                                                                                                   |
| Node (NOD)                      |  &check;  |                                                                                                                                                                                                                   |
| Polling Channel (PCH)           |  &check;  | Support for Request and Notification long-polling via the *pcu* (pollingChannelURI) virtual resource. *requestAggregation* functionality is supported, too.                                                       |
| Remote CSE (CSR)                |  &check;  | Announced resources are  supported. Transit request to resources on registered CSE's are supported.                                                                                                               |
| Request (REQ)                   |  &check;  | Support for non-blocking requests.                                                                                                                                                                                |
| Subscription (SUB)              |  &check;  | Notifications via http(s) (direct url or an AE's Point-of-Access (POA)). BatchNotifications, attributes.                                                                                                          |
| TimeSeries (TS)                 |  &check;  | Including missing data notifications.                                                                                                                                                                             |
| TimeSeriesInstance (TSI)        |  &check;  | *dataGenerationTime* attribute only supports absolute timestamps.                                                                                                                                                 |
| TimeSyncBeacon (TSB)            |  &check;  | Experimental. Implemented functionality might change according to specification changes.                                                                                                                          |

<a name="mgmtobjs"></a>

### Management Objects

The following table presents the supported management object specifications.

| Management Objects       |
|--------------------------|
| Firmware (FWR)           |
| Software (SWR)           |
| Memory (MEM)             |
| AreaNwkInfo (ANI)        |
| AreaNwkDeviceInfo (ANDI) |
| Battery (BAT)            |
| DeviceInfo (DVI)         |
| DeviceCapability (DVC)   |
| Reboot (REB)             |
| EventLog (EVL)           |
| myCertFileCred (NYCFC)   |

## oneM2M Service Features

| Functionality                 | Supported | Remark                                                                                    |
|:------------------------------|:---------:|:------------------------------------------------------------------------------------------|
| Resource addressing           |  &check;  | *CSE-Relative*, *SP-Relative* and *Absolute* as well as hybrid addressing are supported.  |
| Standard oneM2M requests      |  &check;  | CREATE, RETRIEVE, UPDATE, DELETE, NOTIFY                                                  |
| Discovery                     |  &check;  |                                                                                           |
| Subscriptions                 |  &check;  | Incl. batch notification, and resource type and attribute filtering.                      |
| Notifications                 |  &check;  | E.g. for subscriptions and non-blocking requests.                                         |
| AE registration               |  &check;  |                                                                                           |
| Remote CSE registration       |  &check;  |                                                                                           |
| Resource expiration           |  &check;  |                                                                                           |
| Resource announcements        |  &check;  | Under the CSEBaseAnnc resource (R4 feature). Bi-directional update sync.                  |
| Resource validations          |  &check;  |                                                                                           |
| Request parameter validations |  &check;  |                                                                                           |
| Transit requests              |  &check;  | Forwarding requests from one CSE to another.                                              |
| Blocking requests             |  &check;  |                                                                                           |
| Non-blocking requests         |  &check;  | Non-blocking synchronous and asynchronous, and flex-blocking, incl. *Result Persistence*. |
| TimeSeries data handling      |  &check;  | Incl. missing data detection, monitoring and notifications.                               |
| Long polling                  |  &check;  | Long polling for request unreachable AEs and CSEs through &lt;pollingChannel>.            |
| Request expiration            |  &check;  | Through the *Request Expiration Timestamp* request attribute                              |
| Delayed request execution     |  &check;  | Through the *Operation Execution Timestamp* request attribute.                            |
| Testing: Upper Tester         |  &check;  | Basic support for the Upper Tester protocol defined in TS-0019.                           |


## Result Content Types
The following result contents are implemented for standard oneM2M requests & discovery:

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
| discovery result references            | 11  |


## Notification Event Types for Subscriptions

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


## Protocols Bindings
The following Protocol Bindings are supported:

| Protocol Binding | Supported | Remark                                                                          |
|:-----------------|:---------:|:--------------------------------------------------------------------------------|
| http             |  &check;  | incl https.<br/>Experimental: Using PATCH to replace missing DELETE in http/1.0 |
| coap             |  &cross;  |                                                                                 |
| mqtt             |  &check;  | incl. mqtts                                                                     |
| WebSocket        |  &cross;  |                                                                                 |

The supported bindings can be used together, and combined and mixed in any way.

## Serialization Types
The following serialization types are supported:

| Serialization Type | Supported | Remark                                                                                                       |
|:-------------------|:---------:|:-------------------------------------------------------------------------------------------------------------|
| JSON               |  &check;  | In addition to normal JSON syntax, C-style comments ("//...", "#..." and "/\* ... \*/") are supported as well. |
| CBOR               |  &check;  |                                                                                                              |
| XML                |  &cross;  |                      

The supported serializations can be used together, e.g. between different or even the same entity.


<a name="limitations"></a>
# Limitations
- The intention of this CSE implemention is to support education and learning, experiments, and demonstrations, but not a production environment. **Use it at your own risk.**
- The underlying communication stacks and database system are not optimized in any way for high-volume, high-availability, or high-reliability.
- Unsupported resource types are just stored, but no validations or functionality are provided for those resources. 

[← README](../README.md) 
