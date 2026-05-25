;;
;;	init.as
;;
;;	Initialize the lightbulb demo.
;;
;;	(c) 2023 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;
;;	This script is executed on CSE startup and restart to create the necessary resources.
;;

@name Init Lightbulb Demo
@onStartup
@onRestart
@category Lightbulb Demo
@hidden

(include-script "functions")

;;	Include some helper functions
(print "Init Lightbulb Demo")

;;	Provide a description for the category. This is displayed in the Text UI
(set-category-description "Lightbulb Demo" 
"This demo is a simulation that implements a *lightbulb* that is controlled by a *lightswitch*. 

Both the *lightbulb* and the *lightswitch* are implemented as Application Entities (AEs). 

The *lightbulb* AE subscribes to the *lightswitch*'s container and receives notifications whenever new
`<ContentInstance>` resources are created for the *lightswitch*. It then can react to the new status of 
the *lightswitch*.")

;;	Get the CSE's resource name
(setq cseRN (get-config "cse.resourceName"))

;;
;;	Register lightbulb  resources
;;

;;	Register lightbulb AE under the CSE
(eval-if-resource-exists "CDemoLightbulb" "${cseRN}/CDemoLightbulb"
  nil
  '(create-resource "CDemoLightbulb" cseRN 
    { "m2m:ae" : {
      "api" : "NdemoLightbulb",
      "rr" : true,
      "rn" : "CDemoLightbulb",
      "srv" : [ "4" ],
      "poa" : [ "acme://demo-lightbulb/lightswitch" ]
    }}))


;;	Create access control policy to allow notification access to the lightswitch container
(eval-if-resource-exists "CDemoLightbulb" "${cseRN}/CDemoLightbulb/accessControlPolicy"
  nil
  '(create-resource "CDemoLightbulb" "${cseRN}/CDemoLightbulb" 
    { "m2m:acp" : {
      "rn" : "accessControlPolicy",
      "pv": {
        "acr": [
          { ;; Allow CDemoLightbulb only to retrieve					
            "acor": [ "CDemoLightswitch"],
            "acop": 16  ;; NOTIFY
          }, 
          { ;; Allow CDemoLightswitch all access
            "acor": [ "CDemoLightbulb" ],
            "acop": 63  ;; ALL
          }
        ]
      },
      "pvs": {
        "acr": [ 
          { ;; Allow CDemoLightSwitch all access to the accessControlPolicy resource
            "acor": [ "CDemoLightbulb" ],
            "acop": 63  ;; ALL
          } 
        ]
      }
    }}))


;;
;;	Create lightswitch resources
;;

;;	Register lightswitch AE
(eval-if-resource-exists "CDemoLightswitch" "${cseRN}/CDemoLightswitch" 
  nil
  '(create-resource "CDemoLightswitch" cseRN 
	{ "m2m:ae" : {
	  "api" : "NdemoLightswitch",
	  "rr" : true,
	  "rn" : "CDemoLightswitch",
	  "srv" : [ "4" ]
	}}))


;;	Create access control policy to allow access to the lightswitch container
(eval-if-resource-exists "CDemoLightswitch" "${cseRN}/CDemoLightswitch/accessControlPolicy" 
  nil
  '(create-resource "CDemoLightswitch" "${(cseRN)}/CDemoLightswitch" 
    { "m2m:acp" : {
      "rn" : "accessControlPolicy",
      "pv": {
        "acr": [ 
          { ;; Allow CDemoLightbulb only to retrieve					
            "acor": [ "CDemoLightbulb"	],
            "acop": 2	;; RETRIEVE
          } , 
          { ;; Allow CDemoLightswitch all access
            "acor": [ "CDemoLightswitch" ],
            "acop": 63  ;; ALL
          }
        ]
      },
      "pvs": {
        "acr": [ 
          { ;; Allow CDemoLightSwitch all access to the accessControlPolicy resource
            "acor": [ "CDemoLightswitch" ],
            "acop": 63  ;; ALL
          }
        ]
      }
    }}))
    

;;	Create lightswitch container
(eval-if-resource-exists "CDemoLightswitch" "${cseRN}/CDemoLightswitch/switchContainer" 
  nil
  '(create-resource "CDemoLightswitch" "${(cseRN)}/CDemoLightswitch" 
	{ "m2m:cnt" : {
	  "rn" : "switchContainer",
	  "mni" : 10,  ;; Max number of instances
	  "acpi" : [ "${(cseRN)}/CDemoLightswitch/accessControlPolicy" ]
	}}))


;;	Create lightswitch subscription
(eval-if-resource-exists "CDemoLightswitch" "${cseRN}/CDemoLightswitch/switchContainer/switchSubscription" 
  nil
  '(create-resource "CDemoLightswitch" "${(cseRN)}/CDemoLightswitch/switchContainer" 
	{ "m2m:sub" : {
	  "rn" : "switchSubscription",
	  "nu" : ["${(cseRN)}/CDemoLightbulb"],	;; Direct URI, no access control
	  "enc": {
		"net": [ 3 ]  ;; Create of direct child resources
	  }
	}}))


;;
;;	Create first lightswitch with status "off"
;;

(create-resource "CDemoLightswitch" "${(cseRN)}/CDemoLightswitch/switchContainer" 
  { "m2m:cin": {
    "con" : "off"
  }})


;; force a refresh of the resource tree in the Text UI
(tui-refresh-resources)
