[← README](../README.md) 

# Importing

[Resources](#resources)  
[Importing Attribute Policies for FlexContainers](#importing-attribute-policies-for-flexcontainers)

## Resources

During startup it is necessary to import resources into to CSE. Each resource is read from a single file in the [init](../init) resource directory specified in the configuration file. Besides of a few mandatory resources additional resources can be imported to create a default resource structure for the CSE.

Not much validation, access control, or registration procedures are performed for imported resources.

### Importing Mandatory Resources

**Please note** that importing is required for creating the CSEBase resource and at least three (admin) ACP resources. Those are imported before all other resources, so that the CSEBase resource can act as the root for the resource tree. The *admin* ACP is used to access resources with the administrator originator. The *default* ACP resource is the one that is assigned for resources that don't specify an ACP on their own.

The filenames for these resources must be:

- [csebase.json](../init/csebase.json) for the CSEBase.
- [acp.admin.json](../init/acp.admin.json) for the admin ACP.
- [acp.default.json](../init/acp.default.json) for the default ACP.
- [acp.csebaseAccess.json](../init/acp.csebaseAccess.json) for granting AE's and remote CSE's access to the CSEBase. This ACP is dynamically filled with permissions when an AE or remote CSE registers.

### Importing Other Resources

After importing the mandatory resources all other resources in the [init](../init) directory are read in alphabetical order and are added (created) to the CSE's resource tree. Imported resources must have a valid *acpi* attribute, because no default *acpi* is assigned during importing.

### Updating Resources

If the filename contains the substring *update*, then the resource specified by the resource's *ri* attribute is updated instead of created.

### Referencing Configuration Settings

By using macros the initial resources can be kept rather independent from individual settings. Most [configuration](Configuration.md) settings can be referenced and used by a simple macro mechanism. For this a given macro name is enclosed by  ```${...}```, e.g. ```${cse.csi}```.

The following example shows the initial *CSEBase* resource definition.

```json
{	"m2m:cb" : {
		"ri" : "${cse.ri}",
		"ty" : 5,
		"rn" : "${cse.rn}",
		"csi" : "${cse.csi}",
		"acpi" : [ "${cse.security.adminACPI}" ]
	}
}
```

### Examples & Templates

A minimal set of resources is provided in the [init](../init) directory. Definitions for a more sophisticated setup can be found in the [tools/init.example](../tools/init.example) directory. To use these examples, you can either copy the resources to the *init* directory or change the "cse -> resourcesPath" entry in the *acme.ini* configuration file.

The directory [tools/resourceTemplates](../tools/resourceTemplates) contains templates for supported resource types. Please see the [README](../tools/resourceTemplates/README.md) there for further details.


## Importing Attribute Policies for FlexContainers

The CSE uses attribute policies for validating the attributes of all supported resource types (internal to the *m2m* namespace). But for all &lt;flexContainer> specializations, e.g. for oneM2M's TS-0023 ModuleClasses, those attribute policies must be provided. This can be done by adding attribute policy files for import. 

Those files are imported from the common import / init directory. More than one such file can be provided, for example one per domain. The files must have the extension ".ap". 

### Format

The format is a JSON structure that follows the structure described in the following code example.
Some of the fields are not yet used, but will supported by a future version of the CSE.

```
// A file contains a list of Attribute Policies
accessPolicies = [
	
	// Each Attribute Policy is an object
	{
		// The specialisation's namespace and short name. Mandatory.
		"type"      : "namespace:shortname",

		// The specialisation's long name. Optional, and for future developments.
		"lname"     : "attributePolicyLongname",

		// The specialisation's containerDefinition. Optional, and for future developments.
		"cnd"       : "containerDefinition",

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
				"car" : "01|01L|1|1L" 
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

[← README](../README.md) 
