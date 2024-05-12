# ACMEScript - Introduction

The ACME CSE supports a lisp-based scripting language, called ACMEScript, that can be used to configure, execute functions, and control certain aspects of the ACME CSE:

- Import resources during startup.
- CREATE, RETRIEVE, UPDATE, and DELETE resources.
- Send NOTIFICATIONS.
- Update CSE configuration settings.
- Call internal CSE functions.
- Run scheduled script jobs.
- Implement tool scripts for the [Text UI](../setup/TextUI.md).


## ACMEScript Basics

The scripts are stored as normal text files. A script contains so-called [s-expressions](https://en.wikipedia.org/wiki/S-expression){target=_new} that are evaluated one by one and recursively. 

An s-expression is a list of symbols that represent either a value or another s-expression. Usually, the first element in the list is the function that is called to perform a function, and that may have zero, one, or multiple symbols as arguments. If such an argument symbol is executable, then it is recursively evaluated, and its result is taken as the actual argument.

```lisp title="Example"
;; Print "Hello, World" to the console
(print "Hello, World!")

;; Print the result of calculations to the console
(print (+ 1 2))        ;; prints 3
(print (+ 1 (/ 8 4)))  ;; prints 3
```

### Data Types

The following data types are supported by ACMEscript:

- String: for example "Hello, World"
- Number: integer or float, for example 42
- Boolean: `true` or `false`
- JSON: A valid JSON structure
- List or s-expression: a list of symbols or other s-expressions
- Lambda: A nameless function
- nil: An empty list or non-value


### Return Values

Every function and s-expression returns a value. This is usually the function result, but when a list contains multiple s-expressions that are evaluated, then only the last s-expression's result is returned.

```lisp title="Example"
;; First, set the variable a to 3, then use it in a calculation.
;; Then, the result of the calculation is printed.
(print ( (setq a 3) (+ a 4) ))   ;; prints 7
```


### Variables and Function Scopes

Variables are global to a script execution. Variables that are defined globally and that are updated in a function call are updated globally. Variables that are not defined globally but are defined in a function's scope do only exist in the scope of the function and sub-functions calls.

In addition to the normal script variables the runtime environment may pass extra environment (or pre-defined) variables to the script. They are mapped to the script's global variables and can be retrieved like any other global variable (but not updated or deleted). Variables that are set during the execution of a script have precedence over environment variables with the same name.

Variables are removed between script runs.

Variable names are case-sensitive.



### Comments

Comments start with one or two semicolons and continue to the end of the line.



### Quoting

It doesn't matter whether a symbol is another s-expression, a built-in, self-defined or even nameless function, or a variable: If symbols can be evaluated they are evaluated in order. However, sometimes it is necessary to pass an executable symbol without evaluating it first. This is called *quoting* and is achieved by adding a single quote to the beginning of a symbol or list.

Some functions assume that one or more arguments are implicitly quoted, such as the *setq* function that doesn't evaluating its first argument. In this case the argument is not quoted.


```lisp title="Example"
;; Print the string "(+ 1 2)" to the console
(print '(+ 1 2))

;; Set a variable "a" to 42 and print the variable to the console
(setq a 42)  ;; a is not evaluated!
(print a)    ;; a is evaluated. It prints 42
```

Sometimes it is not possible to quote an s-expression or symbol because it is the result of the evaluation of another s-expression. In this case the [quote](ACMEScript-functions.md#quote) function can be used to return a quoted version of an s-expression.

```lisp title="Example"
;; Print the string "(+ 1 2)" to the console
(print (quote (+ 1 2)))
```

### Meta Tags

Meta tags are special commands in a script that are not executed during the runtime of a script, but describe certain capabilities of the script or give, for example, the script a name or provide instructions when a script should be executed.

Meta tags start with a `@` character and may have additional parameters. Meta tags are added as constants to the script's environment, prefixed with "meta.".

Meta tags are described in [a separate documentation](../development/ACMEScript-metatags.md).


## Advanced Topics

### Storing Data

Data can be stored "persistently" during a CSE's runtime. This is intended to pass data across different runs of a script, but not to store data persistently across a CSE restart or reset. The storage format is a simple key/value store.

To store data persistently one may consider to store it in the oneM2M resource tree.

See:  [get-storage](ACMEScript-functions.md#get-storage), [has-storage](ACMEScript-functions.md#has-storage), [put-storage](ACMEScript-functions.md#put-storage)

### Evaluating S-Expressions in Strings and JSON Structures

S-expressions that are enclosed in the pattern `${..}` in a string or JSON structure are evaluated when the string or JSON symbol is evaluated. The result of the s-expression replaces the pattern. 


In the following example the s-expression `(+ 1 2)` is evaluated when the string is processed:

```lisp title="Example"
(print "1 + 2 = ${ + 1 2 }") 	;; Prints "1 + 2 = 3"
```

Evaluation can be locally disabled by escaping the opening part:

```lisp title="Example"
(print "1 + 2 = \\${ + 1 2 }")  ;; Prints "1 + 2 = ${ + 1 2 )}"
```

Evaluation can also be disabled and enabled by using the [evaluate-inline](ACMEScript-functions.md#evaluate-inline) function.

Pattern replacement can be escaped with two backslashes: `\\${..}`.

### "on-error" Function

If the function `on-error` is defined in a script, then this function is executed in case of a script-terminating error, and just before the script terminates because of that error.

In general, the `on-error` function is called as follows:

```lisp title="Example"
(on-error <error type:string> <error message:string)
```

The function is called with two arguments: the error type and the error message.

The following example shows how to define the `on-error` function and how it is called when a division-by-zero error occurs. 

```lisp title="Example"
;; Define the on-error function
(defun on-error (error-type message) (print "Error:" error-type message)) 

;; Cause an division-by-zero error
;; This will implicitly call the function
(/ 0 0)                                      
```

