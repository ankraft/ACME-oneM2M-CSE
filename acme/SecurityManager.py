#
#	SecurityManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles access to resources
#


from Logging import Logging
from Constants import Constants as C
import CSE
from Configuration import Configuration

class SecurityManager(object):

	def __init__(self):
		Logging.log('SecurityManager initialized')
		if Configuration.get('cse.enableACPChecks'):
			Logging.log('ACP checking ENABLED')
		else:
			Logging.log('ACP checking DISABLED')


	def shutdown(self):
		Logging.log('SecurityManager shut down')


	def hasAccess(self, origin, resource, requestedPermission, checkSelf=False):
		if not Configuration.get('cse.enableACPChecks'):	# check or ignore the check
			return True

		# Check parameters
		if origin is None:
			Logging.logWarn("origin must not be None")
			return False
		if resource is None:
			Logging.logWarn("resource must not be None")
			return False
		if requestedPermission is None or not (0 <= requestedPermission <= C.permALL):
			Logging.logWarn("requestedPermission must not be None, and between 0 and 63")
			return False

		Logging.logDebug("Checking permission for origin: %s, ri: %s, permission: %d, selfPrivileges: %r" % (origin, resource.ri, requestedPermission, checkSelf))

		if resource.ty == C.tACP:	# target is an ACP resource
			if resource.checkSelfPermission(origin, requestedPermission):
				Logging.logDebug('Permission granted')
				return True

		else:		# target is not an ACP resource
			
			if (acpi := resource.acpi) is None or len(acpi) == 0:	
				if resource.inheritACP:
					(parentResource, _) = CSE.dispatcher.retrieveResource(resource.pi)
					return self.hasAccess(origin, parentResource, requestedPermission, checkSelf)
				Logging.logDebug("Missing acpi in resource")
				return False

			for a in acpi:
				(acp, _) = CSE.dispatcher.retrieveResource(a)
				if acp is None:
					continue
				if checkSelf:	# forced check for self permissions
					if acp.checkSelfPermission(origin, requestedPermission):
						Logging.logDebug('Permission granted')
						return True				
				else:
					if acp.checkPermission(origin, requestedPermission):
						Logging.logDebug('Permission granted')
						return True

		# no fitting permission identified
		Logging.logDebug('Permission NOT granted')
		return False

