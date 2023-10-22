[← README](../README.md)  
[← ACMEScript](ACMEScript.md) 

# ACMEScript - Functions & Variables

<a name="top"></a>

The following built-in functions and variables are provided by the ACMEScript interpreter.

| Type                       | Function                                                | Description                                                                      |
|----------------------------|---------------------------------------------------------|----------------------------------------------------------------------------------|
| [Basic](#_basic)           | [.](#concat)                                            | Return a string of concatenated symbols                                          |
|                            | [argv](#argv)                                           | Get script arguments                                                             |
|                            | [assert](#assert)                                       | Assert a condition                                                               |
|                            | [base64-encode](#base64-encode)                         | Base64-encode a string                                                           |
|                            | [car](#car)                                             | Return the first element from a list                                             |
|                            | [case](#case)                                           | Conditional execution depending on an input value                                |
|                            | [cdr](#cdr)                                             | Return a list with elements from a list, except the first element                |
|                            | [cons](#cons)                                           | Construct a new list                                                             |
|                            | [datetime](#datetime)                                   | Return a timestamp                                                               |
|                            | [defun](#defun)                                         | Define a function                                                                |
|                            | [dec](#dec)                                             | Decrement a variable                                                             |
|                            | [dolist](#dolist)                                       | Loop over a list                                                                 |
|                            | [dotimes](#dotimes)                                     | Loop over a numeric value                                                        |
|                            | [eval](#eval)                                           | Evaluate and execute a quoted list                                               |
|                            | [evaluate-inline](#evaluate-inline)                     | Enable and disable inline string evaluation                                      |
|                            | [get-json-attribute](#get-json-attribute)               | Get a JSON attribute from a JSON structure                                       |
|                            | [has-json-attribute](#has-json-attribute)               | Determine the existence of a JSON attribute in a JSON structure                  |
|                            | [if](#if)                                               | Conditional execution                                                            |
|                            | [in](#in)                                               | Determine whether a symbol is contained in a list, or a string in another string |
|                            | [inc](#inc)                                             | Increment a variable                                                             |
|                            | [index-of](#index-of)                                   | Determine the position of a value in a list,  or string in another string        |
|                            | [is-defined](#is-defined)                               | Test whether a symbol has been defined                                           |
|                            | [json-to-string](#json-to-string)                       | Convert a JSON structure to a string                                             |
|                            | [jsonify](#jsonify)                                     | Escape characters that would otherwise break a JSON structure                    |
|                            | [lambda](#lambda)                                       | Define a nameless function                                                       |
|                            | [length](#length)                                       | Returns length of a string or a list                                             |
|                            | [let\*](#let-star)                                      | Handles multiple variable assignments sequentially                               |
|                            | [list](#list)                                           | Returns a list from its arguments                                                |
|                            | [log](#log)                                             | Print symbols to the log console (log-level *debug*)                             |
|                            | [log-error](#log-error)                                 | Print symbols to the log console (log-level *warning*)                           |
|                            | [lower](#lower)                                         | Returns a lower case copy of a string                                            |
|                            | [match](#match)                                         | Determines whether a string matches a regex                                      |
|                            | [nl](#nl)                                               | Returns a newline character                                                      |
|                            | [nth](#nth)                                             | Returns the n-th element from a list, or the n-th character from a string        |
|                            | [print](#print)                                         | Print symbols to the console                                                     |
|                            | [progn](#progn)                                         | Evaluate and execute symbols and lists                                           |
|                            | [quit](#quit)                                           | Ends the running script and returns a result                                     |
|                            | [quit-with-error](#quit-with-error)                     | Ends the running script with an error status and returns a result                |
|                            | [quote](#quote)                                         | Return a quoted version of an s-expression                                       |
|                            | [random](#random)                                       | Generate a random number                                                         |
|                            | [return](#return)                                       | Early return from a function or while loop                                       |
|                            | [round](#round)                                         | Return a round number                                                            |
|                            | [set-json-attribute](#set-json-attribute)               | Set a JSON attribute in a JSON structure to a new value                          |
|                            | [setq](#setq)                                           | Assigns a value to a variable                                                    |
|                            | [sleep](#sleep)                                         | Sleep during script exection                                                     |
|                            | [slice](#slice)                                         | Returns the slice of a list or string                                            |
|                            | [sp](#sp)                                               | Returns a space character                                                        |
|                            | [string-to-json](#string-to-json)                       | Convert a string to a JSON structure                                             |
|                            | [to-number](#to-number)                                 | Converts a string to a number                                                    |
|                            | [to-string](#to-string)                                 | Returns a string representation of a symbol                                      |
|                            | [to-symbol](#to-symbol)                                 | Converts a string to a symbol                                                    |
|                            | [upper](#upper)                                         | Returns an upper case copy of a string                                           |
|                            | [url-encode](#url-encode)                               | URL-encode a string                                                              |
|                            | [while](#while)                                         | Evaluate an s-expression in a loop                                               |
| [Operations](#_operations) | [Comparison Operations](#comparison-operations)         | List of supported comparison operations                                          |
|                            | [Logical Operations](#logical-operations)               | List of supported logical operations                                             |
|                            | [Mathematical Operations](#mathematical-operations)     | List of supported mathematical operations                                        |
| [CSE](#_cse)               | [clear-console](#clear-console)                         | Clear the console screen                                                         |
|                            | [cse-attribute-info](#cse-atribute-info)                | Return information about one or more matching attributes                         |
|                            | [cse-status](#cse-status)                               | Return the CSE's current status                                                  |
|                            | [get-config](#get-config)                               | Retrieve a CSE's configuration setting                                           |
|                            | [get-loglevel](#get-loglevel)                           | Retrieve the CSE's current log level                                             |
|                            | [get-storage](#get-storage)                             | Retrieve a value from the CSE's internal script-data storage                     |
|                            | [has-config](#has-config)                               | Determine the existence of a CSE's configuration setting                         |
|                            | [has-storage](#has-storage)                             | Determine the existence of a key/value in the CSE's internal script-data storage |
|                            | [log-divider](#log-divider)                             | Add a line to the DEBUG log                                                      |
|                            | [print-json](#print-json)                               | Print a JSON structure to the console                                            |
|                            | [put-storage](#put-storage)                             | Store a symbol in the CSE's internal script-data storage                         |
|                            | [removes-storage](#removes-storage)                     | Removes a key/value pair from the CSE's internal script-data storage             |
|                            | [reset-cse](#reset-cse)                                 | Initiate a CSE reset                                                             |
|                            | [run-script](#run-script)                               | Removes a key/value pair from the CSE's internal script-data storage             |
|                            | [runs-in-ipython](#runs-in-ipython)                     | Determine whether the CSE runs in an iPython environment                         |
|                            | [schedule-next-script](#schedule-next-script)           | Schedule the nest running script and its arguments                               |
|                            | [set-config](#set-config)                               | Set a CSE's configuation setting                                                 |
|                            | [set-console-logging](#set-console-logging)             | Switch on or off console logging                                                 |
| [oneM2M](#_onem2m)         | [create-resource](#create-resource)                     | Send a oneM2M CREATE request                                                     |
|                            | [delete-resource](#delete-resource)                     | Send a oneM2M DELETE request                                                     |
|                            | [import-raw](#import-raw)                               | Directly create a resource in the CSE's resource tree                            |
|                            | [query-resource](#query-resource)                       | Evaluate an advanced query on a oneM2M resource                                  |
|                            | [retrieve-resource](#retrieve-resource)                 | Send a oneM2M RETRIEVE request                                                   |
|                            | [send-notification](#send-notification)                 | Send a oneM2M NOTIFY request                                                     |
|                            | [update-resource](#update-resource)                     | Send a oneM2M UPDATE request                                                     |
| [Text UI](#_textui)        | [open-web-browser](#open-web-browser)                   | Open a web page in the default browser                                           |
|                            | [set-category-description](#set-category-description)   | Set the description for a whole category of scripts                              |
|                            | [runs-in-tui](#runs-in-tui)                             | Determine whether the CSE runs in Text UI mode                                   |
|                            | [tui-notify](#tui-notify)                               | Display a desktop-like notification                                              |
|                            | [tui-refresh-resources](#tui-refresh-resources)         | Force a refresh of the Text UI's resource tree                                   |
|                            | [tui-visual-bell](#tui-visual-bell)                     | Shortly flashes the script's entry in the text UI's scripts list                 |
| [Network](#_network)       | [http](#http)                                           | Send http requests                                                               |
|                            | [ping-tcp-service](#ping-tcp-service)                   | Check the availability of a network service via TCP                              |
| [Variables](#_variables)   | [argc](#argc)                                           | Get number of arguments                                                          |
|                            | [event.data](#var_event_data)                           | For event handlers: An event's payload data                                      |
|                            | [event.type](#var_event_type)                           | For event handlers: An event's event type                                        |
|                            | [notification.originator](#var_notification_originator) | For notification handlers: A notification's originator                           |
|                            | [notification.resource](#var_notification_resource)     | For notification handlers: A notification's body                                 |
|                            | [notification.uri](#var_notification_uri)               | For notification handlers: A notification's target URI                           |
|                            | [tui.autorun](#var_tui_autorun)                         | Set if autorun from the text UI                                                  |
|                            | [tui.theme](#var_tui_theme)                             | Set to the current text UI theme                                                 |

**ASFunctions.as**

In addition more functions are provided in the file [ASFunctions.as](../init/ASFunctions.as). These functions can be included and made available in own scripts with the [include-script](#include-script) function.

---

<a name="_basic"></a>

## Basic Functions

<a name="concat"></a>

### .

`(. [<symbol>]+)`

Concatenate and return the stringified versions of the symbol arguments.

Note, that this function will not add spaces between the symbols. One can use the [nl](#nl) and [sp](#sp) functions to add newlines and spaces.

See also: [nl](#nl), [sp](#sp), [to-string](#to-string)

Example:

```lisp
(. "Time:" sp (datetime))  ;; Returns "Time: 20230308T231049.934630"
```

[top](#top)

---

<a name="argv"></a>

### argv

`(argv [<n:integer>]*)`	

Evaluates to the n-th argument of the script . The index starts a 0, where the 0-th argument is the name 
of the script. If the `argv` function is called without an argument or stand-alone then a string including 
the name of the function and the arguments is returned. 

The number of arguments available is stored in the variable [argc](#argc).


See also: [argc](#argc)

Example:

```lisp
;; Print the script name
(print "The name of the script is:" (argv 0))

;; Print the first argument
(print "The first argument is:" (argv 1))

;; Print script name and all arguments
(print "All arguments:" argv)
```

[top](#top)

---

<a name="assert"></a>
### assert

`(assert <boolean>)`

The `assert` function terminates the script if its argument evaluates to *false*.

Example:
```lisp
(assert (== (get-configuration "cse.type") 
            "IN"))  ;; Terminates when the setting is different from "IN"
```

[top](#top)

---

<a name="base64-encode"></a>

### base64-encode

`(base64-encode <string>)`

This function encodes a string as base64s.

See also: [url-encode](#url-encode)

Example:

```lisp
(base64-encode "Hello, World")  ;; Returns "SGVsbG8sIFdvcmxk"
```

[top](#top)

---

<a name="car"></a>

### car

`(car <list>)`

The `car` function returns the first symbol from a list. It doesn't change the original list.

Note, that a list needs to be quoted when used directly.

See also:  [cdr](#cdr), [nth](#nth)

Example:

```lisp
(car '(1 2 3))  ;; Returns 1
```

[top](#top)

---

<a name="case"></a>

### case

`(case <key:string> (<condition> <s-expression>)*)`

The `case` function implements the functionality of a `switch...case` statement in other programming languages.

The *key* s-expression is evaluated and its value taken for the following comparisons. After this expression a number of  lists may be given. 

Each of these list contains two symbols that are handled in order: The first symbol evaluates to a value that is compared to the result of the *key* s-expression. If there is a match then the second s-expression is evaluated, and then the comparisons are stopped and the *case* function returns.

The special symbol *otherwise* for a *condition* s-expression always matches and can be used as a default or fallback case .

Example:

```lisp
(case aSymbol
    ( 1 (print "Result: 1"))
    ( (+ 1 1) (print "Result: 2"))
    (otherwise (print "Result: something else")))
```

[top](#top)

---

<a name="cdr"></a>

### cdr

`(cdr <list>)`

The `cdr` function returns a list with all symbols from a list except the first symbol. It doesn't change the original list.

Note, that a list needs to be quoted when used directly.

See also:  [car](#car),  [nth](#nth)

Example:
```lisp
(cdr '(1 2 3))  ;; Returns (2 3)
```

[top](#top)

---

<a name="cons"></a>
### cons

`(cons <symbol> <list>)`

The `cons` function adds a new symbol to the front of a list and returns it. It doesn't change the original list.

Note, that a list needs to be quoted when used directly.


Example:
```lisp
(cons 1 2)	          ;; Returns (1 2)
(cons 1 '(2 3))	      ;; Returns (1 2 3)
(cons '(1 2) '(3 4))  ;; Returns ((1 2) 3 4)
```

[top](#top)

---

<a name="datetime"></a>

### datetime

`(datetime [<format:string>])`

The `datetime` function returns the current date and time. As a default, if not argument is provided, the function returns an ISO8901 timestamp. An optional format string can be provided. With this format string one can define the format for the output based on the format defined by Python's [strftime()](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) function.

All timestamps are UTC-based.

Example:

```lisp
(datetime)          ;; Returns a timestamp, e.g. 20230302T221625.771604
(datetime "%H:%M")  ;; Returns, for example, "22:16"
```

[top](#top)

---

<a name="defun"></a>

### defun

`(defun <function name> <parameter list> <function body>)`

The `defun` function defines a new function. 

The first argument to this function is a string and specifies the new function's name. A function definition overrides already user-defined or built-in functions with the same name.

The second argument is a symbol list with argument names for the function. Arguments act as function-local variables that can be used in the function body.

The third argument is an s-expression that is evaluated as the function body. 

The result of a function is the result of the expression that is evaluated last in a function evaluation.

See also: [lambda](#lambda), [return](#return)

Examples:

```lisp
(defun greeting (name)  ;; define the function
    (print "hello" name)) 
(greeting "Arthur")     ;; call the function

;; Fibonacci
(defun fib (n)          ;; Define the function
    (if (< n 2)
        n
        (+ (fib (- n 1)) 
           (fib (- n 2)))
    ))
(fib 10)                ;; Returns 55
```

[top](#top)

---

<a name="dec"></a>

### dec

`(dec <variable> [<value:number>])`

The `dec` function decrements a provided variable. The default for the increment is 1, but can be given as an optional second argument. If this argument is  provided then the variable is decremented by this value. The value can be an integer or a float.

The function returns the variable's new value.

See also: [inc](#inc)

Example:

```lisp
(setq a 1)   ;; Set variable "a" to 1
(dec a)      ;; Decrement variable "a" by 1
(dec a 2.5)  ;; Decrement variable "a" by 2.5
```

[top](#top)

---

<a name="dolist"></a>

### dolist

`(dolist (<loop variable> <list:list or quoted list> [<result variable>]) (<s-expression>+))`

The `dolist` function loops over a list.  
The first arguments is a list that contains a loop variable, a list to iterate over, and an optional
`result` variable. The second argument is a list that contains one or more s-expressions that are executed in the loop.

If the `result variable` is specified then the loop returns the value of that variable, otherwise `nil`.

See also: [dotimes](#dotimes), [while](#while)

Example:

```lisp
(dolist (i '(1 2 3 4 5 6 7 8 9 10))
	(print i))                   ;; print 1..10

(setq result 0)
(dolist (i '(1 2 3 4 5 6 7 8 9 10) result)
	(setq result (+ result i)))  ;; sum 1..10
(print result)                   ;; 55
```

[top](#top)

---

<a name="dotimes"></a>

### dotimes

`(dotimes (<loop variable> <count:number> [<result variable>]) (<s-expression>+))`

The `dotimes` function provides a simple numeric loop functionality.  
The first arguments is a list that contains a loop variable that starts at 0, the loop `count` (which must be a non-negative number), and an optional
`result` variable. The second argument is a list that contains one or more s-expressions that are executed in the loop.

If the `result variable` is specified then the loop returns the value of that variable, otherwise `nil`.

See also: [dolist](#dolist), [while](#while)

Example:

```lisp
(dotimes (i 10)
	(print i))                   ;; print 0..9

(setq result 0)
(dotimes (i 10 result)
	(setq result (+ result i)))  ;; sum 0..9
(print result)                   ;; 45
```

[top](#top)

---

<a name="eval"></a>

### eval

`(eval <quoted list>)`

The `eval` function evaluates and executes a quoted list or symbol.

See also: [parse-string](#parse-string), [progn](#progn), [to-symbol](#to-symbol)

Example:
```lisp
(eval '(print "Hello, World"))  ;; Prints "Hello, World" 
```

[top](#top)

---

<a name="evaluate-inline"></a>

### evaluate-inline

`(evaluate-inline <boolean>)`

With this function one can disable or enable the [evaluation of s-expressions in strings](ACMEScript.md#extras).

Example:

```lisp
(evaluate-inline false)  ;; Disables inline evaluation
(print "1 + 2 = [(+ 1 2)]")  ;; Prints "1 + 2 = [(+ 1 2)]"
```

[top](#top)

---

<a name="get-json-attribute"></a>

### get-json-attribute

`(get-json-attribute <JSON> <key:string>)`

The `get-json-attribute` function retrieves an attribute from a JSON structure via a *key* path. This *key* may be a structured path to access elements deeper down in the JSON structure. There are the following extra elements to access more complex structures:

- It is possible to address a specific element in a list. This is done be  specifying the element as `{n}`.
- If an element is specified as `{}` then all elements in that list are returned in a list.
- If an element is specified as `{*}` and is targeting a dictionary then a single unknown key is skipped in the path. This can be used to skip, for example, unknown first elements in a structure. This is similar but not the same as `{0}` that works on lists.

See also: [has-json-attribute](#has-json-attribute), [set-json-attribute](#set-json-attribute)

Examples:

```lisp
(get-json-attribute { "a" : { "b" : "c" }} "a/b" )     ;; Returns "c"
(get-json-attribute { "a" : [ "b", "c" ]} "a/{0}" )    ;; Returns "b"
(get-json-attribute { "a" : [ "b", "c" ]} "a/{}" )     ;; Returns ( "b" "c" )
(get-json-attribute { "a" : [ "b", "c" ]} "{*}/{0}" )  ;; Returns "b"
```

[top](#top)

---

<a name="has-json-attribute"></a>

### has-json-attribute

`(has-json-attribute <JSON> <key:string>)`

The `has-json-attribute` function determines  whether an attribute exists in a JSON structure for a *key* path. This *key* may be a structured path to access elements deeper down in the JSON structure. See [get-json-attribute](#get-json-attribute) for further details on how to access JSON attributes.

See also: [get-json-attribute](#get-json-attribute), [set-json-attribute](#set-json-attribute)

Examples:

```lisp
(has-json-attribute { "a" : { "b" : "c" }} "a/b" )  ;; Returns true
(has-json-attribute { "a" : { "b" : "c" }} "a/c" )  ;; Returns false
```

[top](#top)

---

<a name="if"></a>

### if

`(if <boolean expression> <s-expression> [<s-expression>])`

The `if` function works like an “if-then-else” statement in other programing languages. The first argument is a boolean expression. If it evaluates to *true* then the second argument is executed. If it evaluates to *false* then the third (optional) argument is executed, if present.

The boolean expression can be any s-expression that evaluates to a boolean value or *nil*, or a list or a string. *nil* values, empty lists, or zero-length strings evaluate to *false*, or to *true* otherwise.

Example:

```lisp
(if (< 1 2)           ;; Evaluates to "true"
    (print "true")    ;; This expression is executed
    (print "false"))  ;; This expression is not executed
```

[top](#top)

---

<a name="in"></a>

### in

`(in <symbol or list> <list or string>)`

The `in` function determines whether a symbol or list is contained in a list, or whether a string is contained in another string. The function returns *true* if this is the case, or *false* otherwise.

See also: [index-of](#index-of)

Example:

```lisp
(in "Hello" "Hello, World")  ;; Returns true
(in "Bye" "Hello, World")    ;; Returns false
(in 1 '(1 2 3))              ;; Returns true
(in '(1 2) '((1 2) (3 4)))   ;; Increment variable "a" by 2.5
```

[top](#top)

---

<a name="inc"></a>

### inc

`(inc <variable symbol> [<value:number>])`

The `inc` function increments a provided variable. The default for the increment is 1, but can be given as an optional second argument. If this argument is  provided then the variable is incremented by this value. The value can be an integer or a float.

The function returns the variable's new value.

See also: [dec](#dec)

Example:

```lisp
(setq a 1)   ;; Set variable "a" to 1
(inc a)      ;; Increment variable "a" by 1
(inc a 2.5)  ;; Increment variable "a" by 2.5
```

[top](#top)

---

<a name="index-of"></a>

### index-of

`(index-of <value> <list or string>)`

The `index-of` function determines the index of a value in a list, or the index of a string in another string. If the second argument is a string then the first argument must be a string as well. The index is 0-based.

The function returns the index as a number, or *nil* if the value could not be found.

See also: [in](#in), [nth](#nth)

Example:

```lisp
(index-of 1 '(1 2 3))            ;; Returns 0
(index-of "a" '("b", "c", "d"))  ;; Returns nil
(index-of "b" "abc")             ;; Returns 1
```

[top](#top)

---

<a name="is-defined"></a>

### is-defined

`(is-defined <symbol>`)

The `is-defined` function tests whether a symbol (ie. a variable, built-in or defined function) is defined.

Example:

```lisp
(setq a 1)       ;; Define variable "a"
(is-defined 'a)  ;; Evaluates to "true".
(is-defined 'b)  ;; Evaluates to "false"
```

Note:

Most of the time the symbol argument needs to be quoted, otherwise the symbol is evaluated first and the function will not work as expected.

[top](#top)

---

<a name="json-to-string"></a>

### json-to-string

`(json-to-string <JSON>`)

The `json-to-string` function returns a JSON structure in a string.

See also: [string-to-json](#string-to-json), [to-number](#to-number), [to-string](#to-string)

Example:

```lisp
(json-to-string { "a" : { "b" : "c" }})  ;; Returns "{\"a\": {\"b\": \"c\"}}"
```

[top](#top)

---

<a name="jsonify"></a>

### jsonify

`(jsonify <string>`)

The `jsonify` function returns a string where characters are escaped that would otherwise break a JSON structure.

See also: [string-to-json](#string-to-json), [to-number](#to-number), [to-string](#to-string)

Example:

```lisp
(jsonify (jsonify "Hello,
World"))  ;; Returns "Hello\nworld"
```

[top](#top)

---

<a name="lambda"></a>

### lambda

`(lambda <parameter list> <function body>)`

The `lambda` function defines a new nameless function. 

It is similar to the [defun](#defun) function, but the difference is that functions defined as lambda functions cannot be called by name. They need to be used directly, assigned to a variable, or passed, for example, in a function call.

The first argument is a symbol list with argument names for the lambda function. Arguments act as function-local variables that can be used in the function body.

The second argument is an s-expression that is evaluated as the function body. 

The result of a lambda function is the result of the expression that is evaluated last in a function evaluation.

See also: [defun](#defun), [return](#return)

Examples:

```lisp
;; Immediate use
((lambda (x) (* x x)) 5)       ;; Returns 25

;; Assign a lambda function to a variable
(setq y (lambda (x) (* x x)))  ;; Define and assign lambda function
(y)                            ;; Returns ( ( x ) ( * x x ) )
((y) 5)                        ;; Returns 25
```

[top](#top)

---

<a name="length"></a>

### length

`(length <string or list>`)

The `length` function returns the length of a string or the number of elements in a list.

Example:

```lisp
(length "Hello, World")  ;; Returns 12
(length '(1 2 3))        ;; Returns 3
```

[top](#top)

---

<a name="let-star"></a>

### let*

`(let* [( <variable> <s-expression> )]+`)

The `let*` function let one assigns values to variables in multiple steps. 

Each assignment consists, like the [setq](#setq) function, of an implicit quoted list with a variable symbol and an s-expression, but differently from the [setq](#setq) function, the `let*` function handles multiple assignments. The assignments are handled sequentially.

Note: The `let` function (without the star), where assignments are handled in parallel is yet not supported.

See also: [setq](#setq)

Example:

```lisp
(let* (a 1)         ;; Assigns 1 to a
      (a (+ a 1)))  ;; Assigns a + 1 = 2 to a
(let* (b 2) (c 3))  ;; Assigns 2 to b and 3 to c
```

[top](#top)

---

<a name="list"></a>

### list

`(list <symbol>+)`

The `list` function returns a list that contains all the symbol arguments.

See also: [cons](#cons)

Example:

```lisp
(list 1 2 3)  ;; Returns ( 1 2 3 )
```

[top](#top)

---

<a name="log"></a>

### log

`(log <s-expression>*)`

The `log` function prints symbols to the logging console with a *debug* log-level. Usually these symbols are strings or numbers, but representations of other data types are supported as well.

The function always returns *nil*.

See also: [log-error](#log-error), [print](#print)

Example:

```lisp
(log "Hello, World")  ;; Prints "Hello, World" to the log
```

[top](#top)

---

<a name="log-error"></a>

### log-error

`(log <s-expression>*)`

The `log-error` function prints symbols to the logging console with an *warning* log-level. Usually these symbols are strings or numbers, but representations of other data types are supported as well.

The function always returns *nil*.

See also: [log](#log), [print](#print)

Example:

```lisp
(log-error "Hello, World")  ;; Prints "Hello, World" to the warning log
```

[top](#top)

---

<a name="lower"></a>

### lower

`(lower <string>`)

The `lower` function returns a lower case copy of the input string.

See also: [upper](#upper)

Example:

```lisp
(lower "Hello, World")  ;; Returns "hello, world"
```

[top](#top)

---

<a name="match"></a>

### match

`(match <string> <regex:string>`)

The `match` function determines whether a string matches a regular expression *regex*.

Note: The default implementation supports a simplified regex operator set:

- `?` : any single character
- `*` : zero or more characters
- `+` : one or more characters
- `\` : Escape an expression operator

Example:

```lisp
(match "aa" "a?") -> true
(match "aa" "b*") -> false
```

[top](#top)

---

<a name="nl"></a>

### nl

`(nl)`

The `nl` function returns a newline character.

See also: [print](#print),  [sp](#sp)

Example:

```lisp
(. "Hello," nl "World")  ;; Returns "Hello,\nWorld"
```

[top](#top)

---

<a name="nth"></a>

### nth

`(nth <index:number> <list or string>`)

The `nth` function returns the n-th element from a list, or the nth character from a string.

The index is 0-based.

See also: [car](#car),  [cdr](#cdr), [index-of](#index-of)

Example:

```lisp
(nth 2 '(1 2 3))        ;; Returns 3
(nth 2 "Hello, World")  ;; Returns "l"
```

[top](#top)

---

<a name="parse-string"></a>

### parse-string

`(parse-string <string with an <s-expression>)`

The `parse-string` function parses a string that contains an s-expression and returns the result as an executable s-expression for further evaluation, e.g. with the [eval](#eval) function.

See also: [eval](#eval), [to-symbol](#to-symbol)

Example:

```lisp
(eval (parse-string "(print \"hello, world\")")) ;; Prints "hello, world" 
```

[top](#top)

---

<a name="print"></a>

### print

`(print <s-expression>*)`

The `print` function prints symbols to the console. Usually these symbols are strings or numbers, but representations of other data types are supported as well.

The function always returns *nil*.

See also: [log](#log), [log-error](#log-error)

Example:

```lisp
(print "Hello, World")  ;; Prints "Hello, World"
```

[top](#top)

---

<a name="progn"></a>

### progn

`(progn <s-expression>+)`

The `progn` function evaluates all provided symbols or lists, and returns the result of the last evaluation.
All other results are ignored.

This function is implicitly used internally when used to evaluate s-expressions.

See also: [eval](#eval)

Example:

```lisp
(progn (print "Hello, World") 1)  ;; Prints "Hello, World" and returns 1
```

[top](#top)

---

<a name="quit"></a>

### quit

`(quit [<symbol>])`

The `quit` function ends the execution of the current script without an *0* error code.

If a symbol is provided for the optional argument its value is taken as the result of the script. Otherwise, *nil* is returned.

See also: [quit-with-error](#quit-with-error)

Example:

```lisp
(quit)             ;; Returns nil
(quit "a result")  ;; Returns "a result"
```

[top](#top)

---

<a name="quit-with-error"></a>

### quit-with-error

`(quit-with-error [<symbol>])`

The `quit-with-error` function ends the execution of the current script with an *-1* error code.

If a symbol is provided for the optional argument its value is taken as the result of the script. Otherwise, *nil* is returned.

See also: [quit](#quit)

Example:

```lisp
(quit-with-error)             ;; Returns nil
(quit-with-error "a result")  ;; Returns "a result"
```

[top](#top)

---

<a name="quote"></a>

### quote

`(quote  <symbol or list>)`

The `quote` function returns a quoted version of the argument. It can be used to get a quoted version of an s-expression or symbol that is the result of another function.

Example:

```lisp
(setq i 0)       ;; Set loop variable
(while (< i 10)  ;; Loop 10 times
    ((print i)   ;; Print to the console
	(inc i)))    ;; Increment loop variable
```

[top](#top)

---

<a name="random"></a>

### random

`(random [<end:number> or <start:number> <end:number>])`

The `random` function generates a random float number in the given range. 

The default for the range, when no argument is given, is [0.0, 1.0]. If one number argument is given then this indicates a range of [0.0, \<end number>]. If two number arguments are given then this indicates a range of [\<start number>, \<end number>].

Example:

```lisp
(random)         ;; Returns, for example, 0.748786
(random 10)      ;; Returns, for example, 4.976338
(random 10 20)   ;; returns, for example, 12.73221
```

[top](#top)

---

<a name="return"></a>

### return

`(return [<s-expression>])`

The `return` function stops the evaluation of a function or [while](#while) loop and returns the evaluation to the caller. The function may return a symbol, or *nil*.

See also: [defun](#defun), [while](#while)

Example:

```lisp
(if (< 1 2)      ;; Evaluates to "true"
    (return 23)  ;; Return the number 23
```

[top](#top)

---

<a name="round"></a>

### round

`(round <value:number> [<precission:number>])`

The `round` function rounds a number to *precision* digits after the decimal point. The default is 0, meaning to round to nearest integer.

Example:

```lisp
(round 3.1415926)    ;; Returns 3
(round 3.1415926 2)  ;; Returns 3.14
```

[top](#top)

---


<a name="set-json-attribute"></a>

### set-json-attribute

`(set-json-attribute <JSON> <key:string> <value)`

The `set-json-attribute` function sets an attribute in a JSON structure via a *key* path to the new *value*. This *key* may be a structured path to access elements deeper down in the JSON structure. See [get-json-attribute](#get-json-attribute) for further details on how to access JSON attributes.

The function doesn't change the original JSON structure, but returns an updated structure.

See also: [get-json-attribute](#get-json-attribute), [has-json-attribute](#has-json-attribute)

Example:

```lisp
(set-json-attribute { "a" : { "b" : "c" }} "a/b" "e")  ;; Returns {"a": {"b": "e"}}
```

[top](#top)

---

<a name="setq"></a>

### setq

`(setq <variable> <s-expression)`

The `setq` function assigns a value to a variable.

See also: [let*](#let-star)

Example:

```lisp
(setq a "Hello, World")  ;; Returns "Hello, World" and sets the variable "a"
```

[top](#top)

---

<a name="sleep"></a>

### sleep

`(sleep <number>)`

The `sleep` function adds a delay to the script execution. The evaluation stops for a number of seconds. The delay could be provided as an integer or float number.

If the script execution timeouts during a sleep, the function is interrupted and all subsequent s-expressions are not evaluated.

The function returns the delay.

Example:

```lisp
(sleep 1.5)  ;; Sleep for 1.5 seconds
```

[top](#top)

---

<a name="slice"></a>

### slice

`(slice <start:number> <end:number> <list or string>)`

The `slice` function returns the slice of a list or a string.

The behavior is the same as slicing in Python, except that both *start* and *end* must be provided. The first argument is the *start* (including) of the slice, the second is the *end* (excluding) of the slice. The fourth argument is the list or string to slice.

Example:

```lisp
(slice 1 2 '(1 2 3))     ;; Returns (2)
(slice 0 -1 "abcde")     ;; Returns "abcd"
(slice -1 99 "abcde")    ;; Returns "e"
(slice 99 100 '(1 2 3))  ;; Returns ()
```

[top](#top)

---

<a name="sp"></a>

### sp

`(sp)`

The `sp` function returns a space character.

See also: [print](#print),  [nl](#nl)

Example:

```lisp
(. "Hello," sp "World")  ;; Returns "Hello, World"
```

[top](#top)

---

<a name="string-to-json"></a>

### string-to-json

`(string-to-json <string>)`

The `string-to-json` function converts a string to a JSON structure and returns it. The string must contain a valid parseable JSON structure.

See also: [json-to-string](#json-to-string), [to-number](#to-number), [jsonify](#jsonify)

Example:

```lisp
(string-to-json "{ \"a\" : { \"b\" : \"c\" }}")  ;; Returns {"a": {"b": "c"}}
```

[top](#top)

---

<a name="to-number"></a>

### to-number

`(to-number <symbol>)`

The `to-number` function converts a string that contains a number to a number symbol and returns it.

See also: [json-to-string](#json-to-string),  [to-string](#to-string)

Example:

```lisp
(to-string '(1 2))  ;; Returns "[1, 2]"
```

[top](#top)

---

<a name="to-string"></a>

### to-string

`(to-string <symbol>)`

The `to-string` function converts a symbol of any of the built-in types to a string representation and returns it.

See also: [json-to-string](#json-to-string), [to-number](#to-number)

Example:

```lisp
(to-string '(1 2))  ;; Returns "[1, 2]"
```

[top](#top)

---

<a name="to-symbol"></a>

### to-symbol

`(to-symbol <string>)`

The `to-symbol` function converts a string to a symbol and returns it. The resulting symbol has the name and value of the input string, but is itself not a string.

See also: [eval](#eval), [from-string](#from-string), [parse-string](#parse-string)

Example:

```lisp
(to-symbol "a-symbol")  ;; Returns the symbol 'a-symbol'
```

[top](#top)

---

<a name="upper"></a>

### upper

`(upper <string>`)

The `upper` function returns an upper case copy of the input string.

See also: [lower](#lower)

Example:

```lisp
(upper "Hello, World")  ;; Returns "HELLO, WORLD"
```

[top](#top)

---

<a name="url-encode"></a>

### url-encode

`(url-encode <string>)`

The `url-encode` function encodes a string so that may be safely used as part of a URL.

See also: [base64-encode](#base64-encode)

Example:

```lisp
(url-encode "Hello, World")  ;; Returns "Hello%2C+World"
```

[top](#top)

---

<a name="while"></a>

### while

`(while <boolean guard> <body s-expression> `)

The `while` function implements a loop functionality.

A `while` loop continues to run when the first *guard* s-expression evaluates to *true*. Then the *body* s-expression is evaluated. After this the *guard* is evaluated again and the the loops continues or the `while` function returns.

The boolean guard can be any s-expression that evaluates to a boolean value or *nil*, or a list or a string. *nil* values, empty lists, or zero-length strings evaluate to *false*, or to *true* otherwise.

The `while` function returns the result of the last evaluated s-expression in the *body*.

See also: [doloop](#doloop), [dotime](#dotimes), [return](#return)

Example:

```lisp
(setq i 0)       ;; Set loop variable
(while (< i 10)  ;; Loop 10 times
    ((print i)   ;; Print to the console
	(inc i)))    ;; Increment loop variable
```

[top](#top)

---

<a name="_operations"></a>

## Operations

<a name="comparison-operations"></a>

### Comparison Operations

The following comparison operations are supported by ACMEScript. They are used like any other function, and return a boolean value.

Example:

```lisp
(if (< 1 2)           ;; Evaluates to "true"
    (print "true")    ;; This expression is executed
    (print "false"))  ;; This expression is not executed
```

Note that the first operant in comparison operations may be a list or a quoted list. Only if the second operant is not a list, too, then the comparison operation is repeated for every member in the first operant's list. The comparison operation evaluates to *true* if any of these comparisons returns *true*.

Example:

```lisp
(== '(1 2 3) 2)  ;; Evaluates to "true"
```



| operation | Description | Example      |
| --------- | ----------- | ------------ |
| == | Equal to | ` (== a b) ;; equal to: a == b` |
| !=, <> | Not equal to | ` (!= a b) ;; equal to: a != b` |
| < | Smaller than | ` (< a b) ;; equal to: a < b` |
| <= | Smaller or equal than | ` (<= a b) ;; equal to: a <= b` |
| > | Greater than | `(> a b) ;; equal to: a > b` |
| >= | Greater or equal than | `(>= a b) ;; equal to: a >= b` |

[top](#top)

---

<a name="logical-operations"></a>

### Logical Operations

The following logical operations are supported by ACMEScript. They are used like any other function, and return a boolean value.

Examples:

```lisp
(or (< 1 2) (>= 4 3) (== 1 1))   ;; Returns true
(and (or true false) (not true)) ;; Returns false
```

Note that the first operant in logical operations may be a list or quoted list. Only if the second operant is not a list, too, then the logical operation is repeated for every member in the first operant's list. The logical operation evaluates to *true* if any of these operations returns *true*.

Example:

```lisp
(and '(false false true) true)  ;; Evaluates to "true"
(and '(false false false) true)  ;; Evaluates to "false"
```



| operation | Description                                      | Example                      |
| --------- | ------------------------------------------------ | ---------------------------- |
| or, \|    | logical *or* of two or more boolean expressions  | (or a b)  ;; a or b          |
| and, &    | logical *and *of two or more boolean expressions | (and a b c) ;; a and b and c |
| not, !    | logical negation or one boolean expression       | (not true)  ;; false         |

[top](#top)

---

<a name="mathematical-operations"></a>

### Mathematical Operations

The following mathematical operations are supported by ACMEScript. They are used like any other function, and return a number value.

Example:

```lisp
(* 6 7)        ;; Returns 42
(* (+ 3 3) 7)  ;; Return 42
```

| operation | Description                                 | Example                     |
| --------- | ------------------------------------------- | --------------------------- |
| +         | Add two or more numbers                     | (+ 1 2 3)  ;; Returns 6     |
| -         | Subtract two or more numbers                | (- 10  1 2 3)  ;; Returns 4 |
| *         | Multiply two or more numbers                | (* 6 7)  ;; Returns 42      |
| /         | Divide two or more numbers                  | (/ 23 5)  ;; Returns 4.6    |
| **        | Calculates the power of two or more numbers | (** 2 3 4)  ;; Returns 4096 |
| %         | Calculates to modulo of two or more numbers | (% 100 21 13) ;; Returns 3  |

[top](#top)

---

<a name="_cse"></a>

## CSE Functions

The following functions provide support to access certain CSE functionalities, configurations, and other runtime aspects.

<a name="clear-console"></a>

### clear-console

`(clear-console)`

The `clear-console` function clears the console screen.

Example:

```lisp
(clear-console)  ;; Clears the console screen
```

[top](#top)

---

<a name="cse-attribute-info"></a>

### cse-attribute-info

`(cse-attribute-info <name:str>)`

Return a list of CSE attribute infos for the attribute `name``. 
The search is done over the short and long names of the attributes applying
a fuzzy search when searching the long names.

			
The function returns a quoted list where each entry is another quoted list 
with the following symbols:
				
- attribute short name
- attribute long name
- attribute type
				
Example:

```lisp
(cse-attribute-info "acop") ;; Returns ( ( "acop" "accessControlOperations" "nonNegInteger" ) )
```

[top](#top)


---

<a name="cse-status"></a>

### cse-status

`(cse-status)`

The `cse-status` function returns the CSE's current running status as an upper-case string. 

Possible return values are:

- STARTING
- RUNNING
- STOPPING 
- STOPPED 
- RESETTING

Example:

```lisp
(cse-status)  ;; Returns "RUNNING"
```

[top](#top)

---

<a name="get-config"></a>

### get-config

`(get-config <key:string>)`

The `get-config` function retrieves a setting from the CSE's internal configuration. The *key* is a configuration name as defined in the [configuration documentation](Configuration.md).

See also: [has-config](#has-config), [set-config](#set-config)

Examples:

```lisp
(get-config "cse.type")    ;; Returns, for example, 1
(get-config "cse.cseID")   ;; Returns, for example, "/id-in"
```

[top](#top)

---

<a name="get-loglevel"></a>

### get-loglevel

`(get-loglevel)`

The `get-loglevel` function retrieves a the CSE's current log level setting. The return value will be one of the following strings:

- "DEBUG"
- "INFO"
- "WARNING"
- "ERROR"
- "OFF"

Example:
```lisp
(get-loglevel)  ;; Return, for example, INFO
```

[top](#top)

---

<a name="get-storage"></a>

### get-storage

`(get-storage <key:string>)`

The `get-storage` function retrieves a value from the CSE's internal script-data storage. The *key* is a unique name of the value.

See also: [has-storage](#has-storage), [put-storage](#put-storage), [remove-storage](#remove-storage)

Examples:

```lisp
(get-storage "aStorageID" "aKey")  ;; Retrieves the value for "aKey" from "aStorageID"
```

[top](#top)

---

<a name="has-config"></a>

### has-config

`(has-config <key:string>)`

The `has-config` function determines whether a setting from the CSE's internal configuration exists. The *key* is a configuration name as defined in the [configuration documentation](Configuration.md).

See also: [get-config](#get-config), [set-config](#set-config)

Examples:

```lisp
(has-config "cse.cseID")     ;; Returns true
(has-config "cse.unknown")   ;; Returns false
```

[top](#top)

---

<a name="has-storage"></a>

### has-storage

`(has-storage <key:string>)`

The `has-storage` function determines whether a value has been stored under the given *key* in the CSE's internal script-data storage.

See also: [get-storage](#get-storage), [put-storage](#put-storage), [remove-storage](#remove-storage)

Examples:

```lisp
(has-storage "aStorageID" "aKey")       ;; Tests whether the key "aKey" exists in "aStorageID"
```

[top](#top)

---

<a name="include-script"></a>

### include-script

`(include-script <script name:string> [<argument:any>]*)`

The `include-script` function runs another ACMEScript script by its *script name* in its own context. Differently to the [run-script](#run-script) function variables, function definitions etc from the script execution are available in the calling script after the script finished.

The function returns the result of the finished script.

See also: [run-script](#run-script). [schedule-next-script](#schedule-next-script)

Example:

```lisp
(include-script "functions" "an argument")  ;; Run the script "functions"
```

[top](#top)

---

<a name="log-divider"></a>

### log-divider

`(log-divider [<message:string>])`

The `log-divider` function inserts a divider line in the CSE's *DEBUG* log. It can help to easily identify the different sections when working with many requests. An optional (short) message can be provided in the argument.

Examples:

```lisp
(log-divider)                 ;; Add a divider
(log-divider "Hello, World")  ;; Add a divider with a centered message
```

[top](#top)

---

<a name="print-json"></a>

### print-json

`(print-json <JSON>)`

The `print-json` function prints a JSON structure with syntax highlighting to the console.

Example:

```lisp
(print-json { "m2m:cnt" : { "rn": "myCnt" }})  ;; Print the JSON structure
```

[top](#top)

---

<a name="put-storage"></a>

### put-storage

`(put-storage <storageID:string> <key:string> <value:symbol>)`

The `put-storage` function inserts or updates a *value* in the CSE's internal script-data storage with the storage ID *storageID*. The *key* is a unique name of the *value*.

See also: [get-storage](#get-storage), [has-storage](#has-storage), [remove-storage](#remove-storage)

Examples:

```lisp
(put-storage "aStorageID" "aKey" "Hello, World")  ;; Inserts or updates the key "aKey" in "aStorageID"
```

[top](#top)

---

<a name="remove-storage"></a>

### remove-storage

`(remove-storage <key:string>)`
`(remove-storage <storageID:string> <key:string>)`

With 2 parameters the `remove-storage` function removes a *key*/*value* pair from the CSE's internal script-data storage with the storage ID *storageID*. The *key* is a unique name of the *value*.

With only 1 parameter the `remove-storage` function removes all *key*/*value* pairs from the CSE's internal script-data storage with the storage ID *storageID*. 

See also: [get-storage](#get-storage), [has-storage](#has-storage), [put-storage](#put-storage)

Examples:

```lisp
(remove-storage "aStorageID" "aKey")  ;; Removes the key and value from storageID
(remove-storage "aStorageID")         ;; Removes all keys and value from storageID
```

[top](#top)

---

<a name="reset-cse"></a>

### reset-cse

`(reset-cse)`

The `reset-cse` function initiates a CSE reset.

The script execution does continue after the CSE finished the reset.

Example:

```lisp
(reset-cse)  ;; Resets the CSE
```

[top](#top)

---

<a name="run-script"></a>

### run-script

`(run-script <script name:string> [<argument:any>]*)`

The `run-script` function runs another ACMEScript script by its *script name* in its own scope. Variables, function definitions etc from the script execution are not available in the calling script.

The function returns the result of the finished script.

See also: [include-script](#include-script), [schedule-next-script](#schedule-next-script)

Example:

```lisp
(setq result (run-script "aScript" "an argument"))  ;; Run the script "aScript" and assign the result
```

[top](#top)

---

<a name="runs-in-python"></a>

### runs-in-ipython

`(runs-in-ipython)`

The `runs-in-ipython` function determines whether the CSE currently runs in an IPython environment, such as Jupyter Notebooks.

Examples:

```lisp
(runs-in-ipython)  ;; Returns true if the CSE runs in an iPython environment
```

[top](#top)

---

<a name="schedule-next-script"></a>

### schedule-next-script

`(schedule-next-script <scriptName:string> <argument:any>*)`

The `schedule-next-script` function schedules the next script that is run after the current script finished. 

This is different from [include-script](#include-script) and [run-script](#run-script) in so far that the context of the current running script is finished and may be called again. This means that a script can schedule itself, which would not be possible otherwise because scripts can only be run one at a time.

See also: [include-script](#include-script), [run-script](#run-script)

Examples:

```lisp
(schedule-next-script "scriptName" "anArgument")  ;; Schedule a script with an argument
```

[top](#top)

---

<a name="set-config"></a>

### set-config

`(set-config <key:string> <value:any>)`

The `set-config` function updates a setting from the CSE's internal configuration. The *key* is a configuration name as defined in the [configuration documentation](Configuration.md).

It is only possible to update an existing setting, but not to create a new one. The *value* type must be equivalent to the setting's type.

See also: [get-config](#get-config), [has-config](#has-config)

Examples:

```lisp
(set-config "cse.checkExpirationsInterval" 1.5)  ;; Set the configuration to 1.5
```

[top](#top)

---

<a name="set-console-logging"></a>

### set-console-logging

`(set-console-logging <boolean>)`

The `set-console-logging` function enables or disables console logging. It does not turn on or off logging in general. [Printing](#print) to the console is not affected.

Example:

```lisp
(set-console-logging false)  ;; Switch off console logging
```

[top](#top)

---



## oneM2M Functions

The following functions provide support for the oneM2M request operations.

<a name="create-resource"></a>

### create-resource

`(create-resource <originator:string> <resource-id:string> <resource:JSON> [request arguments:JSON])`

The `create-resource` function sends a oneM2M CREATE request to a target resource.

The function has the following arguments:

- *originator* of the request

- The target *resource-id*

- The *resource* JSON structure

- Optional: A JSON structure  with additional *request arguments*

The function will provide defaults for the required request arguments (e.g. rvi, rid). These can be overwritten if necessary by setting them in the *request arguments* argument.

The function returns a list:

`(<response status:number> <resource:JSON>)`

- *response status* is the oneM2M Response Status Code (RSC) for the request

- *resource* is the response content

See also: [delete-resource](#delete-resource), [import-raw](#import-raw), [retrieve-resource](#retrieve-resource),  [send-notification](#send-notification),  [update-resource](#update-resource)

Examples:

```lisp
(create-resource "CAdmin" "cse-in"  { "m2m:cnt" : { "rn": "myCnt" }})  
;; Returns ( 2001 { "m2m:cnt" ... } )
(create-resource "CAdmin" "cse-in"  { "m2m:cnt" : { }} { "rvi": "3"})  ;; Provide requestVersionIndicator
;; Returns ( 2001 { "m2m:cnt" ... } )
```

[top](#top)

---

<a name="delete-resource"></a>

### delete-resource

`(delete-resource <originator:string> <resource-id:string> [request arguments:JSON])`

The `delete-resource` function sends a oneM2M DELETE request to a target resource.

The function has the following arguments:

- *originator* of the request
- The target *resource-id*
- Optional: A JSON structure  with additional *request arguments*

The function will provide defaults for the required request arguments (e.g. rvi, rid). These can be overwritten if necessary by setting them in the *request arguments* argument.

The function returns a list:

`(<response status:number> <resource:JSON>)`

- *response status* is the oneM2M Response Status Code (RSC) for the request

- *resource* is the response content (usually *nil* if successful)

See also: [create-resource](#create-resource), [retrieve-resource](#retrieve-resource), [send-notification](#send-notification), [update-resource](#update-resource)

Examples:

```lisp
(delete-resource "CAdmin" "cse-in/myCnt")  
;; Returns ( 2002 { "m2m:cnt" ... } )
(delete-resource "CAdmin" "cse-in/myCnt" { "rvi": "3"})  ;; Provide requestVersionIndicator
;; Returns ( 2002 { "m2m:cnt" ... } )
```

[top](#top)

---

<a name="import-raw"></a>

### import-raw

`(import-raw <originator:string> <resource:JSON>)`

The `import-raw` function creates a resource in the CSE without using the normal procedures when handling a [CREATE request](#create-resource). The resource is added to the resource tree without much validation.

This function is primarily used when importing initial resources, and when restoring resources during the [startup](ACMEScript-metatags.md#meta_init) of the CSE.

`resource` is a valid oneM2M resource. All necessary attributes must be present in that resource, including the *parentID* ( *pi* ) attribute that determines the location in the resource tree.

The function returns a list:

`(<response status:number> <resource:JSON>)`

- *response status* is the oneM2M Response Status Code (RSC) for the request

- *resource* is the response content (usually *nil* if successful)

Example:

```lisp
;; Add an AE resource under the CSEBase
(import-raw 
    "CmyAE"                                      ;; Originator
    { "m2m:ae": {
        "ri":  "CmyAE",
        "rn":  "CmyAE",
        "pi":  "${ (get-config \"cse.ri\") }",  ;; Get the CSE's resource ID from the configuration
        "rr":  true,
        "api": "NmyAppId",
        "aei": "CmyAE",
        "csz": [ "application/json", "application/cbor" ]
    }})
```

[top](#top)

---

<a name="query-resource"></a>

### query-resource

`(query-resource <query:quoted s-expression> <resource:JSON>)`

The `query-resource` function evaluates a *query* for the attributes in the *resource* structure.

The function has the following arguments:

- *query* to evaluate. This query must be quoted and follows oneM2M's advanced query specification. the unknown symbols in the query are replaced by the resource's attribute values during the evaluation.
    Only a limited set boolean and comparison operators are allowed in the query.
- A oneM2M resource as a JSON structure.

The function returns a boolean indicating the query result.

See also: [get-json-attribute](#get-json-attribute)

Examples:

```lisp
;; Returns true
(query-resource 
	'(& (> x 100) (== rn "cnt1234"))
	{ "m2m:cnt": {
		"rn": "cnt1234",
	  	"x": 123
	}})
```

[top](#top)

---

<a name="retrieve-resource"></a>

### retrieve-resource

`(retrieve-resource <originator:string> <resource-id:string> [request arguments:JSON])`

The `retrieve-resource` function sends a oneM2M RETRIEVE request to a target resource.

The function has the following arguments:

- *originator* of the request
- The target *resource-id*
- Optional: A JSON structure  with additional *request arguments*

The function will provide defaults for the required request arguments (e.g. rvi, rid). These can be overwritten if necessary by setting them in the *request arguments* argument.

The function returns a list:

`(<response status:number> <resource:JSON>)`

- *response status* is the oneM2M Response Status Code (RSC) for the request

- *resource* is the response content (usually the target resource if successful)

See also: [create-resource](#create-resource),  [delete-resource](#delet-resource), [send-notification](#send-notification), [update-resource](#update-resource)

Examples:

```lisp
(retrieve-resource "CAdmin" "cse-in/myCnt")  
;; Returns ( 2000 { "m2m:cnt" ... } )
(retrieve-resource "CAdmin" "cse-in/myCnt" { "rvi": "3"})  ;; Provide requestVersionIndicator
;; Returns ( 2000 { "m2m:cnt" ... } )
```

[top](#top)

---

<a name="send-notification"></a>

### send-notification

`(send-notification <originator:string> <resource-id:string> <notification:JSON> [request arguments:JSON])`

The `send-notification` function sends a oneM2M NOTIFY request to a target resource.

The function has the following arguments:

- *originator* of the request

- The target *resource-id*

- The *notification* JSON structure

- Optional: A JSON structure  with additional *request arguments*

The function will provide defaults for the required request arguments (e.g. rvi, rid). These can be overwritten if necessary by setting them in the *request arguments* argument.

The function returns a list:

`(<response status:number> <resource:JSON>)`

- *response status* is the oneM2M Response Status Code (RSC) for the request

- *resource* is the response content

See also:  [create-resource](#create-resource), [delete-resource](#delete-resource), [retrieve-resource](#retrieve-resource), [update-resource](#update-resource), 

Example:

```lisp
(send-notification "CAdmin" "cse-in/myAE"  { "m2m:sgn" : { ... }})  ;; Returns notification result
```

[top](#top)

---

<a name="update-resource"></a>

### update-resource

`(update-resource <originator:string> <resource-id:string> <resource:JSON> [request arguments:JSON])`

The `update-resource` function sends a oneM2M UPDATE request to a target resource.

The function has the following arguments:

- *originator* of the request

- The target *resource-id*

- The *resource* JSON structure

- Optional: A JSON structure  with additional *request arguments*

The function will provide defaults for the required request arguments (e.g. rvi, rid). These can be overwritten if necessary by setting them in the *request arguments* argument.

The function returns a list:

`(<response status:number> <resource:JSON>)`

- *response status* is the oneM2M Response Status Code (RSC) for the request

- *resource* is the response content

See also:  [create-resource](#create-resource), [delete-resource](#delete-resource), [retrieve-resource](#retrieve-resource), [send-notification](#send-notification), 

Examples:

```lisp
(update-resource "CAdmin" "cse-in"  { "m2m:cnt" : { "mni": 10 }})  
;; Returns ( 2004 { "m2m:cnt" ... } )
(update-resource "CAdmin" "cse-in"  { "m2m:cnt" : { "mni": 10 }} { "rvi": "3"})  
;; Provide requestVersionIndicator
;; Returns ( 2004 { "m2m:cnt" ... } )
```

[top](#top)

---

<a name="_textui"></a>

## Text UI

---

<a name="open-web-browser"></a>

### open-web-browser

`(open-web-browser <url:string>)`

The `open-web-browser` function opens a web browser with the given URL.

Examples:

```lisp
;; Opens the web browser with the URL "http://www.onem2m.org"
(open-web-browser "http://www.onem2m.org")  
```

[top](#top)

---

<a name="set-category-description"></a>

### set-category-description

`(set-category-description <category:string> <description:string>)`

The `set-category-description` function sets the description for a whole category in the CSE's Text UI.

The description may contain Markdown formatting.

Examples:

```lisp
;; Sets the description for the category "myCategory"
(set-category-description "myCategory" "My category description")
```

[top](#top)

---

<a name="runs-in-tui"></a>

### runs-in-tui

`(runs-in-tui)`

The `runs-in-tui` function determines whether the CSE currently runs in Text UI mode.

Examples:

```lisp
(runs-in-tui)  ;; Returns true if the CSE runs in Text UI mode
```

[top](#top)

---

<a name="tui-notify"></a>

### tui-notify

`(tui-notify <message:str> [<title:str>] [<severity>:str>] [<timeout:float>])`

Show a desktop-like notification in the TUI.

This function is only available in TUI mode. It has the following arguments:

- message: The message to show.
- title: (Optional) The title of the notification.
- severity: (Optional) The severity of the notification. This can be one of the following values:
  - information (the default)
  - warning
  - error
- timeout: (Optional) The timeout in seconds after which the notification will disappear again. If not specified, the notification will disappear after 3 seconds.

If one of the optional arguments needs to be left out, a *nil* symbol must be used instead.
The function returns NIL.

Examples:

```lisp
(tui-notify "a message")                ;; Displays "a message" in an information notification for 3 seconds
(tui-notify "a message" "a title")      ;; Displays "a message" with title "a title in an information notification for 3 seconds
(tui-notify "a message")                ;; Displays "a message" in an information notification for 3 seconds
(tui-notify "a message" nil "warning")  ;; Displays "a message" in a warning notification, no title
(tui-notify "a message" nil nil 10)     ;; Displays "a message" in an information notification, no title, for 3 seconds

```

[top](#top)

---

<a name="tui-refresh-resources"></a>

### tui-refresh-resources

`(tui-refresh-resources)`

The `tui-refresh-resources` function refreshes the resources in the CSE's Text UI.

Examples:

```lisp
(tui-refresh-resources)  ;; refreshes the resource tree
```

[top](#top)

---

<a name="tui-visual-bell"></a>

### tui-visual-bell

`(tui-visual-bell)`

The `tui-visual-bell` function shortly flashes the script's entry in the scripts' list/tree.

Examples:

```lisp
(tui-visual-bell)  ;; Flashes the script's name
```

[top](#top)

---

<a name="_network"></a>

## Network

<a name="http"></a>

### http

`(http <operation:quoted symbol> <url:string> [<headers:JSON or nil>] [<body:string or JSON>])`

The `http` function sends an http request to an http server.

The function has the following arguments:

- *operation* of the request. This is one of the following supported quoted symbols: get, post, put, delete, patch

- The target server's *url*. This is a string with a valid URL.

- Optional: A JSON structure of header fields. Each header field is a JSON attribute with the name of the header field and its value. If the optional *body* argument is present then this argument must be present as well, ie. with at least an empty JSON structure or the *nil* symbol.

- Optional: The http request's body, which could be a string or a JSON structure. 

The function returns a list:

`(<http status:number> <response body:JSON> <response headers:list of header fields)`

- *http status* is the htttp status code for the request

- *response body* is the response content

- *response headers* is a list of header fields. The format of these header fields is the same as in the request above.

Examples:

```lisp
;; Retrieve a web page
(http 'get "https://www.onem2m.org")

;; Send a oneM2M CREATE request manually
(http 'post "http://localhost:8080/cse-in"   ;; Operation and URL
	  { "X-M2M-RI":"1234",                   ;; Header fields
        "X-M2M-RVI": "4",
        "X-M2M-Origin": "CAdmin",
		"Content-type": "application/json;ty=3" }
      { "m2m:cnt": {                         ;; Body
          "rn": "myCnt"}})
```

[top](#top)

---

<a name="ping-tcp-service"></a>

### ping-tcp-service

`(ping-tcp-server <hostname:string> <port:number> [<timeout:number>])`

The `ping-tcp-service`function tests the availability and reachability of a TCP-based network service.

It has the following arguments:

- The *hostname* of the target service. This can be a hostname or an IP address.
- The *port* of the target service. This is a number.
- Optional: The request *timeout* in seconds. The default is 5 seconds.

The function returns a boolean value.

Examples:

```lisp
(ping-tcp-service "localhost" 8080 2)  
;; Returns true if the service is reachable. Timeout after 2 seconds.
```

[top](#top)

---

<a name="_variables"></a>

## Variables

<a name="var_argc"></a>

### argc

`argc`

Evaluates to the number of elements in [argv](#argv). A script called with no arguments still has
`argc` set to 1, because the name of the script is always the first element in [argv](#argv).

See also: [argv](#argv)

Example:

```lisp
(if (> argc 2)
    ((log-error "Wrong number of arguments")
     (quit-with-error)))
```

[top](#top)

---

<a name="var_event_data"></a>

### event.data

`event.data`

Evaluates to the payload data of an event. This could be, for example, the string representation in case of an *onKey* event.

Note: This variable is only set when the script was invoked by an event.

See also: [event.type](#var_event_type)

Example:

```lisp
(if (== event.type "onKey")     ;; If the event is "onKey"
    (print "Key:" event.data))  ;; Print the pressed key
```

[top](#top)

---

<a name="var_event_type"></a>

### event.type

`event.type`

Evaluates to the type of an event. This could be, for example, *"onKey"* in case of an *onKey* event.

Note: This variable is only set when the script was invoked by an event.

See also: [event.data](#var_event_data)

Example:

```lisp
(if (== event.type "onKey")     ;; If the event is "onKey"
    (print "Key:" event.data))  ;; Print the pressed key
```

[top](#top)

---

<a name="var_notification_originator"></a> 

### notification.originator

The `notification.originator` variable is set when a script is called to process a notification request. 

It contains the notification's originator.

Example:

```lisp
(print notification.originator)
```

[top](#top)

---

<a name="var_notification_resource"></a> 

### notification.resource

The `notification.resource` variable is set when a script is called to process a notification request. 

It contains the notification's JSON body.

Example:

```lisp
(print notification.resource)
```

[top](#top)

---

<a name="var_notification_uri"></a> 

### notification.uri

The `notification.uri` variable is set when a script is called to process a notification request. 

It contains the notification's target URI.

Example:

```lisp
(print notification.uri)
```

[top](#top)

---

<a name="var_tui_autorun"></a>

### tui.autorun

`tui.autorun`

Evaluates to *true* if the script was started as an "autorun" script. This is the case when the `@tuiAutoRun` meta tag is set
in a script.


See also: [@tuiAutoRun](ACMEScript-metatags.md#meta_tuiAutoRun)

Note: This variable is only set when the script is run from the text UI.

Example:

```lisp
(if (is-defined 'tui.autorun)     ;; If the variable is defined
	(if (== tui.autorun true)     ;; If the script is an autorun script
        (print "Autorun: True")))  ;; Print a message
```

[top](#top)

---

<a name="var_tui_theme"></a>

### tui.theme

`tui.theme`

Evaluates to the state of the current theme of the text UI. This can be either *light* or *dark*.


Example:

```lisp
(print "Theme: " tui.theme)  ;; Print the theme name
```

[top](#top)

---

[← ACMEScript](ACMEScript.md)  
[← README](../README.md)  

