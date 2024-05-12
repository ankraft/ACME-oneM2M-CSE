# Upper Tester Support

The CSE has limited support for the *Upper Tester* (UT) test protocol. This protocol is used to trigger a System Under 
Test (SUT), ie. a CSE, to perform certain oneM2M operations and other actions. See oneM2M's [TS-0019 "Abstract Test Suite and Implementation eXtra Information for Test"](https://specifications.onem2m.org/ts-0019){target=_new} specification for further details.

To support this feature an additional endpoint `__UT__` is available under the HTTP server's root path. It can be enabled by setting the configuration [`[http].enenableUpperTesterEndpoint`](../setup/Configuration-http.md#general-settings) in the configuration file to `True`.

!!! Warning
	Only use this feature in a controlled environment. Enabling it may lead to a total loss of data because several internal functions and resources are exposed or can be managed without added security.

## Supported Functions

The *Upper Tester* endpoint currently only supports a limited set of the functionality specified in [TS-0019](https://specifications.onem2m.org/ts-0019){target=_new}, but offers additional functionality, such as sending commands with arguments and receiving return values. 

The following sections present an overview.


### HTTP Header X-M2M-UTCMD : Run CSE Commands

The `X-M2M-UTCMD` http header field is used to run a command internally by the CSE. The ACME CSE implements these commands 
as [scripts](../development/ACMEScript.md) that have the meta tag [@uppertester](../development/ACMEScript-metatags.md#uppertester) set.

The following commands are available by default, but other can be added. Some of these commands are used to reconfigure the CSE
when running test cases.

| UT Functionality               | Description                                                                                             |
|--------------------------------|---------------------------------------------------------------------------------------------------------|
| reset                          | Resets the CSE to its initial state. No other function or operation present in the request is executed. |
| status                         | Returns the CSE running status in the response header field `X-M2M-UTRSP`.                              |
| disableShortRequestExpiration  | For running [test cases](../development/UnitTests.md): Disables short request expiration.               |
| disableShortResourceExpiration | For running [test cases](../development/UnitTests.md): Disables short resource expiration.              |
| enableShortRequestExpiration   | For running [test cases](../development/UnitTests.md): Enables short request expiration.                |
| enableShortResourceExpiration  | For running [test cases](../development/UnitTests.md): Enables short resource expiration.               |


### Header X-M2M-UTRSP : Return CSE Command Result

In case a command returns a result then it is available in the header field `X-M2M-UTRSP` of the HTTP response to the Uper Tester's request.


## Examples

### Resetting the CSE

This example initiates a reset of the CSE.  
The successful execution is indicated by the Response Status Code header *X-M2M-RSC: 2000* 

```http title="Resetting the CSE"
$ curl -X POST -H "X-M2M-UTCMD:Reset" http://localhost:8080/__ut__
...
< HTTP/1.1 200 OK
< Server: Werkzeug/3.0.2 Python/3.11.7
< Date: Sun, 05 May 2024 11:09:33 GMT
< Server: ACME 2024.DEV
< X-M2M-RSC: 2000
< X-M2M-UTRSP: false
< Content-Type: text/plain; charset=utf-8
< Content-Length: 0
< Connection: close
...
``` 

### Get the CSE Status

This example requests the CSE status. It is returned in the `X-M2M-UTRSP` header.

```http title="Get the CSE Status"
$ curl -v -X POST -H "X-M2M-UTCMD:Status" http://localhost:8080/__ut__
...
< HTTP/1.1 200 OK
< Server: Werkzeug/3.0.2 Python/3.11.7
< Date: Sun, 05 May 2024 11:02:47 GMT
< Server: ACME 2024.04
< X-M2M-RSC: 2000
< X-M2M-UTRSP: RUNNING
< Content-Type: text/plain; charset=utf-8
< Content-Length: 0
< Connection: close
...
``` 
