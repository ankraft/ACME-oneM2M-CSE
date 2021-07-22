#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#

from Types import ResourceTypes as T, Result, JSON
from Validator import constructPolicy, addPolicy
import CSE
from Logging import Logging as L
from .Resource import *
import resources.Factory as Factory



# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'daci', 
])
pchPolicies = constructPolicy([
	# No own attributes
])
attributePolicies = addPolicy(attributePolicies, pchPolicies)


class PCH(Resource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.PCH_PCU ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.PCH, dct, pi, create=create, attributePolicies=attributePolicies)
		self.resourceAttributePolicies = pchPolicies	# only the resource type's own policies


# TODO test Retrieve by AE only! Add new willBeRetrieved() function
# TODO continue with 10.2.5.14 Retrieve <pollingChannel>

	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# NOTE Check for uniqueness is done in <AE>.childWillBeAdded()
		# TODO the same for CSR
			
		
		# register pollingChannelURI virtual resource
		if L.isDebug: L.logDebug(f'Registering <PCU> for: {self.ri}')
		pcu = Factory.resourceFromDict(pi=self.ri, ty=T.PCH_PCU).resource	# rn is assigned by resource itself
		if (res := CSE.dispatcher.createResource(pcu)).resource is None:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)

		return Result(status=True)

