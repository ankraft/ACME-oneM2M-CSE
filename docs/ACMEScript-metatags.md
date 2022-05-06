[← README](../README.md)  
[← ACMEScript](ACMEScript.md) 

# ACMEScript - Meta Tags

Meta tags are special commands in a script that are not executed during the runtime of a script, but describe certain capabilities of the script or give, for example, instructions when a script should be executed. 

Meta tags are lines that start with an at-sign "@". They can appear anywhere in a script file, but it is recommend to collect them either at the start or the end of a script.

| Meta Tag                               | Description                                                                                    |
|----------------------------------------|------------------------------------------------------------------------------------------------|
| [at](#meta_at)                         | Schedule scripts to run on a time interval                                                     |
| [description](#meta_description)       | Provide a one-line script description                                                          |
| [filename](#meta_filename)             | Contains a script's filename (internal only)                                                   |
| [hidden](#meta_hidden)                 | Hide a script from the console's script catalog                                                |
| [name](#meta_name)                     | Assign a name to a script                                                                      |
| [onKey](#meta_onkey)                   | Run a script when a specified key is pressed                                                   |
| [onNotification](#meta_onnotification) | Run a script as a receiver of a NOTIFY request from the CSE                                    |
| [onRestart](#meta_onrestart)           | Run a script just after the CSE restarted                                                      |
| [onShutdown](#meta_onshutdown)         | Run a script just before the CSE shuts down                                                    |
| [onStartup](#meta_onstartup)           | Run a script just after the CSE started                                                        |
| [prompt](#meta_prompt)                 | Prompt the user for input before the script is run                                             |
| [timeout](#meta_timeout)               | Set a timeout after which script execution is stopped                                          |
| [uppertester](#meta_uppertester)       | A script with this test can be run via the [Upper Tester Interface](Operation.md#upper_tester) |
| [usage](#meta_usage)                   | Provide a short usage help                                                                     |


<a name="meta_at"></a>
### @at

Usage:  
@at &lt;cron pattern>

The `@at` meta tag specifies a time / date pattern when a script should be executed. This pattern follows the Unix 
[crontab](https://crontab.guru/crontab.5.html) pattern. 

A crontab pattern consists of the following five fields:  
  
`minute hour dayOfMonth month dayOfWeek`

Each field is mandatory and must comply to the following values:

- `*` : any valid integer number for that field, or
- `*/<number>` : step, or
- `<number>-<number` : range, or
- `value[,value]*` : value is either a number, a step, or a range

Example:
```text
# Run a script every 5 minutes
@at */5 * * * *
# Run a script every Friday at 2:30 am
@at 30 2 * * 4
```


<a name="meta_description"></a>
### @description

Usage:  
@description &lt;string>

A short one-line description of a script's purpose. This is used, for example, for the script catalog of the console.

Example:
```text
@description The purpose of this script is to demonstrate the @description meta tag
```


<a name="meta_filename"></a>
### @filename

Usage:  
@filename &lt;string>

This meta tag is for internal use. It will be assigned the script's full filename when read by the script manager.


<a name="meta_hidden"></a>
### @hidden

Usage:  
@hidden

This meta tag indicates that a script will not be listed in the console's script catalog.

Example:
```text
@hidden
```


<a name="meta_name"></a>
### @name

Usage:  
@name &lt;string>

This meta tag assigns a name to a script. This name is used for identifying the script, for example when running
a script from the console.

Example:
```text
@name exampleScript
```


<a name="meta_onkey"></a>
### @onKey

Usage:  
@onKey &lt;key>

With this meta tag a script registers for a key-press event of the console interface. If the key is pressed then the
script is run. The event and the key are passed as the script arguments.

A script can only register for a single key.

Example:
```text
# Run the script when the '9' key is pressed
@onkey 9

print [argv]
# -> onkey 9
```


<a name="meta_onnotification"></a>
### @onNotification

Usage:  
@onNotification &lt;URI: acme://someID>

With this meta tag a script acts as a receiver of a notification request from the CSE. 
The ACME's own URL scheme "acme://&lt;identifier>" is used to define a URI that is
targeting the script. Such a URI must be used in either the *notificationURI* attribute of a
subscription resource, or the *pointOfAccess* of an AE.

When receiving a notification the following variables are set:


- [notification.originator](ACMEScript-macros.md#macro_not_originator) : The notification's originator
- [notification.resource](ACMEScript-macros.md#macro_not_resource) : The notification resource
- [notification.uri](ACMEScript-macros.md#macro_not_uri) : The notification's target URI


Example:
```text
# Run the script when the '9' key is pressed
@onNotification acme://aNotification

print [notification.resource]
# -> The notification resource
```


<a name="meta_onRestart"></a>
### @onRestart

Usage:  
@onRestart

This meta tag indicates that the script will be run just after the CSE restarted, for example after a reset.
 If multiple scripts have this meta tag set then they will be run in random order.

Example:
```text
@onRestart
```


<a name="meta_onshutdown"></a>
### @onShutdown

Usage:  
@onShutdown

This meta tag indicates that the script will be run just before the CSE shuts down. 
If more than one script have this meta tag set then they will be run in random order.

Example:
```text
@onShutdown
```


<a name="meta_onstartup"></a>
### @onStartup

Usage:  
@onStartup

This meta tag indicates that the script will be run just after the CSE started up. It will be run only after start up, but not
when the CSE restarted. If more than one script have this meta tag set then they will be run in random order.

Example:
```text
@onStartup
```


<a name="meta_prompt"></a>
### @prompt

Usage:  
@prompt &lt;prompt text>

A script with this meta tag will present a prompt before it is executed asking a user for input. The result is then passed on as
the [script arguments](ACMEScript.md#arguments).

The meta tag should only be used when human interaction can be ensured. Running a script with this meta tag scheduled or and unattended
will cause the script to wait for user input forever. 

Example:
```text
@prompt Enter some arguments
```


<a name="meta_timeout"></a>
### @timeout

Usage:  
@timeout &lt;seconds>

This meta tag sets a timeout after which the script execution is terminated with a *timeout* error.
Note, that the script may terminate some time after the timeout when a script command takes longer to run.

Example:
```text
@timeout 10
```


<a name="meta_uppertester"></a>
### @uppertester

Usage:  
@uppertester

This meta tag indicates that a script is runnable through the [Upper Tester Interface](Operation.md#upper_tester) interface.
Scripts without this meta tag cannot be run through that interface.

Example:
```text
@uppertester
```


<a name="meta_usage"></a>
### @usage

Usage:  
@usage &lt;string>

This meta tag provides a short help message for a script's usage.

Example:
```text
@usage exampleScript <a parameter> <another parameter>
```


[← ACMEScript](ACMEScript.md)  
[← README](../README.md) 
