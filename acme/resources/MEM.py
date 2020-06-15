#
#	MEM.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Memory
#

from .MgmtObj import *
from Constants import Constants as C
from Validator import constructPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 
	'mgd', 'obis', 'obps', 'dc', 'mgs', 'cmlk',
	'mma', 'mmt'
])

defaultMemoryAvailable = 0
defaultMemTotal = 0


class MEM(MgmtObj):

	def __init__(self, jsn=None, pi=None, create=False):
		super().__init__(jsn, pi, C.tsMEM, C.mgdMEM, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('mma', defaultMemoryAvailable, overwrite=False)
			self.setAttribute('mmt', defaultMemTotal, overwrite=False)

