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

		return Result.successResult()

	

	def validateValidationEnable(self, smd:SMD) -> Result:
		"""	Check and handle the setting of the *validationEnable* attribute.

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

		return Result.successResult()