//
//  restui.js
//
//  (c) 2020 by Andreas Kraft
//  License: BSD 3-Clause License. See the LICENSE file for further details.
//
//  REST UI components
//

var currentRestRequestMethod = "GET"
var currentResource = null
var currentResourceType = null

var btnGet
var btnPost
var btnPut
var btnDelete
var spanGet
var spanPost
var spanPut
var spanDelete
var requestbody 
var requestarea 
var sendbutton


function initRestUI() {
	requestbody = document.getElementById("rest-requestbody");
	requestarea = document.getElementById("rest-requestarea");
	sendbutton = document.getElementById("sendButton");
	var rad = document.getElementsByName("rest-method");
	for(var i = 0; i < rad.length; i++) {
		rad[i].onclick = function() {
			currentRestRequestMethod = this.value
			fillRequestArea() 
		};
	}

	btnGet     = document.getElementById("methodget")
	btnPost    = document.getElementById("methodpost")
	btnPut     = document.getElementById("methodput")
	btnDelete  = document.getElementById("methoddelete")
	spanGet    = document.getElementById("spanget")
	spanPost   = document.getElementById("spanpost")
	spanPut    = document.getElementById("spanput")
	spanDelete = document.getElementById("spandelete")
}


function setRestUI(resourceFull) {
	currentResourceType = Object.keys(resourceFull)[0];
	currentResource = resourceFull[currentResourceType]
	// bri = document.getElementById("baseri").value
	// cri = "/" + currentResource.ri
	// if (bri == cri) {
	//   document.getElementById("rest-url").value=bri
	// } else {
	//   document.getElementById("rest-url").value=bri + cri
	// }
	document.getElementById("rest-url").value=currentResource.ri


	// check requests for this resource type
	// First enable all buttons
	btnGet.disabled = false
	btnPost.disabled = false
	btnPut.disabled = false
	btnDelete.disabled = false
	spanGet.style.display = "inline-block"
	spanPost.style.display = "inline-block"
	spanPut.style.display = "inline-block"
	spanDelete.style.display = "inline-block"
	if (currentResourceType == "m2m:cb") {              // CSE
		disableButton(btnDelete, spanDelete)
	} else if (currentResourceType == "m2m:acp") {              // ACP 
		disableButton(btnPost, spanPost)
	} else if (currentResourceType == "m2m:cin") {      // CIN
		disableButton(btnPost, spanPost)
		disableButton(btnPut, spanPut)
	} else if (currentResourceType == "m2m:sub") {      // SUB
		disableButton(btnPost, spanPost)
	}
	fillHeaderArea(currentResource.ty)
	fillRequestArea()
}


// disable a button and hide it. If it is selected, then select the GET button
function disableButton(btn, spn) {
	btn.disabled = true
	spn.style.display = "none"
	if (btn.checked) {
		btn.checked = false
		btnGet.checked = true
		currentRestRequestMethod = "GET"
	}
}



function restSendForm() {
	restSendData(document.querySelector('input[name="rest-method"]:checked').value,
				 '/'+document.getElementById("rest-url").value,
				 document.getElementById("rest-headers").value,
				 requestarea.value)
}

function restSendData(method, url, headers, data) {
	var XHR = new XMLHttpRequest();


	XHR.addEventListener('error', function(event) {
		document.getElementById("restui-error").checked = true;
	});

	XHR.onreadystatechange = function() {
		if (this.readyState == 4) {
			switch (this.status) {
				case 200: s = '200 - OK'; break;
				case 201: s = '201 - Created'; break;
				case 204: s = '204 - Updated'; break;
				case 400: s = '400 - Bad Request'; break;
				case 403: s = '403 - Forbidden'; break;
				case 404: s = '404 - Not Found'; break;
				case 405: s = '405 - Method Not Allowed'; break;
				case 409: s = '409 - Conflict'; break;
                default:
                    s = this.status;
                    console.warn("Unhandled HTTP response code! " + s);
                break;
			}
			document.getElementById("rest-status").value = s;

			if (this.responseText.length > 0) {
				document.getElementById("rest-result-body").value = JSON.stringify(JSON.parse(this.responseText), null, 4);                  
			}
			if (this.status == 200 || this.status == 201 || this.status == 204) {
				if (method == "DELETE") {
					document.getElementById("rest-result-body").value = "";
					connectToCSE();
				} else {
					refreshNode()
				}
			} 
			// else {
			// 	document.getElementById("rest-result-body").value = "";
			// }
			document.getElementById("rest-result-headers").value = this.getAllResponseHeaders()
		}
	};


	XHR.open(method, url);

	var headerLines = headers.split("\n");
	for (line of headerLines) {
		x = line.split(":")
		if (x.length == 2) {
			XHR.setRequestHeader(x[0], x[1]);
		}
	}



	// Add the required HTTP header for form data POST requests
	//XHR.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

	// Finally, send our data.
	XHR.send(data);

}


