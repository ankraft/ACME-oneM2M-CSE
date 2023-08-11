[← README](../README.md) 

# CSE Startup, Importing Resources and Other Settings

[Initial Resources](#resources)  
[Attribute and Hierarchy Policies for FlexContainer Specializations](#flexcontainers)  
[Attribute Policies for Common Resources and Complex Types](#attributes)  
[Help Documentation](#help-documentation)


<a name="resources"></a>
## Initial Resources

During CSE startup and restart it is necessary to import a first set of resources to the CSE. This is done automatically by the CSE by running a script that has the [@init](ACMEScript-metatags.md#meta_init) meta tag set. By default this is the [init.as](../init/init.as) script from the [init](../init) directory.

Not much validation, access control, or registration procedures are performed when importing resources this way.

See also [@init meta tag](ACMEScript-metatags.md#meta_init)

**Mandatory Resources to the CSE**

Please note that importing is required for creating the CSEBase, the administration AE, and a general-access ACP resources. Those are imported before all other resources, so that the CSEBase resource can act as the root for the resource tree and the permissions for the admin originator are created.

**Other Resources**

Another option to import more resources automatically whenever the CSE starts or restarts is to have a script as an event handler for the *[onStartup](ACMEScript-metatags.md#meta_onstartup)* and *[onRestart](ACMEScript-metatags.md#meta_onrestart)* events.


### Referencing Configuration Settings

By using macros the initial resources can be kept independent from individual settings. 
Most [configuration](Configuration.md) settings can be referenced and used by a simple macro mechanism.
For this a given macro name is enclosed by  ```${...}```, e.g. ```${cse.cseID}```. 
The following example shows the initial *CSEBase* resource definition from the *startup.as* script file:

```list
(import-raw 
	(get-config "cse.originator") 
	{"m2m:cb": {
		"ri":   "${ get-config \"cse.resourceID\" }",
		"rn":   "${ get-config \"cse.resourceName\" }",
		"csi":  "${ get-config \"cse.cseID\" }",
		"rr":   true,
		"csz":  [ "application/json", "application/cbor" ],
		"acpi": [ "${ get-config \"cse.cseID\" }/acpCreateACPs" ],
		"poa":  [ "${ get-config \"http.address\" }" ]
	}})
```

See the [documentation for scripts](ACMEScript.md).


<a name="flexcontainers"></a>
## FlexContainer Specializations Attribute and Hierarchy Policies

The CSE uses attribute policies for validating the attributes of all supported resource types (internal to the *m2m* namespace). 
But for all &lt;flexContainer> specializations, e.g. for oneM2M's TS-0023 ModuleClasses, those attribute policies and the allowed &lt;flexContainer> hierarchy must be provided. This can be done by adding attribute policy files for import. 

Those files are imported from the common import / init directory. More than one such file can be provided, for example one per domain. The files must have the extension ".fcp". 

### Format

The format is a JSON structure that follows the structures described in the following codes.  
Some of the fields are not yet used, but will supported by a future version of the CSE.

```jsonc
// A file contains a list of Attribute Policies
attributePolicies = [
	
	// Each Attribute Policy is an object
	{
		// The specialisation's namespace and short name. Mandatory.
		"type"      : "namespace:shortname",

		// The specialisation's long name. Optional, and for future developments.
		"lname"     : "attributePolicyLongname",

		// The specialisation's containerDefinition. Must be present for flexContainers, but can be empty to prevent warnings.
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
				//	- dict - any anonymous complex structure. This should be avoided and be replaced by a complex type name
				//	- adict (anonymous dict)
				//	- anyURI
				// 	- boolean
				//	- enum
				//	- geoCoordinates
				//
				//	In addition, the *attributeType* can be the name of any defined complex type. This
				//	complex type must be defined in any of the attribute policy files.
				"type"	: "attributeType", 

				// The sub-type of a list type.
				//	This can be any of the types defined for *type*, or a complex type.
				"ltype" : "type",

				//	Definition of enumeration values. This can only be an integer value, or range definitions
				//	in the format "start..end" that evaluate to all the integer values of the given range.
				"evalues" : [ 1, 2, "3..5", 6 ],

				//	Definition of an enumeration type and an alternative to "evalues".
				//	This is an enumerated data type name that is referenced. 
				"etype" : "enumeratedDataType",

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

```jsonc
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
## Attribute Policies for Common Resources, Complex Types and Enum Types

During startup the CSE reads the attribute policies for common resource types and complex type definitions from the files with the extension ".ap" in the *init* directory, for example [attributePolicies.ap](../init/attributePolicies.ap). More than one attribute file can be defined.  
The attributes for attribute policies are the same as for the &lt;flexContainer> attribute definitions above.

In addition, enumeration types are defined in files with the extension ".ep". 

### Formats

The format is a JSON structure that follows the structure described in the following code.  

```jsonc
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
			// The special names "ALL" (short for all resource types), "REQRESP"
			// (for attributes in requests and responses), and "COMPLEX" (for an attribute
			// that belongs to a complex type definition) can be used accordingly.
			"rtype" : [ "<resource type>", "<resource type>" ],

			// The name of a complex type this attribute defintion belongs to. This
			// attribute is only be present in an attribute policy definition when
			// "rtype" is set to "COMPLEX".
			"ctype" : "<complex type name>",

			// The other definitions that can be used are (see above for details):
			//
			"lname" : ...
			"ns" : ...
			"type" : ...
			"ltype" : ...
			"etype" : ...
			"evalues" : ...
			"car" : ...
			"oc" : ...
			"ou" : ...
			"od" : ...
			"annc" : ...
		}
	]
}
```

The format for enumeration data type definitions is a bit simpler:

```jsonc
// The attributePolicy.ep file contains a dictionary of enumeration data types
{

	// Each enumeration definition is identified by its name. It is a dictionary.
	"enumerationType": {

		// A single enumeration definition is key value pair. The key is the enumeration
		// value, the value is the interpretation of that value.
		"<enumeration value>" : "<enumeration interpretation>"

		// This defines a range of values. Each one gets the same interpretation assigned.
		"<enumeration value start>..<enumeration value end>" : "<enumeration interpretation>"
	}
}
```

**Example**

The following gives an example for the attribute *ty* (*resourceType*).

```jsonc
{
	"rn": [
		{
			"rtypes": [ "ALL" ],
			"lname": "resourceName",
			"ns": "m2m",
			"type": "string",
			"car": "1",
			"oc": "O",
			"ou": "NP",
			"od": "O",
			"annc": "NA"
		}
	],
	"ty": [
		{
			"rtypes": [ "ALL" ],
			"lname": "resourceType",
			"ns": "m2m",
			"type": "enum",
			"etype": "m2m:resourceType",
			"car": "1",
			"oc": "NP",
			"ou": "NP",
			"od": "O",
			"annc": "NA"
		}
	]
}
```

**Complex Type Attribute**

The following example shows the definition of the attribute *operator* (optr) that
belongs to the complex type *m2m:evalCriteria*.

```jsonc
{
	"optr": [
		{
			"rtypes": [ "COMPLEX" ],
			"ctype": "m2m:evalCriteria",
			"lname": "operator",
			"ns": "m2m",
			"type": "enum",
			"etype": "m2m:evalCriteriaOperator",
			"car": "1"
		}
	]
}
```

**Enumeration Data Type**

The following example show the definition for the enumeration data types used in the examples above.

```jsonc
{
	"m2m:evalCriteriaOperator" : {
		"evalues": [ "1..6" ]
	},
	"m2m:resourceType" : {
		"evalues" : [ "1..5", 9, "13..17", 23, 24, "28..30", 48, 58, 60, 65, 
					  "10001..10005", 10009, "10013..10014", 10016, "10028..10030", 10060, 10065 ]
	}
}
```


<a name="help-documentation"></a>
## Help Documentation

Some CSE components provide a markdown documentation to the user, such as the Text UI. That documentation is imported from the 
[init](../init) directory as well. The file extension for documentation files is ".docmd". 

In the documentation file individual sections are separated by markdown level 1 headers where the header title is the help topic
for the following section, which is a markdown text block with the help text.

**Example**

```markdown
# Topic 1

Some help text for topic 1.

## Help sub section

# Topic 2
...
```






[← README](../README.md) 
