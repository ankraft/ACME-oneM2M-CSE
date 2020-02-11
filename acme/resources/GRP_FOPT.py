#
#	GRP_FOPT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: fanOutPoint (virtual resource)
#

from Constants import Constants as C
import CSE
from .Resource import *
from Logging import Logging
from Constants import Constants as C


# TODO:
# - Handle Group Request Target Members parameter
# - Handle Group Request Identifier parameter

# LIMIT
# Only blockingRequest ist supported

class GRP_FOPT(Resource):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsGRP_FOPT, jsn, pi, C.tGRP_FOPT, create=create, inheritACP=True, readOnly=True)
		if self.json is not None:
			self.setAttribute('rn', 'fopt')


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, [])


	def retrieveRequest(self, request, id, originator):
		Logging.logDebug('Retrieving resources from fopt')
		return CSE.group.foptRequest(C.opRETRIEVE, self, request, id, originator)


	def createRequest(self, request, id, originator, ct, ty):
		Logging.logDebug('Creating resources at fopt')
		return CSE.group.foptRequest(C.opCREATE, self, request, id, originator, ct, ty)


	def updateRequest(self, request, id, originator, ct):
		Logging.logDebug('Updating resources at fopt')
		return CSE.group.foptRequest(C.opUPDATE, self, request, id, originator, ct)


	def deleteRequest(self, request, id, originator):
		Logging.logDebug('Deleting resources at fopt')
		return CSE.group.foptRequest(C.opDELETE, self, request, id, originator)


