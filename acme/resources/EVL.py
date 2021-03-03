#
#	EVL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:EventLog
#

from .MgmtObj import *
from Types import ResourceTypes as T, JSON
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
evlPolicies = constructPolicy([
	'lgt', 'lgd', 'lgst', 'lga', 'lgo'
])
attributePolicies = addPolicy(mgmtObjAttributePolicies, evlPolicies)


lgtSystem = 1
lgtSecurity	= 2
lgtEvent = 3
lgtTrace = 4 
lgTPanic = 5

lgstStarted = 1
lgstStopped = 2
lgstUnknown = 3
lgstNotPresent = 4
lgstError = 5

defaultLogTypeId = lgtSystem
defaultLogStatus = lgstUnknown


class EVL(MgmtObj):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		self.resourceAttributePolicies = evlPolicies	# only the resource type's own policies
		super().__init__(dct, pi, mgd=T.EVL, create=create, attributePolicies=attributePolicies)

		if self.dict is not None:
			self.setAttribute('lgt', defaultLogTypeId, overwrite=False)
			self.setAttribute('lgd', '', overwrite=False)
			self.setAttribute('lgst', defaultLogStatus, overwrite=False)
			self.setAttribute('lga', False, overwrite=False)
			self.setAttribute('lgo', False, overwrite=False)

