# Operations

This document describes the operations supported by ACMEScript.

## Comparison Operations

The following comparison operations are supported by ACMEScript. They are used like any other function, and return a boolean value.

| operation | Description           | Example                         |
|-----------|-----------------------|---------------------------------|
| ==        | Equal to              | ` (== a b) ;; equal to: a == b` |
| !=, <>    | Not equal to          | ` (!= a b) ;; equal to: a != b` |
| <         | Smaller than          | ` (< a b) ;; equal to: a < b`   |
| <=        | Smaller or equal than | ` (<= a b) ;; equal to: a <= b` |
| >         | Greater than          | `(> a b) ;; equal to: a > b`    |
| >=        | Greater or equal than | `(>= a b) ;; equal to: a >= b`  |

```lisp title="Example"
(if (< 1 2)           ;; Evaluates to "true"
	(print "true")    ;; This expression is executed
	(print "false"))  ;; This expression is not executed
```

!!! note
	The first operant in comparison operations may be a list or a quoted list. Only if the second operant is not a list, too, then the comparison operation is repeated for every member in the first operant's list. The comparison operation evaluates to *true* if any of these comparisons returns *true*.

```lisp title="Example"
(== '(1 2 3) 2)  ;; Evaluates to "true"
```


## Logical Operations

The following logical operations are supported by ACMEScript. They are used like any other function, and return a boolean value.

| operation | Description                                      | Example                      |
| --------- | ------------------------------------------------ | ---------------------------- |
| or, \|    | logical *or* of two or more boolean expressions  | (or a b)  ;; a or b          |
| and, &    | logical *and *of two or more boolean expressions | (and a b c) ;; a and b and c |
| not, !    | logical negation or one boolean expression       | (not true)  ;; false         |

```lisp title="Example"
(or (< 1 2) (>= 4 3) (== 1 1))   ;; Returns true
(and (or true false) (not true)) ;; Returns false
```

!!! note
	The first operant in logical operations may be a list or quoted list. Only if the second operant is not a list, too, then the logical operation is repeated for every member in the first operant's list. The logical operation evaluates to *true* if any of these operations returns *true*.

```lisp title="Examples"
(and '(false false true) true)   ;; Evaluates to "true"
(and '(false false false) true)  ;; Evaluates to "false"
```


## Mathematical Operations

The following mathematical operations are supported by ACMEScript. They are used like any other function, and return a number value.

| operation | Description                                 | Example                     |
| --------- | ------------------------------------------- | --------------------------- |
| +         | Add two or more numbers                     | (+ 1 2 3)  ;; Returns 6     |
| -         | Subtract two or more numbers                | (- 10  1 2 3)  ;; Returns 4 |
| *         | Multiply two or more numbers                | (* 6 7)  ;; Returns 42      |
| /         | Divide two or more numbers                  | (/ 23 5)  ;; Returns 4.6    |
| **        | Calculates the power of two or more numbers | (** 2 3 4)  ;; Returns 4096 |
| %         | Calculates to modulo of two or more numbers | (% 100 21 13) ;; Returns 3  |

```lisp title="Examples"
(* 6 7)        ;; Returns 42
(* (+ 3 3) 7)  ;; Return 42
```
