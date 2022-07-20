[← README](README.md) 


# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.10.2] - 2022-07-20

### Added
- [CSE] Added debug mode to display hidden exceptions during start-up.

### Fixed
- [CSE] Fixed problems with missing *syslog* module under MS Windows.
- [CONSOLE] Fixed Return-key handling for MS Windows cmd terminal.


## [0.10.1] - 2022-05-30

### Fixed
- [CSE] Fixed crash when restarting &lt;timeSeries> monitoring.


## [0.10.0] - 2022-05-06

### Added
- [CSE] Added *--http-port* command line argument.
- [CSE] Added initial support for the Upper Tester protocol defined in TS-0019.
- [CSE] Added guided setup of a configuration file when the CSE is started without a config file.
- [CSE] Added bi-directional update of announced resources.
- [CSE] Added remote resources support for &lt;group>.
- [CSE] Added support for *dataGenerationTime* attribute for &lt;contentInstance> (R5 feature).
- [CSE] Added "acme://" URL scheme for notifications to run ACMEScript scripts.
- [CSE] Added always setting *Originating Timestamp* in requests and responses.
- [CSE] Added [logging].queueSize configuration to set the internal logging queue (or switch it off).
- [CSE] Added validation of &lt;flexContainer>'s *containerDefinition* attribute during CREATE requests.
- [CSE] Added check for correct Service Provider ID in absolute requests.
- [CSE] Added support for &lt;pollingChannel>'s *requestAggregation* attribute and functionality.
- [CSE] Added support for BLOCKING UPDATE notification event type.
- [CSE] Added a first support for the &lt;timeSyncBeacon> resource type.
- [WEB] Allow to open the WebUI of a registered CSE via the context menu.
- [CONSOLE] Added config for dark (default) and light theme for better readability on consoles with light background.
- [CONSOLE] Added graph plotting for &lt;contentInstance> resources that contain numerical values (also: continuous observation of a container).
- [SCRIPTS] Added scripting to the CSE.
- [SCRIPTS] A dedicated startup script is now executed during startup. This is mainly used to import the base resources and resource structure, and replaces the JSON resource imports.
- [SCRIPTS] Added executing scripts to the console
- [SCRIPTS] Added scripts tagged with "@uppertester" can be executed as upper tester commands.
- [SCRIPTS] Added scripts scheduling vie the "@at" meta tag.
- [SCRIPTS] Added possibility to run scripts on notifications, when using the "acme://" URL scheme.
- [HTTP] Added workaround for missing DELETE method in http/1.0 (by using PATCH instead).

### Changed
- [CSE] Adapted Announcements to latest R4 changes. 
- [CSE] Adapted TimeSeries to latest R4 changes. 
- [CSE] Changed the default release version to 4. Also, the supported and the actual release versions are now fully configurable (in the config file).
- [CSE] Changed name of *holder* attribute to *custodian* according to R4 spec change.
- [CSE] Transit requests will now be handled after the resolution for blocking/non-blocking was handled. Non-blocking happens in the first CSE that received the original request.
- [CSE] Improved feedback instructions when problems during startup are encountered, e.g. how to install missing packages.
- [CSE] Introduced a thread pool to reuse threads.
- [TESTS] Replaced CSE test cases' re-configurations with upper tester commands / script calls.
- [DATABASE] Optimizations when working with resource lists.

### Removed
- [HTTP] Removed the http server's configuration and reset endpoints. This functionality is now handled by the upper tester endpoint, commands and scripts.
- [CSE] Removed import of JSON resources from the init directory during startup. This functionality is now provided by a startup script. 

### Fixed
- [CSE] Improved check that IDs contain only unreserved characters.
- [CSE] Improved check for validating non-empty list attributes.
- [CSE] Improved error detection and handling for RCN=7 (original-resource).
- [CSE] Added missing "creator" attribute in notifications when the creator was set in the &lt;subscription>.
- [CSE] Improved support to recognize structured and unstructured resource IDs for verification notifications.
- [HTTP] HTTP requests will not be sent with a *Date* header field. Instead, the *Originating Timestamp* will be used.

### Experimental
- [CSE] Blocking RETRIEVE notification event type: A RETRIEVE is blocked and a notification is sent to a target to give it a change to update the original RETRIEVE's target resource.

## [0.9.1] - 2021-11-09

