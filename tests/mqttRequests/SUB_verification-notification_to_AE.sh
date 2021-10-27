#!/bin/sh
#
#	Prerequisites:
#		- run notificationServer with MQTT enabled
#
#	Steps:
# 		- create AE1
#		- create AE2
#		- create ACP under AE2
#		- Update AE2 with ACPI to ACP
#		- Create SUB under AE1 with AE2 as target
#

source ./config.sh

mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/reg_req/AE1/$cseid/json" --message '{"op": 1, "to": "cse-in", "fr": "Cxyz", "rqi": "createAE1", "ty": 2, "pc": {"m2m:ae":{"rn": "MyAe1", "api": "NMyApp1Id", "poa": ["'$poa'"], "rr": true, "srv": ["1","2","2a","3"]}}, "rvi": "3"}'
mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/reg_req/AE2/$cseid/json" --message '{"op": 1, "to": "cse-in", "fr": "Cxyz2", "rqi": "createAE2", "ty": 2, "pc": {"m2m:ae":{"rn": "MyAe2", "api": "NMyApp2Id", "poa": ["'$poa'"], "rr": true, "srv": ["1","2","2a","3"]}}, "rvi": "3"}'
mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/req/Cxyz2/$cseid/json" --message '{"op": 1, "to": "cse-in/MyAe2", "fr": "Cxyz2", "rqi": "createACPunderAE2", "ty": 1, "pc": {"m2m:acp":{"rn": "SubscriptionVerificationAcp", "pv": {"acr": [{"acor": ["all"], "acop": 63}]}, "pvs": {"acr": [{"acor": ["all"], "acop": 63}]}}}, "rvi": "3"}'
mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/req/Cxyz/$cseid/json" --message '{"op": 3, "to": "cse-in/MyAe2", "fr": "Cxyz2", "rqi": "updateAE2withACPI", "pc": {"m2m:ae":{"acpi": ["'$csenm'/MyAe2/SubscriptionVerificationAcp"]}}, "rvi": "3"}'
mqtt pub -h $host -p $port $user $password --verbose --topic "/oneM2M/req/Cxyz/$cseid/json" --message '{"op": 1, "to": "cse-in/MyAe1", "fr": "Cxyz", "rqi": "createSUBunderAE", "ty": 23, "pc": {"m2m:sub":{"rn": "MySubscriptionResource", "nu": ["'$csenm'/MyAe2"]}}, "rvi": "3"}'
