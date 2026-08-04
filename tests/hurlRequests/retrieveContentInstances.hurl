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
# Create 3 ContentInstance under the Container using unstructured resource ID
# Repeat the request 10 times
#

POST {{scheme}}://{{host}}:{{port}}/{{cnt-ri}}
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json;ty=4
[Options]
repeat:3

{
  "m2m:cin": {
    "con": "{{newUuid}}"
  }
}

HTTP 201


#
# Retrieve the list of ContentInstances under the Container
#
GET {{scheme}}://{{host}}:{{port}}/{{cnt-ri}}?rcn=8&ty=4
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json

HTTP 200

[Asserts]
jsonpath "$['m2m:cnt']" exists
jsonpath "$['m2m:cnt']['m2m:cin']" exists
jsonpath "$['m2m:cnt']['m2m:cin']" count == 3

#
# Retrieve the list of ContentInstances under the Container
#
GET {{scheme}}://{{host}}:{{port}}/{{cnt-ri}}/la?st=2
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json

HTTP 200

[Asserts]
jsonpath "$['m2m:cin']" exists
jsonpath "$['m2m:cin'].st" exists
jsonpath "$['m2m:cin'].st" == 2

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
