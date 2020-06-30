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
import CSE, Utils
from Configuration import Configuration
from resources.Resource import Resource


# Mapping between request operations and permissions
operationsPermissions =	{ C.opRETRIEVE	: C.permRETRIEVE,
						  C.opCREATE 	: C.permCREATE,
						  C.opUPDATE 	: C.permUPDATE,
		  				  C.opDELETE 	: C.permDELETE
						}

class SecurityManager(object):

	def __init__(self) -> None:
		Logging.log('SecurityManager initialized')
		if Configuration.get('cse.security.enableACPChecks'):
			Logging.log('ACP checking ENABLED')
		else:
			Logging.log('ACP checking DISABLED')


	def shutdown(self) -> None:
		Logging.log('SecurityManager shut down')


	def hasAccess(self, originator: str, resource: Resource, requestedPermission: int, checkSelf: bool = False, ty: int = None, isCreateRequest: bool = False, parentResource: Resource = None) -> bool:
		if not Configuration.get('cse.security.enableACPChecks'):	# check or ignore the check
			return True

		if ty is not None:

			# Checking for AE	
			if ty == C.tAE and isCreateRequest:
				# originator may be None or empty or C or S. 
				# That is okay if type is AE and this is a create request
				if originator is None or len(originator) == 0 or Utils.isAllowedOriginator(originator, Configuration.get('cse.registration.allowedAEOriginators')):
					Logging.logDebug("Originator for AE CREATE. OK.")
					return True

			# Checking for remoteCSE
			if ty == C.tCSR and isCreateRequest:
				if Utils.isAllowedOriginator(originator, Configuration.get('cse.registration.allowedCSROriginators')):
					Logging.logDebug("Originator for CSR CREATE. OK.")
					return True

		# Check parameters
		if resource is None:
			Logging.logWarn("Resource must not be None")
			return False
		if requestedPermission is None or not (0 <= requestedPermission <= C.permALL):
			Logging.logWarn("RequestedPermission must not be None, and between 0 and 63")
			return False

		Logging.logDebug("Checking permission for originator: %s, ri: %s, permission: %d, selfPrivileges: %r" % (originator, resource.ri, requestedPermission, checkSelf))


		if resource.ty == C.tGRP: # target is an group resource
			# Check membersAccessControlPolicyIDs if provided, otherwise accessControlPolicyIDs to be used
			
			if (macp := resource.macp) is None or len(macp) == 0:
				Logging.logDebug("MembersAccessControlPolicyIDs not provided, using AccessControlPolicyIDs")
				# FALLTHROUGH to the permission checks below
			
			else: # handle the permission checks here
				for a in macp:
					acp, _, _ = CSE.dispatcher.retrieveResource(a)
					if acp is None:
						continue
					else:
						if acp.checkPermission(originator, requestedPermission):
							Logging.logDebug('Permission granted')
							return True
				Logging.logDebug('Permission NOT granted')
				return False


		if resource.ty == C.tACP:	# target is an ACP resource
			if resource.checkSelfPermission(originator, requestedPermission):
				Logging.logDebug('Permission granted')
				return True

		else:		# target is any other resource type
			
			# If subscription, check whether originator has retrieve permissions on the subscribed-to resource (parent)	
			if ty == C.tSUB and parentResource is not None:
				if self.hasAccess(originator, parentResource, C.permRETRIEVE) == False:
					return False

			if (acpi := resource.acpi) is None or len(acpi) == 0:	
				if resource.inheritACP:
					parentResource, _, _ = CSE.dispatcher.retrieveResource(resource.pi)
					return self.hasAccess(originator, parentResource, requestedPermission, checkSelf)
				Logging.logDebug('Missing acpi in resource')
				if (orig := resource[resource._originator]) is not None and orig == originator:
					Logging.logDebug('Allow access for creator')
					return True
				return False

			for a in acpi:
				acp, _, _ = CSE.dispatcher.retrieveResource(a)
				if acp is None:
					continue
				if checkSelf:	# forced check for self permissions
					if acp.checkSelfPermission(originator, requestedPermission):
						Logging.logDebug('Permission granted')
						return True				
				else:
					if acp.checkPermission(originator, requestedPermission):
						Logging.logDebug('Permission granted')
						return True

		# no fitting permission identified
		Logging.logDebug('Permission NOT granted')
		return False

