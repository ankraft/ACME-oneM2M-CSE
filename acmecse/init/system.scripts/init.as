;;
;;	init.as
;;
;;	Initialize the system scripts.
;;
;;	(c) 2024 by Andreas Kraft
;;	License: BSD 3-Clause License. See the LICENSE file for further details.
;;

@name Init CSE Operation
@onStartup
@onRestart
@category CSE Operation
@hidden

;;	Provide a description for the categories. These are displayed in the Text UI
(set-category-description "CSE Operation" 
"Scripts under this category are used to perform CSE operations. 

These scripts are not exposed to oneM2M AEs.
They can usually only be executed from the console or text UI, or the Upper Tester API.")


