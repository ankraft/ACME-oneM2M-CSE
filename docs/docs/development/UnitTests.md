# Unit Tests

Almost all aspects of the ACME CSE implementation are covered by unit tests based on the Python [unittest](https://docs.python.org/3/library/unittest.html){target=_new} framework. The files for the individual test suites and the runner application reside in the [project's *tests*](https://github.com/ankraft/ACME-oneM2M-CSE/tree/master/tests){target=_new} directory.


## Configuration

The actual configuration of the test suite is done in the file [config.py](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/tests/config.py){target=_new}. You may change these for your individual set-up. At the top of the configuartion is a configuration setting for the request protocol that should be used. Currently, *http*, *https*, *ws*, *wss*, and *mqtt* are supported. 

!!! Note
	All CSE's involved in the tests must use the same protocol type.

Further configuration settings include the originatores for admin access, self-registration, and remote CSE settings when running tests for CSE-2-CSE (*Mcc*) communications, 

One can also provide OAuth2 settings in case the CSE under test is behind an OAuth2 gateway.

### Enable Remote Configuration (Upper Tester)

The CSE under test must be started with the **remote configuration interface** enabled. During test runs the test suite will temporarily change some of the CSE's delays (e.g. the check for resource expirations) in order to speed up the test. You can either do this by changing the configuration [http.enableUpperTesterEndpoint](../setup/Configuration-http.md#general-settings) in the CSE's [configuration file](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/tests/config.py){target=_new}.

!!! Note
	This ability to remotly re-configure the CSE during runtime is a particular function of the  *ACME* CSE and might not be available with other CSE implementations.

### Internal Settings

Each test suite imports the file [init.py](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/tests/init.pys){target=_new} that contains various helper functions. Also, some low-level configurations, such as time-outs etc, that are used by the test suites can be adjusted here. 


## Test Suites

For each aspect of the CSE there is one test suite file that can be run independently or in the course of an overall test. For example, running the test suite for AE tests would look like this:

```text title="Example Test Suite Run"
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
```

The individual test suites are located in the [tests](https://github.com/ankraft/ACME-oneM2M-CSE/tree/master/tests){target=_new} directory. Their names start with *test...* and are grouped by the aspect of the CSE they are testing.


## Test Runner

### Overview

The `--help` or `-h` command line argument provides a usage overview for the *runTest.py* script.

```text title="Test Runner Overview"
$ python runTests.py -h

usage: runTests.py [-h] [--all] [--load-only] [--verbose-requests] [--disable-teardown]
                   [--exclude-tests EXCLUDETESTS [EXCLUDETESTS ...]] [--run-teardown] [--run-count NUMBEROFRUNS]
                   [--run-tests TESTCASENAME [TESTCASENAME ...]] [--show-skipped] [--no-failfast]
                   [--list-tests | --list-tests-sorted]
                   [TESTSUITE ...]

positional arguments:
  TESTSUITE             specific test suites to run. Run all test suites if empty

options:
  -h, --help            show this help message and exit
  --all                 run all test suites (including load tests)
  --load-only           run only load test suites
  --verbose-requests, -v
                        show verbose requests, responses and notifications output
  --disable-teardown, -notd
                        disable the tear-down / cleanup procedure at the end of a test suite
  --exclude-tests EXCLUDETESTS [EXCLUDETESTS ...], -et EXCLUDETESTS [EXCLUDETESTS ...]
                        exclude the specified test cases from running
  --run-teardown, -runtd
                        run the specified test cases' tear-down functions and exit
  --run-count NUMBEROFRUNS
                        run each test suite n times (default: 1)
  --run-tests TESTCASENAME [TESTCASENAME ...], -run TESTCASENAME [TESTCASENAME ...]
                        run only the specified test cases from the set of test suites
  --show-skipped        show skipped test cases in summary
  --no-failfast         continue running test cases after a failure
  --list-tests, -ls     list the test cases of the specified test suites in the order they are defined and exit
  --list-tests-sorted, -lss
                        alphabetical sorted list the test cases of the specified test suites and exit

```

### Running the Tests

The Python script [runTests.py](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/tests/runTests.py){target=_new} can be used to run all test suites. It looks for all Python scripts starting with *test...* and runs them in alphabetical order. At the end of a full test run it also provides a summary of the test results, including time spend for requests, as a process etc.

Usually, the test suites are run only once, but one can specify the *--run-count* option to execute tests multiple times.

```text title="Example Test Run"
$ python3 runTests.py

...

                                                       [ACME] - Test Results
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃                     ┃       ┃         ┃        ┃            Times             ┃   Exec Time per   ┃   Proc Time per   ┃          ┃
┃ Test Suite          ┃ Count ┃ Skipped ┃ Errors ┃     Exec | Sleep | Proc      ┃  Test | Request   ┃  Test | Request   ┃ Requests ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ testACP             │    45 │       0 │      0 │   0.2232 |   0.00 |   0.0786 │  0.0050 |  0.0030 │  0.0017 |  0.0011 │       74 │
│ testACTR            │    39 │       0 │      0 │  12.6369 |  12.00 |   0.1909 │  0.3240 |  0.1600 │  0.0049 |  0.0024 │       79 │
│ testAE              │    26 │       0 │      0 │   0.1724 |   0.00 |   0.0634 │  0.0066 |  0.0049 │  0.0024 |  0.0018 │       35 │
│ testAddressing      │    10 │       0 │      0 │   0.0543 |   0.00 |   0.0185 │  0.0054 |  0.0034 │  0.0019 |  0.0012 │       16 │
│ testCIN             │    17 │       0 │      0 │   0.0920 |   0.00 |   0.0307 │  0.0054 |  0.0033 │  0.0018 |  0.0011 │       28 │
│ testCNT             │    22 │       0 │      0 │   0.1021 |   0.00 |   0.0345 │  0.0046 |  0.0038 │  0.0016 |  0.0013 │       27 │
│ testCNT_CIN         │    30 │       0 │      0 │   4.9574 |   4.50 |   0.1998 │  0.1652 |  0.0496 │  0.0067 |  0.0020 │      100 │
│ testCRS             │    93 │       0 │      0 │ 185.6518 | 183.10 |   0.7760 │  1.9963 |  0.7672 │  0.0083 |  0.0032 │      242 │
│ testCSE             │     8 │       0 │      0 │   0.0810 |   0.00 |   0.0375 │  0.0101 |  0.0101 │  0.0047 |  0.0047 │        8 │
│ testDEPR            │    18 │       0 │      0 │  10.6709 |  10.00 |   0.2192 │  0.5928 |  0.1270 │  0.0122 |  0.0026 │       84 │
│ testDiscovery       │    58 │       0 │      0 │   0.3509 |   0.00 |   0.1089 │  0.0061 |  0.0038 │  0.0019 |  0.0012 │       92 │
│ testExpiration      │     9 │       0 │      0 │  30.4013 |  30.00 |   0.1313 │  3.3779 |  0.6609 │  0.0146 |  0.0029 │       46 │
│ testFCNT            │    24 │       0 │      0 │   0.1461 |   0.00 |   0.0507 │  0.0061 |  0.0052 │  0.0021 |  0.0018 │       28 │
│ testFCNT_FCI        │    11 │       0 │      0 │   0.0740 |   0.00 |   0.0236 │  0.0067 |  0.0031 │  0.0021 |  0.0010 │       24 │
│ testGRP             │    28 │       0 │      0 │   0.1827 |   0.00 |   0.0541 │  0.0065 |  0.0033 │  0.0019 |  0.0010 │       55 │
│ testLCP             │    13 │       0 │      0 │   8.2762 |   6.00 |   0.1372 │  0.6366 |  0.3448 │  0.0106 |  0.0057 │       24 │
│ testLocation        │    73 │       0 │      0 │   0.5622 |   0.00 |   0.1768 │  0.0077 |  0.0031 │  0.0024 |  0.0010 │      182 │
│ testMgmtObj         │    89 │       0 │      0 │   0.3589 |   0.00 |   0.1246 │  0.0040 |  0.0039 │  0.0014 |  0.0014 │       91 │
│ testMisc            │    27 │       0 │      0 │   5.3855 |   5.00 |   0.2005 │  0.1995 |  0.1346 │  0.0074 |  0.0050 │       40 │
│ testNOD             │    13 │       0 │      0 │   0.1831 |   0.00 |   0.0719 │  0.0141 |  0.0057 │  0.0055 |  0.0022 │       32 │
│ testPCH             │    13 │       0 │      0 │   0.0660 |   0.00 |   0.0233 │  0.0051 |  0.0035 │  0.0018 |  0.0012 │       19 │
│ testPCH_PCU         │    11 │       0 │      0 │  30.4732 |  15.00 |   0.2164 │  2.7703 |  0.7432 │  0.0197 |  0.0053 │       41 │
│ testPRMR_STTE       │     3 │       0 │      0 │   0.0467 |   0.00 |   0.0181 │  0.0156 |  0.0093 │  0.0060 |  0.0036 │        5 │
│ testREQ             │    25 │       0 │      0 │  46.4165 |  45.50 |   0.3721 │  1.8567 |  1.1321 │  0.0149 |  0.0091 │       41 │
│ testRemote          │     7 │       0 │      0 │   0.1056 |   0.00 |   0.0389 │  0.0151 |  0.0075 │  0.0056 |  0.0028 │       14 │
│ testRemote_Annc     │    42 │       0 │      0 │   1.2401 |   0.00 |   0.1910 │  0.0295 |  0.0188 │  0.0045 |  0.0029 │       66 │
│ testRemote_GRP      │     2 │       0 │      0 │   0.0833 |   0.00 |   0.0155 │  0.0416 |  0.0167 │  0.0077 |  0.0031 │        5 │
│ testRemote_Requests │     3 │       0 │      0 │   0.1789 |   0.00 |   0.0288 │  0.0596 |  0.0224 │  0.0096 |  0.0036 │        8 │
│ testRequests        │    15 │       0 │      0 │  16.3307 |   6.00 |   0.1273 │  1.0887 |  0.9073 │  0.0085 |  0.0071 │       18 │
│ testSCH             │    22 │       0 │      0 │  14.6350 |  12.00 |   0.2509 │  0.6652 |  0.2091 │  0.0114 |  0.0036 │       70 │
│ testSMD             │    14 │       0 │      0 │   0.1091 |   0.00 |   0.0406 │  0.0078 |  0.0061 │  0.0029 |  0.0023 │       18 │
│ testSUB             │    94 │       0 │      0 │  29.9202 |  27.50 |   0.8239 │  0.3183 |  0.1847 │  0.0088 |  0.0051 │      162 │
│ testTS              │    34 │       0 │      0 │   0.2189 |   0.00 |   0.0767 │  0.0064 |  0.0055 │  0.0023 |  0.0019 │       40 │
│ testTSB             │     7 │       0 │      0 │   6.1816 |   6.00 |   0.1255 │  0.8831 |  0.4755 │  0.0179 |  0.0097 │       13 │
│ testTS_TSI          │    29 │       0 │      0 │ 121.9209 | 120.47 |   0.4444 │  4.2042 |  1.1185 │  0.0153 |  0.0041 │      109 │
│ testUpperTester     │     6 │       0 │      0 │   0.7547 |   0.00 |   0.0241 │  0.1258 |  0.3774 │  0.0040 |  0.0120 │        2 │
├─────────────────────┼───────┼─────────┼────────┼──────────────────────────────┼───────────────────┼───────────────────┼──────────┤
│ Totals              │   980 │       0 │      0 │ 529.2668 | 483.07 |   5.5679 │  0.5401 |  0.2731 │  0.0057 |  0.0029 │     1938 │
└─────────────────────┴───────┴─────────┴────────┴──────────────────────────────┴───────────────────┴───────────────────┴──────────┘
```

With `--verbose-requests` the each request and response is printed as well. This can be helpful to debug problems with the system under test, the network, and other aspects.

### Running Individual Test Suites

One can  specify which test suites to run like this:

```bash title="Run Specific Test Suites"
$ python3 runTests.py testACP testCin
```

The *runTest.py* script by default will run all test suites, **except** scripts that run load tests. To include those one need to specify the `--load-include` command line argument.


### Running Individual Test Cases

It is also possible to run individual test cases from test suites. This is done by optionally specify the test suites and then with the `--run-tests` or `-run`option a list of test case names to run:

```bash title="Run Single Test Case"
$ python runTests.py testSUB --run-tests test_createCNTforEXC
```

The test cases can be specified in any order, and may appear more than once.

!!! Note
	Most unit tests in a test suite depend on each other (created resources, subscriptions, etc). Just running a single test case may fail. 

The most interesting use of this functionionality is to run a whole test suite together with the `--disable-teardown` option up to the point of a failure, and then run the failed test case again:

```bash title="Run Single Test Case Without Tear-Down"
$ python runTests.py testSUB --disable-teardown
...
$ python runTests.py testSUB  --disable-teardown --run-tests test_createCNTforEXC
```

This disables the clean-up of the CSE after the test suite has run, so that the resources created by the test suite are still present in the CSE. This way one can investigate the state of the CSE after the test suite has run.

To list the available test cases one can use the `--list-tests` (list in the order the test cases have been defined in the test suite) and the `--list-tests-sorted` (list alphabetically) options.


### Exluding Test Cases

One can exclude test cases from running by using the `--exclude-tests` or `-et` option. This option takes a list of test case names to exclude from the test run.

The following example runs all test cases in the *testSUB* test suite except the *test_createCNTforEXC* test case:

```bash title="Exclude Test Cases"
$ python runTests.py testSUB --exclude-tests test_createCNTforEXC 
```


### Tear-down and Clean-up

Each test suite may set-up resources in the CSE that are used during the tests. Usually, those resources should be removed from the CSE at the end of each test suite, but under certain circumstances (like a crash or forceful interruption of a test run) those resources may still be present in the CSE and must be removed manually (or by a reset-restart of the CSE), or by running the test suit with the `--run-teardown` option. The later runs only the tear-down  functions for the specified test suites and then exits.

However, sometimes it would be useful to keep the resources created by the tests for further investigations. In this case specifying the `--disable-teardown` option can help. It disables the execution of the tear-down functions after successful or unsuccessful execution.

## Dependencies

Some test cases in each test suite build on each other (such as adding a resource that is updated by further test cases). This means that the order of the test cases in each test suite is important. Individual test suites, however, can work independent from each other.

Some test suites (for example *testRemote*) need in addition to a running IN- or MN-CSE another MN-CSE that registers to the "main" CSE (the system-under-test) in order to run registration and announcement tests.

