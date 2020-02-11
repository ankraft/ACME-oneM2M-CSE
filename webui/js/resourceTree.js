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
    16 : "RemoteCSE",
    23 : "Subscription",
    28 : "FlexContainer"
}

const shortTypes = {
     1 : "ACP",
     2 : "AE",
     3 : "CNT",
     4 : "CIN",
     5 : "CSE",
     9 : "GRP",
    14 : "NOD",
    16 : "CSR",
    23 : "SUB",
    28 : "FCNT"
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
  1010 : "EventLog"
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
  1010 : "EVL"
}



function clickOnNode(e, node) {
  if (typeof nodeClicked !== "undefined") {
    nodeClicked.setSelected(false)    
  }
  node.setSelected(true)
  nodeClicked = node
  tree.reload()
  resource = node.resource
  clearAttributesTable()
  fillAttributesTable(resource)
  fillJSONArea(node)
  setResourceInfo(resource)
  setRestUI(node.resourceFull)
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

  for (var key in resource) {
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


function setResourceInfo(resource) {
  if (typeof resource === "undefined") {
    return
  }
  // extra infos in the header
  var d  = document.getElementById("resourceType");
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
  if (t == undefined) {
    t = "Unknown"
  }
  var ri = "/" + resource["ri"]
  if (ri == cseid) {
    d.innerText = t + ": " + cseid
  } else {
    d.innerText = t + ": " + cseid + "/" + resource["ri"]
  }
}

function clearResourceInfo() {
  document.getElementById("resourceType").innerHTML = "&nbsp;"
}


function refreshNode() {
  if (typeof nodeClicked !== "undefined") {
    nodeClicked.wasExpanded = nodeClicked.isExpanded()
    removeChildren(nodeClicked)
    getResource(nodeClicked.resource.ri, nodeClicked)
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
        refreshNode()
    }, seconds*1000)
}

function cancelRefreshResource() {
    clearInterval(refreshTimer);
    refreshTimer = undefined
}
