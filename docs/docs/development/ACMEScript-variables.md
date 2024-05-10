# ACMEScript - Variables

This section describes the built-in variables that are available in ACMEScript.

## argc

`argc`

Evaluates to the number of elements in [argv](../development/ACMEScript-functions.md#argv). A script called with no arguments still has `argc` set to 1, because the name of the script is always the first element in [argv](../development/ACMEScript-functions.md#argv).

!!! see-also "See also"
	[argv](../development/ACMEScript-functions.md#argv)

```lisp title="Example"
(if (> argc 2)
	((log-error "Wrong number of arguments")
	(quit-with-error)))
```

---

## event.data

`event.data`

Evaluates to the payload data of an event. This could be, for example, the string representation in case of an [onKey](../development/ACMEScript-metatags.md#onkey) event.

!!! note
	This variable is only set when the script was invoked by an event.

!!! see-also "See also"
	[event.type](#eventtype)

```lisp title="Example"
(if (== event.type "onKey")     ;; If the event is "onKey"
	(print "Key:" event.data))  ;; Print the pressed key
```

---

## event.type

`event.type`

Evaluates to the type of an event. This could be, for example, the value *"onKey"* in case of an [onKey](../development/ACMEScript-metatags.md#onkey) event.

!!! note
	This variable is only set when the script was invoked by an event.

!!! see-also "See also"
	[event.data](#eventdata)

```lisp title="Example"
(if (== event.type "onKey")     ;; If the event is "onKey"
    (print "Key:" event.data))  ;; Print the pressed key
```

---

## notification.originator

`notification.originator`

The `notification.originator` variable is set when a script is called to process a notification request. 

It contains the notification's originator.

```lisp title="Example"
(print notification.originator)
```

---

## notification.resource

`notification.resource`

The `notification.resource` variable is set when a script is called to process a notification request. 

It contains the notification's JSON body.

```lisp title="Example"
(print notification.resource)
```

---

## notification.uri

`notification.uri`

The `notification.uri` variable is set when a script is called to process a notification request. 

It contains the notification's target URI.

```lisp title="Example"
(print notification.uri)
```

---

## tui.autorun

`tui.autorun`

Evaluates to *true* if the script was started as an "autorun" script. This is the case when the [@tuiAutoRun](ACMEScript-metatags.md#tuiautorun) meta tag is set in a script.

!!! see-also "See also"
	[tuiAutoRun](ACMEScript-metatags.md#tuiautorun)

!!! note
	This variable is only set when the script is run from the text UI.

```lisp title="Example"
(if (is-defined 'tui.autorun)     ;; If the variable is defined
	(if (== tui.autorun true)     ;; If the script is an autorun script
		(print "Autorun: True")))  ;; Print a message
```

---

## tui.theme

`tui.theme`

Evaluates to the state of the current theme of the text UI. This can either be the values *light* or *dark*.

```lisp title="Example"
(print "Theme: " tui.theme)  ;; Print the theme name
```

