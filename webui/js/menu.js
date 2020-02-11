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
