# How to Export Resources

Sometimes it is necessary to export resource, for example to backup a part of the resource tree or to save the state of the resource tree for demonstration and experiments.

## Export Resources

The ACME CSE offers a simple and portable way to export single resources or a whole part of the resource tree. In the text UI when clicking on a resource a tab *Services* contains the service "Export Resource". When clicking on the "Export" button a resource and (depending on the "child resource" checkbox) its child resources are exported to a directory as a shell script with the current date and time. The directory is the *tmp* directory under the CSE's root directory.

<figure markdown="1">
![Text UI - Export Resources](../images/export_resource.png#only-light){data-gallery="light"}
![Text UI - Export Resources](../images/export_resource-dark.png#only-dark){data-gallery="dark"}
<figcaption>Text UI - Export Resources</figcaption>
</figure>

The generated script contains the necessary commands to send Mca CREATE requests using *curl* commands over http for the exported resources.

One is free to make modifications to the exported resources as necessary, or to combine various resource scripts into a single script.

## Import Resources Again

The generated shell script contains three sections:

- The variable `cseURL` that is set to the URL of a CSE where the resources will be imported again. This should be set to appropriate address when targeting another CSE.
- Shell functions that construct the CREATE requests and send it using the *curl* command line tool.
- At the bottom are the shell function calls with the originator, resource type, and resource representations. 

!!! Import
	The resource representations can only contain the resource attributes that can be present in CREATE requests. This means, for example, that the *resourceID* of a resource is not present. 
	This also means, unfortunately, that references between resource may be incomplete after an export and need to be set manually afterwards.

To import the resources in an export script just run the script in a (bash) shell:

```sh title="Run the export script"
$ sh export-20240316T131612.sh
```

## Example Script

The following is an example of an export script that exports a container with two content instances and a subscription:

```sh title="Example export script"
#!/bin/bash
# Exported cnt6834189228603991262 from id-in at 20240316T131612,894875

cseURL=http://localhost:8080  # (1)!

function uniqueNumber() { # (2)!
	unique_number=""
	for i in {1..10}
	do
		unique_number+=$RANDOM
	done
	unique_number=${unique_number:0:10}
	echo "$unique_number"
}

function createResource() {	# (3)!
	printf '\nCreating child resource under %s\n' $cseURL/$4
	printf 'Result: '		  
	curl -X POST -H "X-M2M-Origin: $1" -H "X-M2M-RVI: 4" -H "X-M2M-RI: $(uniqueNumber)" -H "Content-Type: application/json;ty=$2" -d "$3" $cseURL/$4
	printf '\n'
}
			
# (4)!

createResource CDemoLightswitch 3 '{"m2m:cnt": {"rn": "switchContainer", "mni": 10, "acpi": ["acp3542208976028337519"]}}' 'cse-in/CDemoLightswitch'
createResource CDemoLightswitch 23 '{"m2m:sub": {"rn": "switchSubscription", "nu": ["cse-in/CDemoLightbulb"], "enc": {"net": [3]}, "nct": 1}}' 'cse-in/CDemoLightswitch/switchContainer'
createResource CDemoLightswitch 4 '{"m2m:cin": {"con": "off", "rn": "cin_KJyrTD7INf"}}' 'cse-in/CDemoLightswitch/switchContainer'
createResource CDemoLightswitch 4 '{"m2m:cin": {"con": "off", "rn": "cin_MQ5AK9WRbs"}}' 'cse-in/CDemoLightswitch/switchContainer'

```

1.	The variable `cseURL` is set to the URL of the CSE where the resources will be imported again. This should be set to the appropriate address when targeting another CSE.
2.	This function generates a unique number that is used for various identifiers. 
3.	This function creates a resource in the CSE using the *curl* command line tool. The function takes four arguments: the originator, the resource type, the resource representation, and the parent resource's URL.
4.	From here on the script creates the resources. The `createResource` function is called with the originator, the resource type, the resource representation, and the parent resource's URL.
