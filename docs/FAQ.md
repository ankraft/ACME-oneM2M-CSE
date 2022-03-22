[← README](../README.md) 

# FAQ

## Network

1. **How can I access the CSE from remote/another computer on my network?**  
   By default the CSE binds to the *localhost* interface. To make it accessible from a remote machine you need to bind the CSE's http server to another network interface, or address. This can be done in the *[server.http]* and *[client.mqtt]* sections of the configuration file. 
   Setting the listen interface to "0.0.0.0" binds the http server to all available interfaces.


## Database

1. **Corrupt database files**  
   In very rare cases, e.g. when the CSE was not properly shut down, the on-disk database files may be corrupted. The CSE tries to detect this during start-up, but there is not much one can do about this. However, a backup of the database file is created every time the CSE starts. This backup can be found in the *backup* sub-directory of the *data* directory. 


## HTTP

1. **What does the error message "[Errno 13] Permission denied" during startup of the CSE mean?**  
   This error is shown by the CSE when the http server tries to bind to a TCP/IP port to listen for incoming requests, 
   but doesn't have enough privileges to do so. This usually happens when an http port < 1024 is configured (e.g. 80) and 
   the CSE is run with normal user privileges. Either run the CSE with admin / superuser rights (NOT recommended), 
   or choose another TCP/IP port, larger than 1024.
1. **Is there a work-around for the missing DELETE method in http/1.0?**  
   Many constraint devices only support version 1.0 of the http protocol. This version of http, though, does not specify the
   DELETE method, which means that those devices cannot invoke oneM2M's DELETE operation.  
   The ACME CSE implements an experimental work-round by supporting the http PATCH operation in addition to the normal DELETE
   operation: Instead of sending oneM2M DELETE requests using the http DELETE method one can send the same request with the http PATCH method.  
   This feature is disabled by default and can be enabled by setting the configuration setting *[server.http].allowPatchForDelete*
   to *true*.

## MQTT

1. **What does the error message "Out of memory" mean that appears sometimes?**  
   This error message should actually read "connection refused" or "general error" that is returned by the underlying MQTT library. The error code "1" indicates this error but the human readable error message seems to be wrongly assigned here.
1. **What is going on when the error "rc=7: The connection was lost" is repeatedly thrown?**  
   This error message might occur when another client (perhaps another running CSE with the same CSE-ID) connected to an MQTT broker with the same client ID. The CSE then tries to re-connect and the other CSE is disconnected by the broker. And then this client tries to reconnect. This will then repeat over and over again.  
   Identify the other client, stop it, and assign it a different CSE-ID.
1. **What does "cannot connect to broker: [Errno 49] Can't assign requested address" mean?**  
   You most likely want to connect to an MQTT broker that does not run on your local machine and you configured the listen interface to "127.0.0.1", which means that only local running services can be reached. Try to set the configuration *[client.mqtt].listenIF* to "0.0.0.0".

## Resources

1. **How can I add my own FlexContainer specializations to the ACME CSE?**  
   All resources and specializations are validated by the CSE. You can add your own specializations and validation policies by providing them in one or more separate files in the *import* directory. Those files must have the file extension ".ap". These files are read during the startup of the CSE.
   See [the documentation about Importing ](Importing.md#attributes) for further details.

## CSE Registrations

1. **Why does my CSE cannot register to another CSE?**  
   One problem could be that the CSE has no access rights to register to the target CSE. To solve this, the CSE's originator (ie. the CSE's CSE-ID, for example "/id-mn") must be added to the
   target CSE's configuration file. The configuration section [cse.registration] has a setting *allowedCSROriginators*, which is a comma separated list of originators. Add the registering CSE's
   CSE-ID (without a leading slash!) to this setting to allow access for this originator.  
   Example:

```ini
[cse.registration]
allowedCSROriginators=id-mn
```

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