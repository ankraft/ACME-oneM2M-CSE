//
//  main.js
//
//  (c) 2020 by Andreas Kraft
//  License: BSD 3-Clause License. See the LICENSE file for further details.
//
//  Main functions, setup etc for the web UI
//


function getChildren(node, errorCallback) {
  resource = node.resource
  // get children
  //var ri = resource['ri'] + "?fu=1&lvl=1&rcn=6" // TODO move this to the getchildren request
  var ri = resource['ri'] + "?lvl=1&rcn=6" // TODO move this to the getchildren request

  httpRoot = document.getElementById("httproot").value;
  if (httpRoot.length > 0) {
	ri = httpRoot + '/' + ri
	while (ri.includes("//")) {	// remove double slashes
		ri = ri.replace("//", "/")
	}	
  }

  var client = new HttpClient();
  // addr = cseid + "/" + ri
  client.getChildren(ri, node, function(response) { // TODo
  //client.getChildren(cseid + "/" + ri, node, function(response) { // TODo


    // remove all children, if any

    removeChildren(node)

    resource = JSON.parse(response)
    chs = resource["m2m:rrl"]["rrf"]	// Normally, the rcn=6 response content is { "m2m:rrl": { "rrf": [ ... s] }}
	if (chs == undefined) {
		chs = resource["m2m:rrl"]		// support also the "wrong" rrl structure { "m2m:rrl": [ ... ] }}
	}
    if (chs != undefined) {
      for (ch of chs) {

        // TODO in extra function createNode()
        var childNode = new TreeNode(ch.val);
        childNode.on("click", clickOnNode)
        childNode.on("expand", expandNode)
        childNode.on("collapse", collapseNode)
        childNode.on("contextmenu", function(e,n) { showContextMenu(e, n) })
        childNode.ri = ch.val
        childNode.wasExpanded = false
        childNode.setExpanded(false)
        childNode.resolved = false

        node.addChild(childNode)
      }
    }
    if (node != root) {
      if (node.wasExpanded) {
        node.setExpanded(true)
        clickOnNode(null, node)
        expandNode(node)
      } else {
        node.setExpanded(false)
      }
    } else { // Display the root node expanded and show attributes etc
      expandNode(root)
      root.setSelected(true)
      clickOnNode(null, root)
    }


    // add short info in front of name
    ty = node.resource['ty']
    pfx = shortTypes[ty]
    if (ty == 13) { // for mgmtObj the definition type
      var mgd = node.resource['mgd']
      if (mgd == undefined) {
        pfx = "MGMTOBJ"
      } else {
        pfx = mgdShortTypes[mgd]
      }
    }
    if (ty == 10013) { // for mgmtObjAnnc the definition type
      var mgd = node.resource['mgd']
      if (mgd == undefined) {
        pfx = "MGMTOBJAnnc"
      } else {
        pfx = mgdAnncShortTypes[mgd]
      }
    }
    if (ty == 28) {   // For FlexContainer the tpe
      pfx = node.tpe
    }
    if (pfx == undefined) {
      pfx = "unknown"
    }
    node.setUserObject(pfx + ": " + node.getUserObject())

    if (tree != null) {
        tree.reload()
    }

  }, function(response, status) {
    typeof errorCallback === 'function' && errorCallback(status);
  });
}


function getResource(ri, node, callback) {
  httpRoot = document.getElementById("httproot").value;
  if (httpRoot.length > 0) {
	ri = httpRoot + '/' + ri
	while (ri.includes("//")) {	// remove double slashes
		ri = ri.replace("//", "/~/")
	}	
  }	

  _getResource(ri, node, function(node) { 
    document.getElementById("connectButton").className = "button success"
    document.getElementById("connectButton").text = "Connected"
    typeof callback === 'function' && callback(node);
  }, function(status) { // error callback
    if (node.ri.endsWith("/la") || node.ri.endsWith("/ol")) { // special handling for empty la or ol
      node.setUserObject(node.ri.slice(-2))
      node.resolved = true
      tree.reload()
      return
    } 
    if (status == 404) {  // if not found remove the node from the tree and continue
      node.parent.removeChild(node)
      return    
    }

    // otherwise disconnect

    document.getElementById("connectButton").className = "button error"
    document.getElementById("connectButton").text = "Reconnect"

    showAppArea(false)

    var x = document.getElementById("treeContainer");
    x.innerHTML = "";
    tree = null;
    root = null;

    clearResourceInfo()
    clearRootResourceName()
    clearAttributesTable()
    clearJSONArea()

      // TODO Display Error message
  })
}


function _getResource(ri, node, callback, errorCallback) {
  var client = new HttpClient();
  client.get(ri, node, function(response) {  // TODO
    resource = JSON.parse(response)

    var k = Object.keys(resource)[0]
    var oldUserObject = node.getUserObject()
    node.hasDetails = true 

    if (oldUserObject.endsWith("/la")) {
      node.setUserObject("la")
    } else if (oldUserObject.endsWith("/ol")) {
      node.setUserObject("ol")
    } else if (oldUserObject.endsWith("/fopt")) {
      node.setUserObject("fopt")
      node.hasDetails = false
	} else if (oldUserObject.endsWith("/pcu")) {
	  node.setUserObject("pcu")
      node.hasDetails = false
    } else {
      node.setUserObject(resource[k].rn)  
    }
    node.resource = resource[k]
    node.tpe = k
    node.resourceFull = resource
    node.resolved = true
    node.ri = ri
    //node.wasExpanded = false

    getChildren(node, null)
    typeof callback === 'function' && callback(node);
  }, function(response, status) {
    typeof errorCallback === 'function' && errorCallback(status);
  });
}
    

