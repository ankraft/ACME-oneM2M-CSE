#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

"""	This module defines the manager for handling announcements.
"""

from __future__ import annotations
from typing import Optional, Tuple, List, cast

import time

from ..etc.IDUtils import isSPRelative
from ..helpers.TextTools import findXPath
from ..etc.Types import DesiredIdentifierResultType, ResourceTypes, JSON, ResultContentType, CSERequest, FilterCriteria 
from ..etc.Types import Operation 
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException
from ..etc.ResponseStatusCodes import BAD_REQUEST, INTERNAL_SERVER_ERROR
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources.CSEBase import getCSE
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration, ConfigurationError

# TODO for anounceable resource:
# - update: update resource here


class AnnouncementManager(object):
	"""	This class implements announcement functionalities.
	"""


	def __init__(self) -> None:
		"""	Initialization of the announcement manager.
		"""
		CSE.event.addHandler(CSE.event.registeredToRegistrarCSE, self.handleRegisteredToRegistrarCSE)			# type: ignore
		CSE.event.addHandler(CSE.event.registreeCSEHasRegistered, self.handleRegistreeCSEHasRegistered)			# type: ignore
		
		L.isInfo and L.log('AnnouncementManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the announcement manager.
		
			Return:
				Always True.
		"""
		if CSE.remote:
			for csr in CSE.remote.getAllLocalCSRs():
				if csr:
					self.checkResourcesForUnAnnouncement(csr)
		L.isInfo and L.log('AnnouncementManager shut down')
		return True


	#########################################################################
	#
	#	Event Handlers. Listen on remote CSE registrations
	#

	def handleRegisteredToRegistrarCSE(self, name:str, remoteCSE:Resource, remoteCSR:Resource) -> None:
		"""	Handle registrations to a registrar CSE.

			Args:
				name:Event name.
				remoteCSE: The remote `CSEBase` resource.
				remoteCSR: The own CSE's remote `CSR` resource.
		"""
		time.sleep(Configuration.cse_announcements_delayAfterRegistration)	# Give some time until remote CSE fully connected
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleRegistreeCSEHasRegistered(self, name:str, remoteCSR:Resource) -> None:
		"""	Handle registrations when a registree CSE has registered.

			Args:
				name:Event name.
				remoteCSR: The own CSE's remote `CSR` resource.
		"""
		time.sleep(Configuration.cse_announcements_delayAfterRegistration) 	# Give some time until remote CSE is fully connected
		self.checkResourcesForAnnouncement(remoteCSR)



	#########################################################################
	#
	#	Access Methods to check, announce, unanounce etc
	#

	#
	#	Announcements
	#

	def checkResourcesForAnnouncement(self, remoteCSR:Resource) -> None:
		"""	Check all resources in the resource tree and announce them if necessary.

			Args:
				remoteCSR: The registree or registrar CSE's `CSR` resource.
			
			See Also:
				- `announceResource`
				- `searchAnnounceableResourcesForCSI`
		"""
		if not remoteCSR:
			return

		# get all reources for this specific CSI that are NOT announced to it yet
		resources = self.searchAnnounceableResourcesForCSI(remoteCSR.csi, False) # only return the resources that are *not* announced to this csi yet
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.announceResource(resource)


	def announceResource(self, resource:AnnounceableResource) -> None:
		"""	Announce a single resource to its announcement target(s).

			Args:
				resource: The resource to announce.
			
			Return:
				Result object indicating the success of the operation.
			
			See Also:
				- `announceResourceToCSI`
		"""
		L.isDebug and L.logDebug(f'Announce resource: {resource.ri} to all connected csr')
		for at in resource.at:
			if (at == RC.cseCsi or at.startswith(RC.cseCsiSlash)) and not Configuration.cse_announcements_allowAnnouncementsToHostingCSE:
				L.isWarn and L.logWarn('Targeting own CSE for announcement. Ignored.')
				self._removeAnnouncementFromResource(resource, at)
				continue
			self.announceResourceToCSI(resource, at)	# ignore result


	def announceResourceToCSI(self, resource:AnnounceableResource, csi:str) -> None:
		"""	Announce a resource to a specific registered remote CSE.

			Args:
				resource: The resource to announce.
				csi: CSE-ID of the remote CSE.
			
			Return:
				Result object indicating the success of the operation.
			
			TODO:
				- Support announcement to direct URL
		"""
		# TODO direct URL

		def checkCSEBaseAnnouncement(cseBase:AnnounceableResource) -> None:
			"""	Check and perform the announcement of a CSE.
			
				Args:
					cseBase: The announceable version of a `CSEBase` (`CSEBaseAnnc`).

			Return:
				Result object indicating the success of the operation.
			"""
			L.isDebug and L.logDebug(f'Check CSEBase announcement')
			if t := self._announcedInfos(cseBase, csi):
				L.isDebug and L.logDebug(f'announcement infos: {t}')
				# CSEBase has "old" announcement infos
				remoteRi = t[1] if isSPRelative(t[1]) else f'{csi}/{t[1]}'
				try:
					_r = CSE.dispatcher.retrieveResource(remoteRi, RC.cseCsi)
				except ResponseException as e:	# basically anything that isn't "OK"
					L.isDebug and L.logDebug('CSEBase is not announced')
					# No, it's not there anymore -> announce it again.
					self._removeAnnouncementFromResource(cseBase, csi)
					# announce CSE recursively
					self.announceResourceToCSI(cseBase, csi)

			else:

				# No internal announcement infos, try to discover it on the remote CSE.
				# This is done by discovering a CSEBaseAnnc resource with a link to our CSE.

				# Get the remote CSE's resource ID

				# We don't know the name of the remote CSEBase, so we have to use the CSI + '-'
				to = f'{csi}/-'
				
				# Here, it is actually important NOT to get the next CSE, but to check whether
				# there is a remots CSEBase with that ID. Only THEN we can send the request and
				# continue with the announcement.

				res = CSE.request.handleSendRequest(CSERequest(op = Operation.RETRIEVE,
															   to = to,
															   originator = RC.cseCsi,
															   rcn = ResultContentType.childResourceReferences,
															   drt = DesiredIdentifierResultType.unstructured,
															   fc = FilterCriteria(ty = [ ResourceTypes.CSEBaseAnnc.value ],
																				   attributes = { 'lnk' : f'{cseBase.csi}/{cseBase.ri}' } ))
													)[0].result		# there should be at least one result
				if res.rsc == ResponseStatusCode.OK and res.data:	# Found a remote CSEBaseAnnc
					# Assign to the local CSEBase
					if (remoteRi := findXPath(cast(dict, res.data), 'm2m:rrl/rrf/{0}/val')):
						atri = remoteRi if isSPRelative(remoteRi) else f'{csi}/{remoteRi}'
						L.isDebug and L.logDebug(f'CSEBase already announced: {atri}. Updating CSEBase announcement')
						cseBase.addAnnouncementToResource(csi, remoteRi)
						cseBase.dbUpdate()
						return

				# Not found, so announce it
				L.isDebug and L.logDebug(f'announcing CSEBase: {cseBase.ri}')
				self.announceResourceToCSI(cseBase, csi)


		L.isDebug and L.logDebug(f'Announce resource: {resource.ri} to: {csi}')
		if self._isResourceAnnouncedTo(resource, csi):
			L.isDebug and L.logDebug(f'resource already announced: {resource.ri}')
			return

		# Create announced resource & type
		dct = resource.createAnnouncedResourceDict(isCreate = True)
		tyAnnc = ResourceTypes(resource.ty).announced()
		targetID = ''

		if resource.ty != ResourceTypes.CSEBase:	# CSEBase is just announced below
			if not (at := resource.at):
				L.isDebug and L.logDebug('at attribute is empty.')
				return	# Not much to do here

			# Check if parent is announced already to the same remote CSE
			try:
				parentResource = CSE.dispatcher.retrieveLocalResource(resource.pi)
			except ResponseException as e:
				raise INTERNAL_SERVER_ERROR(L.logErr(f'cannot retrieve parent. Announcement not possible: {e.dbg}'))
			
			# For announcing the CSEBase we want to take some extra care and check whether it really
			# is available at the remote CSE. It could have been removed (expiration, restart, ...) and
			# this may not be reflected
			if parentResource.ty == ResourceTypes.CSEBase:
				checkCSEBaseAnnouncement(parentResource)	# type:ignore[arg-type]
				parentResource.dbReload() 	# parent is already the CSEBase, just reload from DB

			else:	# parent is not a CSEBase

				if not self._isResourceAnnouncedTo(parentResource, csi):
					L.isDebug and L.logDebug(f'parent resource is not announced: {parentResource.ri}')
					# parent resource is not announced -> announce the resource directly under the CSEBaseAnnc

					# Don't allow instances to be announced without their parents
					if resource.ty in [ResourceTypes.CIN, ResourceTypes.FCI, ResourceTypes.TSI]:
						L.logWarn('Announcing instances without their parents is not allowed. Unsuccessful announcement')
						return
					# Whatever the parent resource is, check whether the CSEBase has been announced. Announce it if necessay
					# and set the announced CSEBase as new parent
					checkCSEBaseAnnouncement(parentResource := getCSE())
					
					# ... then continue with normale announcement of the resource. The parent for the announcement is now the CSEBase
				
			# parent resource is announced -> Announce the resource under the parent resource Annc
			if not (at := self._announcedInfos(parentResource, csi)):
				raise BAD_REQUEST(L.logWarn(f'no announcement for parent resource: {parentResource.ri} to: {csi}'))
			targetID = at[1]

		# Create the announed resource on the remote CSE
		if targetID:
			to = targetID if isSPRelative(targetID) else f'{csi}/{targetID}'
		else:
			# We don't know the name of the remote CSEBase, so we have to use the CSI + '-'
			to = f'{csi}/-'

		L.isDebug and L.logDebug(f'creating announced resource at: {to}')
		try:
			res = CSE.request.handleSendRequest(CSERequest(op = Operation.CREATE,
						  								   to = to, 
														   originator = RC.cseCsi, 
														   ty = tyAnnc, 
														   pc = dct)
											   )[0].result	# there should be at least one result
			if res.rsc == ResponseStatusCode.CREATED:
				resource.addAnnouncementToResource(csi, findXPath(cast(JSON, res.data), '{*}/ri'))
				L.isDebug and L.logDebug(f'Announced resource created: {resource.getAnnouncedTo()}')
				resource.dbUpdate()
			else:
				L.isWarn and L.logWarn(f'Announced resource could not be created at: {to} ({res.rsc})')

		except ResponseException as e:
			e.dbg = L.logDebug(f'Error creating remote announced resource: {int(e.rsc)} ({e.dbg})')
			raise e



	#
	#	De-Announcements
	#

	def checkResourcesForUnAnnouncement(self, remoteCSR:Resource) -> None:
		"""	Check whether resources need announcements, and initiate announcement
			if they do.

			Args:
				remoteCSR: The `CSR` remote resource.
			
			See also:
				- searchAnnounceableResourcesForCSI
		"""
		csi = remoteCSR.csi
		L.isDebug and L.logDebug(f'Checking resources for Unannouncement to: {csi}')
		# get all reources for this specific CSI that are NOT announced to it yet
		resources = self.searchAnnounceableResourcesForCSI(csi, True)
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.deAnnounceResource(resource)
			self._removeAnnouncementFromResource(resource, csi)
			resource.dbUpdate()


	def deAnnounceResource(self, resource:AnnounceableResource) -> None:
		"""	De-announce a single resource from its announcement target(s).

			Args:
				resource: The announceable resource to de-announce.
			
			See also:
				- deAnnounceResourceFromCSI
		"""
		L.isDebug and L.logDebug(f'De-Announce resource: {resource.ri} from all connected csr')

		for (csi, remoteRI) in resource.getAnnouncedTo():
			self.deAnnounceResourceFromCSI(resource, csi, remoteRI)


	def deAnnounceResourceFromCSI(self, resource:AnnounceableResource, csi:str, remoteRI:str) -> None:
		"""	De-Announce a resource from a specific `CSR`.

			Args:
				resource: The announceable resource to de-announce.
				csi: The CSE-ID of the CSE from which the resource is to be de-announced.
				remoteRI: The resource ID of the remote announced resource.
		"""

		# Delete the announed resource from the remote CSE
		csrID = f'{csi}/{remoteRI}'
		L.isDebug and L.logDebug(f'Delete announced resource: {csrID}')	
		res = CSE.request.handleSendRequest(CSERequest(op = Operation.DELETE,
													   to = csrID, 
													   originator = RC.cseCsi))[0].result	# there should be at least one result
		if res.rsc not in [ ResponseStatusCode.DELETED, ResponseStatusCode.OK ]:
			L.isWarn and L.logWarn(f'Error deleting remote announced resource: {res.rsc}')
			# ignore the fact that we cannot delete the announced resource.
			# fall-through for some house-keeping
		self._removeAnnouncementFromResource(resource, csi)
		L.isDebug and L.logDebug('Announced resource deleted')
		resource.dbUpdate()


	#
	#	Update Announcements
	#


	def announceUpdatedResource(self, resource:AnnounceableResource, originator:str) -> None:
		"""	(Newly) announce an updated resource to a remote CSE.

			Args:
				resource: The announceable resource that has been updated.
				originator: The original UPDATE request's originator.
		"""
		L.isDebug and L.logDebug(f'Updating announced resource: {resource.ri}')

		# get all resources for this specific CSI that are announced to it yet
		CSIsFromAnnounceTo = []
		for announcedResourceID in resource.at:
			if len(sp := announcedResourceID.split('/')) >= 2:
				if (csi := f'/{sp[1]}') == RC.cseCsi or csi.startswith(f'{RC.cseCsi}/'):	# Ignore own CSE as target
					continue
				CSIsFromAnnounceTo.append(csi)

		# Update the annoucned remote resources 
		announcedCSIs = []
		for (csi, remoteRI) in resource.getAnnouncedTo():
			if csi == originator:	# Skip the announced resource at the originator !!
				continue
			announcedCSIs.append(csi)	# build a list of already announced CSIs
			self.updateResourceOnCSI(resource, csi, remoteRI)

		# Check for any non-announced csi in at, and possibly announce them 
		for csi in CSIsFromAnnounceTo:
			if csi not in announcedCSIs:
				self.announceResourceToCSI(resource, csi)


	def updateResourceOnCSI(self, resource:AnnounceableResource, csi:str, remoteRI:str) -> None:
		"""	Update an announced resource on a specific remote CSE.

			Args:
				resource: The announceable resource to update.
				csi: The CSE-ID of the CSE where the announced resource is hosted.
				remoteRI: The resource ID of the remote announced resource.
		"""
		dct = resource.createAnnouncedResourceDict(isCreate = False)
		# Create the announed resource on the remote CSE
		csrID = f'{csi}/{remoteRI}'
		L.isDebug and L.logDebug(f'Updating announced resource at: {csrID}')	
		res = CSE.request.handleSendRequest(CSERequest(op = Operation.UPDATE, 
													   to = csrID, 
													   originator = RC.cseCsi, 
													   pc = dct))[0].result		# there should be at least one result
		if res.rsc not in [ ResponseStatusCode.UPDATED, ResponseStatusCode.OK ]:
			L.isDebug and L.logDebug(f'Error updating remote announced resource: {int(res.rsc)}')
			# Ignore and fallthrough
		L.isDebug and L.logDebug('Announced resource updated')


	def _removeAnnouncementFromResource(self, resource:Resource, csi:str) -> None:
		"""	Remove announcement details from a resource.

			Modify the internal *__announcedTo__* attribute as well the *at* attribute
			to remove the reference to the remote CSE from announced resource.

			Args:
				resource: The announceable resource to remove.
				csi: The CSE-ID of the CSE where the announced resource is hosted.
		"""
		remoteRI = resource.removeAnnouncementFromResource(csi)
		
		# Modify the at attribute
		if remoteRI:
			atCsi = f'{csi}/{remoteRI}'
			if (at := resource.at) and atCsi in at:
				at.remove(atCsi)
				resource.setAttribute('at', at)


	def _isResourceAnnouncedTo(self, resource:Resource, csi:str) -> bool:
		"""	Check whether a resource is announced to a specific remote CSE.
		
			This is done by looking at the entries in the internal *__announcedTo__* 
			attribute, ie. whether they will contain the *csi* of the remote CSE.

			Args:
				resource: The announceable resource to check.
				csi: The CSE-ID of the CSE where the announced resource is supposed to be hosted.
			
			Return:
				Boolean indicating the announced status.
		"""
		return (at := resource.getAnnouncedTo()) is not None and any(csi == _csi for (_csi, _) in at)
	

	def _announcedInfos(self, resource:Resource, csi:str) -> Optional[Tuple[str, str]]:
		"""	Return the matching tuple for the given *csi* of a resource announcement,
			or *None* if none is set.

			Args:
				resource: The announceable resource to check.
				csi: The CSE-ID of the CSE where the announced resource is supposed to be hosted.
		"""
		if at := resource.getAnnouncedTo():
			for _at in at:
				if _at[0] == csi:
					return _at
		return None


	def announceResourceViaDirectURL(self, resource:Resource, at:str) -> bool:
		"""	Announce a resource via a direct URL, nit via a csi.

			Attention:
				Not supported yet.

			Args:
				resource: The announceable resource to announce.
				at: The direct URL of the remote CSE to where to announce the resource.
			
			Return:
				Boolean indicating the result.
		"""
		L.logErr('TODO Direct Announcement')
		return False


	#########################################################################
	#
	#	Utilities
	#

	def searchAnnounceableResourcesForCSI(self, csi:str, isAnnounced:bool) -> list[AnnounceableResource]:
		""" Search and retrieve all resources that have the provided CSI in their 
			*at* attribute.
			
			Also distinguish between announced and not announced resources in the filter.

			Args:
				csi: The CSE-ID of the CSE for which the announced resource are searched.
				isAnnounced: Boolean indicating whether announced or non-announced resources are searched for.
			
			Return:
				List of `AnnounceableResource` resources that have been found.

		"""

		mcsi = f'{csi}/'

		def _announcedFilter(r:JSON) -> bool:
			"""	Internal filter function for announced resources.
			
				Args:
					r: Resource to check.
				
				Return:
					Boolean indicating the search filter result.
			"""
			if (at := r.get('at')) and len(list(filter(lambda x: x.startswith(mcsi), at))) > 0:	# check whether any entry in 'at' startswith mcsi
				if ato := r.get(Constants.attrAnnouncedTo):
					for i in ato:
						if csi == i[0]:	# 0=remote csi,
							return isAnnounced
					return not isAnnounced
			return False

		return cast(List[AnnounceableResource], CSE.storage.searchByFilter(_announcedFilter))

