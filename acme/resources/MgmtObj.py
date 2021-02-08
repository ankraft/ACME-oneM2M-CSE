#
#	MgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ManagementObject (base class for specializations)
#

from copy import deepcopy
from .Resource import *
from .AnnounceableResource import AnnounceableResource
import Utils
from Types import ResourceTypes as T, JSON, AttributePolicies
from Validator import constructPolicy, addPolicy

mgmtObjAttributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'hld', 
	'mgd', 'obis', 'obps', 'dc', 'mgs', 'cmlk',
])

class MgmtObj(AnnounceableResource):

	def __init__(self, dct:JSON, pi:str, mgd:T, create:bool=False, attributePolicies:AttributePolicies=None) -> None:
		super().__init__(T.MGMTOBJ, dct, pi, tpe=mgd.tpe(), create=create, attributePolicies=attributePolicies)
		
		self.resourceAttributePolicies:AttributePolicies = deepcopy(self.resourceAttributePolicies)	# We dont want to change the original policy list
		self.resourceAttributePolicies.update(mgmtObjAttributePolicies)			# add mgmtobj policies

		if self.dict is not None:
			self.setAttribute('mgd', int(mgd), overwrite=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [ T.SUB ])