# Operation - Diagrams


## Resource Tree and Deployment Infrastructure Diagram

The CSE can generate a diagram with an overview about the hosted resource tree and the current deployment infrastructure of remote CSEs.
This is available by sending a GET request as follows:

=== "GET request"
	```bash
	curl localhost:8080/__structure__
	```

This returns a PlantUML diagram script that can be rendered with the [PlantUML](https://plantuml.com){target=_new} tool. The diagram shows the resource tree and the deployment infrastructure of remote CSEs. The diagram can be used to get an overview of the current deployment and to identify potential issues.

<figure markdown="1">
![Example Deployment Diagram](../images/structure.png){:, style="height:80%;width:80%"},
<figcaption>Example Deployment Diagram</figcaption>
</figure>

An optional argument *lvl=&lt;int>* can be provided to the URL to limit the number if levels of the resource tree in the diagram.

This feature must be enabled in the configuration file under [`[server.http].enableStructureEndpoint`](../setup/Configuration-http.md#general-settings). 


!!! Warning "Attention"
	Enabling this feature might reveal sensitive data. It should be disabled if not used.

When enabled the http server creates an additional endpoint */\_\_structure__*. A GET request to that endpoint returns a diagram description in [PlantUML](https://plantuml.com){target=_new} format that can be transformed in images with various tools (for example, with the online editor on the PlantUML website). 

A similar text representation of the resource tree only can be retrieved from the endpoint */\_\_structure__/text* .

=== "GET request"
	```bash
	curl localhost:8080/__structure__/text
	...

	cse-in -> m2m:cb (csi=/id-in) | ri=id-in
	├── acpCreateACPs -> m2m:acp | ri=acpCreateACPs
	├── CAdmin -> m2m:ae | ri=CAdmin
	...
	``` 
