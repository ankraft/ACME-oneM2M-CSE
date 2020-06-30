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
from Validator import constructPolicy
import Utils
from .Resource import *

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'cr',
	'mt', 'spty', 'cnm', 'mnm', 'mid', 'macp', 'mtv', 'csy', 'gn', 'ssi', 'nar'
])

class GRP(Resource):

	def __init__(self, jsn: dict = None, pi: str = None, fcntType: str = None, create: bool = False) -> None:
		super().__init__(C.tsGRP, jsn, pi, C.tGRP, create=create, attributePolicies=attributePolicies)
		if self.json is not None:
			self.setAttribute('mt', C.tMIXED, overwrite=False)
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
									 [ C.tSUB, 
									   C.tGRP_FOPT
									 ])

	def activate(self, parentResource: Resource, originator: str) -> Tuple[bool, int, str]:
		if not (result := super().activate(parentResource, originator))[0]:
			return result

		# add fanOutPoint
		ri = self['ri']
		Logging.logDebug('Registering fanOutPoint resource for: %s' % ri)
		fanOutPointResource, _ = Utils.resourceFromJSON({ 'pi' : ri }, acpi=self['acpi'], ty=C.tGRP_FOPT)
		if not (res := CSE.dispatcher.createResource(fanOutPointResource, self, originator))[0]:
			return False, res[1], res[2]
		return True, C.rcOK, None


	def validate(self, originator: str = None, create: bool = False) -> Tuple[bool, int, str]:
		if (res := super().validate(originator, create))[0] == False:
			return res
		return CSE.group.validateGroup(self, originator)




