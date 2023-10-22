[← README](../README.md)

# ACMEScript

The \[ACME] CSE supports a lisp-based scripting language, called ACMEScript, that can be used to configure, execute functions, and control certain aspects of the \[ACME] CSE:

- Import resources during startup.
- CREATE, RETRIEVE, UPDATE, and DELETE resources.
- Send NOTIFICATIONS.
- Update CSE configuration settings.
- Call internal CSE functions.
- Run scheduled script jobs.
- Implement tool scripts for the [Text UI](TextUI.md).

**Table of Contents**

[ACMEScript Basics](#basics)  
[Loading and Running Scripts](#running)  
[Extras](#extras)  
[Upper Tester Integration](#upper_tester)  

**Further Documentation**

[List of Functions and Variables](ACMEScript-functions.md)  
[Meta Tags](ACMEScript-metatags.md)


<a name="basics"></a>
## ACMEScript Basics

Scripts are stored in normal text files. A script contains so-called [s-expressions](https://en.wikipedia.org/wiki/S-expression) that are evaluated one by one and recursively. 

An s-expression is a list of symbols that represent either a value or another s-expression. Usually, the first element in the list is the function that is called to perform a function, and that may have zero, one, or multiple symbols as arguments. If such an argument symbol is executable, then it is recursively evaluated, and its result is taken as the actual argument.

Examples:

```lisp
;; The following expression prints "Hello, World" to the console
(print "Hello, World!")

;; The following expression prints the result of "1 + 2" to the console
(print (+ 1 2))        ;; prints 3
(print (+ 1 (/ 8 4)))  ;; prints 3
```

### Comments

Comments start with two semicolons (;;) and continue to the end of the line.


### Data Types

The following data types are supported by ACMEscript:

- String: for example "Hello, World"
- Number: integer, float, for example 42
- Boolean: true or false
- JSON: A valid JSON structure
- List or s-expression: a list of symbols or other s-expressions
- Lambda: A nameless function
- nil: An empty list or non-value


### Return Values

Every function and s-expression returns a value. This is usually the function result, but when a list contains multiple s-expressions that are evaluated, then only the last s-expression's result is returned.

Example:

```lisp
;; First, set the variable a to 3, then use it in a calculation.
;; Then, the result of the calculation is printed.
(print ( (setq a 3) (+ a 4) ))   ;; prints 7
```


### Variables and Function Scopes

Variables are global to a script execution. Global variables that are updated in a function call are updated globally. Variables that are not defined globally but are defined in a function's scope do only exist in the scope of the function and sub-functions calls.

In addition to the normal script variables the runtime environment may pass extra environment variables to the script. They are mapped to the script's global variables and can be retrieved like any other global variable (but not updated or deleted). Variables that are set during the execution of a script have precedence over environment variables with the same name.

Variables are removed between script runs.

Variable names are case-sensitive.


### Quoting

It doesn't matter whether a symbol is another s-expression, a built-in, self-defined or even nameless function, or a variable:If symbols can be evaluated they are evaluated in order. However, sometimes it is necessary to pass an executable symbol without evaluating it first. This is called quoting and is achieved by adding a single quote to the beginning of a symbol or list.

Some functions assume that one or more arguments are implicitly quoted, such as the *setq* function that doesn't evaluating its first argument.

Example:

```lisp
;; Print the string "(+ 1 2)" to the console
(print '(+ 1 2)))

;; Set a variable "a" to 42 and print the variable to the console
(setq a 42)  ;; a is not evaluated!
(print a)    ;; a is evaluated
```

Sometimes it is not possible to quote an s-expression or symbol because it is the result of the evaluation of another s-Expression. In this case the [quote](ACMEScript-functions.md#quote) function can be used to return a quoted version of an s-expression.

### Meta Tags

Meta tags are special commands in a script that are not executed during the runtime of a script, but describe certain capabilities of the script or give, for example, the script a name or provide instructions when a script should be executed.

Meta tags start with a **@** character and may have additional parameters. Meta tags are added as constants to the script's environment, prefixed with "meta.".

Meta tags are described in [a separate document](ACMEScript-metatags.md).

---

<a name="running"></a>

## Loading and Running Scripts

Scripts are stored in and are imported from the *init* directory and in sub-directories, which names end with *.scripts*, of the *init* directory. 
One can also specify a [list of directories](Configuration.md#scripting) in the configuration file with additional scripts that will be imported.
All files with the extension "*.as*" are treated as ACMEScript files and are automatically imported during CSE startup and also imported and updated during runtime. 

There are different ways to run scripts:

- Scripts can be run from the console interface with the `R` (Run) command.
- They can also be run by a keypress from the console interface (see [onKey](ACMEScript-metatags.md#meta_onkey) meta tag).
- Scripts can be scheduled to run at specific times or dates. This is similar to the Unix cron system (see [at](ACMEScript-metatags.md#meta_at) meta tag).
- It is possible to schedule scripts to run at certain events. Currently, the CSE  [init](ACMEScript-metatags.md#meta_init), [onStartup](ACMEScript-metatags.md#meta_onstartup), [onRestart](ACMEScript-metatags.md#meta_onrestart), and [onShutdown](ACMEScript-metatags.md#meta_onshutdown) events are supported.
- Scrips can be run as a receiver of a NOTIFY request from the CSE. See [onNotification](ACMEScript-metatags.md#meta_onnotification) meta tag.
- They can also be run as a command of the [Upper Tester Interface](Operation.md#upper_tester).
- Scripts can be integrated as tools in the [Text UI](TextUI.md). See also the available [meta-tags](ACMEScript-metatags.md#_textui) for available tags.


<a name="arguments"></a>
### Script Arguments

Scripts may have arguments that can be accessed with the [argv](ACMEScript-functions.md#argv) function and [argc](ACMEScript-functions.md#argc) variable.

### Script Prompt

A script may ask for input before it runs. This can be enabled with the [@prompt](ACMEScript-metatags.md#meta_prompt) meta tag. 
The prompt's answer is then assigned as the script's arguments.

**Attention**: The [@prompt](ACMEScript-metatags.md#meta_prompt) meta tag should only be used when human interaction can be ensured. Running
a script with this meta tag, for example, [scheduled](ACMEScript-metatags.md#meta_at) or unattended will cause the script to wait forever
for user input. 

### Running Scripts at Startup, Restart, and Shutdown

Whenever a CSE starts or is restarted (or reset) it is necessary to create couple of oneM2M resources and to build a basic resource tree. This is done by running a script that has the [@init](ACMEScript-metatags.md#meta_init) meta tag set. A script with this tag is executed right after the start of many of the internal services during the startup of the *importer* service.

Note that only one script may have the [@init](ACMEScript-metatags.md#meta_init) meta tag set. By default this is the [init.as](../init/init.as) script from the [init](../init) directory.

Right after a CSE finished the start-up or restart, or just before a CSE shuts down the CSE looks for scripts that have the [@onStartup](ACMEScript-metatags.md#meta_onstartup), [@onRestart](ACMEScript-metatags.md#meta_onrestart), or [@onShutdown](ACMEScript-metatags.md#meta_onshutdown) meta tags set, and runs them respectively.

---

<a name="extras"></a>

## Extras

### Storing Data

Data can be stored "persistently" during a CSE's runtime. This is intended to pass data across different runs of a script, but not to store data persistently across CSE restarts or reset. The storage format is a simple key/value store.

To store data persistently one may consider to store this data in the oneM2M resource tree.

See:  [get-storage](ACMEScript-functions.md##get-storage), [has-storage](ACMEScript-functions.md##has-storage), [set-storage](ACMEScript-functions.md#set-storage)

### Evaluating S-Expressions in Strings and JSON Structures

S-expressions that are enclosed in the pattern `${..}` in a string or JSON structure are evaluated when the string or JSON symbol is evaluated. The result of the s-expression replaces the pattern. Pattern replacement can be escaped with two backslashes: `\\${..}`.

In the following example the s-expression `(+ 1 2)` is evaluated when the string is processed:

```lisp
(print "1 + 2 = ${ + 1 2 }")  ;; Prints "1 + 2 = 3"
```

Evaluation can be locally disabled by escaping the opening part:

```lisp
 (print "1 + 2 = \\${ + 1 2 }")  ;; Prints "1 + 2 = ${ + 1 2 )}"
```

Evaluation can also be disabled and enabled by using the [evaluate-inline](ACMEScript-functions.md#evaluate-inline) function.

### "on-error" Function

If the function `on-error` is defined in a script, then this function is executed in case of a script-terminating error, and just before the script terminates because of that error.

The `on-error` function is called as follows:

`(on-error <error type:string> <error message:string)`

Example:

```lisp
;; Define the on-error function
(defun on-error (e m) (print "Error:" e m)) 

;; Cause an division-by-zero error
;; This will implicitly call the function
(/ 0 0)                                      
```

---

<a name="upper_tester"></a>

## Upper Tester Integration

ACMEScript is integrated with the [Upper Tester (UT) Interface](Operation.md#upper_tester). To enable this a script must have the [@uppertester](ACMEScript-metatags.md#meta_uppertester) meta tag set. It can then be run through the UT interface by having its [@name](ACMEScript-metatags.md#meta_name) (and optional script arguments) as the parameter of the upper tester's *X-M2M-UTCMD* header field of a http request:

```text
X-M2M-UTCMD: aScript param1 param2
```

A script result is  passed back in a response in the *X-M2M-UTRSP* header of the response:

```text
X-M2M-UTRSP: aResult
```

[← README](../README.md) 

