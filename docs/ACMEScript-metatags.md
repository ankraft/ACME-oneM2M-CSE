[← README](../README.md)  
[← ACMEScript](ACMEScript.md) 

# ACMEScript - Meta Tags

Meta tags are special commands in a script that are not executed during the runtime of a script, but describe certain capabilities of the script or give, for example, the script a name or provide instructions when a script should be executed. 

Meta tags are keyword that start with an at-sign "@". They can appear anywhere in a script file on a single line, but it is recommend to collect them either at the start or the end of a script. Meta tags are case sensitive.

<a name="top"></a>

| Meta Tag                                | Description                                                                                    |
|-----------------------------------------|------------------------------------------------------------------------------------------------|
| [@at](#meta_at)                         | Schedule scripts to run at a certain time or time interval                                     |
| [@description](#meta_description)       | Provide a one-line script description                                                          |
| [@filename](#meta_filename)             | Contains a script's filename (internal only)                                                   |
| [@hidden](#meta_hidden)                 | Hide a script from the console's script catalog                                                |
| [@init](#init)                          | Run a script to initialize the CSE during startup and restart                                  |
| [@name](#meta_name)                     | Assign a name to a script                                                                      |
| [@onKe](#meta_onkey)                    | Run a script when a specified key is pressed                                                   |
| [@onNotification](#meta_onnotification) | Run a script as a receiver of a NOTIFY request from the CSE                                    |
| [@onRestart](#meta_onrestart)           | Run a script just after the CSE restarted                                                      |
| [@onShutdown](#meta_onshutdown)         | Run a script just before the CSE shuts down                                                    |
| [@onStartup](#meta_onstartup)           | Run a script just after the CSE started                                                        |
| [@prompt](#meta_prompt)                 | Prompt the user for input before the script is run                                             |
| [@timeout](#meta_timeout)               | Set a timeout after which script execution is stopped                                          |
| [@uppertester](#meta_uppertester)       | A script with this test can be run via the [Upper Tester Interface](Operation.md#upper_tester) |
| [@usage](#meta_usage)                   | Provide a short usage help                                                                     |

## Accessing Meta Tags
Meta tags are added as constants to the script's environment, prefixed with "meta.".
They can be accessed like any other environment variable, for example:

```lisp
(if (is-defined 'meta.name)            ;; note the quote in front of meta.name
	(print "Script name:" meta.name))  ;; prints the script's name
```

---

## Meta Tags

<a name="meta_at"></a>

### @at

`@at <cron pattern>`

The `@at` meta tag specifies a time / date pattern when a script should be executed. This pattern follows the Unix [crontab](https://crontab.guru/crontab.5.html) pattern. 

A crontab pattern consists of the following five fields:  

`minute hour dayOfMonth month dayOfWeek`

Each field is mandatory and must comply to the following values:

- `*` : any valid integer number for that field, or
- `*/<number>` : step, or
- `<number>-<number` : range, or
- `value[,value]*` : value is either a number, a step, or a range

Example:
```lisp
;; Run a script every 5 minutes
@at */5 * * * *
;; Run a script every Friday at 2:30 am
@at 30 2 * * 4
```

[top](#top)

---

<a name="meta_description"></a>

### @description

`@description <string>`

A short one-line description of a script's purpose. This is used, for example, for the console's script catalog.

See also: [@usage](#meta_usage)

Example:
```lisp
@description The purpose of this script is to demonstrate the @description meta tag
```

[top](#top)

---

<a name="meta_filename"></a>

### @filename

`@filename <string>`

This meta tag is for internal use. It will be assigned the script's full filename when read by the script manager.

[top](#top)

---

<a name="meta_hidden"></a>

### @hidden

`@hidden`

This meta tag indicates that a script will not be listed in the console's script catalog.

Example:
```lisp
@hidden
```

[top](#top)

---

<a name="meta_init"></a>

### @init

`@init`

This meta tag indicates that the script will be executed during the CSE's startup and restart. It is used to initialize the CSE and creates the basic resources.

Only one script can have this meta tag set.

See also: [@onRestart](#meta_onrestart), [@onShutdown](#meta_onshutdown), [@startup](#meta_onstartup)

Example:

```text
@init
```

[top](#top)

---

<a name="meta_name"></a>

### @name

`@name <string>`

This meta tag assigns a name to a script. This name is used for identifying the script, for example when running a script from the console.

See also: [@uppertester](#meta_uppertester)

Example:
```lisp
@name exampleScript
```

[top](#top)

---

<a name="meta_onkey"></a>

### @onKey

`@onKey <key>`

With this meta tag a script registers to a key-press event of the console interface. If the key is pressed then the script is run. The event and the key are passed as the environment variables [event.type]() and [event.data](), respectively.

The keys may be normal ASCII characters or a function key. Please consult the console's [supported function key table](Console.md#function_keys) for the function key's names. Note, that not all function keys are available on all OS platforms.

A script can only register for a single key event.

Example:
```lisp
;; Run the script when the '9' key is pressed
@onkey F9

(print (event.data))
```

[top](#top)

---

<a name="meta_onnotification"></a>

### @onNotification

`@onNotification <URI: acme://someID>`

With this meta tag a script acts as a handler for a notification request from the CSE.

The ACME URL scheme "acme://&lt;identifier>" is used to define a URI that is targeting the script. Such a URI must be used in either the *notificationURI* attribute of a subscription resource, or the *pointOfAccess* of an AE.

When  a notification is received and the handler script is run the following variables are set:


- [notification.originator](ACMEScript-functions.md#var_notification_originator) : The notification's originator
- [notification.resource](ACMEScript-functions.md#var_notification_resource) : The notification's resource
- [notification.uri](ACMEScript-functions.md#var_notification_uri) : The notification's target URI


Example:
```lisp
;; Run the script when the 'acme://aNotification' notificastion is received
@onNotification acme://aNotification

(print (notification.resource))
```

[top](#top)

---

<a name="meta_onrestart"></a>

### @onRestart

`@onRestart`

This meta tag indicates that the script will be executed just after the CSE restarted, for example after a reset.

If multiple scripts have this meta tag set then they will run in random order.

See also: [@init](#meta_init), [@onStartup](#meta_onstartup),  [@onShutdown](#meta_onshutdown)

Example:
```lisp
@onRestart
```

[top](#top)

---

<a name="meta_onshutdown"></a>

### @onShutdown

`@onShutdown`

This meta tag indicates that the script will be executed just before the CSE shuts down.

If more than one script have this meta tag set then they will run in random order.

See also: [@init](#meta_init), [@onRestart](#meta_onrestart), [@onStartup](#meta_onstartup)

Example:
```lisp
@onShutdown
```

[top](#top)

---

<a name="meta_onstartup"></a>

### @onStartup

`@onStartup`

This meta tag indicates that the script will be executed just after the CSE started. It will be run only after start up, but not when the CSE restarted. If more than one script have this meta tag set then they will be run in random order.

See also: [@init](#meta_init), [@onRestart](#meta_onrestart), [@onShutdown](#meta_onshutdown)

Example:
```text
@onStartup
```

[top](#top)

---

<a name="meta_prompt"></a>

### @prompt

`@prompt <prompt text>`

A script with this meta tag will present a prompt before it is executed and ask a user for input. The result is then passed on as  [script arguments](ACMEScript.md#arguments).

This meta tag should only be used when human interaction can be ensured. Running a script with this meta tag scheduled or  unattended will cause the script to wait forever for user input. 

Example:
```lisp
@prompt Enter some arguments
```

[top](#top)

---

<a name="meta_timeout"></a>

### @timeout

`@timeout <seconds>`

This meta tag sets a timeout after which the script execution is terminated with a *timeout* error

Note, that the script may terminate some time after the timeout when a script command takes longer to run.

Example:
```lisp
@timeout 10
```

[top](#top)

---

<a name="meta_uppertester"></a>

### @uppertester

`@uppertester`

This meta tag indicates that a script is runnable through the [Upper Tester Interface](Operation.md#upper_tester) interface. In this case the script name specified by the  [@name](#meta_name) meta tag is used as the command name.

Scripts without this meta tag cannot be run through the Upper Tester interface.

See also: [@name](#meta_name)

Example:
```lisp
@uppertester
```

[top](#top)

---

<a name="meta_usage"></a>

### @usage

`@usage <string>`

This meta tag provides a short help message for a script's usage.

See also: [@description](#meta_description)

Example:
```lisp
@usage exampleScript <a parameter> <another parameter>
```


[← ACMEScript](ACMEScript.md)  
[← README](../README.md) 
