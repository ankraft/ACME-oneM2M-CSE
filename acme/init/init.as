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

;; ;;	Provide a description for the categories. These are displayed in the Text UI
;; (set-category-description "CSE Operation" 
;; "Scripts under this category are used to perform CSE operations. 

;; These scripts are not exposed to oneM2M AEs.
;; They can usually only be executed from the console or text UI, or the Upper Tester API.")


(setq cse-originator (get-config "cse.originator"))


;;
;;	Create the CSEBase
;;

(setq cb 
	{ "m2m:cb": {
		"ri":   "${get-config \"cse.resourceID\"}",
		"rn":   "${get-config \"cse.resourceName\"}",
		"csi":  "${get-config \"cse.cseID\"}",
		"csz":  [ "application/json", "application/cbor" ],
		"acpi": [ "${get-config \"cse.cseID\"}/acpCreateACPs" ]
	}})
(setq cb (set-json-attribute cb "m2m:cb/poa" (get-config "cse.poa")))

(import-raw cse-originator cb)


;;
;;	Allow all originators to create (only) <ACP> under the CSEBase
;;

(import-raw 
	cse-originator
	{ "m2m:acp": {
		"rn": "acpCreateACPs",
		"ri": "acpCreateACPs",
		"pi": "${get-config \"cse.resourceID\"}",
		"pv": {
			"acr": [ {
				"acor": [ "all"	],
				"acod": [ {	"chty": [ 1 ] }	],
				"acop": 1
			} ]
		},
		"pvs": {
			"acr": [ {
				"acor": [ "${cse-originator}" ],
				"acop": 63
			} ]
		}
	}})

;;
;;	Default admin AE
;;

(import-raw 
	cse-originator
	{ "m2m:ae": {
		"ri":  "${cse-originator}",
		"rn":  "${cse-originator}",
		"pi":  "${get-config \"cse.resourceID\"}",
		"rr":  true,
		"api": "N${cse-originator}",
		"aei": "${cse-originator}",
		"csz": [ "application/json", "application/cbor" ]
	}})


