[← README](../README.md) 

# Operation

[Remote CSE Registration](#remote_cse)  
[Resource Announcements](#resource_annc)  
[AE Registration](#ae_registration)  
[Running with MQTT Support](#mqtt)  
[URL Mappings](#url_mappings)  
[Resource Tree and Deployment Infrastructure Diagram](#diagrams)  
[Upper Tester Support](#upper_tester)  


<a name="remote_cse"></a>
## Remote CSE Registration

When a CSE is configured as an MN-CSE of ASN-CSE it can register to a remote CSE, respectively an IN-CSE and MN-CSE can receive connection requests from those CSE types. A &lt;remoteCSE> resource is created in case of a successful registration. A CSE checks regularly the connection to other remote CSEs and removes the *remoteCSE* if the connection could not been established.

Announced resources and transit requests are supported by the CSE. 

You must configure the details of the remote CSE in the configuration file.


<a name="resource_annc"></a>
## Resource Announcements

When a resource is announced to a remote CSE then access is automatically granted when the announced resource's parent is the CSR of the original resource's hosting CSE.


<a name="ae_registration"></a>
## AE Registration

Whenever a new &lt;AE> registers itself with the CSE (using the originators *C* or *S*) then a new originator for that &lt;AE> is created. This originator is the custodian (owner) of that resource and can freely send requests to the &lt;AE> resource.


<a name="mqtt"></a>
## Running with MQTT Support

ACME supports Mca and Mcc communication via MQTT. This binding must be enabled in the configuration file under *\[client.mqtt].enable* (see also [Configuration](Configuration.md#client_mqtt)). 

ACME does not bring an own MQTT broker. Instead any MQTT broker that supports at least MQTT version 3.1.x can be used. This can be either be an own operated or a public broker installation (see, for example, [https://test.mosquitto.org](https://test.mosquitto.org)). The connection details need to be configured in the "[client.mqtt]" section as well.


<a name="url_mappings"></a>
## URL Mappings

As a convenience to access resources on a CSE and to let requests look more like "normal" REST request you can define mappings. The format is a path that maps to another path and arguments. When issued a request to one of those mapped paths the http server issues a redirect to the other path.

For example, the path */access/v1/devices* can be mapped to */cse-mn?ty=14&fu=1&fo=2&rcn=8* to easily retrieve all nodes from the CSE.

See the [configuration](Configuration.md) for more examples.


<a name="diagrams"></a>
## Resource Tree and Deployment Infrastructure Diagram

The CSE can generate a diagram with an overview about the hosted resource tree and the current deployment infrastructure of remote CSEs.
This is available by sending a GET request as follows:

```bash
$ curl localhost:8080/__structure__
```

This returns a PlantUML diagram script:

![](images/structure.png)

This feature must be enabled in the configuration file under *\[server.http].enableStructureEndpoint* (see also [Configuration](Configuration.md#server_http)). 

**ATTENTION**: Enabling this feature might reveal sensitive data. It should be disabled if not used.

When enabled the http server creates an additional endpoint */\_\_structure__*. A GET request to that endpoint returns a diagram description in [PlantUML](https://plantuml.com) format that can be transformed in images with various tools (for example, with the online editor on the PlantUML website). An optional argument *lvl=&lt;int>* can be provided to the URL to limit the size of the resource tree in the diagram.

A similar text representation of the resource tree can be retrieved from the endpoint */\_\_structure__/text* .

```bash
$ curl localhost:8080/__structure__/text

cse-in -> m2m:cb (csi=/id-in) | ri=id-in
├── acpCreateACPs -> m2m:acp | ri=acpCreateACPs
└── CAdmin -> m2m:ae | ri=CAdmin
``` 


<a name="upper_tester"></a>
## Upper Tester Support

The CSE has limited support for the *Upper Tester* (UT) test protocol. This protocol is used to trigger a System Under 
Test (SUT) to perform certain oneM2M operations and other actions. See oneM2M's TS-0019, *Abstract Test Suite and Implementation Information for Test* specification for further details.

To support this feature an additional endpoint *\_\_UT\_\_* is available under the HTTP server's root. It can be enabled by setting the configuration *[http].enenableUpperTesterEndpoint* in the configuration file to True. See also [enableRemoteConfiguration](Configuration.md#server_http). 

**ATTENTION: Only use this feature in a controlled environment. Enabling it may lead to a total loss of data because several internal functions and resources are exposed or can be managed without added security.**

### Supported Functions

The *Upper Tester* endpoint currently only supports a limited set of the functionality specified in TS-0019. 
The following sections present an overview.

#### Header X-M2M-UTCMD : Run CSE Commands
The **X-M2M-UTCMD** http header field is used to run a command by the CSE itself. The ACME CSE implements these commands 
as [scripts](ACMEScript.md) that have the meta tag [@uppertester](ACMEScript-metatags.md#uppertester) set.

The following commands are available by default, but other can be added. Some of these scripts are used to reconfigure the CSE
when running test cases.

| UT Functionality               | Description                                                                                             |
|--------------------------------|---------------------------------------------------------------------------------------------------------|
| reset                          | Resets the CSE to its initial state. No other function or operation present in the request is executed. |
| status                         | Returns the CSE running status in the response header field *X-M2M-UTRSP*.                              |
| disableShortRequestExpiration  | For running [test cases](Development.md#test_cases): Disables short request expiration.                 |
| disableShortResourceExpiration | For running [test cases](Development.md#test_cases): Disables short resource expiration.                |
| enableShortRequestExpiration   | For running [test cases](Development.md#test_cases): Enables short request expiration.                  |
| enableShortResourceExpiration  | For running [test cases](Development.md#test_cases): Enables short resource expiration.                 |


#### Header X-M2M-UTRSP : Return CSE Command Result

In case a command returns a result then this is available in the header field **X-M2M-UTRSP** of the HTTP response.

### Examples

#### Reset the CSE

This example initiates a reset of the CSE.  
The successful execution is indicated by the Response Status Code header *X-M2M-RSC: 2000* 

```http
$ http POST localhost:8080/__ut__ X-M2M-UTCMD:reset

HTTP/1.1 200 OK
Content-Length: 0
Content-Type: text/plain; charset=utf-8
Server: ACME 0.10.0-dev
X-M2M-RSC: 2000
``` 

#### CSE Get Status

This example requests the CSE status. It is returned in the *X-M2M-UTRSP* header.

```http
$ http POST localhost:8080/__ut__ X-M2M-UTCMD:status

HTTP/1.1 200 OK
Content-Length: 0
Content-Type: text/plain; charset=utf-8
Server: ACME 0.10.0-dev
X-M2M-RSC: 2000
X-M2M-UTRSP: RUNNING
``` 


[← README](../README.md) 
