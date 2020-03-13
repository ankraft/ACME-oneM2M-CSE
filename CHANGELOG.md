# Changelog

## Unreleased 0.3.0 - 2020-xx-yy
- [CSE] Discovery supports "attributes + children" return content.
- [CSE] Changed command line argument --reset-db to --db-reset .
- [CSE] Added command line argument --db-storage .

## 0.2.1 - 2020-03-06
- [APPS] Fixed wrong originator handling for already registered AEs.
- [APPS] Added persistent storage support for AEs.

## 0.2.0 - 2020-03-02
- [CSE] Checking and setting "creator" attribute when creating new resources.
- [ACP] Always add "admin" originator to newly created ACPs (configurable).
- [ACP] Imporved default ACP. Any new resource without ACP gets the default ACP assigned.
- [AE] Added proper AE registration. An ACP is automatically created for a new AE, and also removed when the corresponding AE is removed.
- [LOGGING] Added option to enable/disable logging to a log file (Logging:enableFileLogging). If disabled, log-messages are only written to the console.
- [LOGGING] Possibility to disable logging on the command line.
- [IMPORTING] Added default ACP. 
- [WEB] Browser request to "/"" will now redirect to the webui's URL.
- [WEB] REST UI will not refresh anymore when automatic refresh is on.
- [WEB] Added LOGO & favicon.
- [MISC] Various fixes and improvements.

## 0.1.0 - 2020-02-09
- First release
