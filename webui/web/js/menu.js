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
				"events": {
					"click": function(e) {
						refreshNode()
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
  nodeClicked.setSelected(true)
  menu.display(event);
}

function setupContextMenu() {
  menu = new ContextMenu(cmenu);
}
