[← README](../README.md) 

# Applications and Nodes

Currently, two component implementations are provided in addtion to the main CSE. They serve as examples how implement components that are hosted by the CSE itself.

## CSE Node

This component implements a &lt;node> resource that provides additional information about the actual node (system) the CSE is running on. These are specializations of &lt;mgmtObj>'s, namely battery, memory, and device information.

It can be enabled/disabled and configured in the **[app.csenode]** section of the configuration file.


## Statistics AE

The component implements an &lt;AE> resource that provides statistic information about the CSE. It defines a proprietary &lt;flexContainer> specialization that contains custom attributes for various statistic information, and which is updated every few seconds.

It can be enabled/disabled and configured in the **[app.statistics]** section of the configuration file.


## Developing Nodes and AEs

See also [Developing Nodes and AEs](Development.md#developing-nodes-and-aes) on how to develop build-in nodes and applications.

[← README](../README.md) 
