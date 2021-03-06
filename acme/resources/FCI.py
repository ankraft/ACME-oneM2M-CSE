#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from .Resource import *
from .AnnounceableResource import AnnounceableResource
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'ct', 'et', 'lbl', 'acpi', 'at', 'aa', 
])
fcinPolicies = constructPolicy([ 'cs' ])
attributePolicies =  addPolicy(attributePolicies, fcinPolicies)


class FCI(AnnounceableResource):

	def __init__(self, dct:JSON=None, pi:str=None, fcntType:str=None, create:bool=False) -> None:
		super().__init__(T.FCI, dct, pi, tpe=fcntType, create=create, inheritACP=True, readOnly=True, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = fcinPolicies	# only the resource type's own policies


	# Enable check for allowed sub-resources. No Child for CIN
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [])

	# Forbidd updating
	def update(self, dct:JSON=None, originator:str=None) -> Result:
		return Result(status=False, rsc=RC.operationNotAllowed, dbg='updating FCIN is forbidden')

