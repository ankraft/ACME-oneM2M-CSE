#
#	ACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: AccessControlPolicy
#

from Constants import Constants as C
from .Resource import *
import Utils


class ACP(Resource):

	def __init__(self, jsn=None, pi=None, rn=None, create=False):
		super().__init__(C.tsACP, jsn, pi, C.tACP, create=create, inheritACP=True, rn=rn)


		# store permissions for easier access
		self._storePermissions()



	def validate(self, originator, create=False):
		if (res := super().validate(originator, create))[0] == False:
			return res

		# add admin originator	
		if Configuration.get('cse.acp.addAdminOrignator'):
			cseOriginator = Configuration.get('cse.originator')
			if cseOriginator not in self.pv_acor:
				self.addPermissionOriginator(cseOriginator)
			if cseOriginator not in self.pvs_acor:
				self.addSelfPermissionOriginator(cseOriginator)

		self._storePermissions()
		return (True, C.rcOK)


	#########################################################################

	#
	#	Permission handlings
	#

	def addPermissionOriginator(self, originator):
		if originator not in self.pv_acor:
			self.pv_acor.append(originator)
		self.setAttribute('pv/acr/acor', self.pv_acor)


	def setPermissionOperation(self, operation):
		self.pv_acop = operation
		self.setAttribute('pv/acr/acop', self.pv_acop)

	def addSelfPermissionOriginator(self, originator):
		if originator not in self.pvs_acor:
			self.pvs_acor.append(originator)
		self.setAttribute('pvs/acr/acor', self.pvs_acor)


	def setSelfPermissionOperation(self, operation):
		self.pvs_acop = operation
		self.setAttribute('pvs/acr/acop', self.pvs_acop)


	def checkPermission(self, origin, requestedPermission):
		if requestedPermission & self.pv_acop == 0:	# permission not fitting at all
			return False
		return 'all' in self.pv_acor or origin in self.pv_acor or requestedPermission == C.permNOTIFY


	def checkSelfPermission(self, origin, requestedPermission):
		if requestedPermission & self.pvs_acop == 0:	# permission not fitting at all
			return False
		return 'all' in self.pvs_acor or origin in self.pvs_acor


	def _storePermissions(self):
		self.pv_acop = self.attribute('pv/acr/acop', 0)
		self.pv_acor = self.attribute('pv/acr/acor', [])
		self.pvs_acop = self.attribute('pvs/acr/acop', 0)
		self.pvs_acor = self.attribute('pvs/acr/acor', [])


