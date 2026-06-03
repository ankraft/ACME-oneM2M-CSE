#
# Register and unregister an AE
#

#
# Register the AE
#

POST {{scheme}}://{{host}}:{{port}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: C
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json;ty=2
{
  "m2m:ae": {
    "api": "Nmy-application.example.com",
    "rr": false,
    "srv": ["{{release-version}}"]
  }
}

HTTP 201

[Asserts]
header "X-M2M-RVI" == "{{release-version}}"
header "X-M2M-RSC" == "2001"

[Captures]
aei: jsonpath "$['m2m:ae'].aei"
ae-rn: jsonpath "$['m2m:ae'].rn"


#
# Delete the AE
#

DELETE {{scheme}}://{{host}}:{{port}}/-/{{ae-rn}}
Authorization: {{authorization}}
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2002"