function connectToCSE() {
  clearAttributesTable()
  clearJSONArea()
  clearResourceInfo()
  clearRootResourceName()
  delete nodeClicked

  // Get input fields
  originator = document.getElementById("originator").value;
  rootri = document.getElementById("baseri").value;

  root = new TreeNode("");
  root.on("click", clickOnNode)
  root.on("expand", expandNode)
  root.on("collapse", collapseNode)
  root.on("contextmenu", function(e,n) { showContextMenu(e, n) })

  tree = new TreeView(root, "#treeContainer");
  getResource(rootri, root, function(node) {
    showAppArea(true)
    setRootResourceName(node.resource.rn)
    // remove the focus from the input field
    document.activeElement.blur();
    var x = document.getElementById("appArea")
    x.focus()
  })
}

function toggleRefresh() {
  if (typeof refreshTimer !== "undefined") {
    document.getElementById("refreshButton").className = "button"
    cancelRefreshResource()
  } else {
    document.getElementById("refreshButton").className = "button success"
    setupRefreshResource(5) // TODO make configurable
  }
}


function showAppArea(state) {
  var x = document.getElementById("appArea")
  var f = document.getElementById("originator")
  if (state) {
    x.style.display = "block";
  } else {
    x.style.display = "none";
    // inputfield focus
    f.focus()
    // f.select()
  }
}


var cursorEnabled = true;

// callback for info tabs
function tabTo(number) {
  switch(number) {
    case 1: cursorEnabled = true; break;
    case 2: cursorEnabled = true; break;
    case 3: cursorEnabled = false; break;
  }

}


function toggleLongAttributeNames() {
  printLongNames = !printLongNames
  clearAttributesTable()
  if (nodeClicked.hasDetails) {
    fillAttributesTable(nodeClicked.resource)        
  }
}

function setup() {
  // document.body.style.zoom=0.6;
  this.blur();

  var riField = document.getElementById("baseri");
  cseid = getUrlParameterByName("ri")
  riField.value = cseid
  
  var orField = document.getElementById("originator");
  originator = getUrlParameterByName("or")
  orField.value = originator

  var hrField = document.getElementById("httproot");
  httpRoot = getUrlParameterByName("hr")
  if (httpRoot.startsWith("/")) {
	httpRoot = httpRoot.slice(1)
  }
  hrField.value = httpRoot
  
  // open the UI immediately if the parameter is present
  openOnStart = getUrlParameterByName("open")
  
  document.title = "ACME CSE - " + cseid


  getTextFromServer("__version__", function(version) {
    var f = document.getElementById("version");
    f.innerHTML = version;
  })



  // hide when not connected
  showAppArea(false)

  setupContextMenu()

  // add key event listener for refresh
  document.onkeypress = function(e) {
    let key = event.key.toUpperCase();
    if (key == 'R' && e.ctrlKey) {
      refreshNode()
    } else if (key == 'H' && e.ctrlKey) {
      toggleLongAttributeNames();
    } else if (key == 'C' && e.ctrlKey) {
      connectToCSE();
    }
  }
  document.onkeydown = function(e) {
    let keyCode = event.keyCode
    if (cursorEnabled == false) {
      return
    }
    if (typeof nodeClicked === "undefined") {
      return
    }
    p = nodeClicked.parent
    if (typeof p !== "undefined") {
      index = p.getIndexOfChild(nodeClicked)
      count = p.getChildCount()
    }
    if (keyCode == 40) {  // down
		e.preventDefault();
		if (typeof p !== "undefined") {
        index = (index + 1) % count
        newnode = p.getChildren()[index]
	 	clickOnNode(null, newnode)
	  }
	  e.preventDefault();

    } else if (keyCode == 38 && typeof p !== "undefined") { // up
      index = (index + count - 1) % count
      newnode = p.getChildren()[index]
      e.preventDefault();
      clickOnNode(null, newnode)

	} else if (keyCode == 39) { // right or open an unexpanded subtree
      if (nodeClicked.isLeaf()) {
        return
      }
      if (nodeClicked.isExpanded() == false) {
        nodeClicked.setExpanded(true)
        tree.reload()
        return
      }
      clickOnNode(null, nodeClicked.getChildren()[0])
    } else if (keyCode == 37) { // left or close an expanded subtree
      if (nodeClicked.isLeaf() == false && nodeClicked.isExpanded()) {
        nodeClicked.setExpanded(false)
        tree.reload()
        return
      }
      if (typeof p !== "undefined") {
        clickOnNode(null, p)
      }
    } else if (keyCode == 13) { // return
      nodeClicked.toggleExpanded()
      tree.reload()
    } else if (keyCode == 9) {
      e.preventDefault();
      e.stopPropagation();
    }

  }

  initRestUI();

  if (openOnStart != null) {
	  connectToCSE()
  }
}



