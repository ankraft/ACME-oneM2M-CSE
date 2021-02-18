#
#	SUB.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Subscription
#

import random, string
from copy import deepcopy
from Constants import Constants as C
from Configuration import Configuration
from Types import ResourceTypes as T, Result, NotificationContentType, NotificationEventType
import Utils, CSE
from Validator import constructPolicy
from .Resource import *
from Types import ResponseCode as RC, JSON
from Logging import Logging

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([
	'rn', 'ty', 'ri', 'pi', 'et', 'lbl', 'ct', 'lt', 'cr', 'hld', 'acpi', 'daci', 'enc',
	'exc', 'nu', 'gpi', 'nfu', 'bn', 'rl', 'psn', 'pn', 'nsp', 'ln', 'nct', 'nec',
	'su', 'acrs'		#	primitiveProfileID missing in TS-0004
])

# LIMIT: Only http(s) requests in nu or POA is supported yet

class SUB(Resource):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.SUB, dct, pi, create=create, attributePolicies=attributePolicies)

		if self.dict is not None:
			self.setAttribute('nct', NotificationContentType.all, overwrite=False) # LIMIT TODO: only this notificationContentType is supported now
			self.setAttribute('enc/net', [ NotificationEventType.resourceUpdate ], overwrite=False)
			if self.bn is not None:		# set batchNotify default attributes
				self.setAttribute('bn/dur', Configuration.get('cse.sub.dur'), overwrite=False)



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


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		previousNus = deepcopy(self.nu)
		newDict = deepcopy(dct)
		if not (res := super().update(dct, originator)).status:
			return res
		return CSE.notification.updateSubscription(self, newDict, previousNus, originator)

 
	def validate(self, originator:str=None, create:bool=False, dct:JSON=None) -> Result:
		if (res := super().validate(originator, create, dct)).status == False:
			return res
		Logging.logDebug(f'Validating subscription: {self.ri}')

		# Check necessary attributes
		if (nu := self.nu) is None or not isinstance(nu, list):
			Logging.logDebug(dbg := f'"nu" attribute missing for subscription: {self.ri}')
			return Result(status=False, rsc=RC.insufficientArguments, dbg=dbg)

		# check nct and net combinations
		if (nct := self.nct) is not None and (net := self['enc/net']) is not None:
			for n in net:
				if not NotificationEventType(n).isAllowedNCT(NotificationContentType(nct)):
					Logging.logDebug(dbg := f'nct={nct} is not allowed for enc/net={net}')
					return Result(status=False, rsc=RC.badRequest, dbg=dbg)
				# fallthough

		# check other attributes
		self.normalizeURIAttribute('nfu')
		self.normalizeURIAttribute('nu')
		self.normalizeURIAttribute('su')

		return Result(status=True)
