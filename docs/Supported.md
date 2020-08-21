[← README](../README.md) 

# Supported Resource Types and Functionalities

## oneM2M Specification Conformance

The CSE implementation successfully passes most of the oneM2M release 1 test cases (353 out of 361).


## Resources

The CSE supports the following oneM2M resource types:


| Resource Type                 | Supported | Limitations                                                                                                                     |
|:------------------------------|:---------:|:--------------------------------------------------------------------------------------------------------------------------------|
| CSEBase (CB)                  |  &check;  |                                                                                                                                 |
| Remote CSE (CSR)              |  &check;  | Announced resources are yet not supported. Transit request, though, to resources on the remote CSE are supported.               |
| Access Control Policy (ACP)   |  &check;  |                                                                                                                                 |
| Application Entity (AE)       |  &check;  |                                                                                                                                 |
| Container (CNT)               |  &check;  |                                                                                                                                 |
| Content Instance (CIN)        |  &check;  |                                                                                                                                 |
| Group (GRP)                   |  &check;  | The support includes requests via the *fopt* (fan-out-point) virtual resource.                                                  |
| Subscription (SUB)            |  &check;  | Notifications via http to a direct url or an AE's Point-of-Access (POA) are supported as well.                                  |
| Node (NOD)                    |  &check;  |                                                                                                                                 |
| Management Objects            |  &check;  | See also the list of supported [management objects](#mgmtobjs).                                                                 |
| FlexContainer Specializations |  &check;  | Any specialization is supported and validated. See [Importing Attribute Policies](Importing.md#attributes) for further details. |
| FlexContainerInstance         |  &check;  | Experimental. This is an implementation of the draft FlexContainerInstance specification.                                       |
| Polling Channel               |  &cross;  |                                                                                                                                 |

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


## Functionalities

| Functionality                 | Supported | Remark                                                                |
|:------------------------------|:---------:|:----------------------------------------------------------------------|
| Resource addressing           |  &check;  | *CSE-Relative*, *SP-Relative* and *Absolute* addressing is supported. |
| Standard oneM2M requests      |  &check;  | CREATE, RETRIEVE, UPDATE, DELETE                                      |
| Discovery                     |  &check;  |                                                                       |
| Notifications                 |  &check;  | E.g. for subscriptions                                                | 
| AE registration               |  &check;  |                                                                       |
| Remote CSE registration       |  &check;  |                                                                       |
| Resource expiration           |  &cross;  |                                                                       |
| Resource announcements        |  &check;  | Only one hop is supported at the moment.                              |
| Resource validations          |  &check;  |                                                                       |
| Request parameter validations |  &check;  |                                                                       |
| Transit requests              |  &check;  | Forwarding requests from one CSE to another.                          |
| Blocking requests             |  &check;  |                                                                       |
| Non-blocking requests         |  &cross;  |                                                                       |


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

## Protocols Bindings
The following Protocol Bindings are supported:

| Protocol Binding | Supported | Remark                            |
|:-----------------|:---------:|:----------------------------------|
| http             | &check;   | https is currently not supported. |
| coap             | &cross;   |                                   |
| mqtt             | &cross;   |                                   |

## Serialization Types
The following serialization types are supported:

| Serialization Type | Supported | Remark                                                                                               |
|:-------------------|:---------:|:-----------------------------------------------------------------------------------------------------|
| XML                |  &cross;  |                                                                                                      |
| JSON               |  &check;  | In addition to normal JSON syntax, C-style comments ("//..." and "/* ... */") are supported as well. |
| CBOR               |  &cross;  |                                                                                                      |



# Limitations
- **This is by no means a fully compliant, secure or stable CSE! Don't use it in production.**
- This CSE is intended for educational purposes. The underlying database system is not optimized in any way for high-volume, high-availability, or high-reliability.
- No support for https yet.
- Security: None. Please contact me if you have suggestions to improve this.
- Unsupported resource types are just stored, but no check or functionality is provided for those resources. The same is true for unknown resource attributes.

[← README](../README.md) 
