# Text UI

The Text UI is a text-based terminal UI that is enabled by default. It offers a nice way to explore the CSE and its resources, and to perform basic operations. It is also a good way to learn about the CSE's resources and their attributes.

Depending on the terminal it can be operated with the mouse or with the keyboard.

<figure markdown="1">
![Text UI of the ACME CSE](../images/textUI.png#only-light){data-gallery="light"}
![Text UI of the ACME CSE](../images/textUI-dark.png#only-dark){data-gallery="dark"}
<figcaption>Text UI of the ACME CSE</figcaption>
</figure>

## Starting the Text UI

One can switch between the normal console and the text UI by pressing the `#` key.

The text UI is started automatically in some [configuration modes](../setup/Installation.md#guided-configuration) when the CSE is started.

You can also start the text UI directly by providing the `--textui` command line argument when starting the CSE.


## UI Sections
The different sections of the text UI are described below. They can be selected by going to the corresponding tab.

**Resources**
:	This tab shows the resources in the CSE. When you select a resource, the resource's attributes are shown in the right pane. 

:	Here, you also have the option to see the request and response messages that were targeted at the selected resource. This is useful to see what happened in the background when you performed an operation on the resource.

:	You may also *Delete* a resource and its children, or export a resource.

**Requests**
:	This tab shows the requests that were sent to the CSE or were sent by the CSE. You can select a request to see its details and the response.

**Registrations**
:	This tab shows the registrations of AEs and CSEs that were created in the CSE or at a remote CSE.

**Tools**
:	This tab contains some tools that can be used to perform operations on the CSE, or run applications as scrips. 

:	See the [ACMEScript meta-tags](../development/ACMEScript-metatags.md#tuitool) for more information.

**Infos**
:	This tab shows the current number of resources, requests, and other statistics and useful information.

**Configurations**
:	This tab gives a detailed overview about the current configuration of the CSE. Though, it is currently not possible to change the configuration here, each setting is expained in detail.

**About**
:	This tab shows some information about the CSE, including the version number and the license.


## Usage
- You can navigate the text UI with your mouse or with the keyboard.
- The clock in the top right corner shows the time and date. It is UTC-based in order to help when comparing oneM2M timestamps.
