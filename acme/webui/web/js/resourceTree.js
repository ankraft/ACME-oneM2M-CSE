//
// resourceTree.js
//
// (c) 2020 by Andreas Kraft
// License: BSD 3-Clause License. See the LICENSE file for further details.
//
// Javascript tree handling methods
//

var tree
var cseid = ''
var root = null
var rootri = null
var originator = ""
var printLongNames = false
var nodeClicked = undefined

// hack: if this is set to false then the REST UI will not be refreshed.
// useful with auto refresh.
var refreshRESTUI = true 

// TODO Clickable references. For each node add ("ri" : TreePath). expand via TreeView.expandPath.
// Select the entry and display


const types = {
     1 : "ACP",
     2 : "AE",
     3 : "Container",
     4 : "ContentInstance",
     5 : "CSEBase",
     9 : "Group",
    14 : "Node",
	15 : "PollingChannel",
    16 : "RemoteCSE",
    17 : "Request",
    23 : "Subscription",
	24 : "SemanticDescriptor",
    28 : "FlexContainer",
	29 : "TimeSeries",
	30 : "TimeSeriesInstance",
	48 : "CrossResourceSubscription",
    58 : "FlexContainerInstance",
	65 : "Action",

    10001 : "ACPAnnc",
    10002 : "AEAnnc",
    10003 : "ContainerAnnc",
    10004 : "ContentInstanceAnnc",
    10005 : "CSEBaseAnnc",
    10009 : "GroupAnnc",
    10013 : "MgmtObjAnnc",
    10014 : "NodeAnnc",
    10016 : "RemoteCSEAnnc",
	10024 : "SemanticDescriptorAnnc",
    10028 : "FlexContainerAnnc",
	10029 : "TimeSeriesAnnc",
	10030 : "TimeSeriesInstanceAnnc",
    10058 : "FlexContainerInstanceAnnc",
    10065 : "ActionAnnc"

}

const shortTypes = {
     1 : "ACP",
     2 : "AE",
     3 : "CNT",
     4 : "CIN",
     5 : "CSE",
     9 : "GRP",
    14 : "NOD",
    15 : "PCH",
    16 : "CSR",
    17 : "REQ",
    23 : "SUB",
	24 : "SMD",
    28 : "FCNT",
	29 : "TS",
	30 : "TSI",
	48 : "CRS",
    58 : "FCI",
    65 : "ACTR",

    10001 : "ACPAnnc",
    10002 : "AEAnnc",
    10003 : "CNTAnnc",
    10004 : "CINAnnc",
    10005 : "CSEAnnc",
    10009 : "GRPAnnc",
    10013 : "MGMTOBJAnnc",
    10014 : "NODAnnc",
    10016 : "CSRAnnc",
	10024 : "SMDAnnc",
    10028 : "FCNTAnnc",
	10029 : "TSAnnc",
	10030 : "TSIAnnc",
    10058 : "FCIAnnc",
    10065 : "ACTRAnnc" 
}

const mgdTypes = {
  1001 : "Firmware",
  1002 : "Software",
  1003 : "Memory",
  1004 : "AreaNwkInfo",
  1005 : "AreaNwkDeviceInfo",
  1006 : "Battery",
  1007 : "DeviceInfo",
  1008 : "DeviceCapability",
  1009 : "Reboot",
  1010 : "EventLog",
  1021 : "DataCollection",
  1023 : "myCertFileCred"
}

const mgdShortTypes = {
  1001 : "FWR",
  1002 : "SWR",
  1003 : "MEM",
  1004 : "ANI",
  1005 : "ANDI",
  1006 : "BAT",
  1007 : "DVI",
  1008 : "DVC",
  1009 : "REB",
  1010 : "EVL",
  1021 : "DATC",
  1023 : "NYCFC"
}


const mgdAnncShortTypes = {
  1001 : "FWRAnnc",
  1002 : "SWRAnnc",
  1003 : "MEMAnnc",
  1004 : "ANIAnnc",
  1005 : "ANDIAnnc",
  1006 : "BATAnnc",
  1007 : "DVIAnnc",
  1008 : "DVCAnnc",
  1009 : "REBAnnc",
  1010 : "EVLAnnc",
  1023 : "NYCFCAnnc"
}



function clickOnNode(e, node) {
  if (typeof nodeClicked !== "undefined") {
    nodeClicked.setSelected(false)    
  }
  node.setSelected(true)
  nodeClicked = node
  tree.reload()
  updateDetailsOfNode(node)
}


function updateDetailsOfNode(node) {
  clearAttributesTable()
  fillAttributesTable(node.resource)
  fillJSONArea(node)
  setResourceInfo(node)
  if (refreshRESTUI) {
    setRestUI(node.resourceFull)
  } else {
    refreshRESTUI = true
  }
}


//////////////////////////////////////////////////////////////////////////////

//
//  Tree handling
//

function expandNode(node) {
  for (ch of node.getChildren()) {
    if (ch.resolved == false) {
      getResource(ch.ri, ch) 
    }
  }
}


function collapseNode(node) {
  for (ch of node.getChildren()) {
    ch.setExpanded(false)
  }
}


function removeChildren(node) {
  var chc = node.getChildCount()
  for (i = 0; i < chc; i++) {
    node.removeChildPos(0)
  }
}



