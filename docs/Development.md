[← README](../README.md) 
# Development

[The Messy Details](#messy_details)  
[Resource Class Hierarchy](#classes)  
[Integration Into Other Applications](#integration)  
[Running Test Cases](#test_cases)  
[MyPy Static Type Checker](#mypy)  
[Debug Mode](#debug-mode)  


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


<a name="test_cases"></a>
## Running Test Cases

Various aspects of the ACME implementation are covered by unit tests based on the Python [unittest](https://docs.python.org/3/library/unittest.html) framework. The files for test cases and the runner application reside in the [tests](../tests) directory.


### Configuration & Running
Each test suite imports the file [init.py](../tests/init.py) that contains various helper functions used by the test suites. 

The actual configuration of the test suite is done in the file [config.py](../tests/config.py). You may change these for your individual set-up. In this file there is also a configuration setting for the request protocol that should be used. Currently, *http*, *https*, and *mqtt* are supported. Please note, that all CSE's involved in the test runs must use the same protocol type.

One can also provide OAuth2 settings in case the CSE under test is behind an OAuth2 gateway.

#### Enable Remote Configuration

The CSE under test must be started with the **remote configuration interface** enabled. During test runs the test suite will temporarily change some of the CSE's delays (e.g. the check for resource expirations) in order to speed up the test. You can either do this by changing the configuration [enableRemoteConfiguration](Configuration.md#server_http) in the [configuration file](../acme.ini.default), or by providing the [--remote-configuration](Running.md) command line argument during startup.

### Unit Tests

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
	┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
	┃                     ┃       ┃         ┃        ┃            Times             ┃   Exec Time per   ┃   Proc Time per   ┃          ┃
	┃ Test Suite          ┃ Count ┃ Skipped ┃ Errors ┃     Exec | Sleep | Proc      ┃  Test | Request   ┃  Test | Request   ┃ Requests ┃
	┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
	│ testACP             │    42 │       0 │      0 │   0.5873 |   0.00 |   0.1181 │  0.0140 |  0.0109 │  0.0028 |  0.0022 │       54 │
	│ testACTR            │     3 │       0 │      0 │   0.0478 |   0.00 |   0.0127 │  0.0159 |  0.0080 │  0.0042 |  0.0021 │        6 │
	│ testAE              │    25 │       0 │      0 │   0.4417 |   0.00 |   0.0735 │  0.0177 |  0.0134 │  0.0029 |  0.0022 │       33 │
	│ testAddressing      │     8 │       0 │      0 │   0.1895 |   0.00 |   0.0308 │  0.0237 |  0.0135 │  0.0039 |  0.0022 │       14 │
	│ testCIN             │    17 │       0 │      0 │   0.3655 |   0.00 |   0.0585 │  0.0215 |  0.0131 │  0.0034 |  0.0021 │       28 │
	│ testCNT             │    21 │       0 │      0 │   0.4119 |   0.00 |   0.0706 │  0.0196 |  0.0158 │  0.0034 |  0.0027 │       26 │
	│ testCNT_CIN         │    26 │       0 │      0 │   4.9397 |   4.00 |   0.2228 │  0.1900 |  0.0610 │  0.0086 |  0.0028 │       81 │
	│ testCRS             │    62 │       0 │      0 │  84.0746 |  81.80 |   0.5280 │  1.3560 |  0.6369 │  0.0085 |  0.0040 │      132 │
	│ testCSE             │     8 │       0 │      0 │   0.1862 |   0.00 |   0.0503 │  0.0233 |  0.0233 │  0.0063 |  0.0063 │        8 │
	│ testDiscovery       │    54 │       0 │      0 │   1.0766 |   0.00 |   0.1789 │  0.0199 |  0.0135 │  0.0033 |  0.0022 │       80 │
	│ testExpiration      │     8 │       0 │      0 │  30.7233 |  30.00 |   0.1932 │  3.8404 |  0.7145 │  0.0242 |  0.0045 │       43 │
	│ testFCNT            │    23 │       0 │      0 │   0.4121 |   0.00 |   0.0804 │  0.0179 |  0.0153 │  0.0035 |  0.0030 │       27 │
	│ testFCNT_FCI        │    11 │       0 │      0 │   0.2775 |   0.00 |   0.0425 │  0.0252 |  0.0116 │  0.0039 |  0.0018 │       24 │
	│ testGRP             │    28 │       0 │      0 │   0.7579 |   0.00 |   0.1099 │  0.0271 |  0.0138 │  0.0039 |  0.0020 │       55 │
	│ testMgmtObj         │    80 │       0 │      0 │   1.0088 |   0.00 |   0.1998 │  0.0126 |  0.0123 │  0.0025 |  0.0024 │       82 │
	│ testMisc            │    18 │       0 │      0 │   4.4119 |   4.00 |   0.1615 │  0.2451 |  0.1765 │  0.0090 |  0.0065 │       25 │
	│ testNOD             │    12 │       0 │      0 │   0.3239 |   0.00 |   0.0770 │  0.0270 |  0.0130 │  0.0064 |  0.0031 │       25 │
	│ testPCH             │    13 │       0 │      0 │   0.1699 |   0.00 |   0.0395 │  0.0131 |  0.0089 │  0.0030 |  0.0021 │       19 │
	│ testPCH_PCU         │    11 │       0 │      0 │  30.8078 |  15.00 |   0.3497 │  2.8007 |  0.7514 │  0.0318 |  0.0085 │       41 │
	│ testREQ             │    25 │       0 │      0 │  46.5237 |  45.00 |   0.5464 │  1.8609 |  1.1347 │  0.0219 |  0.0133 │       41 │
	│ testRemote          │     7 │       0 │      0 │   0.2121 |   0.00 |   0.0533 │  0.0303 |  0.0151 │  0.0076 |  0.0038 │       14 │
	│ testRemote_Annc     │    37 │       0 │      0 │   0.7482 |   0.00 |   0.1244 │  0.0202 |  0.0125 │  0.0034 |  0.0021 │       60 │
	│ testRemote_GRP      │     2 │       0 │      0 │   0.0659 |   0.00 |   0.0113 │  0.0330 |  0.0132 │  0.0056 |  0.0023 │        5 │
	│ testRemote_Requests │     2 │       0 │      0 │   0.0677 |   0.00 |   0.0119 │  0.0339 |  0.0135 │  0.0060 |  0.0024 │        5 │
	│ testRequests        │    12 │       0 │      0 │  10.3716 |   0.00 |   0.1257 │  0.8643 |  0.7408 │  0.0105 |  0.0090 │       14 │
	│ testSMD             │    14 │       0 │      0 │   0.2395 |   0.00 |   0.0587 │  0.0171 |  0.0133 │  0.0042 |  0.0033 │       18 │
	│ testSUB             │    81 │       0 │      0 │  16.9685 |  15.00 |   0.4738 │  0.2095 |  0.1266 │  0.0058 |  0.0035 │      134 │
	│ testTS              │    33 │       0 │      0 │   0.5149 |   0.00 |   0.1064 │  0.0156 |  0.0135 │  0.0032 |  0.0028 │       38 │
	│ testTSB             │     7 │       0 │      0 │   6.2509 |   6.00 |   0.1507 │  0.8930 |  0.4808 │  0.0215 |  0.0116 │       13 │
	│ testTS_TSI          │    29 │       0 │      0 │ 121.4479 | 119.41 |   0.5758 │  4.1879 |  1.1142 │  0.0199 |  0.0053 │      109 │
	│ testUpperTester     │     6 │       0 │      0 │   0.3926 |   0.00 |   0.0318 │  0.0654 |  0.1963 │  0.0053 |  0.0159 │        2 │
	├─────────────────────┼───────┼─────────┼────────┼──────────────────────────────┼───────────────────┼───────────────────┼──────────┤
	│ Totals              │   725 │       0 │      0 │ 365.0405 | 320.21 |   4.8910 │  0.5035 |  0.2906 │  0.0067 |  0.0039 │     1256 │
	└─────────────────────┴───────┴─────────┴────────┴──────────────────────────────┴───────────────────┴───────────────────┴──────────┘

The ```runTest.py``` script by default will run all test cases, except scripts that runs load tests. To include those one need to specify the ```--load-include``` command line argument.

One can also specify which test cases to run like this:

	$ python3 runTests.py testACP testCin

The ```--help``` command line argument provides a usage overview for the ```runTest.py``` script.


### Dependencies
Each test suite may set-up resources in the CSE that are used during the tests. Usually, those resources should be removed from the CSE at the end of each test suite, but under certain circumstances (like a crash or forceful interruption of the test suite's run) those resources may still be present in the CSE and must be removed manually (or by a reset-restart of the CSE).

Some test cases in each test suite build on each other (such as adding a resource that is updated by further test cases). This means that the order of the test cases in each test suite is important. The test suites, however, can work independent from each other.

Some test suites (for example *testRemote*) need in addition to a running IN- or MN-CSE another MN-CSE that registers to the "main" CSE in order to run registration and announcement tests.


<a name="mypy"></a>
## MyPy Static Type Checker

The CSE code is statically type-checked with [mypy](http://mypy-lang.org). 

Just execute the ```mypy``` command in the project's root directory. It will read its configuration from the configuration file [mypy.ini](../mypy.ini).


## Debug Mode

The CSE tries to catch errors and give helpful advice as much as possible during runtime.
However, there are circumstances when this could not done easily, e.g. during startup.

In order to provide additional information in these situations one can set the *ACME_DEBUG* environment (to any value):

	$ export ACME_DEBUG=1

[← README](../README.md) 