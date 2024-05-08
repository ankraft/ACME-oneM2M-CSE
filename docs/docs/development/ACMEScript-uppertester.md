# Upper Tester Integration

ACMEScript is integrated with the [Upper Tester (UT) Interface](../setup/Operation.md#upper_tester). To enable this a script must have the [@uppertester](ACMEScript-metatags.md#meta_uppertester) meta tag set. It can then be run through the UT interface by having its [@name](ACMEScript-metatags.md#meta_name) (and optional script arguments) as the parameter of the upper tester's *X-M2M-UTCMD* header field of a http request:

```text
X-M2M-UTCMD: aScript param1 param2
```

A script result is  passed back in a response in the *X-M2M-UTRSP* header of the response:

```text
X-M2M-UTRSP: aResult
```