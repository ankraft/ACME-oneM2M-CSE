#
#	DASManager.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

from __future__ import annotations
from typing import Generator, cast, TYPE_CHECKING, Optional

from acmecse.runtime.PluginSupport import plugin, start, stop, restart, requires
from acmecse.runtime.Logging import Logging as L
from acmecse.etc.Constants import RuntimeConstants as RC
from acmecse.etc.Types import ResourceTypes, CSERequest, RequestResponseList, JSON
from acmecse.etc.ResponseStatusCodes import ResponseException, ORIGINATOR_HAS_NO_PRIVILEGE, ResponseStatusCode as RSC
from acmecse.etc.JSONUtils import removeNoneAttributes
from acmecse.resources.Resource import Resource
from acmecse.services.NotificationManager import NotificationManager
from acmecse.services.Dispatcher import Dispatcher


@plugin(property='dasManager', tags=['acme', 'core'])
@requires(dispatcher='acmecse.services.Dispatcher')
@requires(notification='acmecse.services.NotificationManager')
class DASManager(object):

	dispatcher:Dispatcher = None
	""" Injected Dispatcher instance. """

	notification:NotificationManager = None
	""" Injected NotificationManager instance. """

	@start
	def start(self) -> None:
		"""	Initialize the DASManager.
		"""
		L.isInfo and L.log('DASManager initialized')


	@stop
	def stop(self) -> bool:
		"""	Shutdown the DASManager.
		
			Return:
				Boolean, always True.
		"""
		L.isInfo and L.log('DASManager shut down')
		return True


	@restart
	def restart(self) -> None:
		"""	Restart the DASManager services.
		"""
		L.isDebug and L.logDebug('DASManager restarted')


	#########################################################################

	def checkDACIinResource(self, resource: Resource, originator: str, request: Optional[CSERequest] = None) -> bool:

		daci:list[str] = []

		# Traverse up to find a daci
		while True:
			if resource.daci:
				daci = resource.daci
				break
			if resource.ty == ResourceTypes.CSEBase: # don't go beyond CSEBase
				break
			resource = resource.retrieveParentResource()

		if daci:
			L.isDebug and L.logDebug(f'Found daci in resource hierarchy: {resource.ri} : {daci}')

			for daciRi in daci:
				try:
					daciResource = self.dispatcher.retrieveResource(daciRi)
				except ResponseException as e:
					L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource not found: {daciRi}: {e.dbg}')
					raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource not found: {daciRi}') from e

				# Dynamic auth for the resource enabled?
				if not daciResource.dae:
					L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> is disabled: {daciRi}')
					# TODO This needs perhaps to be changed. What if multiple DACs are listed in the daci
					raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> is disabled: {daciRi}')

				if dap := daciResource.dap:

					# EXPERIMENTAL: Traverse over the resource IDs (to AEs) and then the PoAs in those AEs to get the DAS URL
					for id in dap:
						try:
							aeResource = self.dispatcher.retrieveResource(id)
						except ResponseException as e:
							L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource\'s dap contains non-existing resource: {id}: {e.dbg}')
							raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource\'s dap contains non-existing resource: {id}') from e
						if aeResource.ty != ResourceTypes.AE:
							L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource\'s dap contains non-AE resource: {id}. Ignoring.')
							raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource\'s dap contains non-AE resource: {id}')
						if not aeResource.poa:
							L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource\'s dap contains AE resource without PoA: {id}. Ignoring.')
							raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource\'s dap contains AE resource without PoA: {id}')

						# Finally after the checks, consult the DAS 
						if self.consultDAS(aeResource, resource, originator, daciResource.dal, request):
							return True

				
				# TODO do something with the lifetime

		return False


	def getDACIforResource(self, resource: Resource) -> list[str]:
		""" Get the list of DACI resource IDs for a given resource. If no DACI is found for a resource,
			the parent resources are also considered until a DACI is found or the CSEBase is reached.

			Args:
				resource: The resource to get the DACI resource IDs for.

			Return:
				A list of DACI resource IDs, or an empty list if no DACI is found in the resource's hierarchy.
		"""
		daci:list[str] = []

		# Traverse up to find a daci
		while True:
			if resource.daci:
				daci = resource.daci
				break
			if resource.ty == ResourceTypes.CSEBase: # don't go beyond CSEBase
				break
			resource = resource.retrieveParentResource()	# move up to the parent resource

		return daci


	# The following method is a generator function that yields the access control policy rules (ACTRs) for
	# a given resource and originator by consulting the DAS
	def retrieveACTRfromDAS(self, daciRi: str, 
	                        	  resource: Resource, 
								  originator: str, 
								  request: Optional[CSERequest] = None) -> Generator[dict, None, None]:


		try:
			daciResource = self.dispatcher.retrieveResource(daciRi)
		except ResponseException as e:
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource not found: {daciRi}: {e.dbg}')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource not found: {daciRi}') from e

		# Dynamic auth for the resource enabled?
		if not daciResource.dae:
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> is disabled: {daciRi}')
			# TODO This needs perhaps to be changed. What if multiple DACs are listed in the daci
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> is disabled: {daciRi}')

		if dap := daciResource.dap:

			# EXPERIMENTAL: Traverse over the resource IDs (to AEs) and then the PoAs in those AEs to get the DAS URL
			for id in dap:
				try:
					aeResource = self.dispatcher.retrieveResource(id)
				except ResponseException as e:
					L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource\'s dap contains non-existing resource: {id}: {e.dbg}')
					raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource\'s dap contains non-existing resource: {id}') from e
				if aeResource.ty != ResourceTypes.AE:
					L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource\'s dap contains non-AE resource: {id}. Ignoring.')
					raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource\'s dap contains non-AE resource: {id}')
				if not aeResource.poa:
					L.isWarn and L.logWarn(f'Dynamic Authorization Check: referenced <DAC> resource\'s dap contains AE resource without PoA: {id}. Ignoring.')
					raise ORIGINATOR_HAS_NO_PRIVILEGE(f'Referenced <DAC> resource\'s dap contains AE resource without PoA: {id}')

				# Finally after the checks, consult the DAS 
				yield from self.getACTRfromDAS(aeResource, resource, originator, daciResource.dal, request)
				
				# TODO do something with the lifetime

		return


	def getACTRfromDAS(self, ae: Resource, 
							 resource: Resource, 
							 originator: str, 
							 proposedLifetime: Optional[str] = None,
							 request: Optional[CSERequest] = None) -> list[JSON]:
		"""	Consult the DAS for the given originator and resource at the specified URI.

			Args:
				ae: The AE resource representing the DAS.
				resource: The resource to check.
				originator: The originator to check.
				proposedLifetime: The proposed lifetime for the granted privileges. This is optional, but can be used to provide additional information to the DAS.
				request: The original request to check. This is optional, but can be used to provide additional information to the DAS.

			Returns:
		"""
		L.isDebug and L.logDebug(f'Dynamic Authorization Check: invoking DAS at {ae.ri} for originator: {originator} on resource: {resource.ri}')

		# TODO support this in a more generic way, e.g. create a data type for the request and response
		notification = {
			'm2m:seci' : {
				'sit' : 1,		# Dynamic Authorization Request
				'dreq' : {		# dasRequest
					'org' : originator,
					'trt': resource.ty if resource else None,
					'op' : request.op.value if request else None,

					# TODO support ipv4 and ipv6 in the request
					# 'oip': {
					# 	'ipv4': request.ipv4 if request else None,
					# 	'ipv6': request.ipv6 if request else None,
					# }
					
					# TODO support the originatorLocation in the request
					#'olo': request.olo if request else None,

					# TODO support the originatorRoleID in the request
					#'orid': resource.orig if resource else None,

					'rts': resource.ot if resource else None,
					# EXPERIMENTAL: use the structured format of the resourceID
					'trid': resource.getSrn() if resource else None,
					'ppl': proposedLifetime,

					# TODO Later suport the following attributes 
					# NOTE For a description of the roleIDsFromACPs attribute see TS-0003, 7.3.2.2, step 2.2
					# roleIDsFromACPs
					# tokenIDs
					# authorSignIndicator


				}
			}
		}
		# TODO continue with 6.3.5.46-1
		response = self.notification.sendNotificationWithDict(removeNoneAttributes(notification), ae.ri, originator=RC.cseCsi)

		# Some basic checks on the response
		if len(response) != 1:
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: DAS at {ae.ri} returned unexpected number of responses: {len(response)}')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'DAS at {ae.ri} returned unexpected number of responses: {len(response)}')
		if (rsc := response[0].result.rsc) != RSC.OK:
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: DAS at {ae.ri} returned unexpected response with rsc={rsc}')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'DAS at {ae.ri} returned unexpected response with rsc={rsc}')
		if not (seci := response[0].result.data.get('m2m:seci')): # type: ignore[union-attr]
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: DAS at {ae.ri} returned unexpected response without "m2m:seci"')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'DAS at {ae.ri} returned unexpected response without "m2m:seci"')
		if seci.get('sit') != 2:
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: DAS at {ae.ri} returned unexpected response with sit={seci.get("sit")}, expected sit=2')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'DAS at {ae.ri} returned unexpected response with sit={seci.get("sit")}, expected sit=2')
		if not (dai := seci.get('dai')):
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: DAS at {ae.ri} returned unexpected response without "dai"')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'DAS at {ae.ri} returned unexpected response without "dai"')
		if not (gp := dai.get('gp')):
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: DAS at {ae.ri} returned unexpected response without "gp"')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'DAS at {ae.ri} returned unexpected response without "gp"')
		if not isinstance(gp, list):
			L.isWarn and L.logWarn(f'Dynamic Authorization Check: DAS at {ae.ri} returned unexpected response with "gp" not being a list')
			raise ORIGINATOR_HAS_NO_PRIVILEGE(f'DAS at {ae.ri} returned unexpected response with "gp" not being a list')
		
		
		L.inspect(gp)
		return gp



	def consultDAS(self, ae: Resource, 
	               		 resource: Resource, 
						 originator: str, 
						 proposedLifetime: Optional[str] = None,
						 request: Optional[CSERequest] = None) -> bool:
		"""	Consult the DAS for the given originator and resource at the specified URI.

			Args:
				ae: The AE resource representing the DAS.
				resource: The resource to check.
				originator: The originator to check.
				proposedLifetime: The proposed lifetime for the granted privileges. This is optional, but can be used to provide additional information to the DAS.
				request: The original request to check. This is optional, but can be used to provide additional information to the DAS.

			Returns:
				Boolean, True if access is granted by the DAS, False otherwise.
		"""
		L.isDebug and L.logDebug(f'Dynamic Authorization Check: invoking DAS at {ae.ri} for originator: {originator} on resource: {resource.ri}')

		# TODO support this in a more generic way, e.g. create a data type for the request and response
		notification = {
			'm2m:seci' : {
				'sit' : 1,		# Dynamic Authorization Request
				'dreq' : {		# dasRequest
					'org' : originator,
					'trt': resource.ty if resource else None,
					'op' : request.op if request else None,
					# TODO support ipv4 and ipv6 in the request
					# 'oip': {
					# 	'ipv4': request.ipv4 if request else None,
					# 	'ipv6': request.ipv6 if request else None,
					# }
					
					# TODO support the originatorLocation in the request
					#'olo': request.olo if request else None,

					# TODO support the originatorRoleID in the request
					#'orid': resource.orig if resource else None,

					'rts': resource.ot if resource else None,
					# EXPERIMENTAL: use the structured format of the resourceID
					'trid': resource.getSrn() if resource else None,
					'ppl': proposedLifetime,

					# TODO Later suport the following attributes 
					# NOTE For a description of the roleIDsFromACPs attribute see TS-0003, 7.3.2.2, step 2.2
					# roleIDsFromACPs
					# tokenIDs
					# authorSignIndicator


				}
			}
		}
		# TODO continue with 6.3.5.46-1
		response = self.notification.sendNotificationWithDict(removeNoneAttributes(notification), ae.ri, originator=RC.cseCsi)

		# TODO check for sit = 2


