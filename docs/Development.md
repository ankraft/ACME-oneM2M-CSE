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
Each test suite imports the file [init.py](../tests/init.py) that contains various helper functions used by the test suites. 

The actual configuration of the test suite is done in the file [config.py](../tests/config.py). You may change these for your individual set-up. In this file there is also a configuration setting for the request protocol that should be used. Currently, *http* and *https* are supported. Please note, that all CSE's involved in the test runs must use the same protocol type.

One can also provide OAuth2 settings in case the CSE under test is behind an OAuth2 gateway.

#### Enable Remote Configuration

The CSE under test must be started with the remote configuration interface enabled. During test runs the test suite will temporarily change some of the CSE's delays (e.g. the check for resource expirations) in order to speed up the test. You can either do this by changing the configuation [enableRemoteConfiguration](Configuration.md#server_http) in the [configuration file](../acme.ini.default), or by providing the [--remote-configuration](Running.md) command line argument during startup.

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
	┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
	┃ Test Suites     ┃ Test Count ┃ Skipped ┃ Errors ┃ Exec Time  ┃ Process Time ┃ Time / Test ┃
	┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
	│ testACP         │ 38         │ 0       │ 0      │ 2.038394   │ 0.1328       │ 0.0536      │
	│ testAE          │ 22         │ 0       │ 0      │ 1.485972   │ 0.0831       │ 0.0675      │
	│ testAddressing  │ 6          │ 0       │ 0      │ 0.513926   │ 0.0334       │ 0.0857      │
	│ testCIN         │ 15         │ 0       │ 0      │ 1.474164   │ 0.0683       │ 0.0983      │
	│ testCNT         │ 20         │ 0       │ 0      │ 1.260655   │ 0.0725       │ 0.0630      │
	│ testCNT_CIN     │ 21         │ 0       │ 0      │ 7.242389   │ 0.2142       │ 0.3449      │
	│ testCSE         │ 7          │ 0       │ 0      │ 0.261999   │ 0.0271       │ 0.0374      │
	│ testDiscovery   │ 51         │ 0       │ 0      │ 11.553983  │ 0.2574       │ 0.2265      │
	│ testExpiration  │ 8          │ 0       │ 0      │ 33.305452  │ 0.1756       │ 4.1632      │
	│ testFCNT        │ 22         │ 0       │ 0      │ 1.703758   │ 0.0873       │ 0.0774      │
	│ testFCNT_FCI    │ 10         │ 0       │ 0      │ 1.440845   │ 0.0692       │ 0.1441      │
	│ testGRP         │ 19         │ 0       │ 0      │ 3.354424   │ 0.1156       │ 0.1765      │
	│ testMgmtObj     │ 56         │ 0       │ 0      │ 2.426752   │ 0.1805       │ 0.0433      │
	│ testMisc        │ 13         │ 0       │ 0      │ 0.333524   │ 0.0430       │ 0.0257      │
	│ testNOD         │ 11         │ 0       │ 0      │ 0.885265   │ 0.0680       │ 0.0805      │
	│ testPCH         │ 9          │ 0       │ 0      │ 0.559523   │ 0.0355       │ 0.0622      │
	│ testREQ         │ 22         │ 0       │ 0      │ 34.600313  │ 0.2010       │ 1.5727      │
	│ testRemote      │ 5          │ 0       │ 0      │ 0.155780   │ 0.0214       │ 0.0312      │
	│ testRemote_Annc │ 28         │ 0       │ 0      │ 3.529524   │ 0.1642       │ 0.1261      │
	│ testSUB         │ 59         │ 0       │ 0      │ 17.055104  │ 0.3334       │ 0.2891      │
	│ testTS          │ 19         │ 0       │ 0      │ 1.546678   │ 0.0602       │ 0.0814      │
	│ testTS_TSI      │ 33         │ 0       │ 0      │ 110.092743 │ 0.4238       │ 3.3361      │
	├─────────────────┼────────────┼─────────┼────────┼────────────┼──────────────┼─────────────┤
	│ Totals          │ 494        │ 0       │ 0      │ 236.8454   │ 2.8916       │ 0.4794      │
	└─────────────────┴────────────┴─────────┴────────┴────────────┴──────────────┴─────────────┘

The ```runTest.py``` script by default will run all test cases, except scripts that runs load tests. To include those one need to specify the ```--load-include``` command line argument.

One can also specify which test cases to run like this:

	$ python3 runTests.py testACP testCin

The ```--help``` command line argument provides a usage overview for the ```runTest.py``` script.


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
When sending a PUT request to the endpoint followed by the name of a configuration macro and with a new value in the body of the request then a new value is assigned to that configuration setting.  Example

	Request: POST /__config__/cse.checkExpirationsInterval
	Body: 2

A successful operation is answered with an *ack* response, an error or failure to process is answered with a *nak* response.

Only the following configuration settings can updated by this method yet:

| Macro name                   | Description                                                                                                        |
|:-----------------------------|:-------------------------------------------------------------------------------------------------------------------|
| cse.checkExpirationsInterval | Assigning a new value to this configuration setting will also force a restart CSE's *RegistrationManager* module.  |
| cse.req.minet                | Minimum time for &lt;request> resource expiration.                                                                 |
| cse.req.maxnet               | Maximum time for &lt;request> resource expiration.                                                                 |
| cse.checkTimeSeriesInterval  | Assigning a new value to this configuration setting will also force a restart CSE's *TimeSeriesManager* component. |


<a name="mypy"></a>
## MyPy Static Type Checker

The CSE code is statically type-checked with [mypy](http://mypy-lang.org). 

Just execute the ```mypy``` command in the project's root directory. It will read its configuration from the configuration file [mypy.ini](../mypy.ini).

[← README](../README.md) 