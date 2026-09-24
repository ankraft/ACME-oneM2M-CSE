#
#	Simple test to create dynamic authorization PoA
#

#
# Create a Dynamic Authorization Consultation resource
#

POST {{scheme}}://{{host}}:{{port}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: {{admin-originator}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json;ty=34
{
  "m2m:dac": {
	"rn": "testDAC",
	"dae": true,
	"dap": [
		"-/das"
	]
  }
}


#
# Create a container resource that uses the DAC resource
#

POST {{scheme}}://{{host}}:{{port}}/-
Authorization: {{authorization}}
X-M2M-ORIGIN: {{admin-originator}}
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
Content-Type: application/json;ty=3
{
  "m2m:cnt": {
	"rn": "testDACContainer",
	"daci": [
		"-/testDAC"
	]
  }
}

#
# Retrieve the container resource to check if the DAC has been applied
#
GET {{scheme}}://{{host}}:{{port}}/-/testDACContainer
Authorization: {{authorization}}
X-M2M-ORIGIN: C123
X-M2M-RI: {{newUuid}}
X-M2M-RVI: {{release-version}}