// Callback and function to clear the status and rest resuld fields/areas.
function restClearResult() {
	document.getElementById("rest-status").value = '';
	document.getElementById("rest-result-headers").value = '';
	document.getElementById("rest-result-body").value = '';
}


// fill the header fields. Depending on the type and the currently selected
// method this will change, for example, the Content-Type field.
function fillHeaderArea(ty) {
	if (ty != null && currentRestRequestMethod == "POST") {
		text  = "Content-Type: application/json;ty=" + ty + "\n"
	} else {
		text  = "Content-Type: application/json\n"
	}
	text += "Accept: application/json\n"
	text += "X-M2M-Origin: " + document.getElementById("originator").value + "\n"
	text += "X-M2M-RI: " + Math.random().toString(36).slice(2) + "\n"
	text += "X-M2M-RVI: 3"       

	document.getElementById("rest-headers").value = text;
}

/////////////////////////////////////////////////////////////////////////////

tplAE = {
    "m2m:ae": {
		"acpi": [ "==> fill or remove <==" ],
        "api": "==> fill (must start with N or R) <==",
        "nl": "==> fill or remove <==",
        "poa": [ "==> fill or remove <==" ],
        "rn": "==> fill or remove <==",
        "srv": [ "3" ],
        "rr": false
    }
}

tplACP = {
    "m2m:acp": {
        "pv": { "acr": { "acop": 63, "acor": [ "==> fill <==" ] } },
        "pvs": { "acr": { "acop": 51, "acor": [ "==> fill <==" ] } },
        "rn": "==> fill <=="
    }
}

tplContainer = {
	"m2m:cnt" : {
		"acpi": [ "==> fill or remove <==" ],
		"mbs": 10000,
		"mni": 10,
		"rn":  "==> fill <=="

	}
}

tplContentInstance = {
    "m2m:cin": {
        "cnf": "text/plain:0",
        "con": "==> fill <==",
        "rn": "==> fill <=="
    }
}

tplGroup = {
    "m2m:grp": {
		"acpi": [ "==> fill or remove <==" ],
        "csy": 1,
        "gn": "==> fill <==",
        "mid": [ "==> Add members <==" ],
        "mnm": 10,
        "mt": 3,
        "rn": "==> fill <=="
    }
}

tplSubscription = {
    "m2m:sub": {
		"acpi": [ "==> fill or remove <==" ],
        "enc": { "net": [ 1, 2, 3, 4 ] },
        "nu": [ "==> fill <==" ],
        "rn": "==> fill <=="
    }
}

tplFlexContainer = {
    "==> fill <==": {
		"acpi": [ "==> fill or remove <==" ],
		"cnd": "==> fill <==",
        "rn": "==> fill <==",

        "==> custom attributes <==": "==> fill <=="

    }
}

tplNode = {
    "m2m:nod": {
		"acpi": [ "==> fill or remove <==" ],
        "ni": "==> fill <==",
        "rn": "==> fill <=="
    }
}

tplAreaNwkDeviceInfo = {
    "m2m:andi": {
		"acpi": [ "==> fill or remove <==" ],
        "awi": "==> fill <==",
        "dc": "==> fill <==",
        "dvd": "==> fill <==",
        "dvt": "==> fill <==",
        "lnh": [ "==> fill <==" ],
        "mgd": 1005,
        "rn": "==> fill <==",
        "sld": 0,
        "sli": 0
    }
}

tplAreaNwkType = {
    "m2m:ani": {
		"acpi": [ "==> fill or remove <==" ],
        "ant": "==> fill <==",
        "dc": "==> fill <==",
        "ldv": [ "==> fill <==" ],
        "mgd": 1004,
        "rn": "==> fill <=="
    }
}

tplBattery = {
    "m2m:bat": {
		"acpi": [ "==> fill or remove <==" ],
        "btl": 23,
        "bts": 7,
        "dc": "==> fill <==",
        "mgd": 1006,
        "rn": "==> fill <=="
    }
}

