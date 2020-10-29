[← README](../README.md) 
# Development

[The Messy Details](#messy_details)  
[Resource Class Hierarchy](#classes)  
[Integration Into Other Applications](#integration)  
[Developing Nodes and AEs](#developing_nodes_aes)  
[Running Test Cases](#test_cases)  
[HTTP Server Remote Configuration Interface](#config_interface)  
[MyPy Static Type Checker](#mypy)  


<a name="messy_details"></a>
## The Messy Details

### Components

![](images/cse_uml.png)

<a name="classes"></a>
### Resource Class Hierarchy

![](images/resources_uml.png)

<a name="integration"></a>
## Integration Into Other Applications

It is possible to integrate the CSE into other applications, e.g. a Jupyter Notebook. In this case you would possibly like to provide startup arguments, for example the path of the configuration file or the logging level, directly instead of getting them from *argparse*.

You might want to get the example from the starter file [acme.py](acme.py) where you could replace the line:

```python
CSE.startup(parseArgs())
```

with a call to the CSE's *startup()* function:

```python
CSE.startup(None, configfile=defaultConfigFile, loglevel='error')
```

Please note that in case you provide the arguments directly the first argument needs to be `None`. 

The names of the *argparse* variables can be used here, and you may provide all or only some of the arguments. Please note that you need to keep or copy the `import` and `sys.path` statements at the top of that file.


<a name="developing_nodes_aes"></a>
## Developing Nodes and AEs

You can develop your own components that technically run inside the CSE themselves by following the pattern of those two components:

- Implement a class with either *AEBase* or *NodeBase* as a base class. This will create an &lt;AE> or &lt;node> resource for you.
-  Implement a worker method and start it in the *\_\_init\_\_()* method. This method is called regularly in the background. This worker method can implement the main functionality of the &lt;AE> or &lt;node>.
-  Implement a *shutdown()* method that is called when the CSE shuts down.
-  Add your new component to the following methods in [acme/CSE.py](../acme/CSE.py):
	-  *startApps()*: starting your component.
	-  *stopApps()*: shutting down your component.

There are more helper methods provided by the common *AppBase* and *AEBase* base classes, e.g. to send requests to the CSE via Mca, store AE data persistently etc.

<a name="test_cases"></a>
## Running Test Cases

Various aspects of the ACME implementation are covered by unit tests based on the Python [unittest](https://docs.python.org/3/library/unittest.html) framework. The files for test cases and the runner application reside in the [tests](../tests) directory.


### Configuration & Running
Each test suite imports the file [init.py](../tests/init.py) that contains various configuration values used by the test suites. You may change these for your individual set-up.

In the file [init.py](../tests/init.py) there is also a configuration setting for the request protocol that should be used. Currently, *http* and *https* are supported. Please note, that all CSE's involved in the test runs must use the same protocol type.

The CSE under test should be started with the remote configuration interface enabled. During test runs the test suite will temporarily change some of the CSE's delays (e.g. the check for resource expirations) in order to speed up the test. You can either do this by changing the configuation [enableRemoteConfiguration](Configuration.md#server_http) in the [configuration file](../acme.ini.default), or by providing the [--remote-configuration](Running.md) command line argument during startup.

### Test Suites

For each aspect of the CSE there is one test suite file that can be run independently or in the course of an overall test. For example, running the test suite for AE tests would look like this:

	$ python3 testAE.py
	test_createAE (__main__.TestAE) ... ok
	test_createAEUnderAE (__main__.TestAE) ... ok
	test_retrieveAE (__main__.TestAE) ... ok
	test_retrieveAEWithWrongOriginator (__main__.TestAE) ... ok
	test_attributesAE (__main__.TestAE) ... ok
	test_updateAELbl (__main__.TestAE) ... ok
	test_updateAETy (__main__.TestAE) ... ok
	test_updateAEPi (__main__.TestAE) ... ok
	test_updateAEUnknownAttribute (__main__.TestAE) ... ok
	test_retrieveAEACP (__main__.TestAE) ... ok
	test_deleteAEByUnknownOriginator (__main__.TestAE) ... ok
	test_deleteAEByAssignedOriginator (__main__.TestAE) ... ok
	----------------------------------------------------------------------
	Ran 12 tests in 0.116s
	OK

### Test Runner

The Python script [runTests.py](../tests/runTests.py) can be used to run all test suites. It looks for all Python scripts starting with *test..." and runs them in alphabetical order. At the end of a full test run it also provides a nice summary of the test results:

	$ python3 runTests.py

	...

	Successfully executed tests: 19

	                                   [ACME] - Test Results
	┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
	┃ Test Suites     ┃ Test Count ┃ Skipped ┃ Errors ┃ Exec Time ┃ Process Time ┃ Time Ratio ┃
	┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
	│ testACP         │ 9          │ 0       │ 0      │ 0.0811    │ 0.0394       │ 0.4856     │
	│ testAE          │ 12         │ 0       │ 0      │ 0.1142    │ 0.0501       │ 0.4386     │
	│ testAddressing  │ 6          │ 0       │ 0      │ 0.0796    │ 0.0378       │ 0.4747     │
	│ testCIN         │ 6          │ 0       │ 0      │ 0.0753    │ 0.0304       │ 0.4040     │
	│ testCNT         │ 17         │ 0       │ 0      │ 0.1517    │ 0.0673       │ 0.4434     │
	│ testCNT_CIN     │ 5          │ 0       │ 0      │ 0.1375    │ 0.0521       │ 0.3788     │
	│ testCSE         │ 5          │ 0       │ 0      │ 0.0293    │ 0.0155       │ 0.5293     │
	│ testDiscovery   │ 42         │ 0       │ 0      │ 1.7608    │ 0.2052       │ 0.1165     │
	│ testFCNT        │ 14         │ 0       │ 0      │ 0.1418    │ 0.0554       │ 0.3907     │
	│ testFCNT_FCI    │ 6          │ 0       │ 0      │ 0.1009    │ 0.0434       │ 0.4301     │
	│ testGRP         │ 14         │ 0       │ 0      │ 0.2804    │ 0.1135       │ 0.4047     │
	│ testMgmtObj     │ 52         │ 0       │ 0      │ 1.3827    │ 0.1785       │ 0.1291     │
	│ testNOD         │ 11         │ 0       │ 0      │ 0.1507    │ 0.0702       │ 0.4657     │
	│ testRemote      │ 2          │ 0       │ 0      │ 0.0221    │ 0.0114       │ 0.5172     │
	│ testRemote_Annc │ 23         │ 0       │ 0      │ 0.4381    │ 0.1325       │ 0.3025     │
	│ testSUB         │ 19         │ 0       │ 0      │ 1.3818    │ 0.0926       │ 0.0670     │
	├─────────────────┼────────────┼─────────┼────────┼───────────┼──────────────┼────────────┤
	│ Totals          │ 243        │ 0       │ 0      │ 6.3459    │ 1.2125       │ 0.1911     │
	└─────────────────┴────────────┴─────────┴────────┴───────────┴──────────────┴────────────┘

### Dependencies
Each test suite may set-up resources in the CSE that are used during the tests. Usually, those resources should be removed from the CSE at the end of each test suite, but under certain circumstances (like a crash or forceful interruption of the test suite's run) those resources may still be present in the CSE and must be removed manually (or by a reset-restart of the CSE).

Some test cases in each test suite build on each other (such as adding a resource that is updated by further test cases). This means that the order of the test cases in each test suite is important. The test suites, however, can work independent from each other.

Some test suites (for example *testRemote*) need in addition to a running IN- or MN-CSE another MN-CSE that registers to the "main" CSE in order to run registration and announcement tests.

<a name="config_interface"></a>
## HTTP Server Remote Configuration Interface

The http server can register a remote configuration interface (see [enableRemoteConfiguration](Configuration.md#server_http)). This "\_\_config__" endpoint is available under the http server's root. 

**ATTENTION: Enabling this feature exposes configuration values, IDs and passwords, and is a security risk.**

This feature is mainly used for testing and debugging.

### GET Configuration
When sending a GET request to the endpoint then the full configuration is returned. Example:

	Request: GET /__config__


When sending a GET request to the endpoint followed by the name of a configuration macro then the current value of that configuration setting is returned. Example:

	Request: GET /__config__/cse.maxExpirationDelta
 
### PUT Configuration
When sending a PUT request to the endpoint followed by the name of a configuration macro and with a new value in the body of the request then a new value is assigned to that configuation setting.  Example

	Request: POST /__config__/cse.checkExpirationsInterval
	Body: 2

A successful operation is answeredd with an *ack* response, an error or failure to process is answered with a *nak* response.

Only the following configration settings can updated by this method yet:

| Macro name                   | Description                                                                                                   |
|:-----------------------------|:--------------------------------------------------------------------------------------------------------------|
| cse.checkExpirationsInterval | Assigning a new value to this configuration setting will also force a restart CSE's *Registration* component. |
| cse.req.minet                | Minimum time for &lt;request> resource expiration.                                                            |
| cse.req.maxnet               | Maximum time for &lt;request> resource expiration.                                                            |


<a name="mypy"></a>
## MyPy Static Type Checker

The CSE code is statically type-checked with [mypy](http://mypy-lang.org). 

Just execute the ```mypy``` command in the project's root directory. It will read its configuration from the configuration file [mypy.ini](../mypy.ini).

[← README](../README.md) 