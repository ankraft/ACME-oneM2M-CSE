 #
#	SemanticManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module implements semantic service functions
#

"""	This module implements semantic service and helper functions. """

from __future__ import annotations

from ..resources.SMD import SMD
from ..services.Logging import Logging as L
from ..etc.Types import Result, SemanticFormat
from ..helpers import TextTools


class SemanticManager(object):
	"""	This Class implements semantic service and helper functions. """


	def __init__(self) -> None:
		L.isInfo and L.log('SemanticManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the Semantic Manager.
		
			Returns:
				Boolean that indicates the operation
		"""
		L.isInfo and L.log('SemanticManager shut down')
		return True


	#########################################################################
	#
	#	SMD support functions
	#
	

	def validateDescriptor(self, smd:SMD) -> Result:
		"""	Check that the *descriptor* attribute conforms to the syntax defined by
			the *descriptorRepresentation* attribute. 

			Todo:
				Not fully implemented yet.

			Args:
				smd: SMD object to use in the validation.
			Return:
				Result object indicating success or error.
		"""
		# Test base64 encoding is done during validation

		# Validate descriptorRepresentation
		# In TS-0004 this comes after the descriptor validation, but should come before it
		if smd.dcrp == SemanticFormat.IRI:
			return Result.errorResult(dbg = L.logDebug('dcrp format must not be IRI'))
		
		# TODO implement real validation
		L.isWarn and L.logWarn('Validation of SMD.descriptor is not implemented')

		# TODO in case of an erro: generate a Response Status Code indicating an "INVALID_SPARQL_QUERY" error
		return Result.successResult()

	
	def validateSPARQL(self, query:str) -> Result:
		"""	Validate wether an input string is a valid SPARQL query.

			Todo:
				Not implemented yet.

			Args:
				query: String with the SPARQL query to validate.
			Return:
				Result object indicating success or error.
		"""

		L.isWarn and L.logWarn('Validation of SMD.semanticOpExec is not implemented')
		return Result.successResult()


	def validateValidationEnable(self, smd:SMD) -> Result:
		"""	Check and handle the setting of the *validationEnable* attribute.

			Todo:
				Not fully implemented yet.

			Args:
				smd: SMD object to use in the validation. **Attn**: This procedure might update and change the provided *smd* object.
			Return:
				Result object indicating success or error.
		"""
		# TODO implement validation and setting of validationEnable attribute
		# Procedure from TS-0004
		# The Hosting CSE shall set the validationEnable attribute of the <semanticDescriptor> resource based on
		# the value provided in the request and its local policy. Note that the local policy may override the 
		# suggested value provided in the request from the originator to enforce or disable the following semantic 
		# validation procedures. There are different cases depending on how the local policy is configured 
		# (which is out of the scope of the present document) and whether/how the validationEnable attribute 
		# is provided in the request:
		# - validationEnable attribute is not present if it was not provided in the request or if the local policy
		#   does not allow for the validationEnable attribute;
		# - validationEnable attribute is set to true or false according to the local policy no matter how the
		#   value is provided in the request;
		# - validationEnable attribute is set to true or false according to the value provided in the request.
		L.isWarn and L.logWarn('Validation of SMD.validationEnable is not implemented')
		smd.setAttribute('vlde', False)
		smd.setAttribute('svd', False)

		return Result.successResult()


	def validateSemantics(self, smd:SMD) -> Result:
		"""	Perform the semantic validation of the <SMD> resource

			Todo:
				Not fully implemented yet.

			Args:
				smd: SMD object to use in the validation. **Attn**: This procedure might update and change the provided *smd* object.
			Return:
				Result object indicating success or error.
		"""

		if smd.vlde:	# Validation enabled
			...
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
		
		return Result.successResult()
