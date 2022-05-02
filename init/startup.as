#
#	startup.as
#
#	This script creates mandatory resources during the startup/bootstrapping of the CSE.
#	Be careful when making changes to this script.
#

@startup
@name startup
@description This script is run during startup of the CSE
@hidden

#############################################################################
#
#	Create the CSEBase
#

importraw 
{	
	"m2m:cb" : {
			"ri":   "[cse.ri]",
			"rn":   "[cse.rn]",
			"csi":  "[cse.csi]",
			"rr":   true,
			"csz":  \[ "application/json", "application/cbor" ],
			"acpi": \[ "[cse.csi]/acpCreateACPs" ]
	}
}


#############################################################################
#
#	Allow all originators to create (only) <ACP> under the CSEBase
#

importraw 
{	
	"m2m:acp": {
		"rn": "acpCreateACPs",
		"ri": "acpCreateACPs",
		"pi": "[cse.ri]",
		"pv": {
			"acr": \[
				{
					"acor": \[
						"all"
					],
					"acod": \[
						{
							"chty": \[ 1 ]
						}
					],
					"acop": 1
				}
			]
		},
		"pvs": {
			"acr": \[
				{
					"acor": \[
						"[cse.originator]"
					],
					"acop": 63
				}
			]
		}
	}
}


#############################################################################
#
#	Default admin AE
#

importraw 
{
	"m2m:ae": {
		"ri":  "[cse.originator]",
		"rn":  "[cse.originator]",
		"pi":  "[cse.ri]",
		"rr":  true,
		"api": "N[cse.originator]",
		"aei": "[cse.originator]",
		"csz": \[ "application/json", "application/cbor" ]
	}
}
