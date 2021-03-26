[← README](README.md) 


# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.7.3] - 2021-03-26

### Added
- [CSE] Added *cse.resource.cnt.enableLimits* configuration. 
- [CSE] Added "T" command to the console (display only sub-tree of the resource tree).
- [CSE] Improved startup error messages when running in headless mode.

### Changed
- [CSE] Default limits for &lt;container> are now disabled by default.
- [CSE] Limiting supported release versions to 2a, 3, and 4.
- [CSE] Changed spelling of configuration values "cse.statistics.writeIntervall" to "cse.statistics.writeInterval" and "app.statistics.intervall" to "app.statistics.interval".


## [0.7.2] - 2021-03-22

### Security
- [MISC] Bumped referenced library urllib3 from 1.26.2 to 1.26.3
- [MISC] Bumped referenced library jinja2 from 2.11.2 to 2.11.3


## [0.7.1] - 2021-03-09

### Fixed
- [CSE] Fixed crash when receiving no content in CREATE or UPDATE request.
- [CSE] Improved debug response when encountering a wrong type during validation.
- [CSE] Improved statistics output when running inside a Jupyter Notebook.


## [0.7.0] - 2021-03-06

### Added
- [CSE] Added *--http-address* and *--network-interface* command line arguments.
- [CSE] Added configuration to exclude certain attributes in CSR creations and updates.
- [CSE] Added support for CBOR serialization.
- [CSE] Added attribute policies for TS-0023 R4 ModuleClasses, Devices etc.
- [CSE] Added attribute policies for Generic Interworking and AllJoyn specialization.
- [CSE] Added diagram generation (in PlantUML format) of resource tree and deployment structure.
- [CSE] Added better checks for content serialization in AE.
- [CSE] Added command interface to the terminal console (for stopping the CSE, printing statistics, CSE registrations, the resource tree, etc).
- [CSE] Added support for *holder* attribute. Added access control behavior for *holder* and resource creator when an *acpi* attribute is specified for a resource, but doesn't have one.
- [CSE] Added support for Subscription's *expirationCounter*.
- [CSE] Added headless mode to better support docker.
- [NOTIFICATIONS] Added support for handling CBOR serialization and other binary formats to the notification server.
- [WEB] Added dark mode (for supported browsers).
- [TESTS] Added load tests that can be optionally executed. Also improved test runner: select on the command line which tests to run.

### Changed
- [WEB] The web UI can now also be used as a stand-alone application to connect to third-party CSEs.
- [CSE] The filter query for *ty*, *cty*, and *lbl* can now be construct with + operator (e.g. ty=3+4) instead of specifying those filter elements twice.
- [CSE] Changed the importing of attribute policies to a JSON based format.
- [CSE] Supported release version can now be configured via the config file.
- [CSE] Added checks for remote CSE's *csi* (does it exist? Does it begin with a /?)
- [CSE] Removed defaultACPI support. Now supporting correct behavior for *holder* attribute resp. resource creator.
- [CSE] Correctly implemented acpi updates. Also: acpi references are converted to CSE relative unstructured During CREATE and UPDATE.
- [CSE] Changed resourceType values for \<latest> and \<oldest> to the specified values.
- [CSE] Access control clean-up. No more extra ACPs for admin access, CSRs, AEs, REQs etc. The CSE now makes use of *creator* and *holder* access.
- [TESTS] The behavior whether a failed test skips the remaining tests in a test suite can now be configured.
- [TESTS] Improved documentation. Doc strings provide a bit more information about a currently running test.
- [TESTS] Tests now pass mypy checks.
- [MISC] Added: Allow ```# single-line comments``` in JSON as well.
- [MISC] Default configuration for file logging is now *False* (to better support Raspberry Pi and similar systems with flash card file systems).
- [MISC] Now passes ```mypy --strict``` checks.
- [DATABASE] Changed the postfix of data files to the CSE-ID.
- [HTTP] Server runs now in background.

### Fixed
- [CSE] *CSEBase.srt* attribute now also returns the announced attributes.
- [CSE] Improved shutdown behavior. Waiting for internal threads to finish.
- [CSE] When updating a subscription resource's *nu* attribute: Removed URI's don't cause a "deletion notification" anymore.
- [CSE] Improved *creator* attribute handling during CREATE.
- [CSE] Fixed wrong removal procedure when removing contentInstances from a container when either threshold was met.
- [CSE] Added missing checks for mandatory request parameters *RVI* and *RI*
- [SUB] Added missing validation for *nct* / *enc/net* combinations.
- [ACP] Added check that *pvs* is not empty during CREATE or UPDATE.
- [ACP] Added check that *acpi*, if present, is the only attribute in an UPDATE request.
- [TESTS] Fixed test framework checks for CSE connectivity and CSE reconfigurations for test runs.


## [0.6.0] - 2020-10-26

