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

@name Init Documentation Tutorials
@onStartup
@onRestart
@category oneM2M Documentation and Tutorials
@hidden

;;	Provide a description for the category. This is displayed in the Text UI
(set-category-description "Documentation and Tutorials" 
"The following pages provide links to external tutorials and documentation resources.

Note, that the pages in this category are not part of the CSE, but are provied by external sources.")

