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
from Types import ResourceTypes as T, JSON, AttributePolicies
from Validator import constructPolicy, addPolicy

mgmtObjAttributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'hld', 
	'mgd', 'obis', 'obps', 'dc', 'mgs', 'cmlk',
])


class MgmtObj(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.SUB ]


	def __init__(self, dct:JSON, pi:str, mgd:T, create:bool=False, attributePolicies:AttributePolicies=None, isRemote:bool=False) -> None:
		super().__init__(T.MGMTOBJ, dct, pi, tpe=mgd.tpe(), create=create, attributePolicies=attributePolicies, isRemote=isRemote)
		
		self.resourceAttributePolicies:AttributePolicies = deepcopy(self.resourceAttributePolicies)	# We dont want to change the original policy list
		self.resourceAttributePolicies.update(mgmtObjAttributePolicies)			# add mgmtobj policies

		if self.dict is not None:
			self.setAttribute('mgd', int(mgd), overwrite=True)

