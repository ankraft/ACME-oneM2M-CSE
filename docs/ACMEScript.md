[← README](../README.md) 

# ACMEScript

The \[ACME] CSE supports a simple script language, called ACMEScript, that can be used to configure, execute functions, and control certain aspects of the \[ACME] CSE:

- Import resources during startup.
- CREATE, RETRIEVE, UPDATE, and DELETE resources.
- Send NOTIFICATIONS.
- Update CSE configuration settings.
- Call internal CSE functions.
- Run scheduled script jobs.


[ACMEScript Basics](#basics)  
[Variables and Macros](#variables_macros)  
[Commands](#commands)  
[Calculations and Comparisons](#calc_comp)  
[Context, Scopes, Arguments, and Results](#context_scope)  

See also

- [List of Macros and variables](ACMEScript-macros.md)
- [List of commands](ACMEScript-commands.md)
- [Meta Tags](ACMEScript-metatags.md)



<a name="basics"></a>
## ACMEScript Basics

Scripts are stored in simple text files containing lines with commands that get executed in sequence, one after the other.

A command may have none, one, or multiple arguments.  
Example:

```text
print Hello, World!
```

The `print` command takes the rest of the line and prints the nice greeting message to the log.

Some commands that have a JSON structure as an argument, like [IMPORTRAW](#ACMEScript-commands.md#command_importraw) or [CREATE](ACMEScript-commands.md#command_create), allow to span multiple lines and also to start on the line following the command itself. 

Leading and training white spaces are ignored. Lines that start with `#` and `//` characters are treated as comments and are ignored.  
Example:

```text
# This is a comment
print Hello, World!
```

In ACMEScript everything is a string, but interpreted as a number or boolean value depending on the context. All numbers are of type floating point.


### Loading and Running Scripts

Scripts are stored in and read from the *init* directory. All files with the extension "*.as*" are treated as ACMEScript files and are automatically imported during CSE startup and also during runtime. Updated and new scripts are automatically read again from the
directory.

There are different ways to run scripts:

- They can be run from the console interface with the `R` (Run) command.
- They can be run by a keypress from the console interface (see [@onKey](ACMEScript-metatags.md#meta_onkey)).
- They can be scheduled to run at specific times or dates. This is similar to the Unix cron system (see [@at](ACMEScript-metatags.md#meta_at)).
- They can be scheduled to run at certain events. Currently, the CSE [startup](ACMEScript-metatags.md#meta_onstartup), [restart](ACMEScript-metatags.md#meta_onrestart), and [shutdown](ACMEScript-metatags.md#meta_onshutdown) events are supported.
- They can also be run as a command of the [Upper Tester Interface](Operation.md#upper_tester).


<a name="arguments"></a>
#### Script Arguments

Scripts may have arguments that can be accessed with the [argc](ACMEScript-macros.md#macro_argc) and [argv](ACMEScript-macros.md#macro_argv) macros.

#### Script Prompt

A script may ask for input before it runs. This can be enabled with the [@prompt](ACMEScript-metatags.md#meta_prompt) meta tag. 
The prompt's answer is then assigned as the script's arguments.

**Attention**: The [@prompt](ACMEScript-metatags.md#meta_prompt) meta tag should only be used when human interaction can be ensured. Running
a script with this meta tag, for example, [scheduled](ACMEScript-metatags.md#meta_a) and unattended will cause the script to wait
for user input forever. 

<a name="storage"></a>
### Storing Data

Data can be stored "persistently" during a CSE's runtime. This is intended to pass data across different runs of a script, but not to store data persistently across CSE restarts or reset. The storage format is a simple key/value store.

[Macros](ACMEScript-macros.md#macros_storage) and [commands](commands_storage) help to store, access, check and remove key/values.


<a name="variables_macros"></a>
## Variables and Macros

ACMEScript supports variables and macros. The difference is that variables are assigned during the script's flow, and macros are functions evaluated during runtime, and may also have arguments. Both variables and macros are case insensitive.

Variables are evaluated by wrapping them like this: `${name [<arguments>] }` .

```text
# Assign the string "Hello, World!" to the variable "greeting"
set greeting Hello, World!
print ${greeting}
```

Variables and macros can be nested and are evaluated from the inside out:

```text
set variable greeting
set greeting Hello, World!

# The inner "variable" evaluates to "greeting", 
# and is then taken as the name for the outer variable
print ${${variable}}
```

A macro may have zero, one or more arguments:

```text
# Print the name of the script, which is the script's argument with index 0
print ${argv 0}
```

To print the string "${" one escape the special pattern with a backslash:

```text
print \${datetime} = ${datetime}
```

This line will print:

>${datetime} = 20220107T221625.771604

See also the [list of available macros and variables](ACMEScript-macros.md).



<a name="commands"></a>
## Commands

Commands are built-in operations that perform special functions. They are identified as the first "word" on a line.

Commands are used for control the script flow, perform checks, print messages to the log, execute oneM2M requests, etc. Depending on the command it may have none, one, or multiple arguments.

See also the [list of available commands](ACMEScript-commands.md).


<a name="calc_comp"></a>
## Calculations and Comparisons

ACMEScript has only limited support to do calculations. The only command that supports calculations is the [SET](#command_set) command when using the `=` operator:

```text
# Calculate the answer to everything
set answer = 6 * 7
print ${answer}
```

Some commands have a comparison expression, like the conditions for [IF](#command_if) and [WHILE](#command_while):

```text
# Check answer for correctness
if ${answer} == 42
	print Thanks for all the fish!
endif
```


### Arithmetic Operators

The following arithmetic operators are supported:

| Operator | Description    |
|:--------:|----------------|
|    +     | Addition       |
|    -     | Subtraction    |
|    *     | Multiplication |
|    /     | Division       |
|    %     | Remainder      |
|    ^     | Exponentiation |

Example:
```text
set asnwer = 21 * 2
```

<a name="comp_op"></a>
### Comparison Operators
Some commands have a comparison expression, like the conditions for [IF](#command_if) and [WHILE](#command_while):

| Operator | Description        |
|:--------:|--------------------|
|    ==    | Equality           |
|    !=    | Inequality         |
|    <     | Less than          |
|    <=    | Less or equal than |
|    >     | Greater than       |
|    >=    | Greater than       |
|   true   | Explicit true      |
|  false   | Explicit false     |

Example:
```text
set i = 0
while ${i} < 10
	inc i
endwhile
```


<a name="context_scope"></a>
## Context, Scopes, Arguments, and Results

Each script runs in its own context, which holds the script's state, variables, arguments, result etc. 

Also, a script defines has a stack of scopes. Many commands, when run, define a new scope. This allows for these commands to have arguments and also to return results. An obvious example are [procedures](#command_procedure), but also [WHILE](#command_while) loops run in their own scope and may return results.


### Arguments and results of procedures
```text
# Define a procedure to add two numbers and return the result
procedure add
	set r = ${argv 1} + ${argv 2}
endprocedure ${r}

# Call the procedure with arguments and print the result afterwards
add 16 7
print ${result}

``` 


### Result of a while loop
```text
while ${x} < 100

	...do something...

	if ...error condition...
		# "return" aResult
		break aResult
	endif
# "return" anotherResult if while ends normally
endwhile anotherResult

# The `result` macro returns a scope's result
print ${result}

```


[← README](../README.md) 



upper tester integration