### Added
- [CSE] Improved resource expiration a lot.
- [CSE] Added support for *mia* attribute in CNT and FCNT.
- [CSE] Added support for synchronous and asynchronous non-blocking requests (as well as flex-blocking).
- [CSE] Added configuration to enable or disable regular liveliness checks of remote CSE connects (cse.registration.checkLiveliness).
- [REQ] Added support for &lt;request> resource type.
- [SUB] Added support for batchNotifications, latestNotify, eventNotificationCriteria/childResourceType, and eventNotificationCriteria/attribute in subscriptions.
- [HTTP] Added possibility to enable an API to get and set some configuration values remotely.

### Changed
- [CSE] Removed possibility to register unknown resources of an unknown resource type.

### Fixed
- [HTTP] Fixed wrong configuration settings for TLS certificates.
- [CSR] Fixed format of *csebase* attribute.


## [0.5.0] - 2020-09-17

### Added
- [CSE] Added Resource Announcements to remote CSEs.
- [CSE] Added support for 'm2m:dbg' throughout the CSE. This should provide better error reporting for clients.
- [CSE] Added configuration and command line argument to enable and disable validation of attributes and arguments.
- [CSE] Added configuration and command line argument to enable and disable statistics.
- [CSE] Added configuration to make CSE startup delay configurable.
- [CSE] Added import of attribute policies for &lt;flexContainer> specializations validation.
- [CSE] Added support for 'arp' request argument.
- [CSE] JSON in requests may now contain C-style comments ("// ..." and "/* ... */").
- [CSE] Added support for *myCertFileCred* ManagementObject.
- [SUB] Improved support for 'nct' in subscriptions.
- [TESTS] Added unit tests.
- [WEB] Added deletion of resources in the web UI via right-click menu.
- [HTTP] Added https support for the http server and for requests.
- [MISC] Added Python type hints throughout the source code.

### Changed
- [CSE] Reimplemented discovery, filter functions and rcn's.
- [MISC] Refactored most constants to enums.


## [0.4.0] - 2020-06-24

### Added
- [CSE] Added command line arguments --remote-cse, --no-remote-cse .
- [CSE] Improved remote CSE handling.
- [CSE] Improved and corrected remote CSE registration and retargeting requests.
- [CSE] Improved support for expiration handling, e.g. refreshing as well as removal of expired resources.
- [CSE] Added validation of resource attributes during CREATE and UPDATE.
- [CSE] Added support for request arguments validation.
- [CSE] The CSE now passes most of the oneM2M R1 test cases.
- [AE] Added AE Self-Registration.
- [IMPORTING] Added macro mechanism to use configuration settings in imported files.
- [WEB] Add displaying the path of the selected resource and many more small improvements.
- [WEB] Providing default originator.

### Fixed
- [CSE] Fixed crashes when using group resources.
- [CSE] Fixed and reworked resource address handling.
- [CSE] Corrected transit requests.
- [ACP] Fixed format of privileges and self-privileges.
- [NOTIFICATIONS] Corrected error handling.
- [ALL] Many, many small fixes and improvements.

### Changed
- [ACP] Created resources without a provided ACPI will now have the same ACPI of the parent.
- [DATABASE] Upgraded to TinyDB 4.x .
- [Logging] Now using the Rich module for improved terminal logging .
- [MISC] Restructured documentation.


## [0.3.0] - 2020-04-20

### Added
- [CSE] Discovery supports "attributes + children" return content.
- [CSE] Added command line argument --db-storage .
- [CSE] Added support for FlexContainerInstance.
- [CSE] Added command line arguments --apps / --no-apps to enable and disable internal applications. Also added entry in config file.
- [CSE] Added sorting of discovery results. Configurable.

### Fixed
- [CSE] Fixed discovery results: ignore latest, oldest, and fixed result format.

### Changed
- [CSE] Changed command line argument --reset-db to --db-reset .


## [0.2.1] - 2020-03-06

### Added
- [APPS] Added persistent storage support for AEs.

### Fixed
- [APPS] Fixed wrong originator handling for already registered AEs.


## [0.2.0] - 2020-03-02

### Added
- [CSE] Checking and setting "creator" attribute when creating new resources.
- [ACP] Always add "admin" originator to newly created ACPs (configurable).
- [ACP] Improved default ACP. Any new resource without ACP gets the default ACP assigned.
- [AE] Added proper AE registration. An ACP is automatically created for a new AE, and also removed when the corresponding AE is removed.
- [LOGGING] Added option to enable/disable logging to a log file (Logging:enableFileLogging). If disabled, log-messages are only written to the console.
- [LOGGING] Possibility to disable logging on the command line.
- [IMPORTING] Added default ACP. 
- [WEB] Added LOGO & favicon.

### Fixed
- [WEB] Browser request to "/"" will now redirect to the web-ui's URL.
- [WEB] REST UI will not refresh anymore when automatic refresh is on.
- [ALL] Various fixes and improvements.


## [0.1.0] - 2020-02-09
- First release

[← README](README.md) 