function clearAttributesTable() {
  var table = document.getElementById("details");
  var tb = table.getElementsByTagName('tbody')[0]
  tb.innerHTML = "&nbsp;"
}


function fillAttributesTable(resource) {
  // fill attribute table with resource attributes
  var table = document.getElementById("details");
  var tb = table.getElementsByTagName('tbody')[0]
  var keys = Object.keys(resource).sort()	// sort the attributes
  for (var i=0; i<keys.length; i++) {
    var key = keys[i];
    var newRow = tb.insertRow()
    var keyCell  = newRow.insertCell(0)
    var valueCell  = newRow.insertCell(1);

    // Colorful attributes
    switch (attributeRole(key)) {
      case "universal":   keyCell.innerHTML = "<font color=\"#e67e00\">" + shortToLongname(key) + "</font>";
                          break;
      case "common":      keyCell.innerHTML = "<font color=\"#0040ff\">" + shortToLongname(key) + "</font>";
                          break;
      case "custom":      keyCell.innerHTML = "<font color=\"#239023\">" + shortToLongname(key) + "</font>";
                          break;
      default:            keyCell.innerHTML = "<font color=\"black\">" + shortToLongname(key) + "</font>";
                          break;

    }

    valueCell.innerText = JSON.stringify(resource[key])
  }
}


function fillJSONArea(node) {
  // fill JSON text area
  document.getElementById("resource").value = JSON.stringify(node.resourceFull, null, 4)
}


function clearJSONArea() {
  // fill JSON text area
  document.getElementById("resource").value = ""
}


function setRootResourceName(name) {
  document.getElementById("rootResourceName").innerText = name
}


function clearRootResourceName() {
  document.getElementById("rootResourceName").innerHTML = "&nbsp;"
}


function setResourceInfo(node) {
  resource = node.resource
  if (typeof resource === "undefined") {
    return
  }
  // extra infos in the headers

  // type & resource identifier 
  var d  = document.getElementById("rootResourceName");
  var ty = resource['ty']
  var t  = types[ty]
  if (ty == 13) {
    var mgd = resource['mgd']
    if (mgd == undefined) {
      t = "mgmtObj"
    } else {
      t = mgdTypes[mgd]
    }
  }
  if (ty == 28) {
    t = node.tpe
  }
  if (t == undefined) {
    t = "Unknown"
  }
  var ri = "/" + resource["ri"]
  if (ri == cseid) {
    d.innerText = t + ": " + cseid
  } else {
    d.innerText = t + ": " + cseid + "/" + resource["ri"]
  }

  // the resource path

  var element = document.getElementById("resourceType");
  element.innerText =_getResourcePath(nodeClicked)

}



function _getResourcePath(node) {
  var element = document.getElementById("resourceType");
  path = new TreePath(root, node)
  result = ""
  for (p of path.toString().split(" - ")) {
    if (result.length > 0) {  // not for the first element
      result += "/" 
    }
    result += p.replace(/.*: /, "")
  }
  return result
  // return node.ri
}



function clearResourceInfo() {
  document.getElementById("resourceType").innerHTML = "&nbsp;"
}


function refreshNode() {
  if (typeof nodeClicked !== "undefined") {
    nodeClicked.wasExpanded = nodeClicked.isExpanded()
    removeChildren(nodeClicked)
    getResource(nodeClicked.resource.ri, nodeClicked, function() {
        updateDetailsOfNode(nodeClicked)
    })
  }
}


function removeNode(node) {
  var client = new HttpClient();
  ri = node.resource.ri
  client.delete(ri, node, function(response) {  
    if (typeof node.parent !== "undefined") {
      parent = node.parent
      parent.removeChild(node)
      clickOnNode(null, parent)
      refreshNode(parent)
    }
  }, 
  null);
}



function openPOA(node) {
  for (poa of node.resource.poa) {
	let url;
    try {
      url = new URL(poa);
	  if (url.protocol === "http:" || url.protocol === "https:") {
		//window.open(url, '_blank').focus();
		window.open(poa + "?open", poa).focus();
		return
	  }
	} catch (_) {
      return;
	}
  }
}
  


function setNodeAsRoot(node) {
  var riField = document.getElementById("baseri");
  riField.value = _getResourcePath(node)
  connectToCSE()
}



function deleteNode() {
  if (typeof nodeClicked !== "undefined") {
    nodeClicked.wasExpanded = nodeClicked.isExpanded()
    removeChildren(nodeClicked)
    getResource(nodeClicked.resource.ri, nodeClicked, function() {
        updateDetailsOfNode(nodeClicked)
    })
  }
}



//////////////////////////////////////////////////////////////////////////////

//
//  Utilities
//


function getUrlParameterByName(name, url) {
  if (!url) 
    url = window.location.href;
  name = name.replace(/[\[\]]/g, "\\$&");
  var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"), results = regex.exec(url);
  if (!results) 
    return null;
  if (!results[2]) 
    return '';
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}


//////////////////////////////////////////////////////////////////////////////

//
//  Refresh
//

var refreshTimer = undefined

function setupRefreshResource(seconds) {
    refreshTimer = setInterval(function() {
        refreshRESTUI = false
        refreshNode()
    }, seconds*1000)
}

function cancelRefreshResource() {
    clearInterval(refreshTimer);
    refreshTimer = undefined
}
