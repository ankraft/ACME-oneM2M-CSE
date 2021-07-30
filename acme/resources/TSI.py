#
#	TSI.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: timeSeriesInstance
#

from __future__ import annotations
from etc.Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from resources.Resource import *
from resources.AnnounceableResource import AnnounceableResource
from services.Validator import constructPolicy, addPolicy


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'ct', 'lt', 'lbl', 'at', 'aa', 
])
tsiPolicies = constructPolicy([
    'dgt', 'con', 'cs', 'snr'
])
attributePolicies = addPolicy(attributePolicies, tsiPolicies)


class TSI(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes:list[T] = [ ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.TSI, dct, pi, create=create, inheritACP=True, readOnly = True, attributePolicies=attributePolicies)
		self.resourceAttributePolicies = tsiPolicies	# only the resource type's own policies
		self.setAttribute('cs', Utils.getAttributeSize(self['con']))       # Set contentSize


	# Forbid updating
	def update(self, dct:JSON=None, originator:str=None) -> Result:
		return Result(status=False, rsc=RC.operationNotAllowed, dbg='updating CIN is forbidden')

