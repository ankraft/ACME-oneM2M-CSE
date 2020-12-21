[← README](README.md) 


# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - xxxx-xx-xx

### Added
- [CSE] Added *--http-address* and *--network-interface* command line arguments.
- [CSE] Added configuration to exclude certain attributes in CSR creations and updates.
- [NOTIFICATIONS] Added support for handling CBOR serialization and other binary formats.
- [WEB] Added dark mode (for supported browsers).

### Changed
- [WEB] The web UI can now also be used as a stand-alone application to connect to third-party CSEs.
- [CSE] The filter query for *ty*, *cty*, and *lbl* can now be construct with + operator (e.g. ty=3+4) instead of specifying those filter elements twice.
- [CSE] Changed the importing of attribute policies to a JSON based format.
- [CSE] Supported release version can now be configured via the config file.
- [TESTS] The behavior whether a failed test skips the remaining tests in a test suite can now be configured.
- [MISC] Allow ```# single-line comments``` in JSON
- [MISC] Default configuration for file logging is now *False* (to better support Raspberry Pi and similar systems with flash card file systems).

### Fixed
- [CSE] CSEBase.srt attribute now also returns the announced attributes.


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
- [WEB] Added deletion of resources in the webb UI via right-click menu.
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
- [WEB] Browser request to "/"" will now redirect to the webui's URL.
- [WEB] REST UI will not refresh anymore when automatic refresh is on.
- [ALL] Various fixes and improvements.


## [0.1.0] - 2020-02-09
- First release

[← README](README.md) 
