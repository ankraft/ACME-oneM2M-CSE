#
#	SecurityManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This module implements the SecurityManager entity.
"""


from __future__ import annotations
from typing import List, cast, Optional, Any

import ssl

from ..etc.Types import JSON, ResourceTypes, Permission, Result, CSERequest
from ..etc.ResponseStatusCodes import BAD_REQUEST, ORIGINATOR_HAS_NO_PRIVILEGE, NOT_FOUND
from ..etc.Utils import isSPRelative, toCSERelative, getIdFromOriginator
from ..helpers.TextTools import findXPath, simpleMatch
from ..services import CSE
from ..services.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources.PCH import PCH
from ..resources.PCH_PCU import PCH_PCU
from ..resources.ACP import ACP
from ..services.Logging import Logging as L


class SecurityManager(object):
	"""	This manager entity handles access to resources and requests.
	"""

	__slots__ = (
		'enableACPChecks',
		'fullAccessAdmin',
		'useTLSHttp',
		'verifyCertificateHttp',
		'tlsVersionHttp',
		'caCertificateFileHttp',
		'caPrivateKeyFileHttp',
		'useTlsMqtt',
		'verifyCertificateMqtt',
		'caCertificateFileMqtt',
		'usernameMqtt',
		'passwordMqtt',
		'allowedCredentialIDsMqtt',
		'httpBasicAuthFile',
		'httpTokenAuthFile',
		'httpBasicAuthData',
		'httpTokenAuthData'
	)


	def __init__(self) -> None:

		# Get the configuration settings
		self._assignConfig()
		self._readHttpBasicAuthFile()
		self._readHttpTokenAuthFile()

		# Add a handler when the CSE is reset
		CSE.event.addHandler(CSE.event.cseReset, self.restart)	# type: ignore

		# Add handler for configuration updates
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)				# type: ignore

		L.isInfo and L.log('SecurityManager initialized')
		if self.enableACPChecks:
			L.isInfo and L.log('ACP checking ENABLED')
		else:
			L.isInfo and L.log('ACP checking DISABLED')


	def shutdown(self) -> bool:
		L.isInfo and L.log('SecurityManager shut down')
		return True
	

	def restart(self, name:str) -> None:
		"""	Restart the Security manager service.
		"""
		self._assignConfig()
		self._readHttpBasicAuthFile()
		self._readHttpTokenAuthFile()
		L.logDebug('SecurityManager restarted')


	def _assignConfig(self) -> None:
		"""	Assign configurations.
		"""

		self.enableACPChecks 			= Configuration.get('cse.security.enableACPChecks')
		self.fullAccessAdmin			= Configuration.get('cse.security.fullAccessAdmin')

		# TLS configurations (http)
		self.useTLSHttp 				= Configuration.get('http.security.useTLS')
		self.verifyCertificateHttp		= Configuration.get('http.security.verifyCertificate')
		self.tlsVersionHttp				= Configuration.get('http.security.tlsVersion').lower()
		self.caCertificateFileHttp		= Configuration.get('http.security.caCertificateFile')
		self.caPrivateKeyFileHttp		= Configuration.get('http.security.caPrivateKeyFile')

		# TLS and other configuration (mqtt)
		self.useTlsMqtt 				= Configuration.get('mqtt.security.useTLS')
		self.verifyCertificateMqtt		= Configuration.get('mqtt.security.verifyCertificate')
		self.caCertificateFileMqtt		= Configuration.get('mqtt.security.caCertificateFile')
		self.usernameMqtt				= Configuration.get('mqtt.security.username')
		self.passwordMqtt				= Configuration.get('mqtt.security.password')
		self.allowedCredentialIDsMqtt	= Configuration.get('mqtt.security.allowedCredentialIDs')

		# HTTP authentication
		self.httpBasicAuthFile			= Configuration.get('http.security.basicAuthFile')
		self.httpTokenAuthFile			= Configuration.get('http.security.tokenAuthFile')



	def configUpdate(self, name:str, 
						   key:Optional[str] = None,
						   value:Any = None) -> None:
		"""	Handle configuration updates.

			Args:
				name: The name of the configuration section.
				key: The key of the configuration value.
				value: The new value of the configuration value.
		"""
		if key not in ( 'cse.security.enableACPChecks', 
						'cse.security.fullAccessAdmin',
						'http.security.useTLS',
						'http.security.verifyCertificate',
						'http.security.tlsVersion',
						'http.security.caCertificateFile',
						'http.security.caPrivateKeyFile',
						'mqtt.security.useTLS',
						'mqtt.security.verifyCertificate',
						'mqtt.security.caCertificateFile',
						'mqtt.security.username',
						'mqtt.security.password',
						'mqtt.security.allowedCredentialIDs',
						'http.security.basicAuthFile'
					  ):
			return
		self._assignConfig()
		self._readHttpBasicAuthFile()
		self._readHttpTokenAuthFile()


	###############################################################################################


	def hasAccess(self, originator:str, 
						resource:Resource, 
						requestedPermission:Permission, 
						ty:Optional[ResourceTypes] = None, 
						parentResource:Optional[Resource] = None) -> bool:
		""" Test whether an originator has access to a resource for the requested permission.
		
			Args:
				originator: The originator to check for.
				resource: The target resource of a request.
				requestedPermission: The persmission to test.
				ty: Mandatory for CREATE, else optional. The type of the resoure that is about to be created.
				parentResource: Optional, the parent resource of a target resource.
			Return:
				Boolean indicating access.
		"""

		#  Do or ignore the check
		if not self.enableACPChecks:
			return True
		# L.logWarn(ty)
		
		# grant full access to the CSE originator
		if originator is None or originator == CSE.cseOriginator or originator.endswith(f'/{CSE.cseOriginator}') and self.fullAccessAdmin:
			L.isDebug and L.logDebug('Request from CSE Originator. OK.')
			return True
		
		# Remove CSE-ID if this is the same CSE
		if isSPRelative(originator) and originator.startswith(CSE.cseCsiSlash):
			L.isDebug and L.logDebug(f'Originator: {originator} is registered to same CSE. Converting to CSE-Relative format.')
			originator = toCSERelative(originator)
			L.isDebug and L.logDebug(f'Converted originator: {originator}')
	
		if ty is not None:	# ty is an int
			# Some Separate	 tests for some types

			# Checking for AE	
			if ty == ResourceTypes.AE and requestedPermission == Permission.CREATE:
				# originator may be None or empty or C or S. 
				# That is okay if type is AE and this is a create request
				# Originator == None or len == 0
				if not originator or self.isAllowedOriginator(originator, CSE.registration.allowedAEOriginators):
					L.isDebug and L.logDebug('Originator for AE CREATE. OK.')
					return True

			# Checking for remoteCSE or CSEBaseAnnc
			if ty in [ ResourceTypes.CSR, ResourceTypes.CSEBaseAnnc] and requestedPermission == Permission.CREATE:
				if self.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators):
					L.isDebug and L.logDebug('Originator for CSR/CSEBaseAnnc CREATE. OK.')
					return True
				else:
					L.isWarn and L.logWarn(f'Originator for CSR/CSEBaseAnnc registration not found. Add "{getIdFromOriginator(originator)}" to the configuration [cse.registration].allowedCSROriginators in the CSE\'s ini file to allow access for this originator.')
					return False

			if ty.isAnnounced():
				if self.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators) or (parentResource and originator[1:] == parentResource.ri):
					L.isDebug and L.logDebug('Originator for Announcement. OK.')
					return True
				else:
					L.isWarn and L.logWarn('Originator for Announcement not found.')
					return False
		
		# Check for resource == None
		if not resource:
			L.logErr('Resource must not be None')
			return False

		# Allow originator for announced resource
		if resource.isAnnounced():
			if self.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators) and resource.lnk.startswith(f'{originator}/'):
				L.isDebug and L.logDebug('Announcement originator. OK.')
				return True
		
		# Allow originator if resource is announced to the originator and the request is UPDATE
		if (at := resource.at) is not None and requestedPermission == Permission.UPDATE:
			ot = f'{originator}/'
			if any(each.startswith(ot) for each in at):
				L.isDebug and L.logDebug('Announcement target originator. OK.')
				return True

		# Allow some Originators to RETRIEVE the CSEBase
		if resource.ty == ResourceTypes.CSEBase and requestedPermission & Permission.RETRIEVE:

			# Allow registered AEs to RETRIEVE the CSEBase
			try:
				if CSE.storage.retrieveResource(aei = originator):
					L.isDebug and L.logDebug(f'Allow registered AE Orignator {originator} to RETRIEVE CSEBase. OK.')
					return True
			except NOT_FOUND:
				pass # NOT Found is expected
			
			# Allow remote CSE to RETRIEVE the CSEBase

			if originator == CSE.remote.registrarCSI:
				L.isDebug and L.logDebug(f'Allow registrar CSE Originnator {originator} to RETRIEVE CSEBase. OK.')
				return True
			if self.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators):
				L.isDebug and L.logDebug(f'Allow remote CSE Orignator {originator} to RETRIEVE CSEBase. OK.')
				return True

		# Checking for PollingChannel
		if resource.ty == ResourceTypes.PCH:
			if originator != resource.getParentOriginator():
				L.isWarn and L.logWarn('Access to <PCH> resource is only granted to the parent originator.')
				return False
			return True

		# Check parameters
		if not requestedPermission or not (0 <= requestedPermission <= Permission.ALL):
			L.isWarn and L.logWarn('RequestedPermission must not be None, and between 0 and 63')
			return False

		L.isDebug and L.logDebug(f'Permission check originator: {originator} ri: {resource.ri} permission: {requestedPermission}')
		# L.logWarn(resource)

		if resource.ty == ResourceTypes.GRP: # target is a group resource
			# Check membersAccessControlPolicyIDs if provided, otherwise accessControlPolicyIDs to be used
			
			if not (macp := resource.macp):
				L.isDebug and L.logDebug("MembersAccessControlPolicyIDs not provided, using AccessControlPolicyIDs")
				# FALLTHROUGH to the permission checks below
			
			else: # handle the permission checks here
				for a in macp:
					if not (acp := CSE.dispatcher.retrieveResource(a)):
						L.isDebug and L.logDebug(f'ACP resource not found: {a}')
						continue
					else:
						if acp.checkPermission(originator, requestedPermission, ty):
							L.isDebug and L.logDebug('Permission granted')
							return True
				L.isDebug and L.logDebug('Permission NOT granted')
				return False


		# target is an ACP or ACPAnnc resource
		if resource.ty in [ResourceTypes.ACP, ResourceTypes.ACPAnnc]:	
			if resource.checkSelfPermission(originator, requestedPermission):
				L.isDebug and L.logDebug('Permission granted')
				return True
			# fall-through
			return False

		# If subscription, check whether originator has retrieve permissions on the subscribed-to resource (parent)	
		if ty == ResourceTypes.SUB and parentResource:
			if self.hasAccess(originator, parentResource, Permission.RETRIEVE) == False:
				return False

		if requestedPermission == Permission.NOTIFY and originator == CSE.cseCsi:
			L.isDebug and L.logDebug(f'NOTIFY permission granted for CSE: {originator}')
			return True

		#
		# target is any other resource type
		#
		
		# When no acpi is configured for the resource
		if not (acpi := resource.acpi):
			L.isDebug and L.logDebug('Handle with missing acpi in resource')

			# if the resource *may* have an acpi
			if resource._attributes and 'acpi' in resource._attributes:

				# Check custodian attribute
				if custodian := resource.cstn:
					if custodian == originator:	# resource.custodian == originator -> all access
						L.isDebug and L.logDebug(f'Allow access for custodian: {custodian}')
						return True
					# When custodian is set, but doesn't match the originator then fall-through to fail
					L.isDebug and L.logDebug(f'Resource creator: {custodian} != originator: {originator}')
					
				# Check resource creator
				else:
					if (creator := resource.getOriginator()) == originator:
						L.isDebug and L.logDebug('Allow access for creator')
						return True
					# if originator is not the original resource creator
					L.isDebug and L.logDebug(f'Resource creator: {creator} != originator: {originator}')
				
				# Fall-through to fail

			# resource doesn't support acpi attribute
			else:
				if resource.inheritACP:
					L.isDebug and L.logDebug('Checking parent\'s permission')
					if not parentResource:
						parentResource = CSE.dispatcher.retrieveResource(resource.pi)
					return self.hasAccess(originator, parentResource, requestedPermission, ty)

			L.isDebug and L.logDebug('Permission NOT granted for resource w/o acpi')
			return False

		# Finally check the acpi
		for a in acpi:
			if not (acp := CSE.dispatcher.retrieveResource(a)):
				L.isDebug and L.logDebug(f'ACP resource not found: {a}')
				continue
			# if checkSelf:	# forced check for self permissions
			# 	if acp.checkSelfPermission(originator, requestedPermission):
			# 		L.isDebug and L.logDebug('Permission granted')
			# 		return True				
			# else:
			# 	# L.isWarn and L.logWarn(acp)
			# 	if acp.checkPermission(originator, requestedPermission, ty):
			# 		L.isDebug and L.logDebug('Permission granted')
			# 		return True

			# L.isWarn and L.logWarn(acp)
			if acp.checkPermission(originator, requestedPermission, ty):
				L.isDebug and L.logDebug('Permission granted')
				return True

		# no fitting permission identified
		L.isDebug and L.logDebug('Permission NOT granted')
		return False


	def checkAcpiUpdatePermission(self, request:CSERequest, targetResource:Resource, originator:str) -> bool:
		"""	Check whether this is actually a correct update of the acpi attribute, and whether this is actually allowed.

			Args:
				request: The original request.
				targetResource: The request target.
				originator: The request originator.
			
			Return:
				Boolean value. *True* indicates that this is an ACPI update. *False* indicates that this NOT an ACPI update.
			
			Raises
				`BAD_REQUEST`: If the *acpi* attribute is not the only attribute in an UPDATE request.
				`ORIGINATOR_HAS_NO_PRIVILEGE`: If the originator has no access.
		"""
		updatedAttributes = findXPath(request.pc, '{*}')

		# Check that acpi, if present, is the only attribute
		if 'acpi' in updatedAttributes:
			if len(updatedAttributes) > 1:
				raise BAD_REQUEST(L.logDebug('"acpi" must be the only attribute in update'))
			
			# Check whether the originator has UPDATE privileges for the acpi attribute (pvs!)
			if not targetResource.acpi:
				if originator != targetResource.getOriginator():
					raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'No access to update acpi for originator: {originator}'))
				else:
					pass	# allowed for creating originator
			else:
				# test the current acpi whether the originator is allowed to update the acpi
				for ri in targetResource.acpi:
					if not (acp := CSE.dispatcher.retrieveResource(ri)):
						L.isWarn and L.logWarn(f'Access Check for acpi: referenced <ACP> resource not found: {ri}')
						continue
					if acp.checkSelfPermission(originator, Permission.UPDATE):
						break
				else:
					raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator: {originator} has no permission to update acpi for: {targetResource.ri}'))

			return True # True indicates that this is an ACPI update
		return False	# False indicates that this NOT an ACPI update


	def isAllowedOriginator(self, originator:str, allowedOriginators:List[str]) -> bool:
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

		_originator = getIdFromOriginator(originator)
		L.isDebug and L.logDebug(f'Originator: {_originator} - allowed originators: {allowedOriginators}')
		
		# Always allow for the hosting CSE
		if originator in [CSE.cseCsi, CSE.cseSPRelative] :
			return True

		for ao in allowedOriginators:
			if simpleMatch(_originator, ao):
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


	def getRelevantACPforOriginator(self, originator:str, permission:Permission) -> list[ACP]:
		"""	Return a list of relevant <ACP> resources that currently are relevant for an originator.
			This list includes <ACP> resources with permissions for the originator, or for "all" originators.

			Args:
				originator: ID of the originator.
				permission: The operation permission to filter for.

			Return:
				List of <ACP> resources. This list might be empty.
		"""
		origs = [ originator, 'all' ]

		def filter(doc:JSON) -> bool:
			if (acr := findXPath(doc, 'pv/acr')):
				for each in acr:
					if (acop := each.get('acop')) is None or acop & permission == 0:
						continue
					if (acor := each.get('acor')) is None or not any(x in acor for x in origs):
						continue
					return True
			return False

		return cast(List[ACP], CSE.storage.searchByFragment(dct = { 'ty' : ResourceTypes.ACP }, filter = filter))


	##########################################################################
	#
	#	Certificate handling
	#

	def getSSLContext(self) -> ssl.SSLContext:
		"""	Depending on the configuration whether to use TLS, this method creates a new *SSLContext*
			from the configured certificates and returns it. If TLS is disabled then *None* is returned.

			Return:
				SSL / TLD context.
		"""
		context = None
		if self.useTLSHttp:
			L.isDebug and L.logDebug(f'Setup SSL context. Certfile: {self.caCertificateFileHttp}, KeyFile:{self.caPrivateKeyFileHttp}, TLS version: {self.tlsVersionHttp}')
			context = ssl.SSLContext(
							{ 	'tls1.1' : ssl.PROTOCOL_TLSv1_1,
								'tls1.2' : ssl.PROTOCOL_TLSv1_2,
								'auto'   : ssl.PROTOCOL_TLS,			# since Python 3.6. Automatically choose the highest protocol version between client & server
							}[self.tlsVersionHttp.lower()]
						)
			context.load_cert_chain(self.caCertificateFileHttp, self.caPrivateKeyFileHttp)
		return context


	##########################################################################
	#
	#	User authentication
	#

	def validateHttpBasicAuth(self, username:str, password:str) -> bool:
		"""	Validate the provided username and password against the configured basic authentication file.

			Args:
				username: The username to validate.
				password: The password to validate.

			Return:
				Boolean indicating the result.
		"""
		return self.httpBasicAuthData.get(username) == password


	def validateHttpTokenAuth(self, token:str) -> bool:
		"""	Validate the provided token against the configured token authentication file.

			Args:
				token: The token to validate.

			Return:
				Boolean indicating the result.
		"""
		return token in self.httpTokenAuthData


	def _readHttpBasicAuthFile(self) -> None:
		"""	Read the HTTP basic authentication file and store the data in a dictionary.
			The authentication information is stored as username:password.

			The data is stored in the `httpBasicAuthData` dictionary.
		"""
		self.httpBasicAuthData = {}
		# We need to access the configuration directly, since the http server is not yet initialized
		if Configuration.get('http.security.enableBasicAuth') and self.httpBasicAuthFile:
			try:
				with open(self.httpBasicAuthFile, 'r') as f:
					for line in f:
						if line.startswith('#'):
							continue
						if len(line.strip()) == 0:
							continue
						(username, password) = line.strip().split(':')
						self.httpBasicAuthData[username] = password.strip()
			except Exception as e:
				L.logErr(f'Error reading basic authentication file: {e}')


	def _readHttpTokenAuthFile(self) -> None:
		"""	Read the HTTP token authentication file and store the data in a dictionary.
			The authentication information is stored as a single token per line.

			The data is stored in the `httpTokenAuthData` list.
		"""
		self.httpTokenAuthData = []
		# We need to access the configuration directly, since the http server is not yet initialized
		if Configuration.get('http.security.enableTokenAuth') and self.httpTokenAuthFile:
			try:
				with open(self.httpTokenAuthFile, 'r') as f:
					for line in f:
						if line.startswith('#'):
							continue
						if len(line.strip()) == 0:
							continue
						self.httpTokenAuthData.append(line.strip())
			except Exception as e:
				L.logErr(f'Error reading token authentication file: {e}')


	# def getSSLContextMqtt(self) -> ssl.SSLContext:
	# 	"""	Depending on the configuration whether to use TLS for MQTT, this method creates a new `SSLContext`
	# 		from the configured certificates and returns it. If TLS for MQTT is disabled then `None` is returned.
	# 	"""
	# 	context = None
	# 	if self.useMqttTLS:
	# 		L.isDebug and L.logDebug(f'Setup SSL context for MQTT. Certfile: {self.caCertificateFile}, KeyFile:{self.caPrivateKeyFile}, TLS version: {self.tlsVersion}')
	# 		context = ssl.SSLContext(
	# 						{ 	'tls1.1' : ssl.PROTOCOL_TLSv1_1,
	# 							'tls1.2' : ssl.PROTOCOL_TLSv1_2,
	# 							'auto'   : ssl.PROTOCOL_TLS,			# since Python 3.6. Automatically choose the highest protocol version between client & server
	# 						}[self.tlsVersionMqtt.lower()]
	# 					)
	# 		if self.caCertificateFileMqtt:
	# 			#context.load_cert_chain(self.caCertificateFileMqtt, self.caPrivateKeyFileMqtt)
	# 			#print(self.caCertificateFileMqtt)
	# 			context.load_verify_locations(cafile=self.caCertificateFileMqtt)
	# 			#context.load_cert_chain(certfile=self.caCertificateFileMqtt)
	# 		context.verify_mode = ssl.CERT_REQUIRED if self.verifyCertificateMqtt else ssl.CERT_NONE
	# 	return context
