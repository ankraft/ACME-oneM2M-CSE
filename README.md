# ACME oneM2M CSE
An open source CSE Middleware for Education.

Version 0.1

## Introduction

This CSE implements a subset of the oneM2M standard specializations (see [http://www.onem2m.org](http://www.onem2m.org)). The intention is to provide an easy to install, extensible, and easy to use and maintain CSE for educational purposes. Please also see the discussion on [Limitations](#limitations) below.

![](docs/images/webui.png)


## Prerequisites
In order to run the CSE the following prerequisites must be checked:

- **Python 3.8** : Install this or a newer version of Python with your favorite package manager.
- **flask**: The CSE uses the [Flask](https://flask.palletsprojects.com/) web framework. Install it by running the pip command:
  
  		pip3 install flask

- **psutil**: The [psutil](https://pypi.org/project/psutil/)
 package is used to gather various system information for the CSE's hosting node resource. Install it by running the pip command:

		pip3 install psutil

- **requests**: The CSE uses the [Requests](https://requests.readthedocs.io) HTTP Library to send requests vi http. Install it by running the pip command:

		pip3 install requests

- **tinydb** : To store resources the CSE uses the lightweight [TinyDB](https://github.com/msiemens/tinydb) document database. Install it by running the pip command:

		pip3 install tinydb

## Installation and Configuration

The ACME CSE is installed by copying the whole distribution to a new directory. You also need to copy the configuration file [acme.ini.default](acme.ini.default) and make adjustments to it.

	cp acme.ini.default acme.ini

Please have a look at the configuration file. All the CSE's settings are read from this file. 

There are a lot of individual things to configure here. Mostly, the defaults should be sufficient, but individual adaptions can be applied to each of the sections.

## Running

### Running the Notifications Server

You might want to have a Notifications Server running first before starting the CSE. The Notification Server provided here in the [tools/notificationServer](tools/notificationServer) directory provides a very simple implementation that receives and answers all notification requests.

See the [README](tools/notificationServer/README.md) file for further details.

### Running the CSE

You can start the CSE by simply running it from a command line:

	python3 acme.py

In this case the configuration file *acme.ini* must be in the same directory.

In additions, you can provide additional command line arguments that will override the respective values from the configuration file:

- **-h**, **--help** : show a help message and exit.
- **--config CONFIGFILE**: Specify a configuration file that is used instead of the default (*acme.ini*) one.
- **--reset-db**: Reset and clear the database when starting the CSE.
- **--log-level {info, error, warn, debug, off}**: Set the log level, or turn logging off.
- **--import-directory IMPORTDIRECTORY**: Specify the import directory.


### Stopping the CSE

The CSE can be stopped by pressing *CTRL-C* **once** on the command line. 

Please note, that the shutdown might take a moment (e.g. gracefully terminating background processes, writing database caches, sending notifications etc). 

**Being impatient and hitting *CTRL-C* twice might lead to data corruption.**


### Importing Resources

During the startup of the CSE it is possible to import resources into to CSE. Each single resource is read from a file in the resource directory specified in the configuration file. The default directory is the sub-directory *init* under the current working directory.

**Please note** that importing is required for the creating the CSEBase resource and at least one ACP resource. Those two are imported before all other resources, so that the CSEBase resource can act as the root for the resource tree. The ACP resource must be the one that is assigned as the default ACP by the CSE for resources that don't specify an ACP on their own.

The filenames for those resources must be:

- *csebase.json* for the CSEBase, and
- *acp.admin.json* for a default ACP.

All other resources in the resource directory are read in alphabetical order and are added (created) to the CSE's resource tree. 

If the filename contains the substring *update*, then the resource specified by the resource's *ri* attribute is updated instead of created.

A minimal set of resources is provided in the [init](init) directory. Definitions for a more sophisticated setup can be found in the [tools/init.example](tools/init.example) directory. To use this example, you can either copy the resources to the *init* directory or change the "cse -> resourcesPath" entry in the *acme.ini* configuration file.

The directory [tools/resourceTemplates](tools/resourceTemplates) contains templates for supported resource types. Please see the [README](tools/resourceTemplates/README.md) there for further details.


## Web UI

The Web UI is by default enabled and reachable under the (configurable) path *&lt;host>/webui*.

- To login you need to specify a valid originator.
- Beside of the default *CSEBase* resource you can specify a different resource identifier as the root of the resource tree.
- You can navigate the resource tree with arrow keys.
- You can switch between short and long attribute names.


### REST UI

The web ui also provides a REST UI where you can send REST requests directed at resources on the CSE.

![](docs/images/webui-REST.png)

## Remote CSE

When a CSE is configured as an MN-CSE of ASN-CSE it can connect to a remote CSE, respectively an IN-CSE and MN-CSE can receive connection requests from those CSE types. A *remoteCSE* resource is created in case of a successful connection. A CSE checks regularly the connection to other remote CSEs and removes the *remoteCSE* if the connection could not been established.

Announced resources are currently **not** supported by this implementation. But you can issue transfer requests to a remote CSE via its *remoteCSE* resource. These requests are forwarded by the CSE.

You must configure the details of the remote CSE in the configuration file.


## Nodes and Applications

Currently, two component implementations are provided in addtion to the main CSE. They serve as examples how implement components that are hosted by the CSE itself.

### CSE Node

This component implements a &lt;node> resource that provides additional information about the actual node (system) the CSE is running on. These are specializations of &lt;mgmtObj>'s, namely battery, memory, and device information.

It can be enabled/disabled and configured in the **[app.csenode]** section of the configuration file.


### Statistics AE

The component implements an &lt;AE> resource that provides statistic information about the CSE. It defines a proprietary &lt;flexContainer> specialization that contains custom attributes for various statistic information, and which is updated every few seconds.

It can be enabled/disabled and configured in the **[app.statistics]** section of the configuration file.

### Developing Nodes and AEs

You can develop your own components by following the pattern of those two components:

- Implement a class with either *AEBase* or *NodeBase* as a base class. This will create an &lt;AE> or &lt;node> resource for you.
-  Implement a worker method and start it in the *\_\_init\_\_()* method. This method is called regularly in the background. This worker method can implement the main functionality of the &lt;AE> or &lt;node>.
-  Implement a *shutdown()* method that is called when the CSE shuts down.
-  Add your new component to the following methods in [acme/CSE.py](acme/CSE.py):
	-  *startApps()*: starting your component.
	-  *stopApps()*: shutting down your component.

There are more helper methods provided by the common *AppBase* base class, e.g. to send requests to the CSE via Mca.


## Integration Into Other Applications

It is possible to integrate the CSE into other applications, e.g. a Jupyter Notebook. In this case you would possibly like to provide startup arguments, for example the path of the configuration file or the logging level, directly instead of getting them from *argparse*.

You might want to get the example from the starter file [acme.py](acme.py) where you could replace the line:

```python
CSE.startup(parseArgs())
```

with a call to the CSE's *startup()* function:

```python
CSE.startup(None, configfile=defaultConfigFile, loglevel='error')
```

Please note that in case you provide the arguments directly the first argument needs to be `None`. 

The names of the *argparse* variables can be used here, and you may provide all or only some of the arguments. Please note that you need to keep the import statements at the top of that file (or copy them to your application).


## URL Mappings

As a convenience to access resources on a CSE and to let requests look more like "normal" REST request you can define mappings. The format is a path that maps to another path and arguments. When issued a request to one of those mapped paths the http server issues a redirect to the other path.

For example, the path */access/v1/devices* can be mapped to */cse-mn?ty=14&fu=1&fo=2&rcn=8* to easily retrieve all nodes from the CSE.

See the configuration file for more examples.

## Limitations
- **This is by no means a fully compliant, secure or stable CSE! Don't use it in production.**
- This CSE is intended for educational purposes. The underlying database system is not optimized in any way for high-volume, high-accessibility.
- No support for https yet.
- Security: None. Please contact me if you have suggestions to improve this.
- Unsupported resource types are just stored, but no check or functionality is provided for those resources. The same is true for unknown resource attributes. Only a few attributes are validated.

## Supported Resource Types and Functionalities
The CSE supports the following oneM2M resource types:

- **CSEBase (CB)**
- **Access Control Policy (ACP)**
- **Remote CSE (CSR)**  
Announced resources are yet not supported. Transit request, though, to resources on the remote CSE are supported.
- **Application Entity (AE)**
- **Container (CNT)**
- **Content Instance (CIN)**
- **Subscription (SUB)**  
Notifications via http to a direct url or an AE's Point-of-Access (POA) are supported as well.
- **Group (GRP)**  
The support includes requests via the *fopt* (fan-out-point) virtual resource.
- **Node (NOD)**  
The support includes the following **Management Object (mgmtObj)** specializations:
	- **Firmware (FWR)**
	- **Software (SWR)**
	- **Memory (MEM)**
	- **AreaNwkInfo (ANI)**
	- **AreaNwkDeviceInfo (ANDI)**
	- **Battery (BAT)**
	- **DeviceInfo (DVI)**
	- **DeviceCapability (DVC)**
	- **Reboot (REB)**
	- **EventLog (EVL)**
- **FlexContainer Specializations**  
Any specializations is supported. There is no check performed against a schema (e.g. via the *cnd* attribute).

Resources of any other type are stored in the CSE but no further processed and no checks are performed on these resources. The type is marked as *unknown*.


## Third-Party Components

### CSE
- Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/), BSD 3-Clause License
- Requests: [https://requests.readthedocs.io/en/master/](https://requests.readthedocs.io/en/master/), Apache2 License
- TinyDB: [https://github.com/msiemens/tinydb](https://github.com/msiemens/tinydb), MIT License
- PSUtil: [https://github.com/giampaolo/psutil](https://github.com/giampaolo/psutil), BSD 3-Clause License


### UI Components
- TreeJS: [https://github.com/m-thalmann/treejs](https://github.com/m-thalmann/treejs), MIT License
- Picnic CSS : [https://picnicss.com](https://picnicss.com), MIT License


## Roadmap & Backlog
- CSE: Announcements
- CSE: Better resource validations
- CSE: Timeseries
- CSE: Support discovery also for other request types
- UI: Support for resource specific actions (e.g. latest, oldest)
- UI: Graph for Container reosurces
- Importer: Automatically import/update resources when the CSE is running
- App development: support more specializations

## The Messy Details

![](docs/images/cse_uml.png)

## License
BSD 3-Clause License for the CSE and its native components and modules. Please see the individual licenses of the used third-party components.