### Fixed
- [CSE] Added &lt;pollingChannel> to the list of supported resource types for the &lt;CSEBase>.
- [CSE] Removed *acpi* attribute definition from &lt;contentInstance> resource. Added more tests for inheriting ACPs.


## [0.9.0] - 2021-11-04

### Added
- [CSE] Added support for &lt;pollingChannel> and &lt;pollingChannelURI> for polling communication scenarios.
- [CSE] Added [logging].enableBindingsLogging configuration to enable/disable low-level transport bindings logging.
- [CSE] Added converting resource IDs to SP-relative when retargeting to different CSEs.
- [CSE] Added support for request expiration (*Request Expiration Timestamp*) and delayed request execution (*Operation Execution Timestamp*).
- [MQTT] Added MQTT binding support for Mca and Mcc communication.
- [CONSOLE] Added the possibility to toggle through the display modes with "^T" when displaying the resource tree continuously.
- [CONSOLE] Real-time update for the continuous tree (when creating, deleting, updating resources).
- [CONSOLE] Added [cse.console].confirmQuit configuration option. It is switched off by default.
- [DATABASE] Added validation of data base fil∑es during start-up.
- [DATABASE] Added backup of data base files during start-up.

### Changed
- [WEB] Moved the webUI to the acme module.
- [CSE] Improved attribute validation: checking empty lists.
- [CSE] Simplified initial configuration. First time users can now choose between three deployment configurations (IN, MN, ASN) to quickly set-up a CSE.
- [CSE] Improved fallback and debug message of missing Release Version Indicator attribute in requests.
- [CSE] Refactored project directory structure.
- [CSE] Refactored validation to improve attribute policies and validation handling and extension. Policies are now defined by a definition file and assigned to each resource type.
- [CSE] Refactored the handling of target URI's. They are now evaluated as late as possible. This may have impact on, for example, batch notifications and whenever the real target URL may change over time.
- [CSE] Changed rcn = modifiedAttributes to the improved definition in the spec: return only those modified attributes that where *not* in the original request, but were modified by the CSE as a result of the request.
- [CSE] Improved transit requests: serialization according to target's preferences.
- [CSE] Changed optionality of and originator assignment to CSR.csi according to TS-0004 spec change.
- [HTTP] Moved the security setting for http to the separate section *server.http.security*.
- [IMPORTING] Changed the file extension for &lt;flexContainer> attribute policies from ".ap" to ".fcp".
- [IMPORTING] Updated the &lt;flexContainer> attribute policies to the latest version of TS-0023.
- [Logging] Changed the internal handling of log messages. Output should be more immediate than before.
- [RUNTIME] Due to the restructuring of the project structure the CSE must now be started like this: ```python3 -m acme```


### Removed
- [CSE] Removed "cse.enableNotifications" configuration option. Notifications are now always enabled.
- [CSE] Removed "cse.enableTransitRequests" configuration option. Requests are now always forwarded.
- [CSE] Removed "cse.enableValidation" configuration option. Validation is now always performed.
- [CSE] Removed "cse.announcements.enable" configuration option. Resources can now always be announced.
- [APPS] Removed the example AEs from the CSE. This makes the CSE a bit smaller and also removes a big dependency to the non-portable psutils package. They will be available in a separate project in the future.
- [HTTP] Removed the *server.http.multithreaded* configuration option. The http server now always runs in multithread mode.

### Fixed
- [CSE] When the CSE is reset then the statistics are now reset as well.
- [WEB] Error/debug messages are now always shown.


## [0.8.1] - 2021-08-05

### Added
- [CONSOLE] Added [cse.console].confirmQuit configuration option. It is switched off by default.


## [0.8.0] - 2021-07-27

