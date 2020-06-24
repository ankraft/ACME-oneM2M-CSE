#
#	FCI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: FlexContainerInstance
#

from Constants import Constants as C
from .Resource import *
from Validator import constructPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'ct', 'et', 'lbl', 'acpi',
	'cs'
])

class FCI(Resource):

	def __init__(self, jsn=None, pi=None, fcntType=None, create=False):
		super().__init__(fcntType, jsn, pi, C.tFCI, create=create, inheritACP=True, readOnly=True, attributePolicies=attributePolicies)


	# Enable check for allowed sub-resources. No Child for CIN
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource, [])