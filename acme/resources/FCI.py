#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from __future__ import annotations
from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from .Resource import *
from .AnnounceableResource import AnnounceableResource
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'ct', 'et', 'lt', 'st', 'lbl', 'acpi', 'at', 'aa', 
])
fcinPolicies = constructPolicy([ 'cs', 'or' ])
attributePolicies =  addPolicy(attributePolicies, fcinPolicies)


class FCI(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes:list[T] = [ ]


	def __init__(self, dct:JSON=None, pi:str=None, fcntType:str=None, create:bool=False) -> None:
		super().__init__(T.FCI, dct, pi, tpe=fcntType, create=create, inheritACP=True, readOnly=True, attributePolicies=attributePolicies)
		self.resourceAttributePolicies = fcinPolicies	# only the resource type's own policies


	# Forbidd updating
	def update(self, dct:JSON=None, originator:str=None) -> Result:
		return Result(status=False, rsc=RC.operationNotAllowed, dbg='updating FCIN is forbidden')

