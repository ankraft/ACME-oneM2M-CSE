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
[Commands, Variables, Macros, and Procedures](#commands_variables_macros_procedures)  
[Arithmetics and Comparisons](#calc_comp)  
[Context, Scopes, Arguments, and Results](#context_scope)  
[Upper Tester Integration](#upper_tester)

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

Scripts are stored in and read from the *init* directory, and from a list of directories that [can be specified](Configuration.md#scripting) in the configuration file. 
All files with the extension "*.as*" are treated as ACMEScript files and are automatically imported during CSE startup and also during runtime. 
Updated and new scripts are automatically read again from that directory.

There are different ways to run scripts:

- They can be run from the console interface with the `R` (Run) command.
- They can be run by a keypress from the console interface (see [onKey](ACMEScript-metatags.md#meta_onkey) meta tag).
- They can be scheduled to run at specific times or dates. This is similar to the Unix cron system (see [at](ACMEScript-metatags.md#meta_at) meta tag).
- They can be scheduled to run at certain events. Currently, the CSE [startup](ACMEScript-metatags.md#meta_onstartup), [restart](ACMEScript-metatags.md#meta_onrestart), and [shutdown](ACMEScript-metatags.md#meta_onshutdown) events are supported.
- They can be run as a receiver of a NOTIFY request from the CSE. See [onNotification](ACMEScript-metatags.md#meta_onnotification) meta tag.
- They can also be run as a command of the [Upper Tester Interface](Operation.md#upper_tester).


<a name="arguments"></a>
#### Script Arguments

Scripts may have arguments that can be accessed with the [argc](ACMEScript-macros.md#macro_argc) and [argv](ACMEScript-macros.md#macro_argv) macros.


#### Quoting strings

In ACMEScript tokens, arguments, number etc. are separated by spaces. If a string or token needs to contain spaces
then they must be wrapped by double quotes. Everything inside the quotes is then treated as a single token.

Example:

```text
print [in "ab cd" "12 ab cd 34"]
# -> true
```

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


<a name="commands_variables_macros_procedures"></a>
## Commands, Variables, Macros, and Procedures

ACMEScript supports variables, macros, and procedures. The difference is that variables are assigned during the script's flow, and
macros are build-in functions evaluated during runtime, and may also have arguments. Procedures are named command sequences that
are defined in the script itself.  

See also the [list of available macros and variables](ACMEScript-macros.md).


### Commands

Commands are built-in operations that perform special functions. They are identified as the first "word" on a line.

Commands are used for control the script flow, perform checks, print messages to the log, execute oneM2M requests, etc. Depending on the command it may have none, one, or multiple arguments.

See also the [list of available commands](ACMEScript-commands.md).

### Variables, Macros, and Procedures
Variables, macros, and procedures are case insensitive, and they are can be called by wrapping them like this: ```[name [<arguments>] ]``` .

```text
# Assign the string "Hello, World!" to the variable "greeting" and print the variable
set greeting Hello, World!
print [greeting]

# Print the current date and time
print [datetime]
```

Variables, macros, and procedures can be nested and are evaluated from the inside out. This way one can perform 
indirections when accessing macros, operations and variables.

```text
set variable greeting
set greeting Hello, World!

# The inner "variable" evaluates to "greeting", 
# and is then taken as the name for the outer variable
print [[variable]]
```

Macros and procedures may have zero, one or more arguments:

```text
# Print the name of the script, which is the script's argument with index 0
print [argv 0]
```
To print the string "[" one must escape the special pattern with a backslash:

```text
print \[datetime] = [datetime]
```

This line will print:

>[datetime] = 20220107T221625.771604

### Procedures
The following example shows the definition of a procedure that returns a value, and its use:

```text
# Define a procedure to double its argument
procedure double
	set x [* [argv 1] 2]
endProcedure [x]

# Call the double procedure and print the result
print [double 21]
# -> 42
```

One important difference for procedures is that they may be called like normal commands as well. They even might return a value, which is 
then stored in the special variable *result*. Using the procedure defined in the previous example, one may call the procedure like
this:

```text
# Call procedure
double 21
print [result]
# -> 42
```

Note that the *result* variable is overwritten with any subsequent procedure call.

### Evaluation Order

Please note, that the evaluation of variables, macros, and procedures happens in this particular order. If evaluating a ```[name]```
expression the ACMEScript interpreter first looks for a variable, then a macro, and lastly a procedure with that name.



<a name="calc_comp"></a>
## Arithmetics and Comparisons

### Arithmetic operations

ACMEScript supports arithmetic calculations based on a functional approach. Arithmetic operators are defined as macros as it can
be seen in the following example.

```text
# Calculate the answer to everything
set answer [* 6 7]
print [answer]
```

There is no operator precedence, but the arithmetic operations can be nested:

```text
# Calculate the answer to everything
set answer [* 6 [+ 3 4] ]
print [answer]
```

Most arithmetic operations are not limited to 2 numerical arguments. Instead, there could be as many arguments to an operation as
necessary:

```text
# Calculate the answer to everything
set answer [* 2 3 3.5 2]
print [answer]
```


The following arithmetic operators are supported:

| Operator | Description        |
|:--------:|--------------------|
|    +     | Addition           |
|    -     | Subtraction        |
|    *     | Multiplication     |
|    /     | Division           |
|    //    | Rounding Division  |
|    %     | Remainder (Modulo) |
|    **    | Exponentiation     |

### Comparisons and boolean expressions

Some commands evaluate the result of a comparison expression, for example [IF](ACMEScript-commands.md#command_if) 
and [WHILE](ACMEScript-commands.md#command_while):

```text
# Check answer for correctness
if [== answer 42]
	print Thanks for all the fish!
endif
```

Comparison expressions work similar to the arithmetic expressions. One can call a macro that performs
the comparison and evaluates either to *true* or *false.

Example for a while loop:

```text
set i = 0
while [< [i] 10]
	inc i
endwhile
```

Comparisons and boolean expressions can be nested like arithmetic expressions, and combined and evaluated 
via the *and*, *or*, and *not* operators. However, there is no short-circuit evaluation of boolean
expressions, ie. all elements of an expression are evaluated.

```text
procedure TrueOrFalse
	print True or False?
endprocedure true

print [or [not false] [< 42 23] [TrueOrFalse] ]
# -> True or False?
# -> true
```


In addition to use comparison operators, one can always use the boolean values *true* and *false* in an expression.

Example:

```text
if true
	print This line is allways executed
endif
```

The following comparison operators are supported:


| Operator | Description        | Number of possible Arguments |
|:--------:|--------------------|:----------------------------:|
|    ==    | Equality           |              2               |
|    !=    | Inequality         |              2               |
|    <     | Less than          |              2               |
|    <=    | Less or equal than |              2               |
|    >     | Greater than       |              2               |
|    >=    | Greater than       |              2               |
| and, &&  | Logical AND        |            1 .. n            |
| or, \|\| | Logical OR         |            1 .. n            |
|  not, !  | Logical NOT        |              1               |



<a name="context_scope"></a>
## Context, Scopes, Arguments, and Results

Each script runs in its own context, which holds a script's state, variables, arguments, result etc. 

Also, a script defines has a stack of scopes. Many commands, when run, define a new scope. This allows for these commands to have arguments and also to return results. An obvious example are [procedures](ACMEScript-commands.md#command_procedure), but also [WHILE](ACMEScript-commands.md#command_while) loops run in their own scope and may return results.


### Arguments and results of procedures

```text
# Define a procedure to add two numbers and return the result
procedure add
	set r [+ [argv 1] [argv 2] ]
endprocedure [r]

# Call the procedure with arguments and print the result
add 16 7
print [result]

``` 

### Use a procedure like a macro

```text
# Define a procedure to add two numbers and return the result
procedure add
	set r  [+ [argv 1] [argv 2] ]
endprocedure [r]

# Call the procedure with arguments and print the result

print [add 16 7]
``` 

### Result of a while loop
```text
while [< x 100]

	...do something...

	if ...error condition...
		# "return" aResult
		break aResult
	endif
	inc x
# "return" anotherResult if while ends normally
endwhile anotherResult

# The `result` macro returns a scope's result
print [result]
```

### "loop" Variable 

For every *while* loop there is an implicit *loop* variable declared that it only valid in the scope of the *while* loop.
It is incremented in every iteration, and can be used inside the *while* loop's comparison and body.

Example:

```text
while [< [loop] 10]
	print [loop]
endwhile
print [loop]
# -> yields an error because "loop" is not defined outside a while loop
```


<a name="upper_tester"></a>
## Upper Tester Integration

ACMEScript is integrated with the [Upper Tester Interface](Operation.md#upper_tester). To enable this a script must have the
[@uppertester](ACMEScript-metatags.md#meta_uppertester) meta tag set. It can then be run by having its
[@name](ACMEScript-metatags.md#meta_name) (and optional script arguments) as the parameter of the upper tester's *X-M2M-UTCMD*
header field:

```text
X-M2M-UTCMD: aScript param1 param2
```

A script result is then passed back in a response in the *X-M2M-UTRSP* header of the response:

```text
X-M2M-UTRSP: aResult
```

[← README](../README.md) 

