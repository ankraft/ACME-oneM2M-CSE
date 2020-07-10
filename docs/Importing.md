# Importing

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

### Including Configuration Settings

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

<a name="attributes"></a>
## Importing Attribute Policies

The CSE includes attribute policies for validating the attributes of all supported resource types (internal to the *m2m* namespace). But for all &lt;flexContainer> specializations, e.g. for oneM2M's TS-0023 ModuleClasses, those attribute policies must be provided. This can be done by providing attribute policy files for import. 

Those files are imported from the common import directory. More than one such file can be provided, for example one per domain. The files must have the extension ".ap". 

### Format

The format is basically a list of comma separated values with seven values per line and where the first line contains the header with the field names. 

**Example**

```csv
# resourceType, shortName, dataType, cardinality, optionalCreate, optionalUpdate, announced

# Additional attribute policies for <flexContainer> specializations
# !!! Don't change the first line !!!

# ModuleClass: Colour
hd:color,red,nonNegInteger,car1,O,O,OA
hd:color,green,nonNegInteger,car1,O,O,OA
hd:color,blue,nonNegInteger,car1,O,O,OA
```

**Field Format**

| # | Field | Description | Values |
|:-:|-------|-|-|
| 1 | specialization type | Shortname of the specialization, including the domain. This can occur multiple times, once for each attribute. | domain:name |
| 2 | attribute shortname | Shortname of the attribute. This should only appear once per specialization. | string |
| 3 | data type | This field specifies the attribute's data type. | 	<ul><li>positiveInteger</li></ul><ul><li>nonNegInteger</li></ul><ul><li>unsignedInt</li></ul><ul><li>unsignedLong</li></ul><ul><li>string</li></ul><ul><li>timestamp</li></ul><ul><li>list</li></ul><ul><li>dict</li></ul><ul><li>anyURI</li></ul><ul><li>boolean</li></ul><ul><li>geoCoordinates</li></ul> |
| 4 | cardinality | The multiplicity of the attribute. This must be one of the following values. | <ul><li>**car1** : multiplicity of 1</li></ul><ul><li>**car1L** : multiplicity of 1 (list)</li></ul><ul><li>**car01** : multiplicity of 0 or 1</li></ul><ul><li>**car01L** : multiplicity of 0 or 1 (list)</li></ul> |
| 5 | CREATE optionality | This field specifies whether this attribute must be provided etc during a CREATE request.  | <ul><li>**NP** : Not provided</li></ul><ul><li>**O** : Optional provided</li></ul><ul><li>**M** : Mandatory provided</li></ul> |
| 6 | UPDATE optionality | This field specifies whether this attribute must be provided etc during an UPDATE request. | <ul><li>**NP** : Not provided</li></ul><ul><li>**O** : Optional provided</li></ul><ul><li>**M** : Mandatory provided</li></ul> | 
| 7 | Announced optionallity | This field specifies whether an attribute is announced when the resource is announced. | <ul><li>**NA** : Not announced</li></ul><ul><li>**OA** : Optional announced</li></ul><ul><li>**MA** : Mandatory announced</li></ul> |



