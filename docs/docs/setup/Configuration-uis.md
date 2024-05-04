# Configuration - User Interfaces

The CSE provides different user interfaces (UIs) to interact with the CSE. 

## Console

**Section: `[console]`**

These are the settings for the console.

| Setting                     | Description                                                                                                                                                                       | Default     | Configuration Name                  |
|:----------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------|:------------------------------------|
| confirmQuit                 | Quitting the console needs to be confirmed.<br />This may not work under Windows, so it is switched off by default.                                                               | False       | console.confirmQuit                 |
| headless                    | Run the CSE in headless mode, i.e. without a console and without screen logging.                                                                                                  | False       | console.headless                    |
| hideResources               | Hide certain resources from display in the console. This is a list of resource identifiers. Wildcards are allowed.                                                                | empty list  | console.hideResources               |
| refreshInterval             | Interval for continuously refreshing information displays.<br/>Must be > 0.0.                                                                                                     | 2.0 seconds | console.refreshInterval             |
| theme                       | Set the color theme for the console.<br /> Allowed values are "dark" and "light".                                                                                                 | [${basic.config:consoleTheme}](../setup/Configuration-basic.md#basic-configuration)        | console.theme                       |
| treeIncludeVirtualResources | Show virtual resources in the console's and structure endpoint's tree view.                                                                                                       | False       | console.treeIncludeVirtualResources |
| treeMode                    | Set the mode how resources and their content are presented in the console's and structure endpoint's tree view.<br/>Allowed values: `normal`, `compact`, `content`, `contentOnly' | normal      | console.treeMode                    |


## Web UI

**Section: `[webui]`**

These are the settings for the web UI.

| Setting | Description                                 |Default | Configuration Name |
|:--------|:--------------------------------------------|:-------|:-------------------|
| root    | Root path of the web UI.                    | /webui | webui.root         |


## Text UI

**Section: `[textui]`**

These are the settings for the text UI.

| Setting         | Description                                                                                                                                       |Default | Configuration Name     |
|:----------------|:--------------------------------------------------------------------------------------------------------------------------------------------------|-|:-----------------------|
| startWithTUI    | Show the text UI after startup.<br />See also command line argument [–-textui](../setup/Running.md#command-line-arguments).                                 |False | textui.startWithTUI    |
| theme           | Set the color theme for the text UI. Allowed values are `dark` and `light`.                                 | ${console:theme} | textui.theme           |
| refreshInterval | Interval for refreshing various views in the text UI.                                                                           |2.0 | textui.refreshInterval |
| maxRequestSize  | Max size of a request or response in bytes to display. Requests or responses larger than this threshold will not be displayed.| 10.000| textui.maxRequestSize  |


