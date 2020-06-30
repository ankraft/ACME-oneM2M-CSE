//
//  shortnames.js
//
//  (c) 2020 by Andreas Kraft
//  License: BSD 3-Clause License. See the LICENSE file for further details.
//
//  Mapping between oneM2M short and long names
//

// There are basically 4 types of attributes:
// - common & universal : same as oneM2M
// - custom : from flexContainer and mgmtObj specializations
// - all others


const shortNames = {
  "aa"    : { "ln" : "announcedAttribute", "type" : "common" },
  "acn"   : { "ln" : "action", "type": "" },
  "act"   : { "ln" : "activate", "type": "" },
  "acts"  : { "ln" : "activeStatus", "type": "" },
  "acpi"  : { "ln" : "accessControlPolicyIDs", "type": "common" },
  "acn"   : { "ln" : "action", "type": "" },
  "aei"   : { "ln" : "AE-ID", "type": "" },
  "ant"   : { "ln" : "areaNwkType", "type": "custom" },
  "ape"   : { "ln" : "activityPatternElements", "type": "" },
  "api"   : { "ln" : "App-ID", "type": "" },
  "apn"   : { "ln" : "AppName", "type": "" },
  "at"    : { "ln" : "announcedTo", "type" : "common" },
  "att"   : { "ln" : "attached", "type": "custom" },
  "awi"   : { "ln" : "areaNwkId", "type": "custom" },
  "btl"   : { "ln" : "batteryLevel", "type": "custom" },
  "bts"   : { "ln" : "batteryStatus", "type": "custom" },
  "can"   : { "ln" : "capabilityName", "type": "custom" },
  "cas"   : { "ln" : "capabilityActionStatus", "type": "custom" },
  "cbs"   : { "ln" : "currentByteSize", "type": "" },
  "cnd"   : { "ln" : "containerDefinition", "type": "" },
  "cnf"   : { "ln" : "contentInfo", "type": "custom" },
  "cni"   : { "ln" : "currentNrOfInstances", "type": "" },
  "cnm"   : { "ln" : "currentNrOfMembers", "type": "" },
  "cnty"  : { "ln" : "country", "type": "custom" },
  "con"   : { "ln" : "content", "type": "custom" },
  "cr"    : { "ln" : "creator", "type": "common" },
  "cs"    : { "ln" : "contentSize", "type": "" },
  "csi"   : { "ln" : "CSE-ID", "type": "" },
  "cst"   : { "ln" : "cseType", "type": "" },
  "csy"   : { "ln" : "consistencyStrategy", "type": "" },
  "csz"   : { "ln" : "contentSerialization", "type": "" },
  "ct"    : { "ln" : "creationTime", "type": "universal" },
  "cus"   : { "ln" : "currentState", "type": "custom" },
  "daci"  : { "ln" : "dynamicAuthorizationConsultationIDs", "type": "common" },
  "dc"    : { "ln" : "description", "type": "" },
  "dea"   : { "ln" : "deactivate", "type": "" },
  "dis"   : { "ln" : "disable", "type": "" },
  "disr"  : { "ln" : "disableRetrieval", "type": "" },
  "dlb"   : { "ln" : "deviceLabel", "type": "custom" },
  "dty"   : { "ln" : "deviceType", "type": "custom" },
  "dvd"   : { "ln" : "devId", "type": "custom" },
  "dvi"   : { "ln" : "deviceInfo", "type": "" },
  "dvnm"  : { "ln" : "deviceName", "type": "custom" },
  "dvt"   : { "ln" : "devType", "type": "custom" },
  "egid"  : { "ln" : "externalGroupID", "type": "" },
  "ena"   : { "ln" : "enable", "type": "" },
  "enc"   : { "ln" : "eventNotificationCriteria", "type": "" },
  "esi"   : { "ln" : "e2eSecInfo", "type": "common" },
  "et"    : { "ln" : "expirationTime", "type": "common" },
  "far"   : { "ln" : "factoryReset", "type": "" },
  "fwn"   : { "ln" : "firmwareName", "type": "custom" },
  "fwv"   : { "ln" : "fwVersion", "type": "custom" },
  "gn"    : { "ln" : "groupName", "type": "" },
  "hael"  : { "ln" : "hostedAELinks", "type": "" },
  "hcl"   : { "ln" : "hostedCSELink", "type": "" },
  "hsl"   : { "ln" : "hostedServiceLink", "type": "" },
  "hwv"   : { "ln" : "hwVersion", "type": "custom" },
  "in"    : { "ln" : "install",  "type": "" },
  "ins"   : { "ln" : "installStatus", "type": "" },
  "lbl"   : { "ln" : "labels", "type": "common" },
  "ldv"   : { "ln" : "listOfDevices", "type": "custom" },
  "lga"   : { "ln" : "logStart", "type": "custom" },
  "lgd"   : { "ln" : "logData", "type": "custom" },
  "lgo"   : { "ln" : "logStop", "type": "custom" },
  "lgst"  : { "ln" : "logStatus", "type": "custom" },
  "lgt"   : { "ln" : "logTypeId", "type": "custom" },
  "li"    : { "ln" : "locationID", "type": "" },
  "lnh"   : { "ln" : "listOfNeighbors", "type": "custom" },
  "loc"   : { "ln" : "location", "type": "custom" },
  "lt"    : { "ln" : "lastModifiedTime", "type": "universal" },
  "macp"  : { "ln" : "membersAccessControlPolicyIDs", "type": "" },
  "man"   : { "ln" : "manufacturer", "type": "custom" },
  "mbs"   : { "ln" : "maxByteSize", "type": "" },
  "mei"   : { "ln" : "M2M-Ext-ID", "type": "" },
  "mfd"   : { "ln" : "manufacturingDate", "type": "custom" },
  "mfdl"  : { "ln" : "manufacturerDetailsLink", "type": "custom" },
  "mgca"  : { "ln" : "mgmtClientAddress", "type": "" },
  "mgd"   : { "ln" : "mgmtDefinition", "type": "" },
  "mid"   : { "ln" : "memberIDs", "type": "" },
  "mma"   : { "ln" : "memAvailable", "type": "custom" },
  "mmt"   : { "ln" : "memTotal", "type": "custom" },
  "mni"   : { "ln" : "maxNrOfInstances", "type": "" },
  "mnm"   : { "ln" : "maxNrOfMembers", "type": "" },
  "mod"   : { "ln" : "model", "type": "custom" },
  "mt"    : { "ln" : "memberType", "type": "" },
  "mtv"   : { "ln" : "memberTypeValidated", "type": "" },
  "nar"   : { "ln" : "notifyAggregation", "type": "" },
  "nct"   : { "ln" : "notificationContentType", "type": "" },
  "ni"    : { "ln" : "nodeID", "type": "" },
  "nid"   : { "ln" : "networkID", "type": "" },
  "nl"    : { "ln" : "nodeLink", "type": "" },
  "nu"    : { "ln" : "notificationURI",  "type": "" },
  "or"    : { "ln" : "ontologyRef", "type" : "" },
  "osv"   : { "ln" : "osVersion", "type": "custom" },
  "pi"    : { "ln" : "parentID", "type": "universal" },
  "poa"   : { "ln" : "pointOfAccess", "type": "" },
  "ptl"   : { "ln" : "protocol", "type": "custom" },
  "purl"  : { "ln" : "presentationURL", "type": "custom" },
  "pv"    : { "ln" : "privileges", "type": "" },
  "pvs"   : { "ln" : "selfPrivileges", "type": "" },
  "rbo"   : { "ln" : "reboot", "type": "" },
  "regs"  : { "ln" : "registrationStatus", "type": "" },
  "ri"    : { "ln" : "resourceID", "type": "universal" },
  "rms"   : { "ln" : "roamingStatus", "type": "" },
  "rn"    : { "ln" : "resourceName", "type": "universal" },
  "rr"    : { "ln" : "requestReachability", "type": "" },
  "scp"   : { "ln" : "sessionCapabilities", "type": "" },
  "sld"   : { "ln" : "sleepDuration", "type": "custom" },
  "sli"   : { "ln" : "sleepInterval", "type": "custom" },
  "smod"  : { "ln" : "subModel", "type": "custom" },
  "spty"  : { "ln" : "specializationType", "type": "" },
  "spur"  : { "ln" : "supportURL", "type": "custom" },
  "srt"   : { "ln" : "supportedResourceType", "type": "" },
  "srv"   : { "ln" : "supportedReleaseVersions", "type": "" },
  "ssi"   : { "ln" : "semanticSupportIndicator", "type": "" },
  "st"    : { "ln" : "stateTag", "type": "common" },
  "sus"   : { "ln" : "status", "type": "" },
  "swn"   : { "ln" : "softwareName", "type": "" },
  "swr"   : { "ln" : "software", "type": "" },
  "swv"   : { "ln" : "swVersion", "type": "custom" },
  "syst"  : { "ln" : "systemTime", "type": "custom" },
  "tri"   : { "ln" : "trigger-Recipient-ID", "type": "" },
  "tren"  : { "ln" : "triggerEnable", "type": "" },
  "trn"   : { "ln" : "triggerReferenceNumber", "type": "" },
  "trps"  : { "ln" : "trackRegistrationPoints", "type": "" },
  "ty"    : { "ln" : "resourceType", "type": "universal" },
  "ud"    : { "ln" : "update", "type": "" },
  "uds"   : { "ln" : "updateStatus", "type": "" },
  "un"    : { "ln" : "uninstall", "type": "" },
  "url"   : { "ln" : "URL", "type": "custom" },
  "vr"    : { "ln" : "version", "type": "custom" },


  // proprietary custom attributes
  "crRes" : { "ln" : "createdResources", "type": "custom" },
  "cseSU" : { "ln" : "cseStartUpTime", "type": "custom" },
  "cseUT" : { "ln" : "cseUptime", "type": "custom" },
  "ctRes" : { "ln" : "resourceCount", "type": "custom" },
  "htCre" : { "ln" : "httpCreates", "type": "custom" },
  "htDel" : { "ln" : "httpDeletes", "type": "custom" },
  "htRet" : { "ln" : "httpRetrieves", "type": "custom" },
  "htUpd" : { "ln" : "httpUpdates", "type": "custom" },
  "lgErr" : { "ln" : "logErrors", "type": "custom" },
  "lgWrn" : { "ln" : "logWarnings", "type": "custom" },
  "rmRes" : { "ln" : "deletedResources", "type": "custom" },
  "upRes" : { "ln" : "updatedResources", "type": "custom" }
}


function shortToLongname(sn) {
  if (printLongNames && sn in shortNames) {
    return shortNames[sn].ln
  }
  return sn
}

function attributeRole(sn) {
    if (sn in shortNames) {
    return shortNames[sn].type
  }
  return "custom"
}