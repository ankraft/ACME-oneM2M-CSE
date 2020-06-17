#
#	CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ContentInstance
#

from Constants import Constants as C
from Validator import constructPolicy
from .Resource import *
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'ct', 'lt', 'st', 'lbl', 'at', 'aa', 'cr',
	'cnf', 'cs', 'conr', 'con', 'or'

])

class CIN(Resource):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(C.tsCIN, jsn, pi, C.tCIN, create=create, inheritACP=True, readOnly = True, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('con', '', overwrite=False)
			self.setAttribute('cs', len(self['con']))


	# Enable check for allowed sub-resources. No Child for CIN
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, [])


	def activate(self, parentResource, originator):
		super().activate(parentResource, originator)
		parentResource = parentResource.dbReload()	# Read the resource again in case it was updated in the DB
		self.setAttribute('st', parentResource.st)
		return True, C.rcOK


	def update(self, jsn=None, originator=None):
		return False, C.rcOperationNotAllowed
