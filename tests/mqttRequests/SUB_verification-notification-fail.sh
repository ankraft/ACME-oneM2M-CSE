#!/bin/sh
#
#	Prerequisites:
#		- run notificationServer with MQTT enabled and "fail requests" enabled
#
#	Steps:
# 		- create AE1
#		- create ACP under CSE
#		- create AE2 with ACPI
#		- Create SUB under AE1 with AE2 as target	-> Verification Notification fails or succeeds
#

source ./config.sh

mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/reg_req/AE1/$cseid/json" --message '{"op": 1, "to": "cse-in", "fr": "Cxyz", "rqi": "createAE1", "ty": 2, "pc": {"m2m:ae":{"rn": "MyAe1", "api": "NMyApp1Id", "rr": false, "srv": ["1","2","2a","3"]}}, "rvi": "3"}'
mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/req/AE2/$cseid/json" --message '{"op": 1, "to": "cse-in", "fr": "CAdmin", "rqi": "createACP", "ty": 1, "pc": {"m2m:acp":{"rn": "SubscriptionVerificationAcp", "pv": {"acr": [{"acor": ["all"], "acop": 63}]}, "pvs": {"acr": [{"acor": ["all"], "acop": 63}]}}}, "rvi": "3"}'
mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/reg_req/AE2/$cseid/json" --message '{"op": 1, "to": "cse-in", "fr": "", "rqi": "createAE2", "ty": 2, "pc": {"m2m:ae":{"rn": "MyAe2", "acpi": ["cse-in/SubscriptionVerificationAcp"], "api": "NMyApp2Id", "poa": ["'$poa'"], "rr": true, "srv": ["1","2","2a","3"]}}, "rvi": "3"}'
mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/req/id-in:Cxyz/$cseid/json" --message '{"op": 1, "to": "cse-in/MyAe1", "fr": "Cxyz", "rqi": "createSub", "ty": 23, "pc": {"m2m:sub":{"rn": "MySubscriptionResource", "nu": ["cse-in/MyAe2"]}}, "rvi": "3"}'



