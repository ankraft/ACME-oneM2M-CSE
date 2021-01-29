#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#

from Constants import Constants as C
from Types import ResourceTypes as T, Result
from Validator import constructPolicy, addPolicy
import Utils
from .Resource import *
from .AnnounceableResource import AnnounceableResource



# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'daci', 
])
pchPolicies = constructPolicy([
	# No own attributes
])
attributePolicies = addPolicy(attributePolicies, pchPolicies)


class PCH(Resource):

	def __init__(self, dct:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.PCH, dct, pi, create=create, attributePolicies=attributePolicies)
		self.resourceAttributePolicies = pchPolicies	# only the resource type's own policies


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [ T.PCH_PCU ])


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		
		from .Factory import Factory

		# register latest and oldest virtual resources
		Logging.logDebug(f'Registering latest and oldest virtual resources for: {self.ri}')

		# add PCU
		pcu = Factory.resourceFromDict({}, pi=self.ri, ty=T.PCH_PCU).resource
		if (res := CSE.dispatcher.createResource(pcu)).resource is None:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)

		return Result(status=True)

