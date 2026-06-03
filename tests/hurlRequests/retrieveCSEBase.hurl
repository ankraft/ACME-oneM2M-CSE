#
# Retrieve a <CSEBase> resource
#


#
# Get the CSE by its CSE-ID
#

GET {{scheme}}://{{host}}:{{port}}/{{csi}}
Authorization: {{authorization}}
X-M2M-ORIGIN: {{admin-originator}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
jsonpath "$['m2m:cb'].csi" == "/{{csi}}"

[Captures]
cse-rn: jsonpath "$['m2m:cb'].rn"

#
# Get the CSE by its structured resource ID
#

GET {{scheme}}://{{host}}:{{port}}/{{cse-rn}} 
Authorization: {{authorization}}
X-M2M-ORIGIN: {{admin-originator}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
jsonpath "$['m2m:cb'].ri" == {{csi}}
jsonpath "$['m2m:cb'].rn" == "cse-in"


#
# Get the CSE by its structured resource ID with placeholder
#

GET {{scheme}}://{{host}}:{{port}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: {{admin-originator}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
jsonpath "$['m2m:cb'].csi" == "/{{csi}}"
header "X-M2M-RSC" == "2000"

