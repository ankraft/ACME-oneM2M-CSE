# Debug Mode

The CSE tries to catch errors and give helpful advice as much as possible during runtime.
However, there are circumstances when this could not done easily, e.g. during startup.

In order to provide additional information in these situations one can set the *ACME_DEBUG* environment variable (to any value):

```sh title="Set the ACME_DEBUG environment variable"
export ACME_DEBUG=1
```

Then run the CSE as usual. 