tplDeviceCapability = {
    "m2m:dvc": {
		"acpi": [ "==> fill or remove <==" ],
        "att": true,
        "can": "==> fill <==",
        "cas": {
            "acn": "==> fill <==",
            "sus": 1
        },
        "cus": true,
        "dc": "==> fill <==",
        "mgd": 1008,
        "rn": "==> fill <=="	
    }
}

tplDeviceInfo = {
    "m2m:dvi": {
		"acpi": [ "==> fill or remove <==" ],
        "cnty": "==> fill <==",
        "dc": "==> fill <==",
        "dlb": [
            "==> label:value <=="
        ],
        "dty": "==> fill <==",
        "dvnm": "==> fill <==",
        "fwv": "==> fill <==",
        "hwv": "==> fill <==",
        "loc": "==> fill <==",
        "man": "==> fill <==",
        "mfd": "==> fill timestamp <==",
        "mfdl": "==> fill <==",
        "mgd": 1007,
        "mod": "==> fill <==",
        "osv": "==> fill <==",
        "ptl": [ "==> fill <==" ],
        "purl": "==> fill <==",
        "rn": "==> fill <==",
        "smod": "==> fill <==",
        "spur": "==> fill <==",
        "swv": "==> fill <==",
        "syst": "==> fill timestamp <=="
    }
}

tplEventLog = {
    "m2m:evl": {
		"acpi": [ "==> fill or remove <==" ],
        "dc": "==> fill <==",
        "lga": false,
        "lgd": "==> fill <==",
        "lgo": false,
        "lgst": 1,
        "lgt": 0,
        "mgd": 1010,
        "rn": "==> fill <=="
    }
}

tplFirmware = {
    "m2m:fwr": {
		"acpi": [ "==> fill or remove <==" ],
        "dc": "==> fill <==",
        "fwn": "==> fill <==",
        "mgd": 1001,
        "rn": "==> fill <==",
        "ud": false,
        "uds": {
            "acn": "==> fill <==",
            "sus": 0
        },
        "url": "==> fill <==",
        "vr": "==> fill <=="
    }
}

tplMemory = {
    "m2m:mem": {
		"acpi": [ "==> fill or remove <==" ],
        "dc": "==> fill <==",
        "mgd": 1003,
        "mma": 0,
        "mmt": 0,
        "rn": "==> fill <=="
    }
}

tplReboot = {
    "m2m:rbo": {
		"acpi": [ "==> fill or remove <==" ],
        "dc": "==> fill <==",
        "far": false,
        "mgd": 1009,
        "rbo": false,
        "rn": "==> fill <=="
    }
}

tplSoftware = {
    "m2m:swr": {
		"acpi": [ "==> fill or remove <==" ],
        "act": false,
        "acts": {
            "acn": "==> fill <==",
            "sus": 0
        },
        "dc": "==> fill <==",
        "dea": false,
        "in": false,
        "ins": {
            "acn": "==> fill <==",
            "sus": 0
        },
        "mgd": 1002,
        "rn": "==> fill <==",
        "swn": "==> fill <==",
        "un": false,
        "url": "==> fill <==",
        "vr": "==> fill <=="
    }
}

var templates = ["", "", "", "", "", "", "", "", "", ""]
var templateTypes = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
var templateButtons = [null, null, null, null, null, null, null, null, null, null]

function fillTemplate(nr) {
	requestarea.value = templates[nr]
	fillHeaderArea(templateTypes[nr])
}

