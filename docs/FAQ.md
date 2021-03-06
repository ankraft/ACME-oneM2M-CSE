[← README](../README.md) 

# FAQ

## Network

1. **How can I access the CSE from remote/another computer on my network?**
   By default the CSE binds to the *localhost* interface. To make it accessible from a remote machine you need to bind the CSE's http server to another network interface, or address. This can be done in the *[server.http]* section of the configuration file. 
   Setting the listen  interface to "0.0.0.0" binds the http server to all available interfaces.

## Resources

1. **How can I add my own FlexContainer specialisations to the ACME CSE?**
   All resources and specialisations are validated by the CSE. You can add your own specialisations and validation policies by providing them in one or more separate files in the *import* directory. Those files must have the file extension ".ap". These files are read during the startup of the CSE.
   See [the documentation about Importing ](Importing.md#attributes) for further details.

## Performance

1. **How to increase the performance of ACME CSE?**
   The log output provides useful information to analyse the flows of requests inside the CSE. However, it reduces the performance of the CSE a lot. So, reducing the log level to *info* or *warning* already helps. This can be done in the *[logging]* section of the configuration file.
   Another option is to change the database to *memory* mode. This means that all database access happens in memory and not on disk. But please be aware that this also means  that all  data will be lost when the CSE terminates!

## Web UI

1. **Can I use the web UI also with other CSE implementations?**
    The web UI can also be run as an independent application.  Since it communicates with the CSE via the Mca interfave it should be possible to use it with other CSE implementations as well as long as those third party CSEs follow the oneM2M http binding specification. It only supports the resource types that the ACME CSE supports, but at least it will present all other resource types as *unknown*.

[← README](../README.md) 