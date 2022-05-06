#
#	SecurityManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This entity handles access to resources
#


from __future__ import annotations
import ssl
from typing import List

from ..etc.Types import ResourceTypes as T, Permission, Result, CSERequest, ResponseStatusCode as RC
from ..etc import Utils as Utils
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..services.Configuration import Configuration
from ..resources.Resource import Resource
from ..resources.PCH import PCH
from ..resources.PCH_PCU import PCH_PCU
from ..helpers import TextTools


class SecurityManager(object):

	def __init__(self) -> None:
		self.enableACPChecks 			= Configuration.get('cse.security.enableACPChecks')
		self.fullAccessAdmin			= Configuration.get('cse.security.fullAccessAdmin')

		L.isInfo and L.log('SecurityManager initialized')
		if self.enableACPChecks:
			L.isInfo and L.log('ACP checking ENABLED')
		else:
			L.isInfo and L.log('ACP checking DISABLED')
		
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
		


	def shutdown(self) -> bool:
		L.isInfo and L.log('SecurityManager shut down')
		return True


	def hasAccess(self, originator:str, 
						resource:Resource, 
						requestedPermission:Permission, 
						ty:T = None, 
						parentResource:Resource = None) -> bool:
		""" Test whether an originator has access to a resource for the requested permission.
		
			Args:
				originator: The originator to check for.
				resource: The target resource of a request.
				requestedPermission: The persmission to test.
				ty: Mandatory for CREATE, else mandatory. The type of the resoure that is about to be created.
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
	
		if ty is not None:	# ty is an int
			# Some Separate	 tests for some types

			# Checking for AE	
			if ty == T.AE and requestedPermission == Permission.CREATE:
				# originator may be None or empty or C or S. 
				# That is okay if type is AE and this is a create request
				# Originator == None or len == 0
				if not originator or self.isAllowedOriginator(originator, CSE.registration.allowedAEOriginators):
					L.isDebug and L.logDebug('Originator for AE CREATE. OK.')
					return True

			# Checking for remoteCSE or CSEBaseAnnc
			if ty in [ T.CSR, T.CSEBaseAnnc] and requestedPermission == Permission.CREATE:
				if self.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators):
					L.isDebug and L.logDebug('Originator for CSR/CSEBaseAnnc CREATE. OK.')
					return True
				else:
					L.isWarn and L.logWarn(f'Originator for CSR/CSEBaseAnnc registration not found. Add "{originator}" to the configuration [cse.registration].allowedCSROriginators in the CSE\'s ini file to allow access for this originator.')
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
		if resource.ty == T.CSEBase and requestedPermission & Permission.RETRIEVE:

			# Allow registered AEs to RETRIEVE the CSEBase
			if CSE.storage.retrieveResource(aei = originator).resource:
				L.isDebug and L.logDebug(f'Allow registered AE Orignator {originator} to RETRIEVE CSEBase. OK.')
				return True
			
			# Allow remote CSE to RETRIEVE the CSEBase

			if originator == CSE.remote.registrarCSI:
				L.isDebug and L.logDebug(f'Allow registrar CSE Originnator {originator} to RETRIEVE CSEBase. OK.')
				return True
			if self.isAllowedOriginator(originator, CSE.registration.allowedCSROriginators):
				L.isDebug and L.logDebug(f'Allow remote CSE Orignator {originator} to RETRIEVE CSEBase. OK.')
				return True

		# Checking for PollingChannel
		if resource.ty == T.PCH:
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

		if resource.ty == T.GRP: # target is a group resource
			# Check membersAccessControlPolicyIDs if provided, otherwise accessControlPolicyIDs to be used
			
			if not (macp := resource.macp):
				L.isDebug and L.logDebug("MembersAccessControlPolicyIDs not provided, using AccessControlPolicyIDs")
				# FALLTHROUGH to the permission checks below
			
			else: # handle the permission checks here
				for a in macp:
					if not (acp := CSE.dispatcher.retrieveResource(a).resource):
						L.isDebug and L.logDebug(f'ACP resource not found: {a}')
						continue
					else:
						if acp.checkPermission(originator, requestedPermission, ty):
							L.isDebug and L.logDebug('Permission granted')
							return True
				L.isDebug and L.logDebug('Permission NOT granted')
				return False


		# target is an ACP or ACPAnnc resource
		if resource.ty in [T.ACP, T.ACPAnnc]:	
			if resource.checkSelfPermission(originator, requestedPermission):
				L.isDebug and L.logDebug('Permission granted')
				return True
			# fall-through
			return False

		# If subscription, check whether originator has retrieve permissions on the subscribed-to resource (parent)	
		if ty == T.SUB and parentResource:
			if self.hasAccess(originator, parentResource, Permission.RETRIEVE) == False:
				return False

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
						L.isDebug and L.logDebug('Allow access for custodian')
						return True
					# When custodiabn is set, but doesn't match the originator then fall-through to fail
					
				# Check resource creator
				elif (creator := resource.getOriginator()) and creator == originator:
					L.isDebug and L.logDebug('Allow access for creator')
					return True
				
				# Fall-through to fail

			# resource doesn't support acpi attribute
			else:
				if resource.inheritACP:
					L.isDebug and L.logDebug('Checking parent\'s permission')
					if not parentResource:
						parentResource = CSE.dispatcher.retrieveResource(resource.pi).resource
					return self.hasAccess(originator, parentResource, requestedPermission, ty)

			L.isDebug and L.logDebug('Permission NOT granted for resource w/o acpi')
			return False

		# Finally check the acpi
		for a in acpi:
			if not (acp := CSE.dispatcher.retrieveResource(a).resource):
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


	def hasAcpiUpdatePermission(self, request:CSERequest, targetResource:Resource, originator:str) -> Result:
		"""	Check whether this is actually a correct update of the acpi attribute, and whether this is actually allowed.
		"""
		updatedAttributes = Utils.findXPath(request.pc, '{0}')

		# Check that acpi, if present, is the only attribute
		if 'acpi' in updatedAttributes:
			if len(updatedAttributes) > 1:
				L.logDebug(dbg := '"acpi" must be the only attribute in update')
				return Result.errorResult(dbg = dbg)
			
			# Check whether the originator has UPDATE privileges for the acpi attribute (pvs!)
			if not targetResource.acpi:
				if originator != targetResource.getOriginator():
					L.logDebug(dbg := f'No access to update acpi for originator: {originator}')
					return Result.errorResult(rsc = RC.originatorHasNoPrivilege, dbg = dbg)
				else:
					pass	# allowed for creating originator
			else:
				# test the current acpi whether the originator is allowed to update the acpi
				for ri in targetResource.acpi:
					if not (acp := CSE.dispatcher.retrieveResource(ri).resource):
						L.isWarn and L.logWarn(f'Access Check for acpi: referenced <ACP> resource not found: {ri}')
						continue
					if acp.checkSelfPermission(originator, Permission.UPDATE):
						break
				else:
					L.logDebug(dbg := f'Originator: {originator} has no permission to update acpi for: {targetResource.ri}')
					return Result.errorResult(rsc = RC.originatorHasNoPrivilege, dbg = dbg)

			return Result(status = True, data = True)	# hack: data=True indicates that this is an ACPI update after all

		return Result.successResult()


	def isAllowedOriginator(self, originator:str, allowedOriginators:List[str]) -> bool:
		""" Check whether an Originator is in the provided list of allowed 
			originators. This list may contain regex.
		"""
		if L.isDebug: L.logDebug(f'Originator: {originator}')
		if L.isDebug: L.logDebug(f'Allowed originators: {allowedOriginators}')

		if not originator or not allowedOriginators:
			return False
		_id = Utils.getIdFromOriginator(originator)
		if L.isDebug: L.logDebug(f'ID: {_id}')

		for ao in allowedOriginators:
			if TextTools.simpleMatch(_id, ao):
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



	##########################################################################
	#
	#	Certificate handling
	#

	def getSSLContext(self) -> ssl.SSLContext:
		"""	Depending on the configuration whether to use TLS, this method creates a new `SSLContext`
			from the configured certificates and returns it. If TLS is disabled then `None` is returned.
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
