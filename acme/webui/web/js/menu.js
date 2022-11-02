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
                "type": ContextMenu.BUTTON,
				"icon": '&#x27F3;',
				"events": {
                    "checkEnabled": function (ty) {
                        return true; 
                    },
					"click": function(e) {
						refreshNode()
					}
				}
			},
			{
				"text": "Connect to",
                "type": ContextMenu.BUTTON,
				"icon": '&#8594;',
				"enabled" : false,
				"events": {
                    "checkEnabled": function (ty) {
                        // Can only do connection to CSR type
                        return ty == 16; 
                    },
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
                "type": ContextMenu.BUTTON,
				"events": {
                    "checkEnabled": function (ty) {
                        // Don't allow deletion of the CSE!
                        return ty != 5; 
                    },
					"click": function(e) {
						removeNode(nodeClicked)
					}
				}
			},
		];

var menu;

function showContextMenu(event, node) {
  nodeClicked.setSelected(false);
  nodeClicked = node;

  for (var i = 0; i < cmenu.length; i++){
    var item = cmenu[i];
    if (item.type == ContextMenu.DIVIDER) {
        // Don't check enable for a divider
        continue;
    }
    cmenu[i]["enabled"] = item.events.checkEnabled(node.resource.ty); 
  }

  nodeClicked.setSelected(true)
  menu.reload();
  menu.display(event);
}

function setupContextMenu() {
  menu = new ContextMenu(cmenu);
}
