#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from Types import ResourceTypes as T
from .Resource import *
from Validator import constructPolicy, addPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'ct', 'et', 'lbl', 'acpi', 'at', 'aa', 
])
fcinPolicies = constructPolicy([ 'cs' ])
attributePolicies =  addPolicy(attributePolicies, fcinPolicies)


class FCI(Resource):

	def __init__(self, jsn: dict = None, pi: str = None, fcntType: str = None, create: bool = False) -> None:
		super().__init__(T.FCI, jsn, pi, tpe=fcntType, create=create, inheritACP=True, readOnly=True, attributePolicies=attributePolicies)


	# Enable check for allowed sub-resources. No Child for CIN
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource, [])

	# Forbidd updating
	def update(self, jsn: dict = None, originator: str = None) -> Tuple[bool, int, str]:
		return False, C.rcOperationNotAllowed, 'updating FCIN is forbidden'


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(fcinPolicies), C.rcOK, None