### Added
- [CSE] Added possibility to reset a running CSE (via the command console or http endpoint "/\_\_reset\_\_").
- [CSE] Added support for &lt;timeSeries>/&lt;timeSeriesInstance> resource types.
- [CSE] Added support for &lt;timeSeries>'s missing data monitoring in &lt;subscription> resource type and notifications.
- [CSE] Added support for *ctm* (currentTime) attribute for &lt;CSEBase> resource type.
- [CSE] Added wildcard (\*) support for &lt;ACP>'s *acr/acor* originators.
- [CSE] Added support for &lt;ACP>'s *acr/acod* attribute (not for specializations yet, though).
- [CSE] Added support for 'Request Expiration Timestamp' request parameter, also for &lt;request> resources.
- [CSE] Added support for *Vendor Information* request/response header.
- [CSE] Added support for &lt;container> *disableRetrieval* attribute.
- [CSE] Added validation of *cnf* (contentInfo) attribute.
- [CSE] Added support for *dcnt* (deletionCnt) attribute for &lt;contentInstance> resource type.
- [WEB] Added OAuth2 authorization support for the proxied CSE (for the stand-alone web UI).
- [WEB] Added opening the web UI in a browser on startup (for the stand-alone web UI).
- [TESTS] Added OAuth2 authorization support for the tests.
- [CONSOLE] Added "I" command to the console (inspect a resource and its child resources).
- [CONSOLE] Added "L" command to the console (toggle through the various log levels, including *off*)
- [CONSOLE] Added configuration *cse.console.hideResources* to hide certain resources from showing in the the resource tree.
- [CONSOLE] Added various view modes when showing the resource tree (normal, compact, content, contentOnly).

### Changed
- [CSE] Relaxed validation for float in attributes and arguments. Integer are now accepted as well.
- [CSE] Changed format of configuration values "cse.registration.allowedAEOriginators" and "cse.registration.allowedCSROriginators" from regex to a simple wildcard (\* and ?) format.
- [CSE] Changed the internal timed and regular processes to a single priority timer queue.
- [CSE] Removed "logging.enable" configuration setting and added *off* as a possible value to *logging.level".
- [CSE] Improved the size calculation of &lt;contentInstance>, &lt;flexContainer>, and &lt;timeSeriesInstance> to realistic sizes (not the Python-internal type sizes anymore).
- [CSE] Refactored internal request handling to support future protocol binding developments other than http.
- [CSE] Changed the sorting of request result lists to type and creation time for &lt;contentInstance>, &lt;flexContainerInstance> and &lt;timeSeriesInstance>.
- [CSE] Improved the validation when registering &lt;remoteCSE> resources for *csi* and *cb* attributes.
- [CSE] Added validation of complex attributes in general.
- [RUNTIME] The CSE is now started by running the *acme* module (```python3 acme```)

### Fixed
- [CSE] Corrected response status codes for AE registration errors.
- [CSE] Prevent CREATE and UPDATE requests for &lt;flexContainerInstance> resource type.
- [CSE] Improved handling of &lt;flexContainerInstance> resources when versioning is disabled in the parent &lt;flexContainer>.
- [CSE] Re-added: remove comments from received JSON content.
- [CSE] Improved the timely execution of background tasks. The actual task's execution time is not added on top to the interval anymore, and intervals are constant.
- [CSE] Improved support and validation for absRelTimestamp type.
- [CSE] Improved handling of the &lt;request> resource's expiration time. It is now aligned with the 'Request Expiration Timestamp' request parameter.
- [CSE] Improved checking of empty *acpi* attribute lists. Empty lists are not allowed and the *acpi* must be removed from a resource instead.
- [CSE] Optimized log messages. Messages for irrelevant log levels are not even created anymore.
- [CSE] Corrected behavior when oldest &lt;contentInstance>, &lt;flexContainerInstance> and &lt;timeSeriesInstance> resource are deleted. Now NO notification is sent in case a &lt;subscription> monitors for *Delete_of_direct_child_resource*.
- [CSE] Added warnings when an imported &lt;CSEBase> overwrites any of the *csi*, *ri*, *rn* attributes.
- [CSE] Better error handling for ill-formed CSE-ID.
- [CSE] Fixed missing check for &lt;subscription>'s *chty* attribute. The listed resource types therein must be allowed child resource types of the &lt;subscription>'s parent resource.
- [DATABASE] Optimized and unified database searches for fragments in resources.


## [0.7.3] - 2021-03-26

### Added
- [CSE] Added *cse.resource.cnt.enableLimits* configuration. 
- [CSE] Improved startup error messages when running in headless mode.
- [CONSOLE] Added "T" command to the console (display only sub-tree of the resource tree).

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
- [CSE] Added support for *holder* attribute. Added access control behavior for *holder* and resource creator when an *acpi* attribute is specified for a resource, but doesn't have one.
- [CSE] Added support for Subscription's *expirationCounter*.
- [CSE] Added headless mode to better support docker.
- [CONSOLE] Added command interface to the terminal console (for stopping the CSE, printing statistics, CSE registrations, the resource tree, etc).
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
- [CSE] Changed resourceType values for &lt;latest> and &lt;oldest> to the specified values.
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
