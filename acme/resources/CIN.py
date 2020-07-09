#
#	CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ContentInstance
#

from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T
from Validator import constructPolicy, addPolicy
from .Resource import *
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'ct', 'lt', 'st', 'lbl', 'at', 'aa', 'cr',
])
cinPolicies = constructPolicy([
	'cnf', 'cs', 'conr', 'con', 'or'
])
attributePolicies = addPolicy(attributePolicies, cinPolicies)


class CIN(Resource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.CIN, jsn, pi, create=create, inheritACP=True, readOnly = True, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('con', '', overwrite=False)
			self.setAttribute('cs', len(self['con']))


	# Enable check for allowed sub-resources. No Child for CIN
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource, [])


	def activate(self, parentResource: Resource, originator: str) -> Tuple[bool, int, str]:
		if not (result := super().activate(parentResource, originator))[0]:
			return result
		parentResource, _, _ = parentResource.dbReload()	# Read the resource again in case it was updated in the DB
		self.setAttribute('st', parentResource.st)
		return True, C.rcOK, None


	# Forbidd updating
	def update(self, jsn: dict = None, originator: str = None) -> Tuple[bool, int, str]:
		return False, C.rcOperationNotAllowed, 'updating CIN is forbidden'


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  Tuple[dict, int, str]:
		return super()._createAnnouncedJSON(cinPolicies), C.rcOK, None
