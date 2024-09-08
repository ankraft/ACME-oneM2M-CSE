#
#	SemanticManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This module implements semantic service and helper functions.
"""

from __future__ import annotations
from typing import Sequence, cast, Optional, Union, List

import sys
from abc import ABC, abstractmethod
from xml.etree import ElementTree
import base64, binascii

from ..resources.SMD import SMD
from ..resources.Resource import Resource
from ..runtime import CSE
from ..etc.Types import Permission, ResourceTypes, Result, SemanticFormat, ContentSerializationType
from ..etc.ResponseStatusCodes import BAD_REQUEST, ResponseException, INTERNAL_SERVER_ERROR
from ..runtime.Logging import Logging as L


class SemanticHandler(ABC):
	"""	Abstract base class for semantic graph store handlers.
	"""

	@abstractmethod
	def validateDescription(self, description:str, format:SemanticFormat) -> Result:
		"""	Validate a semantic description.
		
			Args:
				description: A string with the semantic description.
				format: The format of the string in *description*. It must be supported.

			Return:
				A `Result` object indicating a valid description, or with an error status.
		"""
		...


	@abstractmethod
	def addDescription(self, description:str, format:SemanticFormat, id:str) -> Result:
		"""	Add a semantic description to the graph store.
		
			Args:
				description: A string with the semantic description.
				format: The format of the string in *description*. It must be a supported format.
				id: Identifier for the graph. It should be a resouce identifier.

			Return:
				A `Result` object. The query result is returned in its *data* attribute.
		"""
		...


	@abstractmethod
	def addParentID(self, id:str, pi:str) -> None:
		"""	Add the parent ID to a resource's graph.
		
			Args:
				id: Identifier for the graph. It should be a resouce identifier.
				pi: Parent ID to add.
		"""


	@abstractmethod
	def updateDescription(self, description:str, format:SemanticFormat, id: str) -> Result:
		"""	Update a description in the graph store.
		
			Args:
				description: A string with the semantic description.
				format: The format of the string in *description*.  It must be a supported format.
				id: Identifier for the graph. It should be a resouce identifier.

			Return:
				A `Result` object indicating success or error.
		"""
		...


	@abstractmethod
	def removeDescription(self, id:str) -> Result:
		"""	Remove a description from the graph store.
		
			Args:
				id: Identifier for the graph. It should be a resouce identifier.

			Return:
				A `Result` object indicating success or error.
		"""
		...


	@abstractmethod
	def query(self, query:str, ids:Sequence[str], format:str) -> Result:
		"""	Run a SPARQL query against a graph.

			Args:
				query: SPARQL query.
				ids: List of resource / graph identifiers used to build the graph for the query.
				format: Desired serialization format for the result. It must be supported.

			Return:
				`Result` object. The serialized query result is stored in *data*.
		"""
		...


	@abstractmethod
	def reset(self) -> None:
		"""	Reset the handler, remove all graphs etc.
		"""	
		...


class SemanticManager(object):
	"""	This class implements semantic service and helper functions.

		Note:
			The semantic graphs are not persisted and only hold in memory at the moment.
			When the CSE is started the *SemanticManager* rebuilds the whole semantic graph
			from the existing <`SMD`> resources in the resource tree.

		Attributes:
			semanticHandler: The semantic graph store handler to be used for the CSE.
			defaultFormat: Serialization format to use as a default
	"""

	__slots__ = (
		'semanticHandler',
		'defaultFormat',
	)

	# TODO: configurable store
	# TODO Update graph
	def __init__(self) -> None:
		"""	Initialization of the SemanticManager module. This includes re-building of the
			semantic graph in memory from the existing resources.
		"""
		self.semanticHandler = RdfLibHandler()
		# TODO determine the format
		self.defaultFormat = SemanticFormat.FF_RdfXml	# TODO configurable

		# Re-Build graph in memory from <SMD> resources.
		for smd in cast(Sequence[SMD], CSE.dispatcher.retrieveResourcesByType(ResourceTypes.SMD)):
			self.addDescriptor(smd)

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore
		L.isInfo and L.log('SemanticManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the Semantic Manager.
		
			Returns:
				Boolean that indicates the success of the operation
		"""
		L.isInfo and L.log('SemanticManager shut down')
		return True


	def restart(self, name:str) -> None:
		"""	Restart the Semantic Manager.
		"""
		self.semanticHandler.reset()
		L.isDebug and L.logDebug('SemanticManager restarted')



	#########################################################################
	#
	#	SMD support functions
	#

	def validateDescriptor(self, smd:SMD) -> None:
		"""	Check that the *descriptor* attribute conforms to the syntax defined by
			the *descriptorRepresentation* attribute. 

			Todo:
				Not fully implemented yet.

			Args:
				smd: `SMD` object to use in the validation.
		"""
		L.isDebug and L.logDebug('Validating descriptor')
		# Test base64 encoding is actually done during validation.
		# But since we need to decode it here anyway error handling is done
		# here as well.

		# Validate descriptorRepresentation
		# In TS-0004 this comes after the descriptor validation, but should come before it
		if smd.dcrp == SemanticFormat.IRI:
			raise BAD_REQUEST(L.logDebug('IRI presentation format is currently not supported (only RDF/XML, JSON-LD, Turtle)'))
		try:
			# Also store the decoded B64 string in the resource
			smd.setDecodedDSP(_desc := base64.b64decode(smd.dsp, validate = True).decode('UTF-8').strip())
		except binascii.Error as e:
			raise BAD_REQUEST(L.logDebug(f'Invalid base64-encoded descriptor: {str(e)}'))

		self.semanticHandler.validateDescription(_desc, smd.dcrp)

	
	def validateSPARQL(self, query:str) -> None:
		"""	Validate wether an input string is a valid SPARQL query.

			Todo:
				Not implemented yet.

			Args:
				query: String with the SPARQL query to validate.
		"""
		L.isDebug and L.logDebug(f'Validating SPARQL request')
		L.isWarn and L.logWarn('Validation of SMD.semanticOpExec is not implemented')


	def validateValidationEnable(self, smd:SMD) -> None:
		"""	Check and handle the setting of the *validationEnable* attribute.

			Todo:
				Not fully implemented yet.

			Args:
				smd: `SMD` object to use in the validation. **Attn**: This procedure might update and change the provided *smd* object.
		"""
		# The default for ACME is to not enable validation
		if smd.vlde is None:
			smd.setAttribute('vlde', False)
			smd.setAttribute('svd', False)


	def addDescriptor(self, smd:SMD) -> None:
		"""	Perform the semantic validation of the <`SMD`> resource

			Todo:
				Not fully implemented yet.

			Args:
				smd: `SMD` resource object to use in the validation. **Attn**: This procedure might update and change the provided *smd* object.
		"""
		L.isDebug and L.logDebug('Adding descriptor for: {smd.ri}')

		try:
			
			self.semanticHandler.addDescription(smd.getDecodeDSP(), smd.dcrp, smd.ri)
		except ResponseException as e:
			# if validation is enabled re-raise the event
			if smd.vlde:
				raise e
		
		# Add parent ID
		self.semanticHandler.addParentID(smd.ri, smd.pi)
		
		# TODO more validation!
		# b) If the validationEnable attribute is set as true, the hosting CSE shall perform the semantic validation process in
		# 	the following steps according to clause 7.10.2 in oneM2M TS-0034 [50]. Otherwise, skip the following steps.
		# c) Check if the addressed <semanticDescriptor> resource is linked to other <semanticDescriptor> resources on a remote CSE
		#	by the relatedSemantics attribute or by triples with annotation property m2m:resourceDescriptorLink in descriptor attribute.
		#	This process shall consider the recursive links.
		#	- If yes, the Hosting CSE shall generate an Update request primitive with itself as the Originator and with the 
		# 		Content parameter set to the addressed <semanticDescriptor> resource representation, and send it to the <semanticValidation>
		# 		virtual resource URI on the CSE which hosts the referenced ontology (following the ontologyRef attribute) of the addressed
		# 		<semanticDescriptor> resource (see details in clause 7.4.48.2.3). After receiving the response primitive, i.e. 
		# 		the validation result, go to step k. If no response primitive was received due to time-out or other exceptional cases,
		# 		the hosting CSE shall generate a Response Status Code indicating a "TARGET_NOT_REACHABLE" error.
		#	-  If no, perform the following steps.
		# d) Access the semantic triples from the descriptor attribute of the received <semanticDescriptor> resource.
		# e) Access the ontology referenced in the ontologyRef attribute of the received <semanticDescriptor> resource.
		# 	- If the ontology referenced by the ontologyRef attribute is an external ontology, not locally hosted by the Hosting CSE,
		# 		the Hosting CSE shall retrieve it using the corresponding protocol and identifier information specified in the ontologyRef attribute.
		#	- If the referenced ontology cannot be retrieved within a reasonable time (as defined by a local policy), the Hosting CSE shall generate
		# 		 a Response Status Code indicating an "ONTOLOGY_NOT_AVAILABLE" error.
		# f) Retrieve any local linked <semanticDescriptor> resources of the received <semanticDescriptor> resource following the URI(s) in
		#  the relatedSemantics attribute (if it exists) and the URI(s) in the triples with annotation property m2m:resourceDescriptorLink (if there are any).
		#	- Repeat this step recursively to Retrieve any further local linked <semanticDescriptor> resources.
		# 	- If the local linked <semanticDescriptor> resources cannot be retrieved within a reasonable time (which is subject to a local policy),
		# 		the Hosting CSE shall generate a Response Status Code indicating a "LINKED_SEMANTICS_NOT_AVAILABLE" error.
		# g) Retrieve the semantic triples from the descriptor attribute of the local linked <semanticDescriptor> resource.
		# h) Retrieve the referenced ontologies of the local linked <semanticDescriptor> resources following the URI(s) in ontologyRef attribute of
		# 	the linked <semanticDescriptor> resources; If the referenced ontologies cannot be retrieved within a reasonable time (as defined by 
		# 	a local policy), the Hosting CSE shall generate a Response Status Code indicating an "ONTOLOGY_NOT_AVAILABLE" error.
		# i) Combine all the semantic triples of the addressed and local linked <semanticDescriptor> resources as the set of semantic triples to be
		# 	validated, and combine all the referenced ontologies as the set of ontologies to validate the semantic triples against.
		# j) Check all the aspects of semantic validation according to clause 7.10.3 in oneM2M TS-0034 [50] based upon the semantic triples and 
		# 	referenced ontology. If any problem occurs, the Hosting CSE shall generate a Response Status Code indicating an "INVALID_SEMANTICS" error.


	def updateDescriptor(self, smd:SMD) -> None:
		"""	Update the graph for a semantic descriptor.
			
			Args:
				smd: `SMD` resource for which the graph is to be updated.
		"""
		L.isDebug and L.logDebug(f'Removing descriptor for: {smd.ri}')

		# Update the semantic description
		self.semanticHandler.updateDescription(smd.getDecodeDSP(), smd.dcrp, smd.ri)
		
		# Add parent ID
		self.semanticHandler.addParentID(smd.ri, smd.pi)



	def removeDescriptor(self, smd:SMD) -> None:
		"""	Remove the graph for a semantic descriptor.
			
			Args:
				smd: `SMD` resource for which the graph is to be update.
		"""
		L.isDebug and L.logDebug(f'Updating descriptor for: {smd.ri}')
		self.semanticHandler.removeDescription(smd.ri)

	

	#########################################################################
	#
	#	SMD discovery functions
	#

	# def getAggregatedDescriptions(self, smds:Sequence[SMD]) -> Sequence[str]:
	# 	# TODO doc
	# 	return [ base64.decodebytes(bytes(smd.dsp, 'utf-8')).decode('utf-8') 
	# 			 for smd in smds ]
	

	def executeSPARQLQuery(self, query:str, 
								 smds:Union[Sequence[SMD], SMD], 
								 ct:ContentSerializationType) -> Result:
		"""	Run a SPARQL query against a list of <`SMD`> resources.
		
			Args:
				query: String with the SPARQL query.
				smds: A list of <`SMD`> resources, or a single <`SMD`> resource, which are to be aggregated for the query.
				ct: Result serialization format to determine the result format.

			Return:
				`Result` object. If successful, the *data* attribute contains the serialized result of the query.
		"""
		L.isDebug and L.logDebug('Performing SPARQL query')

		# Determine the result format from the content serialization format
		serializationFormat = 'json' if ct in ( ContentSerializationType.JSON, ContentSerializationType.CBOR ) else 'xml'

		# Convert to list if necessary
		if isinstance(smds, SMD):
			smds = [ smds ]

		return self.semanticHandler.query(query, 
										  [ smd.ri for smd in smds ], 
										  serializationFormat)
		# aggregatedGraph = self.semanticHandler.getAggregatedGraph([ smd.ri for smd in smds ])
		# qres = self.semanticHandler.query(query, aggregatedGraph).data
		# return Result(status = True, data = qres.serialize(format='xml').decode('UTF-8'))


	def executeSemanticDiscoverySPARQLQuery(self, originator:str, 
												  query:str, 
												  smds:Sequence[SMD], 
												  ct:ContentSerializationType) -> List[Resource]:
		"""	Recursively discover link-related <`SMD`> resources and run a SPARQL query against each of the results.
		
			This implementation support the "resource link-based" method, but not the "annotation-based" method.

			When ann originator doesn't have access to a Link-related <`SMD`> resource then this resource is ignored.
			
			Args:
				query: String with the SPARQL query.
				originator: The originator of the original request. It is used to determine the access to related resources.
				smds: A list of <`SMD`> resources which are to be aggregated and for the query. 
				ct: Result serialization format to determine the result format.
			
			Return:
				`Result` object. If successful, the *data* attribute contains the serialized result of the query.
		"""
		L.isDebug and L.logDebug('Performing semantic resource discovery')
		L.isWarn and L.logWarn('Annotation-based method is not supported')
		graphIDs:dict[str, SMD] = {}	# Dictionary of related ri -> SMD

		for smd in smds:
			graphIDs[smd.ri] = smd
			if smd.rels:
				# Build a recursive list of linked SMD's
				self._buildLinkedBasedGraphIDs(smd.rels, originator, graphIDs)
		L.isDebug and L.logDebug(f'Found SMDs for semantic discovery: {graphIDs}')

		# Determine the matches and add the parent resources for those who have one
		resources:list[Resource] = []
		for smd in graphIDs.values():
			qres = self.executeSPARQLQuery(query, smd, ct)
			try:
				for e in ElementTree.fromstring(cast(str, qres.data)):	
					if e.tag.endswith('results'):	# ignore namespace
						if len(e) > 0:				# Found at least 1 result, so add the *parent resource* to the result set
							resources.append(smd.retrieveParentResource())
							break
			except Exception as e:
				raise INTERNAL_SERVER_ERROR(L.logErr(f'Error parsing SPARQL result: {str(e)}'))
		
		return resources
		


	def _buildLinkedBasedGraphIDs(self, ris:list[str], originator:str, graphIDs:dict[str, SMD]) -> None:
		""" Retrieve the resources in the *ris* attribute and follow the optional *rels* attribute recursively.

			The result does not contain duplicates.
		
			Args:
				ris: List of resource IDs to be included in the result and followed recursively.
				originator: The originator of the original request. It is used to determine the access to related resources.
				graphIDs: A dictionary of resource IDs and <`SMD`> resources that is extended during the recursive walk.
		 """
		# TODO doc
		if ris:
			for ri in ris:
				# Retrieve the resource for the ri and check permissions

				try:
					resource = CSE.dispatcher.retrieveResource(ri, originator)
				except ResponseException as e:
					L.isDebug and L.logDebug(f'skipping unavailable resource: {resource.ri}')
					continue
				ri = resource.ri
				if ri in graphIDs:	# Skip over existing IDS
					# TODO warning or error when finding duplicates?
					continue
				if not CSE.security.hasAccess(originator, resource, Permission.DISCOVERY):
					L.isDebug and L.logDebug(f'no DISCOVERY access to: {ri} for: {originator}')
					continue

				# Add found ri to list
				graphIDs[ri] = cast(SMD, resource)

				# Recursively check relations
				self._buildLinkedBasedGraphIDs(resource.rels, originator, graphIDs)



