#
#	FCNT_LA.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: latest (virtual resource) for flexContainer
#

from flask import Request
from typing import Tuple
from Constants import Constants as C
import CSE, Utils
from .Resource import *
from Logging import Logging


class FCNT_LA(Resource):

	def __init__(self, jsn: dict = None, pi: str = None, create:bool = False) -> None:
		super().__init__(C.tsFCNT_LA, jsn, pi, C.tFCNT_LA, create=create, inheritACP=True, readOnly=True, rn='la', isVirtual=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource : Resource) -> bool:
		return super()._canHaveChild(resource, [])


	# def asJSON(self, embedded=True, update=False, noACP=False):
	# 	pi = self['pi']
	# 	Logging.logDebug('Latest FCI from FCNT: %s' % pi)
	# 	(pr, _) = CSE.dispatcher.retrieveResource(pi)	# get parent
	# 	rs = pr.flexContainerInstances()				# ask parent for all FCIs
	# 	if len(rs) == 0:								# In case of none
	# 		return None
	# 	return rs[-1].asJSON(embedded=embedded, update=update, noACP=noACP)		# result is sorted, so take, and return last


	def handleRetrieveRequest(self, request: Request = None, id: str = None, originator: str = None) -> Tuple[Resource, int, str]:
		""" Handle a RETRIEVE request. Return resource """
		Logging.logDebug('Retrieving latest FCI from FCNT')
		if (r := self._getLatest()) is None:
			return None, C.rcNotFound, 'no instance for <latest>'
		return r, C.rcOK, None


	def handleCreateRequest(self, request: Request, id: str, originator: str, ct: str, ty: int) -> Tuple[Resource, int, str]:
		""" Handle a CREATE request. Fail with error code. """
		return None, C.rcOperationNotAllowed, 'operation not allowed for <latest> resource type'


	def handleUpdateRequest(self, request: Request, id: str, originator: str, ct: str) -> Tuple[Resource, int, str]:
		""" Handle a UPDATE request. Fail with error code. """
		return None, C.rcOperationNotAllowed, 'operation not allowed for <latest> resource type'


	def handleDeleteRequest(self, request: Request, id: str, originator: str) -> Tuple[Resource, int, str]:
		""" Handle a DELETE request. Delete the latest resource. """
		Logging.logDebug('Deleting latest FCI from FCNT')
		if (r := self._getLatest()) is None:
			return None, C.rcNotFound, 'no instance for <latest>'
		return CSE.dispatcher.deleteResource(r, originator, withDeregistration=True)


	def _getLatest(self) -> Resource:
		pi = self['pi']
		pr, _, _ = CSE.dispatcher.retrieveResource(pi)	# get parent
		rs = []
		if pr is not None:
			rs = pr.flexContainerInstances()						# ask parent for all FCI
		return rs[-1] if len(rs) > 0 else None