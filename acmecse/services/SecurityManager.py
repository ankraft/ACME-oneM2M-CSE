#
#	SecurityManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This module implements the SecurityManager entity.
"""


from __future__ import annotations
from typing import Type, cast, Optional, Any, Tuple, Generator, TYPE_CHECKING

import ssl, threading
from dataclasses import dataclass

from ..etc.Types import JSON, ResourceTypes, Permission, CSERequest, BindingType, CSERegistrar
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST, ORIGINATOR_HAS_NO_PRIVILEGE, NOT_FOUND
from ..etc.IDUtils import isSPRelative, isAbsolute, toCSERelative, toSPRelative, toAbsolute, getIdFromOriginator, isValidAEI
from ..etc.DateUtils import utcDatetime, cronMatchesTimestamp
from ..etc.Constants import RuntimeConstants as RC
from ..etc.Utils import hashString
from ..helpers.TextTools import findXPath, simpleMatch
from ..helpers.ACMELRUCache import ACMELRUCache
from ..runtime.Configuration import Configuration
from ..runtime.EventManager import *
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import *
from ..resources.Resource import Resource, isInternalAttribute
from ..resources.PCH import PCH
from ..resources.PCH_PCU import PCH_PCU
from ..resources.ACP import ACP
from ..resources.ACPAnnc import ACPAnnc

if TYPE_CHECKING:
	from ..runtime.Storage import Storage
	from ..runtime.CredentialsManager import CredentialsManager
	from ..services.Dispatcher import Dispatcher
	from acmecse.plugins.bindings.HttpServer import HttpServer
	from acmecse.plugins.bindings.WebSocketServer import WebSocketServer
	from acmecse.plugins.services.DASManager import DASManager


@dataclass
class ACPResult():
	"""	An ACP result structure.
	"""
	allowed:bool
	""" Whether the permission is granted. """

	attributes:list[str]
	""" The attributes that are allowed. """

	authenticated:bool = False
	""" Whether the originator is authenticated. """


@eventHandler
@requires(httpServer='acmecse.plugins.bindings.HttpServer', 
		  websocketServer='acmecse.plugins.bindings.WebSocketServer',
		  required=False)
@requires(dasManager='acmecse.plugins.services.DASManager', required=False)
@requires(storage='acmecse.runtime.Storage')
@requires(dispatcher='acmecse.services.Dispatcher')
@requires(credentialsManager='acmecse.runtime.CredentialsManager')
class SecurityManager(object):
	"""	This manager entity handles access to resources and requests.
	"""

	storage:Storage = None
	""" Injected Storage instance. """

	dispatcher:Dispatcher = None
	""" Injected Dispatcher instance. """

	credentialsManager:CredentialsManager = None
	""" Injected CredentialsManager instance. """

	httpServer: HttpServer = None	# type: ignore
	"""	The injected HttpServer plugin instance."""

	websocketServer: WebSocketServer = None	# type: ignore
	"""	The injected WebSocketServer plugin instance."""

	dasManager: DASManager = None	# type: ignore
	"""	The injected DASManager plugin instance."""


	__slots__ = (
		'requestCredentials',
		'allowedCSIOriginators',
		'riTypeCache',
		'riTypeCacheLock',
	)
	""" Slots for SecurityManager class. """


	def initialize(self) -> None:
		""" Initialize the SecurityManager. 
		"""

		self.allowedCSIOriginators: list[str] = []
		""" List of allowed CSE originators that are allowed to access the CSEBase resource. """


		# Get the configuration settings
		self.initAuthInformation()

		L.isInfo and L.log('SecurityManager initialized')
		if Configuration.cse_security_enableACPChecks:
			L.isInfo and L.log('ACP checking ENABLED')
		else:
			L.isInfo and L.log('ACP checking DISABLED')

		# Initialize the RI type cache
		self.riTypeCache: ACMELRUCache = ACMELRUCache(maxsize=1024)	# TODO make the maxsize configurable
		self.riTypeCacheLock: threading.Lock = threading.Lock()


	def shutdown(self) -> bool:
		""" Shutdown the SecurityManager.
		
			Return:
				Always *True*.
		"""
		L.isInfo and L.log('SecurityManager shut down')
		return True
	

	@onEvent(eventManager.cseReset)
	def restart(self, eventData: EventData) -> None:
		"""	Restart the Security manager service.
		"""
		self.initAuthInformation()
		L.logDebug('SecurityManager restarted')


	@onEvent(eventManager.configUpdate)
	def configUpdate(self, eventData: EventData) -> None:
		"""	Handle configuration updates.

			Args:
				eventData: The event data, containing the name of the updated configuration setting and its new value.
		"""
		key:Optional[str] = eventData[0]
		value:Any = eventData[1]
		if key in ('http.security.basicAuthFile', 
			 	   'http.security.tokenAuthFile', 
				   'websocket.security.basicAuthFile', 
				   'websocket.security.tokenAuthFile'):
			self.initAuthInformation()


	###############################################################################################


	def checkAccess(self, originator: str,
						resource: Resource,
						requestedPermission: Permission,
						ty: Optional[ResourceTypes] = None,
						parentResource: Optional[Resource] = None,
						request: Optional[CSERequest] = None,
						resultResource: Optional[Resource] = None,
						exceptionType: Optional[Type[ResponseException]] = None,
						message: Optional[str] = None) -> None:
		""" Like `hasAccess()`, but raise an exception instead of returning *False*
			when the originator does not have the requested permission.

			This is a convenience wrapper for gating a single operation on one
			resource. It is *not* suitable for filtering a list of resources (e.g.
			in discovery), where a denial should skip just that one resource rather
			than abort the whole request - use `hasAccess()` directly for that.

			Args:
				originator: The originator to check for.
				resource: The target resource of a request.
				requestedPermission: The permission to test.
				ty: Mandatory for CREATE, else optional. The type of the resource that is about to be created.
				parentResource: Optional, the parent resource of a target resource.
				request: The original request, if available.
				resultResource: Optional, the resulting resource of a request.
				exceptionType: The `ResponseException` subclass to raise on denial.
					Defaults to `ORIGINATOR_HAS_NO_PRIVILEGE`.
				message: Optional custom error message. If not given, a default is
					constructed from *originator*, *requestedPermission*, and *resource*.

			Raises:
				The exception given in *exceptionType* (or `ORIGINATOR_HAS_NO_PRIVILEGE`
				by default) if the originator does not have the requested permission.
		"""
		if not self.hasAccess(originator, resource, requestedPermission, ty, parentResource, request, resultResource):
			_exceptionType = exceptionType or ORIGINATOR_HAS_NO_PRIVILEGE
			_message = message or f'originator: {originator} has no {requestedPermission} privileges for resource: {resource.ri}'
			raise _exceptionType(L.logDebug(_message))


	def hasAccess(self, originator: str, 
						resource: Resource, 
						requestedPermission: Permission, 
						ty: Optional[ResourceTypes] = None, 
						parentResource: Optional[Resource] = None,
						request: Optional[CSERequest] = None,
						resultResource: Optional[Resource] = None) -> bool:
		""" Test whether an originator has access to a resource for the requested permission.
		
			Args:
				originator: The originator to check for.
				resource: The target resource of a request.
				requestedPermission: The persmission to test.
				ty: Mandatory for CREATE, else optional. The type of the resoure that is about to be created.
				parentResource: Optional, the parent resource of a target resource.
				request: The original request, if available.
				resultResource: The resulting resource of a request.
			Return:
				Boolean indicating access.
		"""


		def _getACPAccessControlRulesPV(acpRi: str) -> Generator[dict, None, None]:
			""" Return the access control rules for a single ACP resource. This is a generator function that yields
				each accessControlRule of the ACP resource, without any filtering.
				it **does not** include the access control rules from dynamic authorization resources.

				Args:
					acpRi: The resourceID of the ACP resource.

				Return:
					A generator that yields each accessControlRule of the ACP resource.
			"""
			try:
				if not (acp := self.dispatcher.retrieveResource(acpRi)):	# resource could be on another CSE
					L.isDebug and L.logDebug(f'ACP resource not found: {acpRi}')
					return
			except ResponseException as e:
				L.isDebug and L.logDebug(f'ACP resource not found: {acpRi}: {e.dbg}')
				return

			yield from cast(ACP, acp)['pv/acr']



		def _getAccessControlRulesPV(resource: Resource) -> Generator[dict, None, None]:
			""" Return the access control rules for a resource's self-privileges. 
				This is a generator function that yields each accessControlRule of the resource, without
				any filtering. This includes the accessControlRules from *acpi*'s ACP resources, 
				*+and** the accessControlRules from *daci*'s dynamic authorization resources.

				Those methods are generator functions themselves, so this function only yields the results 
				from those methods to minimize DB and network access.

				Args:
					resource: The resource to get the access control rules from.

				Return:
					A generator that yields each accessControlRule of the resource.
			"""
			# ACPI
			if (acpi := resource.acpi):
				for acpRi in acpi:
					# Call a generator method that returns the access control rules for the ACP resource
					yield from _getACPAccessControlRulesPV(acpRi)

			# DACI - if enabled and the DASManager is available
			if self.dasManager is not None and (daci := self.dasManager.getDACIforResource(resource)):
				for daciRi in daci:
					# Call a generator method that returns the access control rules for the DACI resource
					yield from self.dasManager.retrieveACTRfromDAS(daciRi, resource, originator, request)


		#  Do or ignore the check
		if not Configuration.cse_security_enableACPChecks:
			return True
		
		#
		# grant full access to the CSE originator
		#
		if originator is None or (originator in RC.cseOriginators and Configuration.cse_security_fullAccessAdmin):
			# originator == RC.cseOriginator or \
			# originator.endswith(RC.slashCseOriginator) and Configuration.cse_security_fullAccessAdmin:
			L.isDebug and L.logDebug('Request from CSE Admin. OK.')
			return True
		
		#
		# grant full access to the CSE ID
		#
		if originator in RC.cseIDs:
			L.isDebug and L.logDebug(f'Request from CSE ID: {originator}. OK.')
			return True

		#
		# Always allow the CSE to NOTIFY
		#
		if requestedPermission == Permission.NOTIFY and originator == RC.cseCsi:
			L.isDebug and L.logDebug(f'NOTIFY permission granted for CSE: {originator}')
			return True
		
		#
		# Preparation: Remove CSE-ID if this is the same CSE
		#
		if isSPRelative(originator) and originator.startswith(RC.cseCsiSlash):
			L.isDebug and L.logDebug(f'Originator: {originator} is registered to same CSE. Converting it to CSE-Relative format.')
			originator = toCSERelative(originator)
			L.isDebug and L.logDebug(f'Converted originator: {originator}')

		#
		#	Check parameters
		#
		if not requestedPermission or not (0 <= requestedPermission <= Permission.ALL):
			L.isWarn and L.logWarn('RequestedPermission must not be None, and between 0 and 63')
			return False

		#
		# Some Separate	tests for some types
		#
		if ty is not None:	# ty is an int

			if requestedPermission == Permission.CREATE:

				match ty:
					case ResourceTypes.AE:
						# originator may be None or empty or C or S. 
						# That is okay if type is AE and this is a create request
						# Originator == None or len == 0
						if not originator or self.isAllowedOriginator(originator, Configuration.cse_registration_allowedAEOriginators):
							L.isDebug and L.logDebug('Originator for AE CREATE. OK.')
							return True
						# fall-through
					
					case ResourceTypes.CSR | ResourceTypes.CSEBaseAnnc:
						if self.isAllowedOriginator(originator, Configuration.cse_registration_allowedCSROriginators):
							L.isDebug and L.logDebug('Originator for CSR/CSEBaseAnnc CREATE. OK.')
							return True
						else:
							L.isWarn and L.logWarn(f'Originator for CSR/CSEBaseAnnc registration not found. Add "{getIdFromOriginator(originator)}" to the configuration [cse.registration].allowedCSROriginators in the CSE\'s ini file to grant access for this originator.')
							return False
				# fall-through

			if ty.isAnnounced():
				if self.isAllowedOriginator(originator, Configuration.cse_registration_allowedCSROriginators) or (parentResource and originator[1:] == parentResource.ri):
					L.isDebug and L.logDebug('Originator for Announcement. OK.')
					return True
				else:
					L.isWarn and L.logWarn('Originator for Announcement not found.')
					return False
		
		# Allow originator for announced resource
		if resource.isAnnounced():
			if self.isAllowedOriginator(originator, Configuration.cse_registration_allowedCSROriginators) and resource.lnk.startswith(f'{originator}/'):
				L.isDebug and L.logDebug('Announcement originator. OK.')
				return True
		
		# Allow originator if resource is announced to the originator and the request is UPDATE
		if (at := resource.at) is not None and requestedPermission == Permission.UPDATE:
			ot = f'{originator}/'
			if any(each.startswith(ot) for each in at):
				L.isDebug and L.logDebug('Announcement target originator. OK.')
				return True

		L.isDebug and L.logDebug(f'Permission check originator: {originator} | ri: {resource.ri} | parent ri: {parentResource.ri if parentResource else None} | permission: {requestedPermission} | resource type: {resource.ty} | type: {ty} ')

		# Check for the type of the target resource
		match resource.ty:

			# Allow some Originators to RETRIEVE the CSEBase
			case ResourceTypes.CSEBase if requestedPermission & Permission.RETRIEVE:
				# Allow remote CSE to RETRIEVE the CSEBase
				# if originator == Configuration.cse_registrar_cseID:
				if originator in self.allowedCSIOriginators:
					L.isDebug and L.logDebug(f'Grant registrar CSE Originator {originator} to RETRIEVE CSEBase. OK.')
					return True
				if self.isAllowedOriginator(originator, Configuration.cse_registration_allowedCSROriginators):
					L.isDebug and L.logDebug(f'Grant remote CSE Orignator {originator} to RETRIEVE CSEBase. OK.')
					return True

				# Allow registered AEs to RETRIEVE the CSEBase
				# This comes last, since it is the most expensive check
				try:
					# TODO perhaps have a DB with all originators and their kind?

					# TODO add a "raw" attribute that returns the JSON, but doesn't intantiate the object
					if self.storage.retrieveResource(aei=originator):
						L.isDebug and L.logDebug(f'Grant registered AE Orignator {originator} to RETRIEVE CSEBase. OK.')
						return True
				except NOT_FOUND:
					pass # NOT Found is expected
			
				# Fall-through to further checks

				# TODO can we return here already?
				# TODO add a test for accessing the CSEBase by an AE + one that fails
				

			# Checking for PollingChannel
			case ResourceTypes.PCH:
				if originator != resource.getParentOriginator():
					L.isWarn and L.logWarn('Access to <PCH> resource is only granted to the parent originator.')
					return False
				return True
			
			# target is a group resource
			case ResourceTypes.GRP_FOPT:
				parentResource = parentResource if parentResource else resource.retrieveParentResource()
				# Check membersAccessControlPolicyIDs if provided, otherwise accessControlPolicyIDs are to be used
				if not (macp := parentResource.macp):
					L.isDebug and L.logDebug('MembersAccessControlPolicyIDs not provided for GRP, using AccessControlPolicyIDs')
					# fall-through to the permission checks below
				else:
					# handle the permission already checks here

					# Check ALL acp in grp.macp
					for acpRi in macp:
						for acr in _getACPAccessControlRulesPV(acpRi):
							if self.checkACR(acr, originator, requestedPermission, ty, request).allowed:
								L.isDebug and L.logDebug(f'Permission granted by ACP: {acpRi} for GRP resource: {parentResource.ri}')
								return True

					L.isDebug and L.logDebug('Permission NOT granted')
					return False
				
			# target is an ACP or ACPAnnc resource
			case ResourceTypes.ACP | ResourceTypes.ACPAnnc:
				if self.checkSelfPrivileges(cast(ACP, resource), originator, requestedPermission, request=request):
					L.isDebug and L.logDebug('Self-Permission granted')
					return True

				L.isDebug and L.logDebug('Self-Permission NOT granted')
				return False

			case _:
				pass	# fall-through to the permission checks below

		# Different check, for resource CREATE
		match ty:
			# If subscription should be created, then check whether originator has retrieve permissions on the subscribed-to resource (parent)	
			case ResourceTypes.SUB if parentResource and requestedPermission == Permission.CREATE:
				# check whether an originator has also RETRIEVES permissions on the parent resource		
				if self.hasAccess(originator, parentResource, Permission.RETRIEVE) == False:
					return False
				# fall-through to the permission checks below
			
			case _:
				pass	# fall-through to the permission checks below

		#
		# Further permission checks
		#

		# If we have no acpi we need to check for dynamic or other authorization
		if not resource.acpi and not (self.dasManager.getDACIforResource(resource) if self.dasManager else None):
			L.isDebug and L.logDebug('Handle with missing acpi and daci in resource')

			# Not authorized by DACI, now check for missing acpi handling, which is the default behavior
			L.isDebug and L.logDebug('Handle with missing acpi and daci in resource')

			# if the resource *may* have an acpi but doesn't have one set
			if resource._attributes and 'acpi' in resource._attributes:

				# Check custodian attribute
				if custodian := resource.cstn:
					if custodian == originator:	# resource.custodian == originator -> all access
						L.isDebug and L.logDebug(f'Grant access for custodian: {custodian}')
						return True
					# When custodian is set, but doesn't match the originator then fall-through to fail
					L.isDebug and L.logDebug(f'Resource creator: {custodian} != originator: {originator}')
					# Fall-through to fail
					
				# Check resource creator
				else:
					if (creator := resource.getOriginator()) == originator:
						L.isDebug and L.logDebug('Grant access for creator')
						return True
					# if originator is not the original resource creator
					L.isDebug and L.logDebug(f'Resource creator: {creator} != originator: {originator}')
				# Fall-through to fail

			# resource doesn't support acpi attribute
			else:
				if resource.inheritACP:
					L.isDebug and L.logDebug('Checking parent\'s permission')
					try:
						if not parentResource:
							parentResource = self.dispatcher.retrieveResource(resource.pi)
						return self.hasAccess(originator, parentResource, requestedPermission, ty)	# recursive check on parent resource
					except ResponseException as e:
						L.isWarn and L.logWarn(f'Parent resource not found: {resource.pi}: {e.dbg}')
						return False
				# Fall-through to fail

			L.isDebug and L.logDebug('Permission NOT granted for resource w/o set acpi or daci')
			return False

		#
		# Finally check the acpi and daci attributes
		#

		# Check all ACPs and get also the optional accessControlAttributes
		allAcpAttributes = []

		for acr in _getAccessControlRulesPV(resource):
			if (acpResult := self.checkACR(acr, originator, requestedPermission, ty, request)).allowed:
					return True

			# not general grant, but we may need to check the attributes further
			allAcpAttributes.extend(acpResult.attributes)

		# Check the attributes
		#
		if allAcpAttributes:
			
			# This has to be done on a per-operation basis because the handling is always
			# a bit different.
			allAcpAttributes = list(set(allAcpAttributes))	# remove duplicates
			L.isDebug and L.logDebug(f'Checking attributes: {allAcpAttributes}')

			match requestedPermission:

				case Permission.RETRIEVE:

					# Compare with the result if this is a partial retrieval
					if request and request._attributeList:
						L.isDebug and L.logDebug(f'Checking attributes permissions for partial RETRIEVE: {request._attributeList}')
						for attr in request._attributeList:
							if attr not in allAcpAttributes:
								L.isDebug and L.logDebug(f'RETRIEVE permission NOT granted for one or more attributes: e.g. {attr}')
								return False
						L.isDebug and L.logDebug('Grant partial RETRIEVE attribute access')
						return True	# all found attributes are allowed
					
					# Else: Check all result attributes
					L.isDebug and L.logDebug(f'Checking attribute permissions for full RETRIEVE')
					for attr in resultResource.dict:	# Checking the result resource !
						if not isInternalAttribute(attr) and attr not in allAcpAttributes:
							L.isDebug and L.logDebug(f'RETRIEVE permission NOT granted for one or more attributes: e.g. {attr}')
							return False
					L.isDebug and L.logDebug('Grant RETRIEVE attribute access')
					return True # all found attributes are allowed

				case Permission.DELETE:

					L.isDebug and L.logDebug(f'Checking attribute permissions for DELETE')
					for attr in resource.dict:	# checking the full about-to-be deleted resource !
						if not isInternalAttribute(attr) and attr not in allAcpAttributes:
							L.isDebug and L.logDebug(f'DELETE permission NOT granted for one or more attributes: e.g. {attr}')
							return False
					L.isDebug and L.logDebug('Grant DELETE attribute access')
					return True # all found attributes are allowed

				case Permission.UPDATE:

					L.isDebug and L.logDebug(f'Checking attribute permissions for UPDATE')
					for attr in request.pc[list(request.pc.keys())[0]]:	# checking the attributes from the original request
						if not isInternalAttribute(attr) and attr not in allAcpAttributes:
							L.isDebug and L.logDebug(f'UPDATE permission NOT granted for one or more attributes: e.g. {attr}')
							return False
					request.selectedAttributes = allAcpAttributes	# Add list of allowed attributes for the response
					L.isDebug and L.logDebug('Grant UPDATE attribute access')
					return True # all found attributes are allowed

				case Permission.CREATE:

					L.isDebug and L.logDebug(f'Checking attribute permissions for CREATE')
					for attr in request.pc[list(request.pc.keys())[0]]:	# checking the attributes from the original request
						if not isInternalAttribute(attr) and attr not in allAcpAttributes:
							L.isDebug and L.logDebug(f'CREATE permission NOT granted for one or more attributes: e.g. {attr}')
							return False
					request.selectedAttributes = allAcpAttributes	# Add list of allowed attributes for the response
					L.isDebug and L.logDebug('Grant CREATE attribute access')
					return True # all found attributes are allowed

		# no fitting permission identified
		L.isDebug and L.logDebug('Permission NOT granted.')
		return False


	def checkAcpiUpdatePermission(self, request: CSERequest, 
	                              		targetResource: Resource, 
										originator: str) -> bool:
		"""	Check whether this is actually a correct update of the acpi attribute, and whether this is actually allowed.

			Args:
				request: The original request.
				targetResource: The request target.
				originator: The request originator.
			
			Return:
				Boolean value. *True* indicates that this is an ACPI update. *False* indicates that this NOT an ACPI update. if no access is provided then an exception is raised.
			
			Raises
				`BAD_REQUEST`: If the *acpi* attribute is not the only attribute in an UPDATE request.
				`ORIGINATOR_HAS_NO_PRIVILEGE`: If the originator has no access.
		"""
		updatedAttributes = findXPath(request.pc, '{*}')	# Get the attributes under the resource element

		# Check that acpi, if present, is the only attribute
		if 'acpi' in updatedAttributes:
			if len(updatedAttributes) > 1:
				raise BAD_REQUEST(L.logDebug('"acpi" must be the only attribute in an update'))
			
			# Check whether the originator has UPDATE privileges for the acpi attribute (pvs!)
			_originator = getIdFromOriginator(originator)
			if not targetResource.acpi:
				if _originator != targetResource.getOriginator():
					raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'No access to update acpi for originator: {originator}'))
				else:
					pass	# allowed for creating originator
			else:
				# test the current acpi whether the originator is allowed to update the acpi
				for acpRi in targetResource.acpi:
					try:
						if not (acp := self.dispatcher.retrieveResource(acpRi)):
							L.isWarn and L.logWarn(f'Access Check for acpi: referenced <ACP> resource not found: {acpRi}')
							continue
						if self.checkSelfPrivileges(cast(ACP, acp), _originator, Permission.UPDATE, request=request):
							break	# granted
					except ResponseException as e:
						L.isWarn and L.logWarn(f'Access Check for acpi: referenced <ACP> resource not found: {acpRi}: {e.dbg}')
						continue
				else:
					raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator: {originator} has no permission to update acpi for: {targetResource.ri}'))

			return True # True indicates that this is an ACPI update with the correct permissions
		return False	# False indicates that this NOT an ACPI update


	def checkACR(self, acr: JSON, 
					   originator: str, 
					   requestedPermission: Permission, 
					   ty: Optional[ResourceTypes] = None,
					   request: Optional[CSERequest] = None
				) -> ACPResult:
		"""	Check whether an *originator* has the requested permissions with this ACP.

			Args:
				acr: The accessControlRule to check.
				originator: The originator to test the permissions for.
				requestedPermission: The permissions to test.
				ty: If the resource type is given then it is checked for CREATE (as an allowed child resource type), otherwise as an allowed resource type.
			
			Return:
				If any of the configured *accessControlRules* of the ACP resource matches, then the originatorhas access, and *True* is returned, or *False* otherwise. Additionally, a list of accessControlAttributes combined is returned.
		"""
		allAttributes:list[str] = []
		requestAuthenticated = request.rq_authn	if request else False # Get the authentication flag from the request

		# Get through all accessControlRules because we need to collect all attributes from all rules
		# This means we cannot return early
		# The following loop iterates over the rules of 'pv' or 'pvs'

		# Check Permission-to-check first
		if requestedPermission & acr['acop'] == Permission.NONE:	# permission not fitting at all
			return ACPResult(False, allAttributes)

		# Check accessControlContexts
		if (acco := acr.get('acco')) is not None:
			found = False
			_ts = utcDatetime()
			for eachAcco in acco:

				# Check accessControlWindows
				if (actw := eachAcco.get('actw')) is not None:
					for eachActw in actw:
						if cronMatchesTimestamp(eachActw, _ts):
							found = True
							break
					else:
						return ACPResult(False, allAttributes)
	
				# Check accessControlLocationRegion
				if (aclr := eachAcco.get('aclr')) is not None:
					L.isWarn and L.logWarn('AccessControlLocationRegion is not supported yet. Ignoring.')
					found = True

				# Check accessControlIpAddresses - acip
				if (acip := eachAcco.get('acip')) is not None:
					L.isWarn and L.logWarn('AccessControlIpAddresses is not supported yet. Ignoring.')
					found = True

				# Check accessControlUserIDs
				if (acui := eachAcco.get('acui')) is not None:
					L.isWarn and L.logWarn('AccessControlUserIDs is not supported yet. Ignoring.')
					found = True
				
				# Check accessControlEvalCriteria
				if (acec := eachAcco.get('acec')) is not None:
					L.isWarn and L.logWarn('AccessControlEvalCriteria is not supported yet. Ignoring.')
					found = True
				
				# Check accessControlLimit
				if (acl := eachAcco.get('acl')) is not None:
					L.isWarn and L.logWarn('AccessControlLimit is not supported yet. Ignoring.')
					found = True

				if found:
					break
			else:
				return ACPResult(False, allAttributes)	# Not in any context, so continue with the next acr. Dont check further in this acr

		# Check accessControlAuthenticationFlag
		if (acaf := acr.get('acaf')) is not None:
			# Check whether the request is authenticated
			if acaf and not requestAuthenticated:
				return ACPResult(False, allAttributes)

		# Check accessControlAttributes
		if (aca := acr.get('aca')) is not None:
			allAttributes.extend(aca)

		# Check accessControlObjectDetails
		if (acod := acr.get('acod')) is not None:
			for eachAcod in acod:
				# Check type of chty
				if requestedPermission == Permission.CREATE:
					if ty is None or ty not in eachAcod.get('chty'):	# ty is an int, chty a list of ints
						return ACPResult(False, allAttributes)			# for CREATE: type not in chty
				else:
					if ty is not None and ty != eachAcod.get('ty'):		# ty is an int
						return ACPResult(False, allAttributes)			# any other Permission type: ty not in chty
				break # found one, so apply the next checks further down
			else:
				return ACPResult(False, allAttributes)	# NOT found,

		# TODO support acod/specialization

		# Check originator
		# If we arrive here, then all the checks have passed, and we can check the originator
		originatorAllowed = self._checkAcor(acr['acor'], originator)

		# We can return early if the originator is allowed and we don't have attributes for this
		# rule. This is ageneral permit for the originator and this operation.
		if originatorAllowed and not aca:
			return ACPResult(True, [])	# No need to collect attributes when the 

		# Not general grant, but we may have further attributes to check

		return ACPResult(False, allAttributes) 


	def checkSelfPrivileges(self, acp: ACP|ACPAnnc, 
	                           	  originator: str, 
								  requestedPermission: Permission,
								  request: CSERequest) -> bool:
		"""	Check whether an *originator* has the requested permissions to the `ACP` resource itself.
			This includes checks for any supported option in the access control rules.

			Args:
				acp: The ACP resource to check the permissions for.
				originator: The originator to test the permissions for.
				requestedPermission: The permissions to test.
				request: The CSE request object.
			Return:
				If any of the configured *accessControlRules* of the ACP resource matches, then the originator has access, and *True* is returned, or *False* otherwise.
		"""

		match acp.ty:
			case ResourceTypes.ACP:
				for acr in acp['pvs/acr']:
					if self.checkACR(acr, originator, requestedPermission, request=request).allowed:
						return True
				return False

			case ResourceTypes.ACPAnnc:
				# Check for self permissions in the ACPAnnc must be done a bit differently because we 
				# don't have the optimizations that we have in the ACP resource
				
				# TODO verify this approach. Because it seems to be the same as above

				for acr in acp['pvs/acr']:
					if self.checkACR(acr, originator, requestedPermission, request=request).allowed:
						return True
				return False
		return False


	def _checkAcor(self, acor: list[str], originator: str) -> bool:
		""" Check whether an originator is in the list of acor entries.

			Per TS-0003 Table 7.1.3-2, a "*" wildcard's scope never extends across
			a "/": entries are matched form-aware (absolute / SP-relative / CSE-relative)
			and segment-by-segment, not as a single flat glob over the whole ID.

			Args:
				acor: The list of acor entries.
				originator: The originator to check.

			Return:
				True if the originator is in the list of acor entries, False otherwise.
		"""

		# Fast path: the 'all' keyword, or an exact match. This covers the
		# overwhelming majority of real checks without any of the form/wildcard
		# handling below.
		if 'all' in acor or originator in acor:
			return True

		# The originator's own ID form, computed once and reused for the
		# per-entry fast-path check below.
		originatorIsAbsolute = isAbsolute(originator)
		originatorIsSPRelative = isSPRelative(originator)

		# The originator's normalized forms, computed lazily and memoized: several
		# acor entries may need the same conversion, and there's no reason to redo
		# it more than once per call.
		absOriginator: Optional[str] = None
		isSameSP: Optional[bool] = None
		isSameCSE: Optional[bool] = None

		for a in acor:

			# A wildcard rules out this entry being a <group> resource-ID (TS-0003:
			# wildcards are not permitted there), so skip the group lookup - which
			# would otherwise attempt a resource retrieval for what is almost
			# certainly not a resource ID - entirely.
			if '*' not in a:

				# Check for group. If the originator is a member of a group, then the originator has access
				if self.getTypeForRi(a) == ResourceTypes.GRP:
					try:
						if originator in self.dispatcher.retrieveResource(a).mid:
							L.isDebug and L.logDebug(f'Originator found in group member')
							return True
					except ResponseException as e:
						L.logErr(f'GRP resource not found for ACP check: {a}', exc=e)
					continue	# A group entry is never also an ID pattern

				# No wildcard, same ID-form, and same segment count as the originator:
				# the only possible match is literal equality, already ruled out above.
				# (The segment-count check matters here: the S-type AE shortcut below
				# can still make two same-form, wildcard-free entries of *different*
				# segment counts equivalent, e.g. "//sp/S988" and "//sp/cse/S988".)
				if (isAbsolute(a) == originatorIsAbsolute
						and isSPRelative(a) == originatorIsSPRelative
						and a.count('/') == originator.count('/')):
					continue

			# Form-aware match: normalize the originator to the pattern's own form
			# before comparing, so that e.g. an SP-relative pattern can never match
			# an originator from a different Service Provider just because their
			# CSE-ID/AE-ID happen to look alike.
			if isAbsolute(a):
				if absOriginator is None:
					absOriginator = toAbsolute(originator)
				candidate = absOriginator
			elif isSPRelative(a):
				if isSameSP is None:
					if absOriginator is None:
						absOriginator = toAbsolute(originator)
					isSameSP = absOriginator.startswith(RC.cseSPidSlash)
				if not isSameSP:
					continue
				candidate = toSPRelative(originator)
			else:	# CSE-relative: implicitly scoped to this SP *and* this CSE
				if isSameCSE is None:
					if absOriginator is None:
						absOriginator = toAbsolute(originator)
					# RC.cseAbsolute/cseAbsoluteSlash include the CSEBase's own
					# resource name (RC.cseSPRelative == f'{cseCsi}/{cseRn}') - that's
					# for structured resource-tree addressing under the CSEBase, not
					# for AE-ID/originator addressing, which goes directly SP/CSE-ID/AE-ID
					# with no CSEBase-rn hop. RC.cseSPCsi (SP-ID + CSE-ID only) is the
					# right prefix here - it's also what RC.cseIDs uses to recognize
					# this CSE as an originator.
					isSameCSE = absOriginator.startswith(RC.cseSPCsiSlash)
				if not isSameCSE:
					continue
				# Not toCSERelative(originator): from an already-absolute originator
				# it only strips the SP-ID, leaving the CSE-ID in place (it's only
				# fully correct starting from SP-relative input). We've already
				# verified the RC.cseSPCsiSlash prefix above, so strip it directly.
				candidate = absOriginator.removeprefix(RC.cseSPCsiSlash)

			if self._matchIDSegments(candidate, a):
				return True

		# No match found
		return False


	def _matchIDSegments(self, candidate: str, pattern: str) -> bool:
		""" Match a normalized candidate originator ID against an acor pattern of the
			same form (both absolute, both SP-relative, or both CSE-relative), segment
			by segment, per TS-0003 Table 7.1.3-2: a wildcard's scope never extends
			across a "/".

			A pattern may omit the CSE-ID segment entirely when addressing an S-type
			AE-ID, which - unlike a C-type AE-ID - is unique for the whole Service
			Provider and therefore doesn't require one to disambiguate it.

			Args:
				candidate: The originator, already normalized to the same ID form as *pattern*.
				pattern: The acor entry to match against.

			Return:
				True if *candidate* matches *pattern*.
		"""
		candidateSegments = candidate.split('/')
		patternSegments = pattern.split('/')

		if len(candidateSegments) == len(patternSegments):
			return all(simpleMatch(c, p) for c, p in zip(candidateSegments, patternSegments))

		# The pattern omits the CSE-ID segment: only valid for an S-type AE-ID
		if (len(patternSegments) == len(candidateSegments) - 1
				and candidateSegments[-1].startswith('S')
				and patternSegments[-1].startswith('S')):
			return (all(simpleMatch(c, p) for c, p in zip(candidateSegments[:-2], patternSegments[:-1]))
					and simpleMatch(candidateSegments[-1], patternSegments[-1]))

		return False







	def isAllowedOriginator(self, originator:str, allowedOriginators:list[str]) -> bool:
		""" Check whether an Originator is in the provided list of allowed originators. This list may contain regex.
			
			The hosting CSE has always access.

			Args:
				originator: The request originator.
				allowedOriginators: A list of allowed originators, which may include regex.
			
			Return:
				Boolean value indicating the result.
		"""
		if not originator or not allowedOriginators:
			return False

		# Special handling for SP-Relative originators that end with /S, which is the case for AE S-Registration. 
		if isSPRelative(originator) and originator.endswith('/S'):
			L.isDebug and L.logDebug(f'Originator: {originator} is SP-Relative and ends with /S (AE S-Registration). Removing /S for the check.')
			originator = originator[:-2]

		# _originator = getIdFromOriginator(originator) if not isAbsolute(originator) else originator
		L.isDebug and L.logDebug(f'Originator: {originator} - allowed originators: {allowedOriginators}')

		
		# Always allow for the hosting CSE
		if originator in [RC.cseCsi, RC.cseSPRelative] :
			return True

		for ao in allowedOriginators:
			if simpleMatch(originator, ao):
				return True
		return False


	def hasAccessToPollingChannel(self, originator:str, resource:PCH|PCH_PCU) -> bool:
		"""	Check whether the originator has access to the PCU resource.
			This should be done to check the parent PCH, but the originator
			would be the same as the PCU, so we can optimize this a bit.

			Args:
				originator: The request originator
				resource: Either a PCH or PCU resource

			Return:
				Boolean indicating the result.
		"""
		return originator == resource.getOriginator()


	def isAEOriginator(self, originator:str) -> bool:
		"""	Check whether the provided originator could be an AE-ID.

			Args:
				originator: The request originator.

			Return:
				Boolean indicating the result.
		"""
		return isValidAEI(originator)


	##########################################################################
	#
	#	Certificate handling
	#

	def _getContext(self, useTLS:bool, verifyCertificate:bool, tlsVersion:str, caCertificateFile:str, caPrivateKeyFile:str) -> ssl.SSLContext:
		"""	Depending on the configuration whether to use TLS, this method creates a new *SSLContext*
			from the configured certificates and returns it. If TLS is disabled then *None* is returned.

			Return:
				SSL / TLD context.
		"""
		context = None
		if useTLS:
			L.isDebug and L.logDebug(f'Certfile: {caCertificateFile}, KeyFile:{caPrivateKeyFile}, TLS version: {tlsVersion}')
			context = ssl.SSLContext(
							{ 	'tls1.1' : ssl.PROTOCOL_TLSv1_1,
								'tls1.2' : ssl.PROTOCOL_TLSv1_2,
								'auto'   : ssl.PROTOCOL_TLS,			# since Python 3.6. Automatically choose the highest protocol version between client & server
							}[tlsVersion.lower()]
						)
			context.load_cert_chain(caCertificateFile, caPrivateKeyFile)
			context.verify_mode = ssl.CERT_REQUIRED if verifyCertificate else ssl.CERT_NONE
		return context
	

	def getSSLContextHttp(self) -> ssl.SSLContext:
		"""	Depending on the configuration whether to use TLS, this method creates a new *SSLContext*
			from the configured certificates and returns it. If TLS is disabled then *None* is returned.

			This method is used for HTTP connections.

			Return:
				SSL / TLD context.
		"""
		L.isDebug and L.logDebug(f'Setup HTTPS SSL context.')
		return self._getContext(Configuration.http_security_useTLS, 
						  		Configuration.http_security_verifyCertificate, 
								Configuration.http_security_tlsVersion, 
								Configuration.http_security_caCertificateFile,
								Configuration.http_security_caPrivateKeyFile)	# type: ignore


	def getSSLContextCoAP(self) -> ssl.SSLContext:
		"""	Depending on the configuration whether to use DTLS, this method creates a new *SSLContext*
			from the configured certificates and returns it. If TLS is disabled then *None* is returned.

			This method is used for CoAP connections.

			Return:
				SSL / TLD context.
		"""
		L.isDebug and L.logDebug(f'Setup CoAP SSL context.')
		return self._getContext(Configuration.coap_security_useDTLS, 
						  		Configuration.coap_security_verifyCertificate, 
								Configuration.coap_security_dtlsVersion, 
								Configuration.coap_security_caCertificateFile,
								Configuration.coap_security_caPrivateKeyFile)	# type: ignore



	def getSSLContextWs(self) -> ssl.SSLContext:
		"""	Depending on the configuration whether to use TLS, this method creates a new *SSLContext*
			from the configured certificates and returns it. If TLS is disabled then *None* is returned.

			This method is used for WebSocket connections.

			Return:
				SSL / TLD context.
		"""
		L.isDebug and L.logDebug(f'Setup WSS SSL context.')
		return self._getContext(Configuration.websocket_security_useTLS,
						  		Configuration.websocket_security_verifyCertificate,
								Configuration.websocket_security_tlsVersion,
								Configuration.websocket_security_caCertificateFile,
								Configuration.websocket_security_caPrivateKeyFile)


	##########################################################################
	#
	#	User authentication
	#

	def validateHttpBasicAuth(self, username:str, password:str) -> bool:
		"""	Validate the provided username and password against the configured HTTP basic authentication file.

			Args:
				username: The username to validate.
				password: The password to validate.

			Return:
				Boolean indicating the result.
		"""
		return self.credentialsManager.httpBasicAuthData.get(username) == hashString(password, Configuration.cse_security_secret)


	def validateHttpTokenAuth(self, token:str) -> bool:
		"""	Validate the provided token against the configured HTTP token authentication file.

			Args:
				token: The token to validate.

			Return:
				Boolean indicating the result.
		"""
		return hashString(token, Configuration.cse_security_secret) in self.credentialsManager.httpTokenAuthData
	

	def validateWSBasicAuth(self, username:str, password:str) -> bool:
		"""	Validate the provided username and password against the configured WebSocket basic authentication file.

			Args:
				username: The username to validate.
				password: The password to validate.

			Return:
				Boolean indicating the result.
		"""
		return self.credentialsManager.wsBasicAuthData.get(username) == hashString(password, Configuration.cse_security_secret)


	def validateWSTokenAuth(self, token:str) -> bool:
		"""	Validate the provided token against the configured WebSocket token authentication file.

			Args:
				token: The token to validate.

			Return:
				Boolean indicating the result.
		"""
		return hashString(token, Configuration.cse_security_secret) in self.credentialsManager.wsTokenAuthData


	def initAuthInformation(self) -> None:
		""" Initialize the authentication information by reading the configured authentication files for HTTP and WebSocket.

			Raises:
				ValueError: If there is an error reading any of the authentication files.
		"""
		L.configUpdate and L.log('reading and initializing authentication information.')
		if self.httpServer:
			L.isDebug and L.logDebug('Initializing HTTP authentication information.')
			self.credentialsManager.readHttpBasicAuthFile()
			self.credentialsManager.readHttpTokenFile()
		if self.websocketServer:
			L.isDebug and L.logDebug('Initializing WebSocket authentication information.')
			self.credentialsManager.readWSBasicAuthFile()
			self.credentialsManager.readWSTokenFile()
		self.allowedCSIOriginators = [ r.cseID for r in Configuration.cse_registrars.values() ]


	# def _readWSBasicAuthFile(self) -> None:
	# 	"""	Read the WebSocket basic authentication file and store the data in a dictionary.
	# 		The authentication information is stored as username:password.

	# 		The data is stored in the `wsBasicAuthData` dictionary.

	# 		Raises:
	# 			ValueError: If there is an error reading the basic authentication file.
	# 	"""
	# 	_newAuthData: dict[str, str] = {}
	# 	# We need to access the configuration directly, since the http server is not yet initialized
	# 	if Configuration.websocket_security_basicAuthFile:
	# 		try:
	# 			with open(Configuration.websocket_security_basicAuthFile, 'r') as f:
	# 				for line in f:
	# 					if line.startswith('#') or len(_l := line.strip()) == 0:
	# 						continue
	# 					(username, password) = _l.split(':')

	# 					# Do not allow duplicate usernames in the basic authentication file
	# 					if username in _newAuthData:
	# 						raise ValueError(f'Duplicate username "{username}" in ws basic authentication file.')

	# 					_newAuthData[username] = password.strip()
	# 		except FileNotFoundError as e:
	# 			if Configuration.websocket_security_enableBasicAuth:
	# 				raise ValueError(L.logErr(f'WebSocket basic authentication file not found: {e}')) from e
	# 			else:
	# 				L.isDebug and L.logDebug(f'WebSocket basic authentication file not found, but basic authentication is disabled: {e}')
	# 		except Exception as e:
	# 			raise ValueError(L.logErr(f'Error reading ws basic authentication file: {e}')) from e

	# 	# only update the wsBasicAuthData if the file was read successfully
	# 	self.wsBasicAuthData = _newAuthData


	# def _readWSTokenAuthFile(self) -> None:
	# 	"""	Read the WebSocket token authentication file and store the data in a dictionary.
	# 		The authentication information is stored as a single token per line.

	# 		The data is stored in the `wsTokenAuthData` list.

	# 		Raises:
	# 			ValueError: If there is an error reading the token authentication file.
	# 	"""
	# 	_newAuthData: list[str] = []
	# 	# We need to access the configuration directly, since the http server is not yet initialized
	# 	if Configuration.websocket_security_tokenAuthFile:
	# 		try:
	# 			with open(Configuration.websocket_security_tokenAuthFile, 'r') as f:
	# 				for line in f:
	# 					if line.startswith('#') or len(_l := line.strip()) == 0:
	# 						continue

	# 					# Do not allow duplicate tokens in the token authentication file
	# 					if _l in _newAuthData:
	# 						raise ValueError(f'Duplicate token "{truncateMiddle(_l)}" in ws token authentication file.')

	# 					_newAuthData.append(_l)

	# 		except FileNotFoundError as e:
	# 			if Configuration.websocket_security_enableTokenAuth:
	# 				raise ValueError(L.logErr(f'WebSocket token authentication file not found: {e}')) from e
	# 			else:
	# 				L.isDebug and L.logDebug(f'WebSocket token authentication file not found, but token authentication is disabled: {e}')
	# 		except Exception as e:
	# 			raise ValueError(L.logErr(f'Error reading ws token authentication file: {e}')) from e

	# 	# only update the wsTokenAuthData if the file was read successfully
	# 	self.wsTokenAuthData = _newAuthData


	def getPOACredentialsForCSEID(self, registrarConfig:CSERegistrar, cseID:Optional[str]=None, binding:Optional[BindingType]=BindingType.HTTP) -> Optional[Tuple[str, str]]:
		"""	Return the credentials for the Point of Access (POA) for the given CSE-ID.
			These credentials are used by the registrar CSE to access this hosting CSE, 
			or by the hosting CSE to access the registrar CSE. The credentials are used
			in the POA attribute. Currently, only HTTP and WS bindings are supported.

			Args:
				registrarConfig: The CSERegistrar configuration to use.
				cseID: The CSE-ID to get the credentials for.
				binding: The binding type to get the credentials for. Default is HTTP.

			Return:
				A tuple with the username and password or token for the given CSE-ID and binding.
			
		"""
		match binding:
			case BindingType.HTTP if cseID == registrarConfig.cseID:
				return registrarConfig.security.selfCredentials.httpUsername, registrarConfig.security.selfCredentials.httpPassword
			case BindingType.HTTP if cseID in (None, Configuration.cse_cseID):
				return registrarConfig.security.credentials.httpUsername, registrarConfig.security.credentials.httpPassword
			case BindingType.WS if cseID == registrarConfig.cseID:
				return registrarConfig.security.selfCredentials.wsUsername, registrarConfig.security.selfCredentials.wsPassword
			case BindingType.WS if cseID in (None, Configuration.cse_cseID):
				return registrarConfig.security.credentials.wsUsername, registrarConfig.security.credentials.wsPassword
		return None, None
		

	##########################################################################
	#
	#	Resource & type cache handling
	#

	def getTypeForRi(self, ri:str) -> Optional[ResourceTypes]:
		"""	Get the resource type for a given resource ID (ri).

			Args:
				ri: The resource ID to get the resource type for.

			Return:
				The resource type for the given resource ID, or None if not found.
		"""

		# Check the cache first
		with self.riTypeCacheLock:
			if ri in self.riTypeCache:
				#print(self.riTypeCache)
				return self.riTypeCache[ri]

		# If not found in the cache, retrieve the resource and get its type
		try:
			resource = self.dispatcher.retrieveResource(ri)
			with self.riTypeCacheLock:
				self.riTypeCache[ri] = resource.ty
			#print(self.riTypeCache)
			return resource.ty
		except ResponseException as e:
			L.isWarn and L.logWarn(f'Could not retrieve resource for ri: {ri}: {e.dbg}')
		
		return ResourceTypes.UNKNOWN
		

	@onEvent(eventManager.deleteResource)
	def onResourceDeleted(self,  eventData: EventData) -> None:
		"""	Handle the deletion of a resource by removing it from the type cache.	"""
		with self.riTypeCacheLock:
			ri = cast(Resource, eventData.payload).ri
			if ri in self.riTypeCache:
				del self.riTypeCache[ri]
