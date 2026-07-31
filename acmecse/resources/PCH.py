#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#
"""	This module implements the PollingChannel (PCH) resource.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import ResourceTypes, JSON, CSERequest
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..helpers.TextTools import findXPath
from ..resources.Resource import Resource, addToInternalAttributes
from ..runtime.PluginSupport import requires

from ..runtime.Logging import Logging as L

if TYPE_CHECKING:
	from ..services.Dispatcher import Dispatcher


# Add to internal attributes
addToInternalAttributes(Constants.attrParentOriginator)	
addToInternalAttributes(Constants.attrPCURI)


# Tests for special access to PCH resource is done in SecurityManager.hasAccess()

@requires(dispatcher='acmecse.services.Dispatcher')
class PCH(Resource):
	"""	PollingChannel resource class.
	"""

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	def activate(self, parentResource: Resource, originator: str) -> None:
		"""	Activate the PCH resource. Create the PCU resource and set the parent's originator.

			Args:
				parentResource:	The parent resource.
				originator:		The originator of the request.
		"""
		super().activate(parentResource, originator)

		# Store the parent's orginator/AE-ID/CSE-ID
		if parentResource.ty in [ ResourceTypes.CSEBase, ResourceTypes.AE]:
			self.setAttribute(Constants.attrParentOriginator, parentResource.getOriginator())
		else:
			raise BAD_REQUEST(L.logWarn(f'PCH must be registered under CSE or AE, not {str(ResourceTypes(parentResource.ty))}'))

		L.isDebug and L.logDebug(f'Registering <PCU> for: {self.ri}')
		(pcuResource, pcuRi) = self.createChildResourceFromDict({ 'rn' : 'pcu'}, 
											  					ty=ResourceTypes.PCH_PCU, 
																originator=originator)		# rn is assigned by resource itself. Activation later!
		self.setAttribute(Constants.attrPCURI, pcuRi)	# store own PCU ri

		# Set the aggregation state in the own PCU
		if RC.releaseVersion >= '4':
			pcuResource.setAggregate(self.rqag)
			pcuResource.dbUpdate(True)


		# NOTE Check for uniqueness is done in <AE>.childWillBeAdded()
		
	
	def update(self, dct: JSON=None, 
					 originator: Optional[str]=None,
					 doValidateAttributes: Optional[bool]=True) -> None:
		
		# Set the aggregation state in the own PCU if rqag is updated

		if dct is not None:
			_dct = dct[self.typeShortname]
			rqagNew = _dct.get('rqag')
			if rqagNew is not None and RC.releaseVersion >= '4':
				# Update the aggregation state in the own PCU
				pcuResource = self.dispatcher.retrieveLocalResource(self.attribute(Constants.attrPCURI))
				pcuResource.setAggregate(rqagNew)
				pcuResource.dbUpdate(True)

			else: 
				if rqagNew is None and 'rqag' in _dct:
					# If the rqag attribute is removed, then set the aggregation state in the own PCU to False
					pcuResource = self.dispatcher.retrieveLocalResource(self.attribute(Constants.attrPCURI))
					pcuResource.setAggregate(None)
					pcuResource.dbUpdate(True)

		super().update(dct, originator, doValidateAttributes)

	
	def getParentOriginator(self) -> str:
		"""	Return the <PCU>'s parent originator.
		
			Return:
				The <PCU>'s parent originator.
		"""
		return self.attribute(Constants.attrParentOriginator)


	def willBeRetrieved(self, originator: str, 
							  request: Optional[CSERequest] = None, 
							  subCheck: Optional[bool] = True) -> None:
		super().willBeRetrieved(originator, request, subCheck=subCheck)

		# remove the aggregate attribute from the response if the CSE is not Release 4 or higher, or if the request's rvi is lower than 4
		if RC.releaseVersion < '4' or request.rvi < '4':
			self.delAttribute('rqag', setNone=False)	# really remove the attribute from the resource instance


