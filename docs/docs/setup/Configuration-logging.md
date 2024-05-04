# Configuration - Logging

The CSE supports logging to the screen and to a file. 

By default, logging to the screen is enabled and logging to a file is disabled. If logging to a file is enabled, the log files are rotated when they reach a certain size or number of files. 


## General Settings

**Section: `[logging]`**

These are the general logging settings.

| Setting               | Description                                                                                                                                                        | Default                                                                                              | Configuration Name            |
|:----------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------|:------------------------------|
| enableFileLogging     | Enable logging to file.                                                                                                                                            | false                                                                                                | logging.enableFileLogging     |
| enableScreenLogging   | Enable logging to the screen.                                                                                                                                      | true                                                                                                 | logging.enableScreenLogging   |
| path                  | Pathname for log files.                                                                                                                                            | [${basic.config:baseDirectory}](../setup/Configuration-basic.md#configuration---basic-settings)/logs | logging.path                  |
| level                 | Loglevel. Allowed values: `debug`, `info`, `warning`, `error`, `off`.<br/>See also command line argument [–log-level](../setup/Running.md#command-line-arguments). | debug                                                                                                | logging.level                 |
| count                 | Number of files for log rotation.                                                                                                                                  | 10                                                                                                   | logging.count                 |
| size                  | Size per log file.                                                                                                                                                 | 100.000 bytes                                                                                        | logging.size                  |
| maxLogMessageLength   | Maximum length of a log message. Longer messages will be truncated. A value of 0 means no truncation.                                                              | 1000 characters                                                                                      | logging.maxLogMessageLength   |
| stackTraceOnError     | Print a stack trace when logging an 'error' level message.                                                                                                         | True                                                                                                 | logging.stackTraceOnError     |
| enableBindingsLogging | Enable logging of low-level HTTP & MQTT client events.                                                                                                             | False                                                                                                | logging.enableBindingsLogging |
| queueSize             | Number of log entries that can be added to the asynchronous queue before blocking. A queue size of 0 means disabling the queue.                                    | 5000 entries                                                                                         | logging.queueSize             |
| filter                | List of component names to exclude from logging.                                                                                                                   | werkzeug,markdown_it                                                                                 | logging.filter                |
