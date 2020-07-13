#
#	GRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Group
#

from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
import Utils
from .Resource import *
from .AnnounceableResource import AnnounceableResource


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'cr',
])
grpPolicies = constructPolicy([
	'mt', 'spty', 'cnm', 'mnm', 'mid', 'macp', 'mtv', 'csy', 'gn', 'ssi', 'nar'
])
attributePolicies = addPolicy(attributePolicies, grpPolicies)


class GRP(AnnounceableResource):

	def __init__(self, jsn: dict = None, pi: str = None, fcntType: str = None, create: bool = False) -> None:
		super().__init__(T.GRP, jsn, pi, create=create, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = grpPolicies	# only the resource type's own policies

		if self.json is not None:
			self.setAttribute('mt', int(T.MIXED), overwrite=False)
			self.setAttribute('ssi', False, overwrite=True)
			self.setAttribute('cnm', 0, overwrite=False)	# calculated later
			self.setAttribute('mid', [], overwrite=False)			
			self.setAttribute('mtv', False, overwrite=False)
			self.setAttribute('csy', C.csyAbandonMember, overwrite=False)

			# These attributes are not provided by default: mnm (no default), macp (no default)
			# optional set: spty, gn, nar


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.SUB, 
									   T.GRP_FOPT
									 ])

	def activate(self, parentResource: Resource, originator: str) -> Tuple[bool, int, str]:
		if not (result := super().activate(parentResource, originator))[0]:
			return result

		# add fanOutPoint
		ri = self['ri']
		Logging.logDebug('Registering fanOutPoint resource for: %s' % ri)
		fanOutPointResource, _ = Utils.resourceFromJSON({ 'pi' : ri }, acpi=self['acpi'], ty=T.GRP_FOPT)
		if not (res := CSE.dispatcher.createResource(fanOutPointResource, self, originator))[0]:
			return False, res[1], res[2]
		return True, C.rcOK, None


	def validate(self, originator: str = None, create: bool = False) -> Tuple[bool, int, str]:
		if (res := super().validate(originator, create))[0] == False:
			return res
		return CSE.group.validateGroup(self, originator)


