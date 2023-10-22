[← README](../README.md) 

# FAQ

## Network

1. **How can I access the CSE from remote/another computer on my network?**  
   By default the CSE binds to the *localhost/loopback* interface, meaning it **will not** be able to receive requests from remote machines. To make it accessible from a remote machine you need to bind the CSE's http server or MQTT client to another network interface, or address. This can be done in the *[http]* and *[mqtt]* sections of the configuration file. 
   Setting the listen interface to "0.0.0.0" binds the http server to all available interfaces.  
   The reason for this default setting is security: making the CSE accessible from remote machines should be a conscious decision and not the default.


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
1. **Is there a way to enable CORS (Cross-Origin Resource Sharing) for ACME?**  
   CORS allows browser-based applications to access resources on a web server outside the domain of the
   original hosting web server. This could be useful, for example, to allow a web UI that is hosted on 
   one web server to access oneM2M resources that are hosted on external CSE(s).  
   ACME's http binding implementation supports CORS. This feature is disabled by default and can be 
   enabled by setting the configuration setting *[http.cors].enable* to *true*. CORS access is granted
   by default to all HTTP resources. This can be limited by specifying the resource paths in the 
   configuration setting *[http.cors].resources*.  
   **Note**: Most modern web browsers don't allow unsecured (http) access via CORS. This means that the
   CSE must be configured to run the http server with TLS support enabled (https).


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

1. **Why does my CSE not register to another CSE or announce resources?**  
   One problem could be that the CSE has no access rights to register to the target CSE. To solve this, the CSE's originator (ie. the CSE's CSE-ID, for example "/id-mn") must be added to the target CSE's configuration file. The configuration section [cse.registration] has a setting *allowedCSROriginators*, which is a comma separated list of originators. Add the registering CSE's
   CSE-ID (**without a leading slash!**) to this configuration section to allow access for this originator.  
   
   This must be done for both the CSEs that want to register and announce resources.  

   Example for an IN-CSE with the CSE-ID "*/id-in*":

	```ini
	[cse.registration]
	allowedCSROriginators=id-mn
	```
  
   And for an MN-CSE with the CSE-ID "*/id-mn*":

	```ini
	[cse.registration]
	allowedCSROriginators=id-in
	```
  

## Performance

1. **How to increase the performance of ACME CSE?**  
   The log output provides useful information to analyze the flows of requests inside the CSE. However, it reduces the performance of the CSE by a lot. So, reducing the log level to *info* or *warning* already helps. This can be done in the *[logging]* section of the configuration file, or by pressing *L* on the console to change the logging level to the desired value.  
   Another option is to change the database to *memory* mode. This means that all database access happens in memory and not on disk. But please be aware that this also means that all data will be lost when the CSE terminates!  
   Lastly, the ACME CSE can be run with Python 3.11, which is way faster than previous versions of Python.

1. **Increase database performance with *disk* mode**  
   When running the CSE with the database mode set to *disk* (ie. store the database on disk rather then in memory) one can improve the performance by increasing the time before data is actually written to disk. The default is 1 second, but it can be increased as necessary.  
   Be aware, though, that the risk of losing data increases with higher delays in case of a crash or when the CSE shutdown is interrupted.

	```ini
	[database]
	writeDelay=10
	```


## Web UI

1. **Can I use the web UI also with other CSE implementations?**  
    The web UI can also be run as an independent application.  Since it communicates with the CSE via the Mca interface it should be possible to use it with other CSE implementations as well as long as those third party CSEs follow the oneM2M http binding specification. It only supports the resource types that the ACME CSE supports, but at least it will present all other resource types as *unknown*.


## Console and Text UI

1. **Some of the tables, text graphics etc are not aligned or correctly displayed in the console**  
	Some mono-spaced fonts don't work well with UTF-8 character sets and graphic elements. Especially the MS Windows *cmd.exe* console seems to have problems.
	Try one of the more extended fonts like *JuliaMono* or *DejaVu Sans Mono*.
1. **There is an error message "UnicodeEncodeError: 'latin-1' codec can't encode character"**  
	This error message is shown when the console tries to display a character that is not supported by the current console encoding. Try to set the console encoding to UTF-8 by setting the environment variable *PYTHONIOENCODING* to *utf-8*, for example:

	```bash
	export PYTHONIOENCODING=utf-8
	``` 
	
## Operating Systems

### RaspberryPi

1. **Restrictions on 32 bit Systems**  
	Currently, the normally installed Raspbian OS is a 32 bit system. This means that several restrictions apply here, such as the maximum date supported (~2038). It needs to be determined whether these restrictions still apply when the 64 bit version of Raspbian is available.
1. **The console or the text UI is not displayed correctly**  
	It could be that the OS's terminal applications doesn't support rendering of extra characters, like line graphics. One recommendation on Linux systems is to install the [Mate Terminal](https://wiki.mate-desktop.org/mate-desktop/applications/mate-terminal/), which supports UTF-8 and line graphics. It also renders the output much faster.

	```bash
	sudo apt-get install mate-terminal
	```
1. **Timing Issues**  
	 Also, the resolution of the available Python timers is rather low on Raspbian, and background tasks might not run exactly on the desired time.  
	 Unfortunately, this is also why sometimes a couple of the CSE's tests cases may fail randomly.


[← README](../README.md) 