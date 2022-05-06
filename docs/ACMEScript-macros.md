[← README](../README.md)  
[← ACMEScript](ACMEScript.md) 

# ACMEScript - Macros and Variables


| Type                       | Macro / Variable                                 | Description                                                             |
|----------------------------|--------------------------------------------------|-------------------------------------------------------------------------|
| [Basic](#macros_basic)     | [argc](#macro_argc)                              | Get number of arguments                                                 |
|                            | [argv](#macro_argv)                              | Get script or procedure arguments                                       |
|                            | [datetime](#macro_datetime)                      | Get current date and time                                               |
|                            | [in](#macro_in)                                  | Text whether a string exists in another string                          |
|                            | [loop](#macro_loop)                              | Get the current while loop's loop count                                 |
|                            | [lower](#macro_lower)                            | Get a lower-case version of the provided string argument                |
|                            | [match](#macro_match)                            | Evaluate an argument against a simple regular expression                |
|                            | [random](#macro_random)                          | Generate a random number.                                               |
|                            | [result](#macro_result)                          | Get the last result of a while, procedure etc.                          |
|                            | [round](#round)                                  | Round a float number.                                                   |
|                            | [runCount](#macro_runcount)                      | Get the number of script runs.                                          |
|                            | [upper](#macro_upper)                            | Get an upper-case version of the provided string argument               |
| [Storage](#macros_storage) | [storageGet](#macro_storageget)                  | Get a value from the persistent key/value storage                       |
|                            | [storageHas](#macro_storagehas)                  | Test the existence of a key in the persistent key/value storage         |
| [oneM2M](#macros_onem2m)   | [attribute](#macro_attribute)                    | Get the value of an attribute from a oneM2M resource                    |
|                            | [hasAttribute](#macro_hasattribute)              | Test the existence of an attribute from a oneM2M resource               |
|                            | [notification.originator](#macro_not_originator) | Get a notification's originator                                         |
|                            | [notification.resource](#macro_not_resource)     | Get a notification's resource                                           |
|                            | [notification.uri](#macro_not_uri)               | Get a notification's URI                                                |
|                            | [request.originator](#macro_req_originator)      | Get the assigned originator used in requests                            |
|                            | [response.resource](#macro_resp_resource)        | Get the resource of the last oneM2M request                             |
|                            | [response.status](#macro_resp_status)            | Get the status of the last oneM2M request                               |
| [CSE](#macros_cse)         | [isIPython](#macro_isipython)                    | Check whether the runtime environment is IPython, e.g. Jupyter Notebook |
|                            | [cseStatus](#macro_csestatus)                    | Get the current CSE runtime status                                      |
|                            | [&lt;any CSE configuration>](#macro_default)     | Get the value of any of the CSE's configuration settings                |

---

The following builtin macros and variables are available.

<a name="macros_basic"></a>
## Basic
<a name="macro_argc"></a>
### argc

Usage:  [argc]

Evaluates to the number of arguments to the script or the current scope.

Example:

```text
if [> [argc] 2]
	logError Wrong number of arguments
	error
endif
``` 

<a name="macro_argv"></a>
### argv

Usage:  
[argv &lt;n:integer>\*]

Evaluates to the n-th argument to the script or a procedure. The index starts a 1, because the 0-th argument is the name 
of the script or the procedure. If the `argv` macro is called without an argument then the original string of arguments
is returned (but without the script name).

Example:

```text
print The name of the script is: [argv 0]
print The first argument is: [argv 1]
print All arguments: [argv]
``` 

<a name="macro_datetime"></a>
### datetime

Usage:  
[datetime &lt;format pattern>\* ]

Evaluates to a UTC-based date/time string. With the optional format pattern one can specify the output format. The format is the same as the Python `strftime()` function. See [https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior) for further details.

The default is `%Y%m%dT%H%M%S.%f`, which evaluates to an ISO8901 timestamp.

Example:

```text
print [datetime]
# -> 20220107T221625.771604
print [datetime %H:%M]
# -> 22:26
```


<a name="macro_in"></a>
### in

Usage:  
[in &lt;text> &lt;string>]

Check whether a text can be found in a string. The macro returns *true* or *false* accordingly.

Example:

```text
print [in Hello "Hello World"]
```


<a name="macro_loop"></a>
### loop

Usage:  
[loop]

Return the current [while](ACMEScript-commands.md#command_while) loop's loop count. 
This counter is automatically incremented by 1 for every iteration of a while loop. 
It starts at 0 when the while loop is entered. Every (nested) while loop has its own loop counter.

It is not defined outside a while loop.

Example:

```text
while [< [loop] 10]
	print [loop]
endwhile
print [loop]
# -> yields an error because "loop" is not defined outside a while loop
```


<a name="macro_lower"></a>
### lower

Usage:  
[lower &lt;text:string>]

Return a lower-case version of the provided string `text`.

Example:

```text
print [upper Hello]
# -> hello
```


<a name="macro_match"></a>
### match

Usage:  
[match &lt;text:string> &lt;regex>]

Match the `text` against the regular expression `regex`, and return the result as *true* or *false*.

The regular expression format is a very simplified version that only supports the following expression operators:

- ? : any single character
- \* : zero or more characters
- \+ : one or more characters
- \\ : Escape an expression operator

Examples:

```text
"hello" - "h?llo" -> true
"hello" - "h?lo" -> false
"hello" - "h*lo" -> true
"hello" - "h*" -> true
"hello" - "*lo" -> true
"hello" - "*l?" -> true
```

Example:

```text
if [match hello h*o[]
	print found
endif
# -> hello
```


<a name="macro_random"></a>
### random

Usage:  
[random]  
[random &lt;end> ]  
[random &lt;start> &lt;end> ]

Generate a random number. If no argument is given then a random number in the range [0.0, 1.0] will be generated.

If only one argument is given then this argument is treated as the end of the range [0.0, &lt;end>].

If two argument are given then these arguments are treated as the start and end of the range [&lt;start>, &lt;end>].

Example:

```text
print [random]
# -> random number in the range [0.0, 1.0] 
print [random 10]
# -> random number in the range [0.0, 10.0] 
print [random -5 5]
# -> random number in the range [-5.0, 5.0]
``` 


<a name="macro_result"></a>
### result

Usage:  
[result]

Evaluates to the result of the last scope, or nothing. See also [Context, Scopes, Arguments, and Results](ACMEScript.md#context_scope).

Example:

```text
# Define a procedure that only returns the string "nothing"
procedure getNothing
endprocedure nothing

# Call the procedure and print the result afterwards
getNothing
print [result]
# -> nothing
``` 


<a name="macro_round"></a>
### round

Usage:  
[round &lt;number:float> [ &lt; ndigits> ] ]

Get a number rounded to `ndigits` precision after the decimal point. If `ndigits` is omitted, 
then this macro returns the nearest integer. `ndigits` may be negative.

Example:

```text
print [round 1.6]
# -> 2
print ]round 1.678]
# -> 1.68
print ]round 2361.678 -2]
# -> 2400.0
```


<a name="macro_runcount"></a>
### runCount

Usage:  
[runCount]

Evaluates to the number of runs of the script.

Example:

```text
print [runCount]
# -> 42
``` 


<a name="macro_round"></a>
### round

Usage:  
[round &lt;number:float> [ &lt; ndigits> ] ]

Get a number rounded to `ndigits` precision after the decimal point. If `ndigits` is omitted, 
then this macro returns the nearest integer. `ndigits` may be negative.

Example:

```text
print [round 1.6]
# -> 2
print [round 1.678]
# -> 1.68
print [round 2361.678 -2]
# -> 2400.0
```


<a name="macro_upper"></a>
### upper

Usage:  
[upper &lt;text:string>]

Return a upper-case version of the provided string `text`.


Example:

```text
print [upper hello]
# -> HELLO
```


<a name="macros_storage"></a>
## Storage
These macros help to access key/values in the [persistent storage](ACMEScript.md#storage).

<a name="macro_storageget"></a>
### storageGet

Usage:  
[storageGet &lt;key:string>]

Evaluates to the value stored for the key `key` that has previously been stored with the [storagePut](ACMEScript-commands.md#command_storageput) command in the persistent storage. If the key does not exist then the script is terminated with an error.

Example:

```text
storagePut aKey aValue
print [storageGet aKey]
# -> aValue
```

<a name="macro_storagehas"></a>
### storageHas

Usage [storageHas &lt;key:string>]

Evaluates to the string `true` or `false`, depending whether the provided key exists in the persistent storage.

Example:
```text
storagePut aKey aValue
if [storageHas aKey]
	print [storageGet aKey]
endif
# -> aValue
```


<a name="macros_onem2m"></a>
## oneM2M

<a name="macro_attribute"></a>
### attribute

Usage:  
[attribute &lt;key:pattern> &lt;resource:JSON>]

This macro finds a structured `key` in the JSON structure `resource` and returns its value. This could be a single value or a JSON structure.
If `key` does not exists or could not be found then the script terminates with an error.

`key` can be the name of a JSON element, or one of the following pattern elements

- It is possible to address a specific element in an array. This is done by specifying the element as `{n}`.  
&ensp;  
Example: 

```text
print [attribute m2m:cin/{1}/lbl/{0} [response.resource]]
```

- If an element is specified as `{}` then all elements in that array are returned in an array.  
&ensp;  
Example: 

```text
print [attribute m2m:cin/{1}/lbl/{} [response.resource]]
```

- If an element is specified as `{_}` and is targeting a dictionary then a single random path is chosen. This can be used to skip, for example, unknown first elements in a structure.  
&ensp;  
Example:

```text
print [attribute {_}/rn [response.resource]]
```


<a name="macro_hasattribute"></a>
### hasAttribute

Usage:  
[hasAttribute &lt;key:pattern> &lt;resource:JSON>]

This macro checks whether an attribute exists in a JSON structure. It evaluates to `true` or `false`, respectively.

See the the description of the [attribute](#macro_attribute) macro for an explanation of the key pattern.


<a name="macro_not_originator"></a>
### notification.originator

Usage:  
[notification.originator≤6

Get a notification's originator. This variable is only set in a script that is a notification target.

Example:

```text
print [notification.originator]
# -> ... the notification's originator ...
```


<a name="macro_not_resource"></a>
### notification.resource

Usage:  
[notification.resource]

Get a notification's resource. This variable is only set in a script that is a notification target.

Example:

```text
printJSON [notification.resource]
# -> ... the notification's resource ...
```

<a name="macro_not_uri"></a>
### notification.uri

Usage:  
[notification.uri]

Get a notification's target URI. This variable is only set in a script that is a notification target.

Example:

```text
print [notification.uri]
# -> ... the notification's URI ...
```


<a name="macro_resp_resource"></a>
### response.resource

Usage:  
[response.resource]

Evaluates to the resource returned by the last oneM2M request, the debug message, or nothing.

Example:

```text
retrieve cse-in
print [response.resource]
# -> ... the retrieved resource ...
```


<a name="macro_req_originator"></a>
### request.originator

Usage:  
[request.originator]

Evaluates to the assigned originator for all following oneM2M requests. See also the command [ORIGINATOR](ACMEScript-commands.md#command_originator).

Example:

```text
print [request.originator]
# -> ... the originator ...
```


<a name="macro_response_status"></a>
### response.status

Usage:  
[response.status]

Evaluates to the response status code returned by the last oneM2M request, or nothing.

Example:

```text
retrieve cse-in
print [response.status]
# -> ... the request's status code ...
```

<a name="macros_cse"></a>
## CSE

<a name="macro_csestatus"></a>
### cseStatus

Usage:  
[cseStatus]

Return the CSE's runtime status. This is one of the following values:

- STOPPED	
- STARTING
- RUNNING	
- STOPPING
- RESETTING

Example:
```text
# Only reset when CSE is running
if [== [cseStatus] RUNNING]
	reset
endif
```

<a name="macro_isipython"></a>
### isIPython

Usage:  
[isIPython]

This macro evaluates to `true` if the CSE is currently running in an IPython environment, such as Jupyter Notebooks,
or to `false` otherwise.

Example:
```text
if [isIPython]
	print Running in IPython
endif
```


<a name="macro_default"></a>
### Configuration Settings

Usage:  
[&lt;CSE configuration>]

Any of the CSE's configuration settings that are defined in [Configuration](Configuration.md) can be used as a variable. It evaluates to the respective configuration value.

Some of the configuration settings can also be set to a new value.  
**Attention: Assigning wrong values to configuration settings can do a lot of harm to the CSE and the stored data, even render it non-functional.**  
Also note, that not all configuration changes may have an immediate effect, but will stay in effect after the script terminated.

Example:
```text
print [cse.type]
# -> IN
print [logging.level]
# -> DEBUG
```

[← ACMEScript](ACMEScript.md)  
[← README](../README.md)  
