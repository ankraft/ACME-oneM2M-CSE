#
# Create a small application structure, 
# then create several ContentInstances under a Container
# using unstructured resource IDs.
#

#
# Register an AE
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
    "rr": true,
    "srv": ["{{release-version}}"]
  }
}

HTTP 201

[Captures]
aei: jsonpath "$['m2m:ae'].aei"
ae-rn: jsonpath "$['m2m:ae'].rn"


#
# Create a Container under the AE
#

POST {{scheme}}://{{host}}:{{port}}/-/{{ae-rn}}
Authorization: {{authorization}}
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json;ty=3
{
  "m2m:cnt": { }
}

HTTP 201
[Captures]
cnt-ri: jsonpath "$['m2m:cnt'].ri"


#
# Create a ContentInstance under the Container using unstructured resource ID
# Repeat the request 10 times
#

POST {{scheme}}://{{host}}:{{port}}/{{cnt-ri}}
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json;ty=4
[Options]
repeat:10

{
  "m2m:cin": {
    "con": "{{newUuid}}"
  }
}

HTTP 201


#
# Delete the AE
#

DELETE {{scheme}}://{{host}}:{{port}}/{{aei}}
Authorization: {{authorization}}
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2002"