function fillRequestArea() {

	templateButtons[0] = document.getElementById("tplButton0")
	templateButtons[1] = document.getElementById("tplButton1")
	templateButtons[2] = document.getElementById("tplButton2")
	templateButtons[3] = document.getElementById("tplButton3")
	templateButtons[4] = document.getElementById("tplButton4")
	templateButtons[5] = document.getElementById("tplButton5")
	templateButtons[6] = document.getElementById("tplButton6")
	templateButtons[7] = document.getElementById("tplButton7")
	templateButtons[8] = document.getElementById("tplButton8")
	templateButtons[9] = document.getElementById("tplButton9")
	templateButtons[10] = document.getElementById("tplButton10")


	// enable / disable the area depending on the currently selected method
	if (currentRestRequestMethod == "POST" || currentRestRequestMethod == "PUT") {
		requestarea.readOnly = false;
		requestbody.style.display = 'block';

	} else {
	  requestarea.readOnly = true;
		requestbody.style.display = 'none';
	}
	if (currentRestRequestMethod == "DELETE") {
		sendButton.className = "error"
	} else {
		sendButton.className = "button success"             
	}

	// hide buttons and fill with resource for PUT
	if (currentRestRequestMethod == "GET" || currentRestRequestMethod == "DELETE") {
		hideTemplateButtons()
		return
	} else  if (currentRestRequestMethod == "PUT") {
		hideTemplateButtons()
		requestarea.value = JSON.stringify(prepareNodeForPUT(currentResource, currentResourceType), null, 4)
		return
	} 

	// only POST from here

	// add templates and buttons
	requestarea.value = ""
	hideTemplateButtons()
	if (currentResourceType == "m2m:ae") {  // AE
		showTemplateButton(0, "Container", tplContainer, 3)
		showTemplateButton(1, "FlexContainer", tplFlexContainer, 28)
		showTemplateButton(2, "Group", tplGroup, 9)
		showTemplateButton(3, "Subscription", tplSubscription, 23)
	} else if (currentResourceType == "m2m:cnt") {	// Container
		showTemplateButton(0, "Container", tplContainer, 3)
		showTemplateButton(1, "ContentInstance", tplContentInstance, 4)
		showTemplateButton(2, "Subscription", tplSubscription, 23)
	} else if (currentResourceType == "m2m:cb") {	// CSEBase
		showTemplateButton(0, "ACP", tplACP, 1)
		showTemplateButton(1, "AE", tplAE, 2)
		showTemplateButton(2, "Container", tplContainer, 3)
		showTemplateButton(3, "FlexContainer", tplFlexContainer, 28)
		showTemplateButton(4, "Group", tplGroup, 9)
		showTemplateButton(5, "Node", tplNode, 14)
		showTemplateButton(6, "Subscription", tplSubscription, 23)
	} else if (currentResourceType == "m2m:nod") {	// Node
		showTemplateButton(0, "AreaNwkDeviceInfo", tplAreaNwkDeviceInfo, 13)
		showTemplateButton(1, "AreaNwkType", tplAreaNwkType, 13)
		showTemplateButton(2, "Battery", tplBattery, 13)
		showTemplateButton(3, "Firmware", tplFirmware, 13)
		showTemplateButton(4, "DeviceCapability", tplDeviceCapability, 13)
		showTemplateButton(5, "DeviceInfo", tplDeviceInfo, 13)
		showTemplateButton(6, "EventLog", tplEventLog, 13)
		showTemplateButton(7, "Memory", tplMemory, 13)
		showTemplateButton(8, "Reboot", tplReboot, 13)
		showTemplateButton(9, "Software", tplSoftware, 13)
		showTemplateButton(10, "Subscription", tplSubscription, 23)
	} else if (currentResourceType == "m2m:grp") {	// Group
		showTemplateButton(0, "Subscription", tplSubscription, 23)
	} else if (currentResource.ty == 28) {	// FlexContainer
		showTemplateButton(0, "Container", tplContainer, 3)
		showTemplateButton(1, "FlexContainer", tplFlexContainer, 28)
		showTemplateButton(2, "Subscription", tplSubscription, 23)
	} else if (currentResource.ty == 13) {	// FlexContainer
		showTemplateButton(0, "Subscription", tplSubscription, 23)
	} 
}

function hideTemplateButtons() {
	for (b in templateButtons) {
		templateButtons[b].style.display = "none"
	}
	for (var i = templateTypes.length - 1; i >= 0; i--) {
		templateTypes[i] = 0
	}
}

function showTemplateButton(idx, text, template, ty) {
	templateButtons[idx].text = text
	templateButtons[idx].style.display = 'inline-block'
	templates[idx] = JSON.stringify(template, null, 4)
	templateTypes[idx] = ty
}



function prepareNodeForPUT(resource, tpe) {
	let r = Object.assign({}, resource);
	delete r["ct"]
	delete r["lt"]
	delete r["ri"]
	delete r["pi"]
	delete r["rn"]
	delete r["st"]
	delete r["ty"]
	delete r["cbs"]
	delete r["cni"]
	delete r["acpi"]
	delete r["mgd"]
	delete r["srt"]
	delete r["csi"]
	let result = {}
	result[tpe] = r
	return result
}
