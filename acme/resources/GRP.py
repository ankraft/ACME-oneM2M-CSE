#
#	GRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Group
#

from etc.Types import ResourceTypes as T, Result, ConsistencyStrategy, JSON
from resources.Resource import *
from resources.AnnounceableResource import AnnounceableResource
from services.Validator import constructPolicy, addPolicy
from services.Logging import Logging as L
import services.CSE as CSE
import resources.Factory as Factory


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'cr', 'hld', 
])
grpPolicies = constructPolicy([
	'mt', 'spty', 'cnm', 'mnm', 'mid', 'macp', 'mtv', 'csy', 'gn', 'ssi', 'nar'
])
attributePolicies = addPolicy(attributePolicies, grpPolicies)


class GRP(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.SUB, T.GRP_FOPT ]


	def __init__(self, dct:JSON=None, pi:str=None, fcntType:str=None, create:bool=False) -> None:
		super().__init__(T.GRP, dct, pi, create=create, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = grpPolicies	# only the resource type's own policies

		self.setAttribute('mt', int(T.MIXED), overwrite=False)
		self.setAttribute('ssi', False, overwrite=True)
		self.setAttribute('cnm', 0, overwrite=False)	# calculated later
		self.setAttribute('mid', [], overwrite=False)			
		self.setAttribute('mtv', False, overwrite=False)
		self.setAttribute('csy', ConsistencyStrategy.abandonMember, overwrite=False)

		# These attributes are not provided by default: mnm (no default), macp (no default)
		# optional set: spty, gn, nar


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		
		# add fanOutPoint
		ri = self.ri
		if L.isDebug: L.logDebug(f'Registering fanOutPoint resource for: {ri}')
		fanOutPointResource = Factory.resourceFromDict({ 'pi' : ri }, ty=T.GRP_FOPT).resource
		if not (res := CSE.dispatcher.createResource(fanOutPointResource, self, originator)).resource:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)
		return Result(status=True)


	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		return CSE.group.validateGroup(self, originator)


