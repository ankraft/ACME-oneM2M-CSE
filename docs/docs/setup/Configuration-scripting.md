# Configuration - Scripting

The ACME CSE [supports scripting](../development/ACMEScript.md) using a Lisp-like scripting language. Scripts can be used to extend the functionality of the CSE, for example, to implement custom logic, writing small applications or to interact with external systems.

## Scripting

**Section: `[scripting]`**

These are the settings for the scripting engine.

| Setting                | Description                                                                                                                               | Default      | Configuration Name               |
|:-----------------------|:------------------------------------------------------------------------------------------------------------------------------------------|:-------------|:---------------------------------|
| scriptDirectories      | Add one or multiple directory paths to look for scripts, in addition to the ones in the system or runtime `init` directory. Must be a comma-separated list. | not set      | scripting.scriptDirectories      |
| verbose                | Enable debug output during script execution, such as the current executed line.                                                           | False        | scripting.verbose                |
| fileMonitoringInterval | Set the interval to check for new files in the script directories.<br/>0 means disable monitoring. Must be >= 0.0.                   | 2.0 seconds  | scripting.fileMonitoringInterval |
| maxRuntime             | Set the timeout for script execution in seconds. 0.0 seconds means no timeout.<br/>Must be >= 0.0.                                        | 60.0 seconds | scripting.maxRuntime             |

 