###############################################################################

import rdflib
from rdflib.plugins.stores.memory import Memory
from rdflib.term import URIRef


class RdfLibHandler(SemanticHandler):
	"""	A SemanticHandler implementation for the *rdflib* library.

		Note:
			Only the in-memory storage method is supported.

		Attributes:
			store: The store that stores the graphs.
			graph: The root graph for the CSE.
	"""

	__slots__ = (
		'store',
		'graph',
	)

	supportedFormats =	{ SemanticFormat.FF_RdfXml		: 'xml',
						  SemanticFormat.FF_JsonLD		: 'json-ld',
						  SemanticFormat.FF_RdfTurtle	: 'turtle',
						}
	"""	A map between the *SemanticFormat* enum and the rdflib string representation. Only the
		supported formats are listed here.
	"""

	storeIdentifier =	'acme'
	"""	The identifier for the graph stores."""


	def __init__(self) -> None:
		"""	Initializer for the RdfLibHandler class.
		"""
		super().__init__()
		L.isInfo and L.log('Using RDFLIB handler for semantics')

		self.store = Memory() 								# type:ignore [no-untyped-call]
		self._openStore()

		self.graph = rdflib.Dataset(store = self.store)		# type:ignore [no-untyped-call]
	

	#
	#	Implementation of the abstract methods
	#

	def validateDescription(self, description:str, format:SemanticFormat) -> None:
		if not (_format := self.getFormat(format)):
			raise BAD_REQUEST(L.logWarn(f'Unsupported format: {format} for semantic descriptor'))

		# Parse once to validate, but throw away the result
		try:
			rdflib.Graph().parse(data = description, format = _format)
		except Exception as e:
			raise BAD_REQUEST(L.logWarn(f'Invalid descriptor: {str(e)}'))
	

	def addDescription(self, description:str, format:SemanticFormat, id:str) -> None:
		if not (_format := self.getFormat(format)):
			raise BAD_REQUEST(L.logWarn(f'Unsupported format: {format} for semantic descriptor'))
		
		# Parse into its own graph
		try:
			g = rdflib.Graph(store = self.store, identifier = id)
			g.parse(data = description, format = _format)
		except Exception as e:
			L.logErr('', exc = e)
			raise BAD_REQUEST(L.logWarn(f'Invalid descriptor: {str(e)}'))
	

	def addParentID(self, id: str, pi: str) -> None:
		graph = self.graph.get_graph(URIRef(id))
		graph.add( (rdflib.Literal('m2m:resource'), rdflib.Literal('m2m:isChildOf'), rdflib.Literal(pi)) )


	def updateDescription(self, description:str, format:SemanticFormat, id: str) -> None:
		self.removeDescription(id)
		self.addDescription(description, format, id)
		
		
	def removeDescription(self, id:str) -> None:
		graph = self.getGraph(id)

		# Remove the triples from the graph
		for i in list(graph):	
			graph.remove(i)						# type:ignore [no-untyped-call]
		
		# Remove the grapth from the store. In theory, this should also delete the triples, but doesn't seem in reality, though
		# self.store.remove_graph(URIRef(id))		# type:ignore [no-untyped-call]
		self.store.remove_graph(graph)		# type:ignore [no-untyped-call]


	def query(self, query:str, ids:Sequence[str], format:str) -> Result:
		L.isDebug and L.logDebug(f'Querying graphs')

		# Check serialization format
		if not format in ( 'json', 'xml', 'csv', 'txt' ):
			raise BAD_REQUEST(L.logWarn(f'Unsupported result serialization format: {format}'))

		# Aggregate a new graph for the query
		aggregatedGraph = self.getAggregatedGraph(ids)

		# Query the graph
		try:
			qres = aggregatedGraph.query(query) # type: ignore

			# Pretty print the result to the log
			# ET.indent is only available in Python 3.9+
			if L.isDebug and sys.version_info >= (3, 9) and format == 'xml':
				element = ElementTree.XML(qres.serialize(format = format).decode('UTF-8'))
				ElementTree.indent(element)	# type:ignore
				L.logDebug(ElementTree.tostring(element, encoding = 'unicode'))
		except Exception as e:
			raise BAD_REQUEST(L.logWarn(f'Query error: {str(e)} for result'))


		# Serialize the result in the desired format and return
		return Result(data = qres.serialize(format = format).decode('UTF-8'))


	def reset(self) -> None:
		L.isDebug and L.logDebug(f'Removing all graphs from the store')
		self.store.close()								# type:ignore [no-untyped-call]
		self.store.destroy(self.storeIdentifier)		# type:ignore [no-untyped-call]
		self._openStore()

	#
	#	Handler-internal methods
	#

	def getFormat(self, format:SemanticFormat) -> Optional[str]:
		"""	Return a representation of a semantic format supported by the graph framework.

			Args:
				format:	The semantic format.
			Return:
				A string representation of the *format* that is supported, or *None* if unsupported.
		"""
		return self.supportedFormats.get(format)


	def getGraph(self, id:str) -> Optional[rdflib.Graph]:
		"""	Find and return the stored graph with the given identifier.

			Args:
				id: The graph's identifier.
			Return:
				A *Graph* object, or None.
		"""
		return self.graph.get_graph(URIRef(id))


	def getAggregatedGraph(self, ids:Sequence[str]) -> Optional[rdflib.Dataset]:
		"""	Return an aggregated graph with all the triple for the individuel
			graphs for the list of resources indicated by their resource IDs. 

			Args:
				ids: List of <semanticDescriptor> resource Identifiers.
			Return:
				Return a *DataSet* object with the aggregated graph, or None.

		"""
		L.isDebug and L.logDebug(f'Aggregating graphs for ids: {ids}')
		# create a common store for the aggregation
		dataset = rdflib.Dataset(store = Memory())		# type:ignore [no-untyped-call]
		for id in ids:
			if not (g := self.getGraph(id)):
				L.logErr(f'Graph for id: {id} not found')
				return None
			[ dataset.add(_g) for _g in g ]
				
		#L.logDebug(dataset.serialize(format='xml'))
		return dataset		

	#
	#	Graph store methods
	#

	def _openStore(self) -> None:
		"""	Open the graph store.
		"""
		self.store.open(self.storeIdentifier, create = True)
