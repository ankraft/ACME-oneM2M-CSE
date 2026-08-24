#
# Register an AE & TriggerRequest to send a notification via Pushover
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
    "srv": ["{{release-version}}"],
    "mei": "pushover@notification.example.com",
    "tri": 23
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
# CREATE a TriggerRequest to send a notification via Pushover
#

POST {{scheme}}://{{host}}:{{port}}/-/{{ae-rn}}
Authorization: {{authorization}}
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json;ty=47
{
  "m2m:tgr": {
	"lbl": ["message:Hello, oneM2M!", "title:Notification from ACME CSE"],
    "rn": "tgr",
    "mei": "23@notification.example.com",
    "tvt": "PT5S"
  }
}


#
# Delete the AE
#

DELETE {{scheme}}://{{host}}:{{port}}/-/{{ae-rn}}
Authorization: {{authorization}}
X-M2M-ORIGIN: {{aei}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
[Options]
delay: 3s

HTTP 200

[Asserts]
header "X-M2M-RSC" == "2002"

