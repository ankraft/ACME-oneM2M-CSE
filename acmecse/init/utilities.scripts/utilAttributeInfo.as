@name Attribute Info Search
@tuiTool
@category Utilities
@tuiInput Attribute
@tuiExecuteButton Search
@description This tool provides fuzzy searches for an attribute name or short name, and prints out the attribute(s) information.\n\n*Note, that some scalar types are mapped to a more general type, such as "string"*.


(clear-console)

(if (!= argc 2)
	((print "[red]Add a single identifier without spaces")
	 (quit)))

(dolist (attribute (cse-attribute-infos (argv 1)))
	((print "[dodger_blue2]attribute  = " (nth 1 attribute))
	 (print "[dark_orange]short name = " (nth 0 attribute))
	 (print "type       = " (nth 2 attribute) nl)))

