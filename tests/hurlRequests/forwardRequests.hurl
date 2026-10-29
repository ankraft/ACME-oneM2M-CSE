#
# Forward requests from CSEs to remote CSEs
#
# Expected CSE registration setup: ASN -> MN -> IN 
#

#############################################################################
#
# Requests to ASN
#

# Retrieve ASN CSEBase

GET {{scheme-asn}}://{{host-asn}}:{{port-asn}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: {{admin-originator-asn}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2000"
jsonpath "$['m2m:cb']" exists
jsonpath "$['m2m:cb'].ri" == "{{csi-asn}}"


# Retrieve MN CSEBase via forwarded request to ASN

GET {{scheme-asn}}://{{host-asn}}:{{port-asn}}/~/{{csi-mn}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: /{{csi-mn}}/{{admin-originator-mn}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2000"
jsonpath "$['m2m:cb']" exists
jsonpath "$['m2m:cb'].ri" == "{{csi-mn}}"


# Retrieve IN CSEBase via forwarded request to ASN
	
GET {{scheme-asn}}://{{host-asn}}:{{port-asn}}/~/{{csi}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: /{{csi}}/{{admin-originator}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2000"
jsonpath "$['m2m:cb']" exists
jsonpath "$['m2m:cb'].ri" == "{{csi}}"


#############################################################################
#
# Requests to IN
#

# Retrieve IN CSEBase

GET {{scheme}}://{{host}}:{{port}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: {{admin-originator}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2000"
jsonpath "$['m2m:cb']" exists
jsonpath "$['m2m:cb'].ri" == "{{csi}}"

# Retrieve MN CSEBase via forwarded request to IN

GET {{scheme}}://{{host}}:{{port}}/~/{{csi-mn}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: /{{csi-mn}}/{{admin-originator-mn}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2000"
jsonpath "$['m2m:cb']" exists
jsonpath "$['m2m:cb'].ri" == "{{csi-mn}}"


# Retrieve ASN CSEBase via forwarded request to IN
	
GET {{scheme}}://{{host}}:{{port}}/~/{{csi-asn}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: /{{csi-asn}}/{{admin-originator-asn}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2000"
jsonpath "$['m2m:cb']" exists
jsonpath "$['m2m:cb'].ri" == "{{csi-asn}}"

