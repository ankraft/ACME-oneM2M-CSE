# Attribute Policies

This article describes the attribute policies used by the ACME CSE. 

During startup the CSE reads the attribute policies for common resource types and complex type definitions from the files with the extension `.ap` in the [init](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init){target=_new} and [secondary init](../setup/Running.md#secondary-init-directory) directory, for example [attributePolicies.ap](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init/attributePolicies.ap){target=_new}. More than one attribute policy file can be added.


## Attribute Policy Format

The CSE uses *attribute policies* for validating the attributes of all the supported resource types. The following code specifies the JSON structure to describe a single atttribute. 

Some of the fields are not yet used, but will supported by a future version of the CSE. 

```json title="Attribute Policy Format"
// A single attribute is a JSON object.
{
	// A list of oneM2M resource types that use this attribute.
	// This attribute is optional and used for the general 
	// attributePolicies, but not for flexContainers.
	//
	// The folling special attribute types are also allowed:
	//
	// - ALL     : This attribute definition is suitable for all resource types 
	//             for which it is a member
	// - REQRESP : This attribute definition is suitable for request and 
	//             response type resources.
	// - COMPLEX : This attribute definition is suitable for complex type
	"rtypes" : [ <ResourceType> ]

	// The attribute's short name. 
	// Mandatory.
	"sname" : "attributeShortName", 

	// The attribute's long name. 
	// Optional, and for future developments.
	"lname" : "attributeLongName", 

	// The attribute's namespace.
	// Optional, the default is "m2m".
	"ns"	: "namespace",

	// The attribute's data type. 
	// Mandatory, and one from this list:
	// 
	// - integer
	// - positiveInteger
	// - nonNegInteger
	// - unsignedInt
	// - unsignedLong
	// - string
	// - timestamp
	// - list
	// - dict - any anonymous complex structure. This should be avoided and 
	//          be replaced by a complex type name
	// - adict (anonymous dict)
	// - anyURI
	// - boolean
	// - enum
	// - geoCoordinates
	// - schedule
	// - base64
	// - duration
	//
	// In addition to the list above, the *attributeType* can be the name of any defined
	// complex type. This complex type must be defined in any of the attribute policy files.
	"type"	: "attributeType", 

	// The sub-type of a list type.
	// This can be any of the types defined for *type*, or a complex type.
	"ltype" : "type",

	// The complex type name for a complex type attribute.
	// This is the name of the parent complex type to which an attribute belongs.
	// This attribute is only present in an attribute policy definition when
	// this attribute belongs to a complex type.
	"ctype" : "complexType",

	// Definition of enumeration values.
	// This can only be an integer value, or range definitions in the format
	// "start..end" that evaluate to all the integer values of the given range.
	"evalues" : [ 1, 2, "3..5", 6 ],

	// Definition of an enumeration type and an alternative to "evalues".
	// This is an enumerated data type name that is referenced. 
	"etype" : "enumeratedDataType",

	// The "oc" field specifies the CREATE request optionality. Optional, and one from this list:
	//	- O  : Optional provided (default)
	// 	- M  : Mandatory provided
	//	- NP : Not provided
	"oc"	: "O|M|NP",

	// The "ou" field specifies the UPDATE request optionality. 
	// Optional, and one from this list:
	//
	// - O  : Optional provided (default)
	// - M  : Mandatory provided
	// - NP : Not provided
	"ou"	: "O|M|NP",

	// The "od" field specifies the DISCOVERY request optionality. 
	// Optional, and one from this list:
	//
	// - O  : Optional provided (default)
	// - M  : Mandatory provided
	// - NP : Not provided
	"od"	: "O|M|NP",

	// The "annc" field specifies whether an announced optionality. 
	// Optional, and one from this list:
	//
	// - OA : Optional announced (default)
	// - MA : Mandatory announced
	// - NA : Not announced
	"annc": "OA|MA|NA",

	// The attribute multiplicity. 
	// Optional, and one from this list:
	//
	// - 01  : The attribute is optional (default)
	// - 01L : the attribute is an optional list
	// - 1   : The attribute is mandatory
	// - 1L  : The attribute is a mandatory list
	"car" : "01|01L|1|1L",
}
```

## Complex Types 

Complex types are defined in the attribute policy files as well. Complex types are defined in files with the extension `.ap`. The CSE reads the complex type definitions from the [init](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init){target=_new} and [secondary init](../setup/Running.md#secondary-init-directory) directory, for example [complexTypePolicies.ap](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init/complexTypePolicies.ap){target=_new}. More than one complex type file can be provided.

Complex types are defined indirectly by assigning attributes to them. Attributes for a complex types are defined in the same way as for common resource types. The only difference is that the *ctype* field is set to the name of the complex type the attribute belongs to. If an attribute belongs to more than one complex type, the attribute definition is repeated for each complex type.

The *rtypes* field must by set to "COMPLEX" for complex type attributes. 

The following example shows the definition of an attribute that belongs to multiple complex types.

```json title="Complex Type Attribute Example"
	"dur": [
		// This attribute is defined for the complex type m2m:batchNotify
		{
			"rtypes": [ "COMPLEX" ],
			"ctype": "m2m:batchNotify",
			"lname": "duration",			
			"ns": "m2m",
			"type": "duration",
			"car": "01"
		},

		// This attribute is defined for the complex type m2m:misingData
		{
			"rtypes": [ "COMPLEX" ],
			"ctype": "m2m:missingData",
			"lname": "duration",			
			"ns": "m2m",
			"type": "duration",
			"car": "1"
		}
	]
```


## Enumeration Data Types

In addition to the attribute and complex type policies defined above, enumeration types are defined in files with the extension `.ep`. The CSE reads the enumeration data types from the [init](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init){target=_new} and [secondary init](../setup/Running.md#secondary-init-directory) directory, for example [enumTypesPolicies.ep](https://github.com/ankraft/ACME-oneM2M-CSE/blob/master/acme/init/enumTypesPolicies.ep){target=_new}. More than one enumeration data type file can be provided.

The format is a JSON structure that follows the structure described in the following code.  

```json title="Enumeration Data Type Format"
// The attributePolicy.ep file contains a dictionary of enumeration data types
{

	// Each enumeration definition is identified by its name. 
	It is a dictionary.
	"enumerationType": {

		// An enumeration definition is key value pair.
		// The key is the enumeration value (usually an integer),
	    // and  the value is the  interpretation of that value.
		// This entry can be repeated for each enumeration value.
		"<enumeration value>" : "<enumeration interpretation>"
	}
}
```

The following example show the definition for an enumeration data type.

```json title="Enumeration Data Type Example"
{
	"m2m:resultContent" : {
		"0": "Nothing",
		"1": "Attributes",
		"2": "Hierarchical address",
		"3": "Hierarchical address and attributes",
		"4": "Attributes and child resources",
		"5": "Attributes and child resource references",
		"6": "Child resource references",
		"7": "Original resource",
		"8": "Child resources",
		"9": "Modified attributes",
		"10": "Semantic content",	
		"11": "Semantic content and child resources",
		"12": "Permissions"
	},
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
