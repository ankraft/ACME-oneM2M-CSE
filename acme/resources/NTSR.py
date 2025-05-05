#
#	NTSR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: NotificationTargetSelfReference virtual resource
#

from __future__ import annotations
from typing import cast, Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, CSERequest, Result
from ..etc.Constants import Constants
from ..resources.VirtualResource import VirtualResource
from ..resources.Resource import addToInternalAttributes
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException, OPERATION_NOT_ALLOWED


# Add to internal attributes to ignore in validation etc
addToInternalAttributes(Constants.attrPCUAggregate)	


class NTSR(VirtualResource):

	resourceType = ResourceTypes.NTSR
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	resourceName = 'ntsr'
	""" Possibility for virtual sub-classes to provide a specific resource name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# None for virtual resources
	}


	# Disallowing CREATE is handled in the handleCreateRequest() method in Dispatcher

	def handleRetrieveRequest(self, request:Optional[CSERequest] = None, 
									id:Optional[str] = None, 
									originator:Optional[str] = None) -> Result:
		raise OPERATION_NOT_ALLOWED(L.logDebug(f'RETRIEVE not allowed for {self.typeShortname} resource'))


	def handleUpdateRequest(self, request:Optional[CSERequest] = None, 
									id:Optional[str] = None, 
									originator:Optional[str] = None) -> Result:
		raise OPERATION_NOT_ALLOWED(L.logDebug(f'UPDATE not allowed for {self.typeShortname} resource'))


	def handleDeleteRequest(self, request:Optional[CSERequest] = None, 
									id:Optional[str] = None, 
									originator:Optional[str] = None) -> Result:
			
		try:
			CSE.notification.removeNotificationTarget(self, originator)
		except ResponseException as e:
			return Result(rsc=e.rsc, dbg=e.dbg, request=request)

		return Result(rsc=ResponseStatusCode.DELETED, resource=None, request=request)

