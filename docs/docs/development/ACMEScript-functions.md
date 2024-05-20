# ACMEScript - Functions

This section provides an overview of the functions that are available in ACMEScript. 


## Basic Functions

### . (concat)

`(. [<symbol>]+)`

Concatenate and return the stringified versions of the symbol arguments.

!!! Note
	This function will not add spaces between the symbols. One can use the [nl](#nl) and [sp](#sp) functions to add newlines and spaces.

!!! see-also "See also"
	[nl](#nl), [sp](#sp), [to-string](#to-string)

```lisp title="Example"
(. "Time:" sp (datetime))  ;; Returns "Time: 20230308T231049.934630"
```

---

### all

`(all <boolean>+ | <list of <boolean>+ >)`

The `all` function returns *true* if all of the *boolean* expressions evaluate to *true*. If a *list of boolean* expressions is provided then the function returns *true* if all of the expressions in the list evaluate to *true*.

!!! see-also "See also"
	[any](#any)

```lisp title="Examples"
(all (< 1 2) (< 2 3))    ;; Returns true
(all (< 1 2) (< 2 1))    ;; Returns false
(all ((< 1 2) (< 2 3)))  ;; Returns true
```

---

### any

`(any <boolean>+ | <list of <boolean>+ >)`

The `any` function returns *true* if at least one of the *boolean* expression evaluates to *true*. If a *list of boolean* expressions is provided then the function returns *true* if at least one of the expressions in the list evaluates to *true*.

!!! see-also "See also"
	[all](#all)

```lisp title="Examples"
(any (< 1 2) (< 2 1))    ;; Returns true
(any (< 1 2) (< 2 3))    ;; Returns true
(any (< 2 1) (< 3 2))    ;; Returns false
(any ((< 1 2) (< 2 1)))  ;; Returns true
```


---

### argv

`(argv [<n:integer>]*)`	

Evaluates to the n-th argument of the script. The index starts a `0`, where the 0-th argument is the name 
of the script. If the `argv` function is called without an argument or stand-alone then a string including 
the name of the function and the arguments is returned. 

The number of arguments available is stored in the variable [argc](../development/ACMEScript-variables.md#argc).

!!! see-also "See also"
	[argc](../development/ACMEScript-variables.md#argc)

```lisp title="Example"
;; Print the script name
(print "The name of the script is:" (argv 0))

;; Print the first argument
(print "The first argument is:" (argv 1))

;; Print script name and all arguments
(print "All arguments:" argv)
```

---

### assert

`(assert <boolean>)`

The `assert` function terminates the script if its argument evaluates to *false*.

```lisp title="Example"
(assert (== (get-configuration "cse.type") 
			"IN"))  ;; Terminates when the setting is different from "IN"
```

---

### base64-encode

`(base64-encode <string>)`

This function encodes a string as base64.

!!! see-also "See also"
	[url-encode](#url-encode)

```lisp title="Example"
(base64-encode "Hello, World")  ;; Returns "SGVsbG8sIFdvcmxk"
```

---

### block

`(block <name:string> <s-expression>+)`

The `block` function executes a number of expressions in a named context. The first argument is a string that specifies the block's name. 
The following arguments are s-expressions that are executed in the block.

The result of the last expression is returned. A block can be exited early with the [return-from](#return-from) function.

!!! see-also "See also"
	[return-from](#return-from)

```lisp title="Examples"
(block "myBlock" 1 2 3)  ;; Returns 3
(block "myBlock" 1 (return-from "myBlock" 2) 3)  ;; Returns 2
```

One can use the `block` function to implement *break* and *continue* functionality in loops:

```lisp title="Examples"
;; Example for a break block
;; The following example breaks the loop when the value of "i" is 5
(block break
	(dotimes (i 10)
		((print i) 
		(if (== i 5) 
			(return-from break)))))

;; Example for a continue block
;; The following example skips the value of "i" when it is 5
(dotimes (i 10)
	(block continue
		(if (== i 5) 
			(return-from continue))
		(print i)))
```

---

### car

`(car <list>)`

The `car` function returns the first symbol from a list. It doesn't change the original list.

!!! note
	A list needs to be quoted when used directly.

!!! see-also "See also"
	[cdr](#cdr), [nth](#nth)

```lisp title="Example"
(car '(1 2 3))  ;; Returns 1
```

---

### case

`(case <key:string> (<condition> <s-expression>)*)`

The `case` function implements the functionality of a `switch...case` statement in other programming languages.

The *key* s-expression is evaluated and its value taken for the following comparisons. After this expression a number of lists may be given. 

Each of these list contains two symbols that are handled in order: 

- The first symbol evaluates to a value that is compared to the result of the *key* s-expression. 
- If there is a match then the second s-expression is evaluated, and then the comparisons are stopped and the *case* function returns.

The special symbol `otherwise` for a *condition* s-expression always matches and can be used as a default or fallback case .

```lisp title="Example"
(case aSymbol
	( 1 (print "Result: 1"))
	( (+ 1 1) (print "Result: 2"))
	(otherwise (print "Result: something else")))
```

---

### cdr

`(cdr <list>)`

The `cdr` function returns a list with all symbols from a list except the first symbol. It doesn't change the original list.

!!! note
	A list needs to be quoted when used directly.

!!! see-also "See also"
	[car](#car),  [nth](#nth)

```lisp title="Example"
(cdr '(1 2 3))  ;; Returns (2 3)
```

---

### cons

`(cons <symbol> <list>)`

The `cons` function adds a new symbol to the front of a list and returns it. It doesn't change the original list.

!!! Note
	A list needs to be quoted when used directly.

```lisp title="Examples"
(cons 1 2)	          ;; Returns (1 2)
(cons 1 '(2 3))	      ;; Returns (1 2 3)
(cons '(1 2) '(3 4))  ;; Returns ((1 2) 3 4)
```

---

### datetime

`(datetime [<format:string>])`

The `datetime` function returns the current date and time. As a default, if not argument is provided, the function returns an ISO8901 timestamp. An optional format string can be provided. With this format string one can define the format for the output based on the format defined by Python's [strftime()](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior){target=_new} function.

All timestamps are UTC-based.

```lisp title="Examples"
(datetime)          ;; Returns a timestamp, e.g. 20230302T221625.771604
(datetime "%H:%M")  ;; Returns, for example, "22:16"
```

---

### defun

`(defun <function name> <parameter list> <function body>)`

The `defun` function defines a new function. 

The first argument to this function is a string and specifies the new function's name. A function definition overrides already user-defined or built-in functions with the same name.

The second argument is a symbol list with argument names for the function. Arguments act as function-local variables that can be used in the function body.

The third argument is an s-expression that is evaluated as the function body. 

The result of a function is the result of the expression that is evaluated last in a function evaluation.

!!! see-also "See also"
	[lambda](#lambda), [return](#return)

```lisp title="Example"
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

---

### dec

`(dec <variable> [<value:number>])`

The `dec` function decrements a variable. The default for the increment is 1, but can be given as an optional second argument. If this argument is  provided then the variable is decremented by this value. The value can be an integer or a float.

The function returns the variable's new value.

!!! see-also "See also"
	[inc](#inc)

```lisp title="Examples"
(setq a 1)   ;; Set variable "a" to 1
(dec a)      ;; Decrement variable "a" by 1
(dec a 2.5)  ;; Decrement variable "a" by 2.5
```

---

### dolist

`(dolist (<loop variable> <list:list or quoted list> [<result variable>]) (<s-expression>+))`

The `dolist` function loops over a list.  
The first arguments is a list that contains a loop variable, a list to iterate over, and an optional
`result` variable. The second argument is a list that contains one or more s-expressions that are executed in the loop.

If the `result variable` is specified then the loop returns the value of that variable, otherwise `nil`.

!!! see-also "See also"
	[dotimes](#dotimes), [while](#while)

```lisp title="Examples"
(dolist (i '(1 2 3 4 5 6 7 8 9 10))
	(print i)                   ;; print 1..10

(setq result 0)
(dolist (i '(1 2 3 4 5 6 7 8 9 10) result)
	(setq result (+ result i)))  ;; sum 1..10
(print result)                   ;; 55
```

---

### dotimes

`(dotimes (<loop variable> <count:number> [<result variable>]) (<s-expression>+))`

The `dotimes` function provides a simple numeric loop functionality.  
The first arguments is a list that contains a loop variable that starts at 0, the loop `count` (which must be a non-negative number), and an optional
`result` variable. The second argument is a list that contains one or more s-expressions that are executed in the loop.

If the `result variable` is specified then the loop returns the value of that variable, otherwise `nil`.

!!! see-also "See also"
	[dolist](#dolist), [while](#while)

```lisp title="Examples"
(dotimes (i 10)
	(print i)                   ;; print 0..9

(setq result 0)
(dotimes (i 10 result)
	(setq result (+ result i)))  ;; sum 0..9
(print result)                   ;; 45
```

---

### eval

`(eval <quoted list>)`

The `eval` function evaluates and executes a quoted list or symbol.

!!! see-also "See also"
	[parse-string](#parse-string), [progn](#progn), [to-symbol](#to-symbol)

```lisp title="Example"
(eval '(print "Hello, World"))  ;; Prints "Hello, World" 
```

---

### evaluate-inline

`(evaluate-inline <boolean>)`

With this function one can disable or enable the [evaluation of s-expressions in strings](../development/ACMEScript.md#evaluating-s-expressions-in-strings-and-json-structures).

```lisp title="Example"
(evaluate-inline false)  ;; Disables inline evaluation
(print "1 + 2 = [(+ 1 2)]")  ;; Prints "1 + 2 = [(+ 1 2)]"
```

---

### filter

`(filter <function> <list>)`

The `filter` function filters a list based on a *function*. The *function* is applied to each element of the list, and it must return a boolean value. If it returns *true* then the element is included in the result list, otherwise the element is excluded.

!!! see-also "See also"
	[map](#map), [reduce](#reduce)

```lisp title="Example"
(filter (lambda (x) (< x 3)) '(1 2 3 4 5))  ;; Returns (1 2)
```

---

### get-json-attribute

`(get-json-attribute <JSON> <key:string>)`

The `get-json-attribute` function retrieves an attribute from a JSON structure via a *key* path. This *key* may be a structured path to access elements deeper down in the JSON structure. There are the following extra elements to access more complex structures:

- It is possible to address a specific element in a list. This is done be  specifying the element as `{n}`.
- If an element is specified as `{}` then all elements in that list are returned in a list.
- If an element is specified as `{*}` and is targeting a dictionary then a single unknown key is skipped in the path. This can be used to skip, for example, unknown first elements in a structure. This is similar but not the same as `{0}` that works on lists.

!!! see-also "See also"
	[has-json-attribute](#has-json-attribute), [remove-json-attribute](#remove-json-attribute), [set-json-attribute](#set-json-attribute)

```lisp title="Examples"
(get-json-attribute { "a" : { "b" : "c" }} "a/b" )     ;; Returns "c"
(get-json-attribute { "a" : [ "b", "c" ]} "a/{0}" )    ;; Returns "b"
(get-json-attribute { "a" : [ "b", "c" ]} "a/{}" )     ;; Returns ( "b" "c" )
(get-json-attribute { "a" : [ "b", "c" ]} "{*}/{0}" )  ;; Returns "b"
```

---

### has-json-attribute

`(has-json-attribute <JSON> <key:string>)`

The `has-json-attribute` function determines  whether an attribute exists in a JSON structure for a *key* path. 
This *key* may be a structured path to access elements deeper down in the JSON structure. 

!!! see-also "See also"

	[get-json-attribute](#get-json-attribute), [remove-json-attribute](#remove-json-attribute), [set-json-attribute]	(#set-json-attribute)

	See [get-json-attribute](#get-json-attribute) for further details on how to access JSON attributes.

```lisp title="Examples"
(has-json-attribute { "a" : { "b" : "c" }} "a/b" )  ;; Returns true
(has-json-attribute { "a" : { "b" : "c" }} "a/c" )  ;; Returns false
```

---

### if

`(if <boolean expression> <s-expression> [<s-expression>])`

The `if` function works like an “if-then-else” statement in other programing languages. 
The first argument is a boolean expression. If it evaluates to *true* then the second argument is executed.
If it evaluates to *false* then the third (optional) argument is executed, if present.

The boolean expression can be any s-expression that evaluates to a boolean value or *nil*, or a list or a string. *nil* values, empty lists, or zero-length strings evaluate to *false*, or to *true* otherwise.

```lisp title="Examples"
(if (< 1 2)           ;; Evaluates to "true"
	(print "true")    ;; This expression is executed
	(print "false"))  ;; This expression is not executed
```

---

### in

`(in <symbol or list> <list or string>)`

The `in` function determines whether a symbol or list is contained in a list, or whether a string is contained in another string. 
The function returns *true* if this is the case, or *false* otherwise.

!!! see-also "See also"
	[index-of](#index-of)

```lisp title="Examples"
(in "Hello" "Hello, World")  ;; Returns true
(in "Bye" "Hello, World")    ;; Returns false
(in 1 '(1 2 3))              ;; Returns true
(in '(1 2) '((1 2) (3 4)))   ;; Returns true
```

---

### inc

`(inc <variable symbol> [<value:number>])`

The `inc` function increments a provided variable.
The default for the increment is 1, but can be given as an optional second argument.
If this argument is  provided then the variable is incremented by this value. The value can be an integer or a float.

The function returns the variable's new value.

!!! see-also "See also"
	[dec](#dec)

```lisp title="Example"
(setq a 1)   ;; Set variable "a" to 1
(inc a)      ;; Increment variable "a" by 1
(inc a 2.5)  ;; Increment variable "a" by 2.5
```

---

### index-of

`(index-of <value> <list or string>)`

The `index-of` function determines the index of a value in a list, or the index of a string in another string.
If the second argument is a string then the first argument must be a string as well. The index is 0-based.

The function returns the index as a number, or *nil* if the value could not be found.

!!! see-also "See also"
	[in](#in), [nth](#nth)

```lisp title="Examples"
(index-of 1 '(1 2 3))            ;; Returns 0
(index-of "a" '("b", "c", "d"))  ;; Returns nil
(index-of "b" "abc")             ;; Returns 1
```

---

### is-defined

`(is-defined <symbol>`)

The `is-defined` function tests whether a symbol (ie. a variable, built-in or defined function) is defined.

```lisp title="Examples"
(setq a 1)       ;; Define variable "a"
(is-defined 'a)  ;; Evaluates to "true".
(is-defined 'b)  ;; Evaluates to "false"
```

!!! note
	Most of the time the symbol argument needs to be quoted, otherwise the symbol is evaluated first and the function will not work as expected.

---

### json-to-string

`(json-to-string <JSON>`)

The `json-to-string` function returns a JSON structure in a string.

!!! see-also "See also"
	[string-to-json](#string-to-json), [to-number](#to-number), [to-string](#to-string)

```lisp title="Example"
(json-to-string { "a" : { "b" : "c" }})  ;; Returns "{\"a\": {\"b\": \"c\"}}"
```

---

### jsonify

`(jsonify <string>`)

The `jsonify` function returns a string where characters are escaped that would otherwise break a JSON structure.

!!! see-also "See also"
	[string-to-json](#string-to-json), [to-number](#to-number), [to-string](#to-string)

```lisp title="Example"
(jsonify "Hello, World")  ;; Returns "Hello,\nWorld"
```

---

### lambda

`(lambda <parameter list> <function body>)`

The `lambda` function defines a new nameless function. 

It is similar to the [defun](#defun) function, with the difference that functions defined as lambda functions cannot be called by name. They need to be used directly, assigned to a variable, or passed, for example, in a function call.

The first argument is a symbol list with argument names for the lambda function. Arguments act as function-local variables that can be used in the function body.

The second argument is an s-expression that is evaluated as the function body. 

The result of a lambda function is the result of the expression that is evaluated last in a function evaluation.

!!! see-also "See also"
	[defun](#defun), [return](#return)

```lisp title="Examples"
((lambda (x) (* x x)) 5)       ;; Returns 25

(setq y (lambda (x) (* x x)))  ;; Define and assign lambda function
(y)                            ;; Returns ( ( x ) ( * x x ) )
((y) 5)                        ;; Returns 25
```

---

### length

`(length <string or list>`)

The `length` function returns the length of a string or the number of elements in a list.

```lisp title="Examples"
(length "Hello, World")  ;; Returns 12
(length '(1 2 3))        ;; Returns 3
```

<a name="let-star"></a>
### let*

`(let* [( <variable> <s-expression> )]+`)

The `let*` function let one assigns values to variables in multiple steps. 

Each assignment consists, like the [setq](#setq) function, of an implicit quoted list with a variable symbol and an s-expression, but differently from the [setq](#setq) function, the `let*` function handles multiple assignments. The assignments are handled sequentially.

!!! note
	The `let` function (without the star), where assignments are handled in parallel is yet not supported.

!!! see-also "See also"
	[setq](#setq)

```lisp title="Examples"
(let* (a 1)         ;; Assigns 1 to a
	(a (+ a 1)))    ;; Assigns a + 1 = 2 to a
(let* (b 2) (c 3))  ;; Assigns 2 to b and 3 to c
```

---

### list

`(list <symbol>+)`

The `list` function returns a list that contains all the symbol arguments.

!!! see-also "See also"
	[cons](#cons)

```lisp title="Example"
(list 1 2 3)  ;; Returns ( 1 2 3 )
```

---

### log

`(log <s-expression>*)`

The `log` function prints symbols to the logging console with a *debug* log-level. Usually these symbols are strings or numbers, but representations of other data types are supported as well.

The function always returns *nil*.

!!! see-also "See also"
	[log-error](#log-error), [print](#print)

```lisp title="Example"
(log "Hello, World")  ;; Prints "Hello, World" to the log
```

---

### log-error

`(log <s-expression>*)`

The `log-error` function prints symbols to the logging console with an *warning* log-level. Usually these symbols are strings or numbers, but representations of other data types are supported as well.

The function always returns *nil*.

!!! see-also "See also"
	[log](#log), [print](#print)

```lisp title="Example"
(log-error "Hello, World")  ;; Prints "Hello, World" to the warning log
```

---

### lower

`(lower <string>`)

The `lower` function returns a lower case copy of the input string.

!!! see-also "See also"
	[upper](#upper)

```lisp title="Example"
(lower "Hello, World")  ;; Returns "hello, world"
```

---

### map

`(map <function> <list>+)`

The `map` function iterates over one or more lists and applies a *function* to each element of the *list*(s). The function must take as many arguments as there are lists provided. The shortest *list* determines the number of iterations.

The *function* could be a [lambda](#lambda), built-in or [user-defined](#defun) function.

!!! note
	The `map` function's arguments need to be quoted when used directly.

!!! see-also "See also"
	[reduce](#reduce), [zip](#zip)

```lisp title="Examples"
(map (lambda (x) (+ x 1)) '(1 2 3))  ;; Returns (2 3 4)
(map '+ '(1 2 3) '(4 5 6))           ;; Returns (5 7 9)
```


---

### match

`(match <string> <regex:string>`)

The `match` function determines whether a string matches a regular expression *regex*.

!!! note
	The default implementation supports a simplified regex operator set:

- `?` : any single character
- `*` : zero or more characters
- `+` : one or more characters
- `\` : Escape an expression operator

```lisp title="Examples"
(match "aa" "a?")  ;; Returns true
(match "aa" "b*")  ;; Returns false
```

---

### max

`(max <list>+ | <any value>+ )`

The `max` function returns the maximum value of a *list* of any comparable values. The function can take a *list* of values or any number of values as arguments.

```lisp title="Examples"
(max 1 2 3)              ;; Returns 3
(max '(1 2 3))           ;; Returns 3
(max '(1 2 3) '(4 5 6))  ;; Returns (4 5 6)
(max 1 2 3 4 5 6)        ;; Returns 6
```

!!! see-also "See also"
	[min](#min)


---

### min

`(min <list>+ | <any value>+ )`

The `min` function returns the minimum value of a *list* of any comparable values. The function can take a *list* of values or any number of values as arguments.

```lisp title="Examples"
(min 1 2 3)              ;; Returns 1
(min '(1 2 3))           ;; Returns 1
(min '(1 2 3) '(4 5 6))  ;; Returns (1 2 3)
(min 1 2 3 4 5 6)        ;; Returns 1
```


---

### nl

`(nl)`

The `nl` function returns a newline character.

!!! see-also "See also"
	[print](#print),  [sp](#sp)

```lisp title="Example"
(. "Hello," nl "World")  ;; Returns "Hello,\nWorld"
```

---

### nth

`(nth <index:number> <list or string>`)

The `nth` function returns the n-th element from a list, or the nth character from a string.

The index is 0-based.

!!! see-also "See also"
	[car](#car),  [cdr](#cdr), [index-of](#index-of)

```lisp title="Examples"
(nth 2 '(1 2 3))        ;; Returns 3
(nth 2 "Hello, World")  ;; Returns "l"
```

---

### parse-string

`(parse-string <string with an <s-expression>)`

The `parse-string` function parses a string that contains an s-expression and returns the result as an executable s-expression for further evaluation, e.g. with the [eval](#eval) function.

!!! see-also "See also"
	[eval](#eval), [to-symbol](#to-symbol)

```lisp title="Example"
(eval (parse-string "(print \"hello, world\")"))  ;; Prints "hello, world" 
```

---

### print

`(print <s-expression>*)`

The `print` function prints symbols to the console. Usually these symbols are strings or numbers, but representations of other data types are supported as well.

The function always returns *nil*.

!!! see-also "See also"
	[log](#log), [log-error](#log-error)

```lisp title="Example"
(print "Hello, World")  ;; Prints "Hello, World"
```

---

### progn

`(progn <s-expression>+)`

The `progn` function evaluates all provided symbols or lists, and returns the result of the last evaluation.
All other results are ignored.

This function is implicitly used internally when used to evaluate s-expressions.

!!! see-also "See also"
	[eval](#eval)

```lisp title="Example"
(progn (print "Hello, World") 1)  ;; Prints "Hello, World" and returns 1
```

---

### quit

`(quit [<symbol>])`

The `quit` function ends the execution of the current script without an *0* error code.

If a symbol is provided for the optional argument its value is taken as the result of the script. Otherwise, *nil* is returned.

!!! see-also "See also"
	[quit-with-error](#quit-with-error)

```lisp title="Examples"
(quit)             ;; Returns nil
(quit "a result")  ;; Returns "a result"
```

---

### quit-with-error

`(quit-with-error [<symbol>])`

The `quit-with-error` function ends the execution of the current script with an *-1* error code.

If a symbol is provided for the optional argument its value is taken as the result of the script. Otherwise, *nil* is returned.

!!! see-also "See also"
	[quit](#quit)

```lisp title="Examples"
(quit-with-error)             ;; Returns nil
(quit-with-error "a result")  ;; Returns "a result"
```

---

### quote

`(quote  <symbol or list>)`

The `quote` function returns a quoted version of the argument. It can be used to get a quoted version of an s-expression or symbol that is the result of another function.

```lisp title="Example"
(quote (1 2 3))  ;; Returns (1 2 3)
```

---

### random

`(random [<end:number> or <start:number> <end:number>])`

The `random` function generates a random float number in the given range. 

The default for the range, when no argument is given, is [0.0, 1.0]. If one number argument is given then this indicates a range of [0.0, &lt;end number>]. If two number arguments are given then this indicates a range of [&lt;start number>, &lt;end number>].

```lisp title="Examples"
(random)         ;; Returns, for example, 0.748786
(random 10)      ;; Returns, for example, 4.976338
(random 10 20)   ;; returns, for example, 12.73221
```

---

### reduce

`(reduce <function> <list> [<initial value>])`

The `reduce` function applies a function to all elements of a list, starting with an optional initial value. The *function* is applied to the first two elements of the *list*, then to the result of the first application and the third element, and so on. If no *initial* value is provided, the first element of the list is used as the initial value, otherwise the *initial value* is used as the first argument.

The &lt;function&gt; could be a [lambda](#lambda), built-in or [user-defined](#defun) function. The function must take two arguments.

The optional *initial value* or the first element of the *list*, if no *initial value* is provided, determines the type for all further calculations. If the *initial value* is a number then the result is a number, if it is a string then the result is a string, and so on.	All elements of the *list* must be of that type, otherwise the function will fail.

!!! note
	The `reduce` function's arguments need to be quoted when used directly.

!!! see-also "See also"
	[map](#map), [zip](#zip)

```lisp title="Examples"
(reduce (lambda (x y) (+ x y)) '(1 2 3 4 5))  ;; Returns 15
(reduce '+ '(1 2 3 4 5) 10)                   ;; Returns 25
```

---

### remove-json-attribute

`(remove-json-attribute <JSON> <key:string>+)`

The `remove-json-attribute` function removes one or more attributes and their values from a JSON structure via their *key* paths. This *key* may be a structured path to access elements deeper down in the JSON structure. See [get-json-attribute](#get-json-attribute) for further details on how to access JSON attributes.

The function doesn't change the original JSON structure, but returns an updated structure.

!!! see-also "See also"
	[get-json-attribute](#get-json-attribute), [has-json-attribute](#has-json-attribute), [set-json-attribute](#set-json-attribute)

```lisp title="Examples"
(remove-json-attribute { "a" : { "b" : "c" }} "a/b")  ;; Returns { "a" : {} }
```

---

### return

`(return [<s-expression>])`

The `return` function stops the evaluation of a function or [while](#while) loop and returns the evaluation to the caller. The function may return a symbol, or *nil*.

!!! see-also "See also"
	[defun](#defun), [while](#while)

```lisp title="Example"
(if (< 1 2)      ;; Evaluates to "true"
	(return 23)  ;; Return the number 23
)
```

---

### return-from

`(return-from <block name:string> [<s-expression>])`

The `return-from` function stops the evaluation of a [block](#block) with the given name and returns the evaluation to the caller. 

The function may return a symbol, or *nil*.

!!! see-also "See also"
	[block](#block)

```lisp title="Examples"
(block "myBlock" 1 (return-from "myBlock" 2) 3)  ;; Returns 2
```

---

### reverse

`(reverse <list> | <string>)`

The `reverse` function returns a reversed copy of a list or a string.

```lisp title="Examples"
(reverse '(1 2 3))    ;; Returns (3 2 1)
(reverse "abc")       ;; Returns "cba"
```

---

### round

`(round <value:number> [<precission:number>])`

The `round` function rounds a number to *precision* digits after the decimal point. The default is 0, meaning to round to nearest integer.

```lisp title="Examples"
(round 3.1415926)    ;; Returns 3
(round 3.1415926 2)  ;; Returns 3.14
```

---

### set-json-attribute

`(set-json-attribute <JSON> <key:string> <value>)`  
`(set-json-attribute <JSON> '( '(<key:string> <value>)* )`

The `set-json-attribute` function adds or updates an attribute in a JSON structure via a *key* path to the new *value*. This *key* may be a structured path to access elements deeper down in the JSON structure. See [get-json-attribute](#get-json-attribute) for further details on how to access JSON attributes.

There are two forms to use this function:

- The first form takes a JSON structure, a *key* path, and a *value* as arguments. The function sets the attribute in the JSON structure and returns the updated structure.
- The second form takes a JSON structure and a list of list of key-value pairs as arguments. The function sets the attributes in the JSON structure and returns the updated structure. This form is useful when multiple attributes need to be set in one call.

	!!! note
		The list as well as each list of key-value pairs need to be quoted if provided directly.

The function doesn't change the original JSON structure, but returns an updated structure.

!!! see-also "See also"
	[get-json-attribute](#get-json-attribute), [has-json-attribute](#has-json-attribute), [remove-json-attribute](#remove-json-attribute)

```lisp title="Examples"
(set-json-attribute { "a" : { "b" : "c" }} "a/b" "e")  ;; Returns {"a": {"b": "e"}}
(set-json-attribute { "a" : { "b" : "c" }} '('("a/b" "d") '("a/c" "e")))  ;; Returns { "a" : { "b" : "d", "c" : "e"}
```

---

### setq

`(setq <variable> <s-expression)`

The `setq` function assigns a value to a variable.

!!! see-also "See also"
	[let*](#let-star)

```lisp title="Example"
(setq a "Hello, World")  ;; Returns "Hello, World" and sets the variable "a"
```

---

### sleep

`(sleep <number>)`

The `sleep` function adds a delay to the script execution. The evaluation stops for a number of seconds. The delay could be provided as an integer or float number.

If the script execution timeouts during a sleep, the function is interrupted and all subsequent s-expressions are not evaluated.

The function returns the delay.

```lisp title="Example"
(sleep 1.5)  ;; Sleep for 1.5 seconds
```

---

### slice

`(slice <start:number> <end:number> <list or string>)`

The `slice` function returns the slice of a list or a string.

The behavior is the same as slicing in Python, except that both *start* and *end* must be provided. The first argument is the *start* (including) of the slice, the second is the *end* (excluding) of the slice. The fourth argument is the list or string to slice.

```lisp title="Examples"
(slice 1 2 '(1 2 3))     ;; Returns (2)
(slice 0 -1 "abcde")     ;; Returns "abcd"
(slice -1 99 "abcde")    ;; Returns "e"
(slice 99 100 '(1 2 3))  ;; Returns ()
```

---

### sp

`(sp)`

The `sp` function returns a space character.

!!! see-also "See also"
	[print](#print),  [nl](#nl)

```lisp title="Example"
(. "Hello," sp "World")  ;; Returns "Hello, World"
```

---

### string-to-json

`(string-to-json <string>)`

The `string-to-json` function converts a string to a JSON structure and returns it. The string must contain a valid parseable JSON structure.

!!! see-also "See also"
	[json-to-string](#json-to-string), [to-number](#to-number), [jsonify](#jsonify)

```lisp title="Example"
(string-to-json "{ \"a\" : { \"b\" : \"c\" }}")  ;; Returns {"a": {"b": "c"}}
```

---

### to-number

`(to-number <symbol>)`

The `to-number` function converts a string that contains a number to a number symbol and returns it.

!!! see-also "See also"
	[json-to-string](#json-to-string),  [to-string](#to-string)

```lisp title="Example"
(to-number "123")  ;; Returns the number 123
```

---

### to-string

`(to-string <symbol>)`

The `to-string` function converts a symbol of any of the built-in types to a string representation and returns it.

!!! see-also "See also"
	[json-to-string](#json-to-string), [to-number](#to-number)

```lisp title="Example"
(to-string '(1 2))  ;; Returns "[1, 2]"
```

---

### to-symbol

`(to-symbol <string>)`

The `to-symbol` function converts a string to a symbol and returns it. The resulting symbol has the name and value of the input string, but is itself not a string.

!!! see-also "See also"
	[eval](#eval), [parse-string](#parse-string), [parse-string](#parse-string)

```lisp title="Example"
(to-symbol "a-symbol")  ;; Returns the symbol 'a-symbol'
```

---

### unwind-protect

`(unwind-protect <s-expression> <cleanup s-expression>)`

The `unwind-protect` function evaluates the first s-expression and then the second s-expression. 
The second s-expression is always evaluated, even if the first s-expression throws an error or returns early.
This is effectively a try/finally block (without a catch)

Currently only programmatic flow interrupts are supported to trigger the cleanup form:
[assert](#assert), [quit](#quit), [quit-with-error](#quit-with-error), [return](#return), [return-from](#return-from).

The function always returns the result of the cleanup s-expression.

```lisp title="Example"
;; Prints "main form" and "cleanup form" and returns 2
(unwind-protect
	((print "main form") 1)
	((print "cleanup form") 2))
```

---

### upper

`(upper <string>`)

The `upper` function returns an upper case copy of the input string.

!!! see-also "See also"
	[lower](#lower)

```lisp title="Example"
(upper "Hello, World")  ;; Returns "HELLO, WORLD"
```

---

### url-encode

`(url-encode <string>)`

The `url-encode` function encodes a string so that may be safely used as part of a URL.

!!! see-also "See also"
	[base64-encode](#base64-encode)

```lisp title="Example"
(url-encode "Hello, World")  ;; Returns "Hello%2C+World"
```

---

### while

`(while <boolean guard> <body s-expression> `)

The `while` function implements a loop functionality.

A `while` loop continues to run when the first *guard* s-expression evaluates to *true*. Then the *body* s-expression is evaluated. After this the *guard* is evaluated again and the the loops continues or the `while` function returns.

The boolean guard can be any s-expression that evaluates to a boolean value or *nil*, or a list or a string. *nil* values, empty lists, or zero-length strings evaluate to *false*, or to *true* otherwise.

The `while` function returns the result of the last evaluated s-expression in the *body*.

!!! see-also "See also"
	[dolist](#dolist), [dotime](#dotimes), [return](#return)

```lisp title="Example"
(setq i 0)       ;; Set loop variable
(while (< i 10)  ;; Loop 10 times
	((print i)   ;; Print to the console
	(inc i)))    ;; Increment loop variable
```

---

### zip

`(zip <list>+)`

The `zip` function takes a *list* of lists and returns a list of lists where the first element of each input list is combined into a new list, the second element of each input list is combined into a new list, and so on. The function stops when the shortest list is exhausted.

!!! see-also "See also"
	[map](#map), [reduce](#reduce)

```lisp title="Examples"
(zip '(1 2 3) '(4 5 6))  ;; Returns ((1 4) (2 5) (3 6))
(zip '(1 2 3) '(4 5))    ;; Returns ((1 4) (2 5))
(zip '(1 2 3))           ;; Returns ((1) (2) (3))
```


## CSE-Specific Functions

The following functions provide support to access certain CSE functionalities, configurations, and other runtime aspects.

### clear-console

`(clear-console)`

The `clear-console` function clears the console screen.

```lisp title="Example"
(clear-console)  ;; Clears the console screen
```

---

### cse-attribute-info

`(cse-attribute-info <name:str>)`

Return a list of CSE attribute infos for the attribute `name``. 
The search is done over the short and long names of the attributes applying a fuzzy search when searching the long names.
			
The function returns a quoted list where each entry is another quoted list with the following symbols:
				
- attribute short name
- attribute long name
- attribute type

```lisp title="Example"
(cse-attribute-info "acop")  ;; Returns ( ( "acop" "accessControlOperations" "nonNegInteger" ) )
```

---

### cse-status

`(cse-status)`

The `cse-status` function returns the CSE's current running status as an upper-case string. 

The return value is one of the following strings:

- STARTING
- RUNNING
- STOPPING 
- STOPPED 
- RESETTING

```lisp title="Example"
(cse-status)  ;; Returns "RUNNING"
```

---

### get-config

`(get-config <key:string>)`

The `get-config` function retrieves a setting from the CSE's internal configuration. The *key* is a configuration name as defined in the [configuration documentation](../setup/Configuration-basic.md).

!!! see-also "See also"
	[has-config](#has-config), [set-config](#set-config)

```lisp title="Examples"
(get-config "cse.type")    ;; Returns, for example, 1
(get-config "cse.cseID")   ;; Returns, for example, "/id-in"
```

---

### get-loglevel

`(get-loglevel)`

The `get-loglevel` function retrieves a the CSE's current log level setting. The return value is one of the following strings:

- DEBUG
- INFO
- WARNING
- ERROR
- OFF

```lisp title="Example"
(get-loglevel)  ;; Return, for example, INFO
```

---

### get-storage

`(get-storage <key:string>)`

The `get-storage` function retrieves a value from the CSE's internal script-data storage. The *key* is a unique name of the value.

!!! see-also "See also"
	[has-storage](#has-storage), [put-storage](#put-storage), [remove-storage](#remove-storage)

```lisp title="Example"
(get-storage "aStorageID" "aKey")  ;; Retrieves the value for "aKey" from "aStorageID"
```

---

### has-config

`(has-config <key:string>)`

The `has-config` function determines whether a setting from the CSE's internal configuration exists. The *key* is a configuration name as defined in the [configuration documentation](../setup/Configuration-basic.md).

!!! see-also "See also"
	[get-config](#get-config), [set-config](#set-config)

```lisp title="Examples"
(has-config "cse.cseID")     ;; Returns true
(has-config "cse.unknown")   ;; Returns false
```

---

### has-storage

`(has-storage <key:string>)`

The `has-storage` function determines whether a value has been stored under the given *key* in the CSE's internal script-data storage.

!!! see-also "See also"
	[get-storage](#get-storage), [put-storage](#put-storage), [remove-storage](#remove-storage)

```lisp title="Example"
(has-storage "aStorageID" "aKey")       ;; Tests whether the key "aKey" exists in "aStorageID"
```

---

### include-script

`(include-script <script name:string> [<argument:any>]*)`

The `include-script` function runs another ACMEScript script by its *script name* in its own context. Differently to the [run-script](#run-script) function variables, function definitions etc from the script execution are available in the calling script after the script finished.

The function returns the result of the finished script.

!!! see-also "See also"
	[run-script](#run-script), [schedule-next-script](#schedule-next-script)

```lisp title="Example"
(include-script "functions" "an argument")  ;; Run the script "functions"
```

---

### log-divider

`(log-divider [<message:string>])`

The `log-divider` function inserts a divider line in the CSE's *DEBUG* log. It can help to easily identify the different sections when working with many requests. An optional (short) message can be provided in the argument.

```lisp title="Examples"
(log-divider)                 ;; Add a divider
(log-divider "Hello, World")  ;; Add a divider with a centered message
```

---

### print-json

`(print-json <JSON>)`

The `print-json` function prints a JSON structure with syntax highlighting to the console.

```lisp title="Example"
(print-json { "m2m:cnt" : { "rn": "myCnt" }})  ;; Print the JSON structure
```

---

### put-storage

`(put-storage <storageID:string> <key:string> <value:symbol>)`

The `put-storage` function inserts or updates a *value* in the CSE's internal script-data storage with the storage ID *storageID*. The *key* is a unique name of the *value*.

!!! see-also "See also"
	[get-storage](#get-storage), [has-storage](#has-storage), [remove-storage](#remove-storage)

```lisp title="Example"
(put-storage "aStorageID" "aKey" "Hello, World")  ;; Inserts or updates the key "aKey" in "aStorageID"
```

---

### remove-storage

`(remove-storage <key:string>)`
`(remove-storage <storageID:string> <key:string>)`

There are two forms of the `remove-storage` function.

With only one parameter the `remove-storage` function removes all *key*/*value* pairs from the CSE's internal script-data storage with the storage ID *storageID*. 

With two parameters the `remove-storage` function removes a *key*/*value* pair from the CSE's internal script-data storage with the storage ID *storageID*. The *key* is a unique name of the *value*.

!!! see-also "See also"
	[get-storage](#get-storage), [has-storage](#has-storage), [put-storage](#put-storage)

```lisp title="Examples"
(remove-storage "aStorageID" "aKey")  ;; Removes the key and value from storageID
(remove-storage "aStorageID")         ;; Removes all keys and value from storageID
```

---

### reset-cse

`(reset-cse)`

The `reset-cse` function initiates a CSE reset.

The script execution does continue after the CSE finished the reset.

```lisp title="Example"
(reset-cse)  ;; Resets the CSE
```

---

### run-script

`(run-script <script name:string> [<argument:any>]*)`

The `run-script` function runs another ACMEScript script by its *script name* in its own scope. Variables, function definitions etc from the script execution are not available in the calling script.

The function returns the result of the finished script.

!!! see-also "See also"
	[include-script](#include-script), [schedule-next-script](#schedule-next-script)

```lisp title="Example"
(setq result (run-script "aScript" "an argument"))  ;; Run the script "aScript" and assign the result
```

---

### runs-in-ipython

`(runs-in-ipython)`

The `runs-in-ipython` function determines whether the CSE currently runs in an IPython environment, such as Jupyter Notebooks.

```lisp title="Example"
(runs-in-ipython)  ;; Returns true if the CSE runs in an iPython environment
```

---

### schedule-next-script

`(schedule-next-script <scriptName:string> <argument:any>*)`

The `schedule-next-script` function schedules the next script that is run after the current script finished. 

This is different from [include-script](#include-script) and [run-script](#run-script) in so far that the context of the current running script is finished and may be called again. This means that a script can schedule itself, which would not be possible otherwise because scripts can only be run one at a time.

!!! see-also "See also"
	[include-script](#include-script), [run-script](#run-script)

```lisp title="Example"
(schedule-next-script "scriptName" "anArgument")  ;; Schedule a script with an argument
```

---

### set-config

`(set-config <key:string> <value:any>)`

The `set-config` function updates a setting from the CSE's internal configuration. The *key* is a configuration name as defined in the [configuration documentation](../setup/Configuration-basic.md).

It is only possible to update an existing setting, but not to create a new one. The *value* type must be equivalent to the setting's type.

!!! see-also "See also"
	[get-config](#get-config), [has-config](#has-config)

```lisp title="Example"
(set-config "cse.checkExpirationsInterval" 1.5)  ;; Set the configuration to 1.5
```

---

### set-console-logging

`(set-console-logging <boolean>)`

The `set-console-logging` function enables or disables console logging. It does not turn on or off logging in general. [Printing](#print) to the console is not affected.

```lisp title="Example"
(set-console-logging false)  ;; Switch off console logging
```


## oneM2M-Specific Functions

The following functions provide support for the oneM2M request operations.

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

!!! see-also "See also"
	[delete-resource](#delete-resource), [import-raw](#import-raw), [retrieve-resource](#retrieve-resource), [send-notification](#send-notification), [update-resource](#update-resource)

```lisp title="Example"
(create-resource "CAdmin" "cse-in"  { "m2m:cnt" : { "rn": "myCnt" }})  ;; Returns ( 2001 { "m2m:cnt" ... } )

;; Provide extra requestVersionIndicator
(create-resource "CAdmin" "cse-in"  { "m2m:cnt" : { }} { "rvi": "3"})  ;; Returns ( 2001 { "m2m:cnt" ... } )
```

---

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

!!! see-also "See also"
	[create-resource](#create-resource), [retrieve-resource](#retrieve-resource), [send-notification](#send-notification), [update-resource](#update-resource)

```lisp title="Example"
(delete-resource "CAdmin" "cse-in/myCnt")                ;; Returns ( 2002 { "m2m:cnt" ... } )

;; Provide extra requestVersionIndicator
(delete-resource "CAdmin" "cse-in/myCnt" { "rvi": "3"})  ;; Returns ( 2002 { "m2m:cnt" ... } )
```

---

### import-raw

`(import-raw <originator:string> <resource:JSON>)`

The `import-raw` function creates a resource in the CSE without using the normal procedures when handling a [CREATE request](#create-resource). The resource is added to the resource tree without much validation.

This function is primarily used when importing initial resources, and when restoring resources during the [startup](ACMEScript-metatags.md#init) of the CSE.

`resource` is a valid oneM2M resource. All necessary attributes must be present in that resource, including the *parentID* (*pi*) attribute that determines the location in the resource tree.

The function returns a list:

`(<response status:number> <resource:JSON>)`

- *response status* is the oneM2M Response Status Code (*RSC*) for the request
- *resource* is the response content (usually *nil* if successful)

```lisp title="Example"
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

---

### query-resource

`(query-resource <query:quoted s-expression> <resource:JSON>)`

The `query-resource` function evaluates a *query* for the attributes in the *resource* structure.

The function has the following arguments:

- *query* to evaluate. This query must be quoted and follows oneM2M's advanced query specification. the unknown symbols in the query are replaced by the resource's attribute values during the evaluation.
    Only a limited set boolean and comparison operators are allowed in the query.
- A oneM2M resource as a JSON structure.

The function returns a boolean indicating the query result.

!!! see-also "See also"
	[get-json-attribute](#get-json-attribute)

```lisp title="Example"
;; Returns true
(query-resource 
	'(& (> x 100) (== rn "cnt1234"))
	{ "m2m:cnt": {
		"rn": "cnt1234",
		"x": 123
	}})
```

---

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

!!! see-also "See also"
	[create-resource](#create-resource), [delete-resource](#delete-resource), [send-notification](#send-notification), [update-resource](#update-resource)

```lisp title="Example"
(retrieve-resource "CAdmin" "cse-in/myCnt")                ;; Returns ( 2000 { "m2m:cnt" ... } )

;; Provide extra requestVersionIndicator
(retrieve-resource "CAdmin" "cse-in/myCnt" { "rvi": "3"})  ;; Returns ( 2000 { "m2m:cnt" ... } )
```

---

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

!!! see-also "See also"
	[create-resource](#create-resource), [delete-resource](#delete-resource), [retrieve-resource](#retrieve-resource), [update-resource](#update-resource)

```lisp title="Example"
(send-notification "CAdmin" "cse-in/myAE"  { "m2m:sgn" : { ... }})  ;; Returns notification result
```

---

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

!!! see-also "See also"
	[create-resource](#create-resource), [delete-resource](#delete-resource), [retrieve-resource](#retrieve-resource), [send-notification](#send-notification)

```lisp title="Example"
(update-resource "CAdmin" "cse-in"  { "m2m:cnt" : { "mni": 10 }})                ;; Returns ( 2004 { "m2m:cnt" ... } )

;; Provide extra requestVersionIndicator
(update-resource "CAdmin" "cse-in"  { "m2m:cnt" : { "mni": 10 }} { "rvi": "3"})  ;; Returns ( 2004 { "m2m:cnt" ... } )
```


## Text UI

### open-web-browser

`(open-web-browser <url:string>)`

The `open-web-browser` function opens a web browser with the given URL.

```lisp title="Example"
(open-web-browser "https://www.onem2m.org")  ;; Opens the web browser with the URL "https://www.onem2m.org"
```

---

### set-category-description

`(set-category-description <category:string> <description:string>)`

The `set-category-description` function sets the description for a whole category in the CSE's Text UI.

The description may contain Markdown formatting.

```lisp title="Example"
(set-category-description "myCategory" "My category description")  ;; Sets the description for the category "myCategory"
```

---

### runs-in-tui

`(runs-in-tui)`

The `runs-in-tui` function determines whether the CSE currently runs in Text UI mode.

```lisp title="Example"
(runs-in-tui)  ;; Returns true if the CSE runs in Text UI mode
```

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

```lisp title="Examples"
(tui-notify "a message")                ;; Displays "a message" in an information notification for 3 seconds
(tui-notify "a message" "a title")      ;; Displays "a message" with title "a title in an information notification for 3 seconds
(tui-notify "a message")                ;; Displays "a message" in an information notification for 3 seconds
(tui-notify "a message" nil "warning")  ;; Displays "a message" in a warning notification, no title
(tui-notify "a message" nil nil 10)     ;; Displays "a message" in an information notification, no title, for 3 seconds
```

---

### tui-refresh-resources

`(tui-refresh-resources)`

The `tui-refresh-resources` function refreshes the resources in the CSE's Text UI.

```lisp title="Example"
(tui-refresh-resources)  ;; Refreshes the resource tree
```

---

### tui-visual-bell

`(tui-visual-bell)`

The `tui-visual-bell` function shortly flashes the script's entry in the scripts' list/tree.

```lisp title="Example"
(tui-visual-bell)  ;; Flashes the script's name
```


## Network

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

```lisp title="Examples"
;; Retrieve a web page
(http 'get "https://www.onem2m.org")

;; Send a oneM2M CREATE request manually
(http 'post "http://localhost:8080/cse-in"   ;; Operation and URL
	{ "X-M2M-RI":"1234",                     ;; Header fields
		"X-M2M-RVI": "4",
		"X-M2M-Origin": "CAdmin",
		"Content-type": "application/json;ty=3" }
	{ "m2m:cnt": {                           ;; Body
		"rn": "myCnt"
		...
	}})
```

---

### ping-tcp-service

`(ping-tcp-server <hostname:string> <port:number> [<timeout:number>])`

The `ping-tcp-service`function tests the availability and reachability of a TCP-based network service.

It has the following arguments:

- The *hostname* of the target service. This can be a hostname or an IP address.
- The *port* of the target service. This is a number.
- Optional: The request *timeout* in seconds. The default is 5 seconds.

The function returns a boolean value.

```lisp title="Examples"
(ping-tcp-service "localhost" 8080)    ;; Returns true if the service is reachable
(ping-tcp-service "localhost" 8080 2)  ;; Returns true if the service is reachable. Timeout after 2 seconds.
```

## Provided Functions

In addition to the functions defined in this documentation, more functions are provided in the file [ASFunctions.as](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init/ASFunctions.as). 

These functions can be included and made available in own scripts with the [include-script](#include-script) function:

```lisp title="Example"
(include-script "ASFunctions")
```

### cadr

`(cadr <list>)`

The `cadr` function returns the second element of a list.

!!! see-also "See also"
	[caddr](#caddr)

```lisp title="Example"
(cadr '(1 2 3))  ;; Returns 2
```

---

### caddr

`(caddr <list>)`

The `caddr` function returns the third element of a list.

!!! see-also "See also"
	[cadr](#cadr)

```lisp title="Example"
(caddr '(1 2 3))  ;; Returns 3
```

---

### set-and-store-config-value

`(set-and-store-config-value <key:string> <value:any>)`

The `set-and-store-config-value` function stores the current value of a configuration setting and then updates the setting with a new value.

The function has the following arguments:

- The *key* of the configuration setting
- The *value* to set

The function returns the previous value of the configuration setting.

!!! see-also "See also"
	[restore-config-value](#restore-config-value)

```lisp title="Example"
(set-and-store-config-value "cse.checkExpirationsInterval" 10)  ;; Returns the previous value of the configuration setting
```

---

### restore-config-value

`(restore-config-value <key:string>)`

The `restore-config-value` function restores a configuration setting to its previous value.

The function has the following arguments:

- The *key* of the configuration setting

!!! see-also "See also"
	[set-and-store-config-value](#set-and-store-config-value)

```lisp title="Example"
(restore-config-value "cse.checkExpirationsInterval")  ;; Restores the configuration setting
```

---

### get-response-status

`(get-response-status <response:list>)`

The `get-response-status` function returns the response status of a oneM2M request.

The function has the following arguments:

- The *response* list 

The function returns the response status.

!!! see-also "See also"
	[get-response-resource](#get-response-resource) 

```lisp title="Example"
(get-response-status (retrieve-resource "CAdmin" "cse-in/myCnt"))  ;; Returns the response status
```

---

### get-response-resource

`(get-response-resource <response:list>)`

The `get-response-resource` function returns the response resource of a oneM2M request.

The function has the following arguments:

- The *response* list

The function returns the response resource.

!!! see-also "See also"
	[get-response-status](#get-response-status)

```lisp title="Example"
(get-response-resource (retrieve-resource "CAdmin" "cse-in/myCnt"))  ;; Returns the response resource
```

---

### eval-if-resource-exists

`(eval-if-resource-exists <originator:string> <id:string> <cmd:s-expression> <else-cmd:s-expression>)`

The `eval-if-resource-exists` function evaluates a command if a resource exists and can be retrieved. Otherwise, it evaluates an alternative command.

If found, the resource is stored in the "_resource" variable that can be used in the "cmd" command.

The function has the following arguments:

- The *originator* of the request
- The *id* of the resource
- The *cmd* to evaluate if the resource exists
- The *else-cmd* to evaluate if the resource does not exist

The function returns the result of the evaluated command.

```lisp title="Example"
(eval-if-resource-exists "CAdmin" 
                         "cse-in/myCnt" 
						 (print "Resource exists") 
						 (print "Resource does not exist"))  ;; Evaluates the command
```

