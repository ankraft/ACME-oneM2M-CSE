//
//  main.js
//
//  (c) 2020 by Andreas Kraft
//  License: BSD 3-Clause License. See the LICENSE file for further details.
//
//  Adding a context menu for the web UI
//

var cmenu = [
			{
				"text": "Refresh",
				"icon": '&#x27F3;',
				"events": {
					"click": function(e) {
						refreshNode()
					}
				}
			},
			{
				"text": "Connect to",
				"icon": '&#8594;',
				"enabled" : false,
				"events": {
					"click": function(e) {
						openPOA(nodeClicked)
					}
				}
			},
			// {
			// 	"text": "Set Root",
			// 	"events": {
			// 		"click": function(e) {
			// 			setNodeAsRoot(nodeClicked)
			// 		}
			// 	}
			// },
	        {
	          "type": ContextMenu.DIVIDER
	        },
			{
				"text": "Delete",
				"icon": '&#x21;',
				"enabled" : false,

				"events": {
					"click": function(e) {
						removeNode(nodeClicked)
					}
				}
			}
		];

var menu

function showContextMenu(event, node) {
  nodeClicked.setSelected(false)
  nodeClicked = node
  
  // CSE
  cmenu[3]["enabled"] = (node.resource.ty != 5) 

  // CSR
  cmenu[1]["enabled"] = (node.resource.ty == 16) 

  nodeClicked.setSelected(true)
  menu.reload()
  menu.display(event);
}

function setupContextMenu() {
  menu = new ContextMenu(cmenu);
}
