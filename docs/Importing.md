# Importing Resources

During startup it is possible to import resources into to CSE. Each resource is read from a single file in the [init](../init) resource directory specified in the configuration file.

Not much validation, access control, or registration procedures are performedfor imported resources.

## Importing Mandatory Resources

**Please note** that importing is required for creating the CSEBase resource and at least two (admin) ACP resources. Those are imported before all other resources, so that the CSEBase resource can act as the root for the resource tree. The *admin* ACP is used to access resources with the administrator originator. The *default* ACP resource is the one that is assigned for resources that don't specify an ACP on their own.

The filenames for these resources must be:

- [csebase.json](../init/csebase.json) for the CSEBase.
- [acp.admin.json](../init/acp.admin.json) for the admin ACP.
- [acp.default.json](../init/acp.default.json) for the default ACP.

## Importing Other Resources

After importing the mandatory resources all other resources in the [init](../init) directory are read in alphabetical order and are added (created) to the CSE's resource tree. Imported resources must have a valid *acpi* attribute, because no default *acpi* is assigned during importing.

## Updating Resources

If the filename contains the substring *update*, then the resource specified by the resource's *ri* attribute is updated instead of created.

## Including Configuration Settings

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

## Examples & Templates

A minimal set of resources is provided in the [init](../init) directory. Definitions for a more sophisticated setup can be found in the [tools/init.example](../tools/init.example) directory. To use these examples, you can either copy the resources to the *init* directory or change the "cse -> resourcesPath" entry in the *acme.ini* configuration file.

The directory [tools/resourceTemplates](../tools/resourceTemplates) contains templates for supported resource types. Please see the [README](../tools/resourceTemplates/README.md) there for further details.
