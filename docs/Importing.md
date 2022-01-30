[← README](../README.md) 

# Importing

[Resources](#resources)  
[Attribute and Hierarchy Policies for FlexContainers](#flexcontainers)  
[Attribute Policies for Common Resources](#attributes)


<a name="resources"></a>
## Resources

During startup and CSE restart it is necessary to import a first set of resources to the CSE. This is done automatically by the CSE by running the script *startup.as* from the
[init](../init) directory.

Besides of a few mandatory resources additional resources can be imported to create a default resource structure for the CSE.

Not much validation, access control, or registration procedures are performed when importing resources this way.

### Mandatory Resources to the CSE

**Please note** that importing is required for creating the CSEBase, the administration AE, and a general-access ACP resources. Those are imported before all other resources, so that the CSEBase resource can act as the root for the resource tree and the permissions for 
the admin originator are created.


### Importing Other Resources

The script *startup.as* can be extended to import other resources as well, or it can call other scripts.

Another option to import resources automatically whenever the CSE starts or restarts is to have a script as an event handler for the [onStartup](ACMEScript-metatags.md#meta_onstartup) and *[onRestart](ACMEScript-metatags.md#meta_onrestart)* events.


### Referencing Configuration Settings

By using macros the initial resources can be kept independent from individual settings. Most [configuration](Configuration.md) settings can be referenced and used by a simple macro mechanism. For this a given macro name is enclosed by  ```${...}```, e.g. ```${cse.csi}```.

The following example shows the initial *CSEBase* resource definition from the *startup.as* script file:

```json
importraw 
{	
	"m2m:cb" : {
			"ri":   "${cse.ri}",
			"rn":   "${cse.rn}",
			"csi":  "${cse.csi}",
			"rr":   true,
			"csz":  [ "application/json", "application/cbor" ],
			"acpi": [ "${cse.csi}/acpCreateACPs" ]
	}
}
```

See the [documentation for scripts](ACMEScript.md).


<a name="flexcontainers"></a>
## Attribute and Hierarchy Policies for FlexContainers

The CSE uses attribute policies for validating the attributes of all supported resource types (internal to the *m2m* namespace). 
But for all &lt;flexContainer> specializations, e.g. for oneM2M's TS-0023 ModuleClasses, those attribute policies and the allowed &lt;flexContainer> hierarchy must be provided. This can be done by adding attribute policy files for import. 

Those files are imported from the common import / init directory. More than one such file can be provided, for example one per domain. The files must have the extension ".fcp". 

### Format

The format is a JSON structure that follows the structure described in the following code.  
Some of the fields are not yet used, but will supported by a future version of the CSE.

```JSON
// A file contains a list of Attribute Policies
attributePolicies = [
	
	// Each Attribute Policy is an object
	{
		// The specialisation's namespace and short name. Mandatory.
		"type"      : "namespace:shortname",

		// The specialisation's long name. Optional, and for future developments.
		"lname"     : "attributePolicyLongname",

		// The specialisation's containerDefinition. Optional, and for future developments.
		"cnd"       : "containerDefinition",

		// The specialisation's SDT type. Could be "device", "subdevice", "moduleclass", or "action". Optional, and for future developments.
		"sdttype"   : "SDTcontainerType",

		// A list of attributes. Each entry specifies a single attribute of the specialization. Optional.
        "attributes": [

			// A single attribute is an object.
            {
				// The attribute's short name. Mandatory.
				"sname" : "attributeShortName", 

				// The attribute's long name. Optional, and for future developments.
				"lname" : "attributeLongName", 

				// The attribute's data type. Mandatory, and one from this list:
				// 	- positiveInteger
				// 	- nonNegInteger
				//	- unsignedInt
				//	- unsignedLong
				//	- string
				//	- timestamp
				//	- list
				//	- dict
				//	- anyURI
				// 	- boolean
				//	- geoCoordinates
				"type"	: "attributeType", 

				// The "oc" field specifies the CREATE request optionality. Optional, and one from this list:
				//	- O  : Optional provided (default)
				// 	- M  : Mandatory provided
				//	- NP : Not provided
				"oc"	: "O|M|NP",

				// The "ou" field specifies the UPDATE request optionality. Optional, and one from this list:
				//	- O  : Optional provided (default)
				// 	- M  : Mandatory provided
				//	- NP : Not provided
				"ou"	: "O|M|NP",

				// The "od" field specifies the DISCOVERY request optionality. Optional, and one from this list:
				//	- O  : Optional provided (default)
				// 	- M  : Mandatory provided
				//	- NP : Not provided
				"od"	: "O|M|NP",

				// The "annc" field specifies whether an announced optionality. Optional, and one from this list:
				//	- OA : Optional announced (default)
				//	- MA : Mandatory announced
				//	- NA : Not announced
				"annc": "OA|MA|NA",

				// The attribute multiplicity. Optional, and one from this list:
				//	- 01  : The attribute is optional (default)
				//	- 01L : the attribute is an optional list
				//	- 1   : The attribute is mandatory
				// 	- 1L  : The attribute is a mandatory list
				"car" : "01|01L|1|1L",

				// A list of oneM2M resource types that use this attribute.
				// The folling special attribute types are also allowed:
				//	- ALL     : This attribute definition is suitable for all resource types for which it is a member
				//	- REQRESP : This attribute definition is suitable for request and response type resources.
				// This attribute is optional and used for the general attributePolicies, but not for flexContainers.
				"rtypes" : [ <ResourceType> ]
			}, 

		],

		// A list of child resource types. Optional.
		"children"  : [
			// This list consists of one or more strings, each of those is the name of an additional
			// child resource specialisation. It is not necessary to specify here the already allowed
			// child resource types of <flexContainer>.
		]
	}
]
```

**Examples**

The following examples show the attribute policies for the *binarySwitch* and *deviceLight* specialisations, both defined in oneM2M's TS-0023 specification.

```JSON
[
    // ModuleClass: binarySwitch (binSh)
    {
        "type"      : "cod:binSh",
        "lname"     : "binarySwitch",
        "cnd"       : "org.onem2m.common.moduleclass.binarySwitch",
        "attributes": [
            // DataPoint: dataGenerationTime
            { "sname" : "dgt", "lname" : "dataGenerationTime", "type" : "timestamp", "car" : "01" }, 
            // DataPoint: powerState
            { "sname" : "powSe", "lname" : "powerState", "type" : "boolean", "car" : "1" }
        ]
    }, 

    // DeviceClass: deviceLight
    {
        "type"      : "cod:devLt",
        "lname"     : "deviceLight",
        "cnd"       : "org.onem2m.common.device.deviceLight",
        "children"  : [
            "cod:fauDn", 
            "cod:binSh", 
            "cod:runSe", 
            "cod:color", 
            "cod:colSn", 
            "cod:brigs"
        ]
	}
]
```

<a name="attributes"></a>
## Attribute Policies for Common Resources

During startup the CSE reads the attribute policies for normal/common resources from the file [attributePolicies.ap](../init/attributePolicies.ap) in the import / init directory.

### Format

The format is a JSON structure that follows the structure described in the following code.  

```JSON
// The attributePolicy.ap file contains a dictionary of AttributePolicies
{

	// Each Attribute Policy is identified for an attribute's short name
	"attributeShortname": [

		// A list of attribute policies may be defined for each short name.
		// There might be some definitions for the same attribute that are defined
		// slighly from each other. Therefore, a list of resource types is given
		// for each definition for which that definition is valid.
		// See the attributes definition for flexContainer attribute policies above.
			
		{
			// The rtypes definition is mandatory here. It defines a list of oneM2M
			// resource types for which this definition is valid. This way slight
			// differences in attributes in some resource can be distinguished.
			// The special names "ALL" (short for all resource types) and "REQRESP"
			// (for attributes in requests and responses) can be used accordingly.
			"rtype" : [ "<resource type>", "<resource type>" ]

			// The other definitions that can be used are (see above for details):
			//
			"lname" : ...
			"ns" : ...
			"type" : ...
			"car" : ...
			"oc" : ...
			"ou" : ...
			"od" : ...
			"annc" : ...
		}
	]
}
```

**Example**

The following gives an example for the attribute *ty* (*resourceType*).

```JSON
{
	"ty": [
		{
			"rtypes": [ "ALL" ],
			"lname": "resourceType",
			"ns": "m2m",
			"type": "positiveInteger",
			"car": "1",
			"oc": "NP",
			"ou": "NP",
			"od": "O",
			"annc": "NA"
		}
	]
}
```
[← README](../README.md) 
