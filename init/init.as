;;
;;	init.as
;;
;;	This script creates mandatory resources during the startup/bootstrapping of the CSE.
;;	Be careful when making changes to this script.
;;

@init
@name init
@description This script is run to initialize the CSE structure
@hidden

;;
;;	Create the CSEBase
;;

(import-raw 
	(get-config "cse.originator") 
	{"m2m:cb": {
		"ri":   "${ (get-config \"cse.ri\") }$",
		"rn":   "${ (get-config \"cse.rn\") }$",
		"csi":  "${ (get-config \"cse.csi\") }$",
		"rr":   true,
		"csz":  [ "application/json", "application/cbor" ],
		"acpi": [ "${ (get-config \"cse.csi\") }$/acpCreateACPs" ],
		"poa":  [ "${ (get-config \"http.address\") }$" ]
	}})

;;
;;	Allow all originators to create (only) <ACP> under the CSEBase
;;

(import-raw 
	(get-config "cse.originator")
	{ "m2m:acp": {
		"rn": "acpCreateACPs",
		"ri": "acpCreateACPs",
		"pi": "${ (get-config \"cse.ri\") }$",
		"pv": {
			"acr": [ {
				"acor": [ "all"	],
				"acod": [ {	"chty": [ 1 ] }	],
				"acop": 1
			} ]
		},
		"pvs": {
			"acr": [ {
				"acor": [ "${ (get-config \"cse.originator\") }$" ],
				"acop": 63
			} ]
		}
	}})

;;
;;	Default admin AE
;;

(import-raw 
	(get-config "cse.originator")
	{ "m2m:ae": {
		"ri":  "${ (get-config \"cse.originator\") }$",
		"rn":  "${ (get-config \"cse.originator\") }$",
		"pi":  "${ (get-config \"cse.ri\") }$",
		"rr":  true,
		"api": "N${ (get-config \"cse.originator\") }$",
		"aei": "${ (get-config \"cse.originator\") }$",
		"csz": [ "application/json", "application/cbor" ]
	}})


