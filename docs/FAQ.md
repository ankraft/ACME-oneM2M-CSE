[← README](../README.md) 

# FAQ

## Network

1. **How can I access the CSE from remote/another computer on my network?**  
   By default the CSE binds to the *localhost* interface. To make it accessible from a remote machine you need to bind the CSE's http server to another network interface, or address. This can be done in the *[server.http]* and *[client.mqtt]* sections of the configuration file. 
   Setting the listen interface to "0.0.0.0" binds the http server to all available interfaces.

## MQTT

1. **What does this error message "Out of memory" mean that appears sometimes?**  
   This error message should actually read "connection refused" or "general error" that is returned by the underlying MQTT library. The error code "1" indicates this error but the human readable error message seems to be wrongly assigned here.
1. **What does "cannot connect to broker: [Errno 49] Can't assign requested address" mean?**  
   You most likely want to connect to an MQTT broker that does not run on your local machine and you configured the listen interface to "127.0.0.1", which means that only local running services can be reached. Try to set the configuration *[client.mqtt].listenIF* to "0.0.0.0".

## Resources

1. **How can I add my own FlexContainer specializations to the ACME CSE?**  
   All resources and specializations are validated by the CSE. You can add your own specializations and validation policies by providing them in one or more separate files in the *import* directory. Those files must have the file extension ".ap". These files are read during the startup of the CSE.
   See [the documentation about Importing ](Importing.md#attributes) for further details.

## Performance

1. **How to increase the performance of ACME CSE?**  
   The log output provides useful information to analyze the flows of requests inside the CSE. However, it reduces the performance of the CSE a lot. So, reducing the log level to *info* or *warning* already helps. This can be done in the *[logging]* section of the configuration file, or by pressing *L* on the console to change the logging level to the desired value.  
   Another option is to change the database to *memory* mode. This means that all database access happens in memory and not on disk. But please be aware that this also means that all  data will be lost when the CSE terminates!

## Web UI

1. **Can I use the web UI also with other CSE implementations?**  
    The web UI can also be run as an independent application.  Since it communicates with the CSE via the Mca interface it should be possible to use it with other CSE implementations as well as long as those third party CSEs follow the oneM2M http binding specification. It only supports the resource types that the ACME CSE supports, but at least it will present all other resource types as *unknown*.

## Operating Systems

### RaspberryPi

1. **Restrictions**  
	Currently, the normally installed Raspbian OS is a 32 bit system. This means that several restrictions apply here, such as the maximum date supported (~2038). It needs to be determined whether these restrictions still apply when the 64 bit version of Raspbian is available.
1. **Timing Issues**  
	 Also, the resolution of the available Python timers is rather low on Raspbian, and background tasks might not run exactly on the desired time.  
	 Unfortunately, this is also why sometimes a couple of the CSE's tests cases may fail randomly.

[← README](../README.md) 