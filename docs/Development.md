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

									[ACME] - Test Results
	┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
	┃ Test Suites     ┃ Test Count ┃ Skipped ┃ Errors ┃ Exec Time ┃ Process Time ┃ Time / Test ┃
	┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
	│ testACP         │ 24         │ 0       │ 0      │ 0.254555  │ 0.0883       │ 0.0106      │
	│ testAE          │ 20         │ 0       │ 0      │ 0.264547  │ 0.0795       │ 0.0132      │
	│ testAddressing  │ 6          │ 0       │ 0      │ 0.109203  │ 0.0385       │ 0.0182      │
	│ testCIN         │ 6          │ 0       │ 0      │ 0.112126  │ 0.0310       │ 0.0187      │
	│ testCNT         │ 17         │ 0       │ 0      │ 0.285828  │ 0.0714       │ 0.0168      │
	│ testCNT_CIN     │ 5          │ 0       │ 0      │ 0.207681  │ 0.0530       │ 0.0415      │
	│ testCSE         │ 6          │ 0       │ 0      │ 0.034428  │ 0.0180       │ 0.0057      │
	│ testDiscovery   │ 50         │ 0       │ 0      │ 2.394407  │ 0.2640       │ 0.0479      │
	│ testExpiration  │ 8          │ 0       │ 0      │ 30.936923 │ 0.1602       │ 3.8671      │
	│ testFCNT        │ 20         │ 0       │ 0      │ 0.265955  │ 0.0801       │ 0.0133      │
	│ testFCNT_FCI    │ 6          │ 0       │ 0      │ 0.188589  │ 0.0463       │ 0.0314      │
	│ testGRP         │ 17         │ 0       │ 0      │ 0.653116  │ 0.1336       │ 0.0384      │
	│ testMgmtObj     │ 56         │ 0       │ 0      │ 0.521094  │ 0.1958       │ 0.0093      │
	│ testMisc        │ 3          │ 0       │ 0      │ 0.016969  │ 0.0094       │ 0.0057      │
	│ testNOD         │ 11         │ 0       │ 0      │ 0.287916  │ 0.0766       │ 0.0262      │
	│ testREQ         │ 17         │ 0       │ 0      │ 26.000516 │ 0.1090       │ 1.5294      │
	│ testRemote      │ 2          │ 0       │ 0      │ 0.040013  │ 0.0121       │ 0.0200      │
	│ testRemote_Annc │ 28         │ 0       │ 0      │ 2.969211  │ 0.1714       │ 0.1060      │
	│ testSUB         │ 48         │ 0       │ 0      │ 9.867077  │ 0.3084       │ 0.2056      │
	├─────────────────┼────────────┼─────────┼────────┼───────────┼──────────────┼─────────────┤
	│ Totals          │ 350        │ 0       │ 0      │ 75.4322   │ 1.9680       │ 0.2155      │
	└─────────────────┴────────────┴─────────┴────────┴───────────┴──────────────┴─────────────┘

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