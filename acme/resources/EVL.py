#
#	EVL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:EventLog
#

from .MgmtObj import *
from Constants import Constants as C
from Validator import constructPolicy
import Utils

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 
	'mgd', 'obis', 'obps', 'dc', 'mgs', 'cmlk',
	'lgt', 'lgd', 'lgst', 'lga', 'lgo'
])

lgtSystem = 1
lgtSecurity	= 2
lgtEvent = 3
lgtTrace = 4 
lgTPanic = 5

lgstStarted = 1
lgstStopped = 2
lgstUnknown = 3
lgstNotPresent = 4
lgstError = 5

defaultLogTypeId = lgtSystem
defaultLogStatus = lgstUnknown


class EVL(MgmtObj):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(jsn, pi, C.tsEVL, C.mgdEVL, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('lgt', defaultLogTypeId, overwrite=False)
			self.setAttribute('lgd', '', overwrite=False)
			self.setAttribute('lgst', defaultLogStatus, overwrite=False)
			self.setAttribute('lga', False, overwrite=False)
			self.setAttribute('lgo', False, overwrite=False)

