# FlexContainer Specialization Policies

This article describes the flexContainer specialization policies used by the ACME CSE.

For all &lt;flexContainer> specializations, e.g. for oneM2M's TS-0023 ModuleClasses, the [attribute policies](../development/AttributePolicies.md) and the allowed &lt;flexContainer> hierarchy must be provided. 

The files for &lt;flexContainer> specializations are also imported from the [init](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init){target=_new} and [secondary init](../setup/Running.md#secondary-init-directory) directory. More than one such file can be provided, for example one per domain. The files must have the extension `.fcp`. 

The format is a JSON structure that follows the structure described in the following code.  

```json title="FlexContainer Specialization Policy Format"
[
// A file contains a list of FlexContainer Specialization Policies
specializationPolicy = [
	
	// Each FlexContainer Specialization Policies is a JSON object
	{
		// The specialisation's namespace and short name. 
		// Mandatory.
		"type"      : "namespace:shortname",

		// The specialisation's long name. 
		// Optional, and for future developments.
		"lname"     : "attributePolicyLongname",

		// The specialisation's containerDefinition. 
		// Mandatory for flexContainers, but can be empty to prevent warnings.
		"cnd"       : "containerDefinition",

		// The specialisation's SDT type. 
		// Could be one of "device", "subdevice", "moduleclass", or "action". 
		// Optional, and for future developments.
		"sdttype"   : "SDTcontainerType",

		// A list of attribute policies. 
		// Each entry specifies a single attribute of the specialization.
		// Optional.
        "attributes": [ attributePolicy, attributePolicy, ... ],

		// A list of child resource types. Optional.
		"children"  : [
			// This list consists of one or more strings, each of those is the name of an additional
			// child resource specialisation. It is not necessary to specify here the already allowed
			// child resource types of <flexContainer>.
		]
	}]
]
```
The *attributePolicies* are the same as described in the [Attribute Policies](../development/AttributePolicies.md) article.

## Examples

The following examples show the attribute policies for the *binarySwitch* and *deviceLight* specialisations, both defined in oneM2M's TS-0023 specification.

```json title="FlexContainer specialization binarySwitch.fcp"
[
	// ModuleClass: binarySwitch (binSh)
	{
		"type"      : "cod:binSh",
		"lname"     : "binarySwitch",
		"cnd"       : "org.onem2m.common.moduleclass.binarySwitch",
		"attributes": [
			// DataPoint: dataGenerationTime
			{
				"sname" : "dgt", 
				"lname" : "dataGenerationTime", 
				"type" : "timestamp", 
				"car" : "01"
			}, 
			
			// DataPoint: powerState
			{ 
				"sname" : "powSe", 
				"lname" : "powerState", 
				"type" : "boolean", 
				"car" : "1" 
			}
		]
	}
]
```

```json title="deviceLight.fcp"
[
    // ModuleClass: binarySwitch (binSh)
    {
        "type"      : "cod:binSh",
        "lname"     : "binarySwitch",
        "cnd"       : "org.onem2m.common.moduleclass.binarySwitch",
        "attributes": [
            // DataPoint: dataGenerationTime
            { 
				"sname" : "dgt",
				"lname" : "dataGenerationTime",
				"type" : "timestamp",
				"car" : "01"
			}, 
            
			// DataPoint: powerState
            { 
				"sname" : "powSe", 
				"lname" : "powerState", "type" :
				"boolean", 
				"car" : "1" 
			}
        ]
    }, 

    // DeviceClass: deviceLight
    {
        "type"      : "cod:devLt",
        "lname"     : "deviceLight",
        "cnd"       : "org.onem2m.common.device.deviceLight",

		// The allowed child resource types
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