# When the Hosting CSE receives a notification response for dynamic authorization, it performs 
# the following steps in order:

# 1) The Hosting CSE shall verify that the securityInfoType element of the m2m:securityInfo 
# element of the notification is configured as "2" (Dynamic Authorization Response). If it is not,
# the Hosting CSE shall not grant privileges to the Originator of the request for which the Hosting
#  CSE was attempting dynamic authorization. If Distributed Authorization is not supported (see 
# oneM2M TS-0001 Functional Architecture [6] clause 10.2.3) the Hosting CSE shall reject the request
#  by returning an "ORIGINATOR_HAS_NO_PRIVILEGE" Response Status Code to the Originator of the received
#  request and no additional steps shall be performed.

# 2) The Hosting CSE shall check whether the response contains a dynamicACPInfo element. If present,
# the Hosting CSE shall create a <accessControlPolicy> child resource under the targeted resource and 
# configure its privileges using the dynamicACPInfo. In this case, the Hosting CSE shall configure
# the privileges attribute with the grantedPrivileges and the expirationTime attribute with the
# privilegesLifetime. The Hosting CSE shall also configure the selfPrivileges attribute to allow 
# itself to perform Update/Retrieve/Delete operations on the newly created <accessControlPolicy> resource.

# 3) The Hosting CSE shall check whether the response contains a tokens element. If present the Hosting
# CSE shall perform verification and caching of the token as specified in clause 7.3.2 in oneM2M 
# TS-0003 [7] and the Hosting CSE shall check whether an AuthorSignReqInfo is contained in the response.
# If it is present, the Hosting CSE shall add the AuthorSignReqInfo into the response to the Originator
# of the incoming request.

		return False
