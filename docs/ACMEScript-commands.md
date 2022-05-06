[← README](../README.md)  
[← ACMEScript](ACMEScript.md) 

# ACMEScript - Commands


| Type                         | Command                                         | Description                                                                  |
|------------------------------|-------------------------------------------------|------------------------------------------------------------------------------|
| [Basic](#commands_basic)     | [ASSERT](#command_assert)                       | Assert a condition                                                           |
|                              | [BREAK](#command_break)                         | Break out of a [WHILE](#command_while) loop                                  |
|                              | [CASE](#command_case)                           | Conditional command block for a  [SWITCH](#command_switch) block          M  |
|                              | [CONTINUE](#command_break)                      | Continue with the next iteration of a [WHILE](#command_while) loop           |
|                              | [DEC](#command_dec)                             | Decrements a numeric variable                                                |
|                              | [ELSE](#command_else)                           | Start the ELSE part of an [IF](#command_if) block                            |
|                              | [ENDIF](#command_endif)                         | End an [IF](#command_if) or [ELSE](#command_else) block                      |
|                              | [ENDPROCEDURE](#command_endprocedure)           | End a [PROCEDURE](#command_procedure)                                        |
|                              | [ENDSWITCH](#command_endswitch)                 | End a [SWITCH](#command_switch) block                                        |
|                              | [ENDWHILE](#command_endwhile)                   | End a [WHILE](#command_while) loop                                           |
|                              | [IF](#command_if)                               | Check comparison condition and begin a conditional IF block                  |
|                              | [INC](#command_inc)                             | Increments a numeric variable                                                |
|                              | [LOG](#command_log)                             | Print a message to the debug-level log                                       |
|                              | [LOGERROR](#command_logerror)                   | Print a message to the error-level log                                       |
|                              | [PROCEDURE](#command_procedure)                 | Define a procedure                                                           |
|                              | [QUIT](#command_quit)                           | Quit the running script                                                      |
|                              | [QUITWITHERROR](#command_quiterror)             | Quit the running script with error result                                    |
|                              | [RUN](#command_run)                             | Run another script                                                           |
|                              | [SET](#command_set)                             | Set or remove a variable, or perform a calculation                           |
|                              | [SLEEP](#command_sleep)                         | Pause the script execution                                                   |
|                              | [SWITCH](#command_switch)                       | Start a switch block                                                         |
|                              | [WHILE](#command_while)                         | Start a while loop                                                           |
| [Console](#commands_console) | [CLEAR](#command_clear)                         | Clear the console screen                                                     |
|                              | [PRINT](#command_print)                         | Print a message to the info-level log                                        |
|                              | [PRINTJSON](#command_printjson)                 | Print a beautified JSON document to the console                              |
|                              | [SETLOGGING](#command_setlogging)               | Enable/disable console screen logging                                        |
| [Storage](#commands_storage) | [STORAGEPUT](#command_storageput)               | Store a key/value pair in the [persistent storage](ACMEScript.md#storage)    |
|                              | [STORAGEREMOVE](#command_storageremove)         | Remove a key/value pair from the [persistent storage](ACMEScript.md#storage) |
| [oneM2M](#commands_onem2m)   | [CREATE](#command_create)                       | Send a CREATE request to a oneM2M CSE                                        |
|                              | [DELETE](#command_delete)                       | Send a DELETE request to a oneM2M CSE                                        |
|                              | [IMPORTRAW](#command_importraw)                 | Create a raw resource in the CSE's resource tree                             |
|                              | [NOTIFY](#command_notify)                       | Send a NOTIFY request to a target                                            |
|                              | [ORIGINATOR](#command_originator)               | Set the originator for following oneM2M requests                             |
|                              | [POA](#command_poa)                             | Assign a URI to a target for requests                                        |
|                              | [REQUESTATTRIBUTES](#command_requestattributes) | Add additional attributes to a request                                       |
|                              | [RETRIEVE](#command_retrieve)                   | Send a RETRIEVE request to a oneM2M CSE                                      |
|                              | [UPDATE](#command_update)                       | Send an UPDATE request to a oneM2M CSE                                       |
| [CSE](#commands_CSE)         | [RESET](#command_reset)                         | Reset and restart the CSE                                                    |
|                              | [SETCONFIG](#command_setconfig)                 | Assign a new value to a configuration setting                                |




---

<a name="commands_basic"></a>
## Basic

The following basic commands for running scripts in general are available.

<a name="command_assert"></a>
### ASSERT

Usage:  
ASSERT &lt;boolean expression>

The ASSERT command will terminate the script if its argument turns out to be false.

Example:
```text
assert [== [cse.type] IN]
```

<a name="command_break"></a>
### BREAK

Usage:  
BREAK &lt;result>\*

Break out of a [WHILE](#command_while) loop. The command may have an optional result argument that is returned as the result of the loop.

Example:
```text
while true
	...
	break aResult
	...
endwhile
```

Example using the [loop](ACMEScript-macros.md#macro_loop) macro.
```text
while [< [loop] 10]
	print [loop]
endwhile
```


<a name="command_case"></a>
### CASE

Usage:  
CASE &lt;match\*

This command starts a CASE block inside a [SWITCH](#command_switch) block. 
If present then the *match* argument will be compared against the argument of the surrounding SWITCH block.
If it matches then the code lines up to the next CASE or [ENDSWITCH](#command_endswitch) are executed.
If multiple CASE statements would match the comparison then only the first matching block is executed.

If the *match* argument is missing then the CASE block is executed when encountered and no previous
CASE statement did match before. It can be used as a default or catch-all block of a [SWITCH](#command_switch).
An empty CASE should always be the last CASE statement in a [SWITCH](#command_switch) block, 
because all the following CASE statements will be skipped.

The *match* argument can be a simplified regular expression for fuzzy comparisons. See the description of the
[match](ACMEScript-macros.md#macro_match) macro for a description of the supported operators and examples.


Example:

```text
switch [aVariable]
	case aValue
		...
	case anotherValue
		...
	case aR*x
		# e.g. matches aRegex
		...
	case
		# always matches
		...
endSwitch
```

There is second form of the CASE statement: When the SWITCH statement does not have a parameter then
CASE statements can have boolean expressions, or any procedure and macro, which, when those evaluate
to *true*, will have their code blocks executed. As with the other format only the first CASE that 
evaluates to *true* is executed.  
This can be used to replace otherwise overly complicated IF code sequences.

Example:

```text
switch
	case [< 4 3]
		print No
	case [> 4 3]
		print Yes
endswitch
```


<a name="command_continue"></a>
### CONTINUE

Usage:  
CONTINUE

Continue with the next iteration of a [WHILE](#command_while) loop.

Example:
```text
while true
	...
	continue
	...
endwhile
```


<a name="command_dec"></a>
### DEC

Usage:  
DEC &lt;variable> &lt;step>\*

This command decrements a numeric variable by the optional value `step`. The default is 1.

Example:
```text
set var 10
dec var
print [var]
# -> 9
```


<a name="command_else"></a>
### ELSE

Usage:  
ELSE

Start the ELSE part of an [IF](#command_if) block.

Example:
```text
if false
	...
else
	print This is the ELSE part
endif
```


<a name="command_endif"></a>
### ENDIF

Usage:  
ENDIF 

End an [IF](#command_if) or [ELSE](#command_else) block. 

Example:
```text
if true
	...
endif
```


<a name="command_endprocedure"></a>
### ENDPROCEDURE

Usage:  
ENDPROCEDURE &lt;result>\*

This command marks the end of a [PROCEDURE](#command_procedure). The command may have an optional result argument that is 
returned as the result of the procedure. The result is stored in the variable [result](ACMEScript-macros.md#macro_result).

Example:
```text
procedure aProcedure
	...
endProcedure aResult

aProcedure
print [result]
# -> aResult
```


<a name="command_endswitch"></a>
### ENDSWITCH

Usage:  
ENDSWITCH

This command marks the end of a [SWITCH](#command_switch) block.


Example:
```text
switch [variable]
	case aValue
		...
	case anotherValue
		...
	case
		...
endSwitch
```


<a name="command_endwhile"></a>
### ENDWHILE

Usage:  
ENDWHILE &lt;result>\*

End a [WHILE](#command_while) loop. The command may have an optional result argument that is returned as the result of the procedure.

Example:
```text
while [< [i] 10]
	...
endWhile aResult
```


<a name="command_if"></a>
### IF

Usage:  
IF &lt;boolean expression>

Check comparison condition and begin a conditional IF block. An IF block may have an optional
[ELSE](#command_else) block that is executed instead in case the [comparison expression](ACMEScript.md#comp_op) 
turns out to be false.


Example:
```text
if [== [response.status] 200]
	...
else
	...
endif
```


<a name="command_inc"></a>
### INC

Usage:  
INC &lt;variable> &lt;step>\*

This command increments a numeric variable by the optional value `step`. The default is 1.

Example:
```text
set var 10
inc var
print [var]
# -> 11
```


<a name="command_log"></a>
### LOG

Usage:  
LOG &lt;message>

Print a message to the debug-level log.

Example:
```text
log Hello, World!
```


<a name="command_logerror"></a>
### LOGERROR

Usage:  
LOGERROR &lt;message>

Print a message to the error-level log.

Example:
```text
LOGERROR Danger, Will Robinson!
```


<a name="command_procedure"></a>
### PROCEDURE

Usage:  
PROCEDURE &lt;name>\*

This command defines a procedure. A procedure is a named sequence of commands that is executed in its own context. 
A procedure may have zero, one, or more arguments, which can be accessed via the [argc](ACMEScript-macros.md#macro_argc) and [argv](ACMEScript-macros.md#macro_argv)  macros. A procedure may also return a result, which is returned to the calling scope, 
see [ENDPROCEDURE](#command_endprocedure) for details.

One can regard a procedure as a script-local command definition.

Also, it is allowed to call other or the same procedure inside a procedure, however it is not allowed to define procedures inside procedures.

Example:
```text
# Define a procedure to double its argument
procedure double
	set x [* [argv 1] 2]
endProcedure [x]

# Call procedure
print [double 21]
```

Procedures may be called like normal commands as well. If they return a value then that is stored in the special 
variable *result*. Using the procedure defined in the previous example, one may call the procedure like
this:

```text
# Call procedure
double 21
print [result]
```

<a name="command_quit"></a>
### QUIT

Usage:  
QUIT &lt;result>\*

Terminate the running script successfully and return an optional result.

Example:
```text
quit aResult
```


<a name="command_quiterror"></a>
### QUITWITHERROR

Usage:  
QUITWITHERROR &lt;result>\*

Terminate the running script with an error and return an optional result.

Example:
```text
quitWithError aResult
```


<a name="command_run"></a>
### RUN

Usage:  
RUN &lt;script name> &lt;arguments>\*

Run another script. The first argument is the name of the script as set in the [name](ACMEScript.md#meta_name) 
[meta tag](ACMEScript.md#meta_tags) of that script. All other arguments are optional, and will be passed on as arguments to the called
script. The called script may return a result, which would then be available via the [result](#ACMEScript-macros.md#macro_result) variable.

Example:
```text
run anotherScript arg1 arg2
print [result]
```


<a name="command_set"></a>
### SET

Usage:   
SET &lt;variable> &lt;value>  
SET &lt;variable>

This command has two different formats:

- SET &lt;variable> &lt;value>  
Set the variable `variable` to the value `value`. The variable is created if it does not exist.
- SET &lt;variable>  
Deletes the variable `variable`.


Example:
```text
set a 21
set b 2
set c [* [a] [b]]
print [c]
# -> 42
set c
```


<a name="command_sleep"></a>
### SLEEP

Usage:  
SLEEP &lt;seconds>

Pause the script execution for `seconds` seconds.

Example:
```text
# sleep for 1.5 seconds
sleep 1.5
```


<a name="command_switch"></a>
### SWITCH

Usage:  
SWITCH &lt;argument>\*

Start a SWITCH block. The argument is then matched against individual [CASE](#command_case) statement. The code block of the first matching 
statement is executed. SWITCH blocks may be nested. A SWITCH block is closed by a [ENDSWITCH](#command_endswitch) command.

Example:
```text
switch [variable]
	case aValue
		...
	case anotherValue
		...
	case aR*x
		# e.g. matches aRegex
		...
	case
		# always matches
		...
endSwitch
```

The SWITCH statement may also not have a parameter. In this case the CASE statements can have
boolean expressions, or any procedure and macro, which, when those evaluate to *true*, will have 
their code blocks executed. As with the other format only the first CASE that evaluates to *true*
is executed.  
This can be used to replace otherwise overly complicated IF code sequences.

Example:

```text
switch
	case [< 4 3]
		print No
	case [> 4 3]
		print Yes
endswitch
```


<a name="command_while"></a>
### WHILE

Usage:  
WHILE &lt;boolean expression>

Start a WHILE loop. The loop is executed as long as the [comparison expression](ACMEScript.md#calc_comp) is true, or until the loop is 
left through a [BREAK](#command_break) command.

Example:
```text
set i = 0
while [< [i] 10]
	inc i
	...
endwhile
```

See also the special variable [loop](ACME-macros.md#macro_loop) for an automated loop variable. It can
be used to replace the variable in the example above:

Example:
```text
while [< [loop] 10]
	...
endwhile
```


---

<a name="commands_console"></a>
## Console

The following commands for working with the CSE's console are available.


<a name="command_clear"></a>
### CLEAR

Usage:  
CLEAR

Clear the console screen.

Example:
```text
clear
```


<a name="command_print"></a>
### PRINT

Usage:  
PRINT &lt;message>

Print a message to the INFO-level log. Basic markdown formatting, like \* and \*\* is supported.

An empty ```print``` command prints an empty line.

Example:
```text
print Hello, World!
print **bold** and *italics*
```


<a name="command_printjson"></a>
### PRINTJSON

Usage:  
PRINTJSON &lt;JSON document>

Print a beautified JSON document to the console.

Example:
```text
printJSON [response.resource]
```


<a name="command_setlogging"></a>
### SETLOGGING

Usage:  
SETLOGGING on | off

Enable or disable the logging to the console. Arguments are `on` and `off`.

Example:
```text
setLogging off
```


---

<a name="commands_storage"></a>
## Storage

The following storage commands for working with the [persistent storage](ACMEScript.md#storage) are available.


<a name="command_storageput"></a>
### STORAGEPUT

Usage:  
STORAGEPUT &lt;key> &lt;value>

Store the `value` with the key `key` in the [persistent storage](ACMEScript.md#storage).

Example:
```text
storagePut aKey avalue
```


<a name="command_storageremove"></a>
### STORAGEREMOVE

Usage:  
STORAGEREMOVE &lt;key>

Remove the key/value pair for the key `key` from the [persistent storage](ACMEScript.md#storage).

Example:
```text
storageRemove aKey
```

---

<a name="commands_onem2m"></a>
## oneM2M

The following oneM2M commands are available.


<a name="command_create"></a>
### CREATE

Usage:  
CREATE &lt;target> &lt;resource>

Send a *create* request to a CSE. `target` can either be a oneM2M target resource, or a supported URL scheme.
`resource` is a valid oneM2M resource, which may start on the same or the next line.

The requests originator must be set before with the [ORIGINATOR](#command_originator) command.

The requests status and response are available through the [response.status](ACMEScript-macros.md#macro_resp_status) and
[response.resource](ACMEScript-macros.md#macro_resp_resource) variables.


Example:
```text
originator CAdmin
create /id-in/cse-in
	{ "m2m:cnt" : 
		{
			"rn": "myCnt"
		}
	}
print [response.status]
print [response.resource]
```


<a name="command_delete"></a>
### DELETE

Usage:  
DELETE &lt;target>

Send a *delete* request to a CSE. `target` can either be a oneM2M target resource, or a supported URL scheme.

The requests originator must be set before with the [ORIGINATOR](#command_originator) command.

The requests status and response are available through the [response.status](ACMEScript-macros.md#macro_resp_status) and
[response.resource](ACMEScript-macros.md#macro_resp_resource) variables.


Example:
```text
originator CAdmin
delete /id-in/cse-in/myCnt
print [response.resource]
```


<a name="command_importraw"></a>
### IMPORTRAW

Usage:  
IMPORTRAW &lt;resource>

Create a raw resource in the CSE. The resource is added to the resource tree without much validation. 
This command is mainly used when importing initial and restoring resources during the startup of the CSE.

`resource` is a valid oneM2M resource, which may start on the same or the next line.
All necessary attributes must be 
present in the provided resource, including the *parentID* (pi) attribute that determines the location in the resource tree.


Example:
```text
# Add an AE resource under the CSEBase
importraw 
	{
	"m2m:ae": {
		"ri":  "CanAE",
		"rn":  "CanAE",
		"pi":  "[cse.ri]",
		"rr":  true,
		"api": "NanAppId",
		"aei": "CanAE",
		"csz": [ "application/json", "application/cbor" ]
	}
	}
```


<a name="command_notify"></a>
### NOTIFY

Usage:  
NOTIFY &lt;target> &lt;resource>

Send a *notify* request to a CSE. `target` can either be a oneM2M target resource, or a supported URL scheme.
`resource` is a valid oneM2M resource, which may start on the same or the next line.

The requests originator must be set before with the [ORIGINATOR](#command_originator) command.

The requests status and response are available through the [response.status](ACMEScript-macros.md#macro_resp_status) and
[response.resource](ACMEScript-macros.md#macro_resp_resource) variables.


Example:
```text
originator CAdmin
notify http://localhost:8080
	{ "m2m:rqp" : 
		{
			"fr"  : "anOriginator",
			"rqi" : "1234",
			"rvi" : "4",
			"rsc" : 2000
		}
	}
print [response.status]
print [response.resource]
```


<a name="command_originator"></a>
### ORIGINATOR

Usage:  
ORIGINATOR &lt;originator>

Set the originator for following oneM2M requests.  
This command also sets the variable [request.originator](ACMEScript-macros.md#macro_req_originator).


Example:
```text
originator CAdmin
delete /id-in/cse-in/myCnt
```


<a name="command_poa"></a>
### POA

Usage:  
POA &lt;target> &lt;targetURI>

Set the point-of-access `targetURI` for a `target`. `target` could be an unknown originator, 
or be used as an alias for a URI.
The list of targets is used to resolve targets in the request commands.

Each call of the `POA` command adds a new `target`/`targetURI` pair.

Example:
```text
POA local http://localhost:8008/id-in
POA cse /id-in/cse-in
```


<a name="command_requestattributes"></a>
### REQUESTATTRIBUTES

Usage:  
REQUESTATTRIBUTES &lt;JSON>

Add additional request attributes to a request. The argument to this command is a JSON 
structure with the attributes. The attributes are added to all following requests until
a new or empty structure is defined with this command.

Some of the most common attributes are recognized (see following list), all others are 
assigned to *filterCriteria*.

> rqi


Example:
```text
requestAttributes
{ 
	"rqi" : "myOwnRequestID"
}
retrieve /id-in/cse-in/myCnt
```


<a name="command_retrieve"></a>
### RETRIEVE

Usage:  
RETRIEVE &lt;target>

Send a *retrieve* request to a CSE. `target` can either be a oneM2M target resource, or a supported URL scheme.

The requests originator must be set before with the [ORIGINATOR](#command_originator) command.

The requests status and response are available through the [response.status](ACMEScript-macros.md#macro_resp_status) and
[response.resource](ACMEScript-macros.md#macro_resp_resource) variables.


Example:
```text
originator CAdmin
retrieve /id-in/cse-in/myCnt
print [response.resource]
```


<a name="command_update"></a>
### UPDATE

Usage:  
UPDATE &lt;target> &lt;resource>

Send an *update* request to a CSE. `target` can either be a oneM2M target resource, or a supported URL scheme.
`resource` is a valid oneM2M resource, which may start on the same or the next line.

The requests originator must be set before with the [ORIGINATOR](#command_originator) command.

The requests status and response are available through the [response.status](ACMEScript-macros.md#macro_resp_status) and
[response.resource](ACMEScript-macros.md#macro_resp_resource) variables.


Example:
```text
originator CAdmin
update /id-in/cse-in/myCnt
	{ "m2m:cnt" : 
		{
			"lbl": [ "aLabel" ]
		}
	}
print [response.status]
print [response.resource]
```

### CSE Commands

<a name="command_reset"></a>
### RESET

Usage:  
RESET

Reset the CSE. Remove all resources, restart the components, and initialize the CSE again.

Example:
```text
# reset the CSE
reset
```

<a name="command_setconfig"></a>
### SETCONFIG

Usage:  
SETCONFIG &lt;configuration> &lt;value> 

Assign a new value to a configuration setting. Some updates may not have an immediate effect.  
See [Configuration](Configuration.md) for the list of configuration names.

**Be careful**: Updating some configurations may render the CSE inoperable.


Example:
```text
# Switch off logging
setConfig logging.level off
```


[← ACMEScript](ACMEScript.md)  
[← README](../README.md)  
