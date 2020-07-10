#
#	MgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ManagementObject (base class for specializations)
#

from .Resource import *
import Utils
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy

mgmtObjAttributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 
	'mgd', 'obis', 'obps', 'dc', 'mgs', 'cmlk',
])

class MgmtObj(Resource):

	def __init__(self, jsn: dict, pi: str, mgd: T, create: bool = False, attributePolicies: dict = None) -> None:
		super().__init__(T.MGMTOBJ, jsn, pi, tpe=mgd.tpe(), create=create, attributePolicies=attributePolicies)
		
		if self.json is not None:
			self.setAttribute('mgd', int(mgd), overwrite=True)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource, [ T.SUB ])