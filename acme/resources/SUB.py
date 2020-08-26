#
#	SUB.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Subscription
#

import random, string
from Constants import Constants as C
from Types import ResourceTypes as T, Result, NotificationContentType, NotificationEventType
import Utils, CSE
from Validator import constructPolicy
from .Resource import *
from Types import ResponseCode as RC

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([
	'rn', 'ty', 'ri', 'pi', 'et', 'lbl', 'ct', 'lt', 'acpi', 'daci', 'cr', 'enc',
	'exc', 'nu', 'gpi', 'nfu', 'bn', 'rl', 'psn', 'pn', 'nsp', 'ln', 'nct', 'nec',
	'su', 'acrs'		#	primitiveProfileID missing in TS-0004
])

# LIMIT: Only http(s) requests in nu or POA is supported yet

class SUB(Resource):

	def __init__(self, jsn:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.SUB, jsn, pi, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('nct', NotificationContentType.all, overwrite=False) # LIMIT TODO: only this notificationContentType is supported now
			self.setAttribute('enc/net', [ NotificationEventType.resourceUpdate ], overwrite=False)


# TODO expirationCounter
# TODO notificationForwardingURI

	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource, [])


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (result := super().activate(parentResource, originator)).status:
			return result
		return CSE.notification.addSubscription(self, originator)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)
		CSE.notification.removeSubscription(self)


	def update(self, jsn:dict=None, originator:str=None) -> Result:
		previousNus = self['nu'].copy()
		newJson = jsn.copy()
		if not (res := super().update(jsn, originator)).status:
			return res
		return CSE.notification.updateSubscription(self, newJson, previousNus, originator)

 

	def validate(self, originator:str=None, create:bool=False) -> Result:
		if (res := super().validate(originator, create)).status == False:
			return res
		Logging.logDebug('Validating subscription: %s' % self['ri'])

		# Check necessary attributes
		if (nu := self['nu']) is None or not isinstance(nu, list):
			Logging.logDebug('"nu" attribute missing for subscription: %s' % self['ri'])
			return Result(status=False, rsc=RC.insufficientArguments, dbg='"nu" is missing or wrong type')

		# check other attributes
		self.normalizeURIAttribute('nfu')
		self.normalizeURIAttribute('nu')
		self.normalizeURIAttribute('su')

		return Result(status=True)
