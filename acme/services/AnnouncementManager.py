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
from typing import Optional, Tuple, List, cast, Any

import time
from ..etc import Utils
from ..etc import RequestUtils
from ..etc.Types import DesiredIdentifierResultType, ResourceTypes, ResponseStatusCode, JSON, Result, ResultContentType
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from . import CSE
from .Configuration import Configuration
from .Logging import Logging as L

# TODO for anounceable resource:
# - update: update resource here

# TODO Remove marked code below after 0.10.0, also remove checkInterval configuration setting

waitBeforeAnnouncement = 3	# seconds # TODO configurable
"""	Number of seconds to wait before performing announcements when a new CSE has registered. """

class AnnouncementManager(object):
	"""	This class implements announcement functionalities.

		Attributes:
			checkInterval: Number of seconds to wait between tries to announce resources to remote CSEs (configurable).
			allowAnnouncementsToHostingCSE: Allow or disallow resources to announce to the own hosting CSE (configurable).

	"""

	def __init__(self) -> None:
		"""	Initialization of the announcement manager.
		"""
		CSE.event.addHandler(CSE.event.registeredToRegistrarCSE, self.handleRegisteredToRegistrarCSE)			# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRegistrarCSE, self.handleDeRegisteredFromRegistrarCSE)	# type: ignore
		CSE.event.addHandler(CSE.event.registreeCSEHasRegistered, self.handleRegistreeCSEHasRegistered)			# type: ignore
		CSE.event.addHandler(CSE.event.registreeCSEHasDeregistered, self.handleRegistreeCSEHasDeregistered)		# type: ignore
		
		# Configuration values
		self._assignConfig()

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		# self.start()	# TODO remove after 0.10.0
		L.isInfo and L.log('AnnouncementManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the announcement manager.
		
			Return:
				Always True.
		"""
		# self.stop()	# TODO remove after 0.10.0
		if CSE.remote:
			for csr in CSE.remote.getAllLocalCSRs():
				if csr:
					self.checkResourcesForUnAnnouncement(csr)
		L.isInfo and L.log('AnnouncementManager shut down')
		return True


	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the announcement manager.
		"""
		self.checkInterval					= Configuration.get('cse.announcements.checkInterval')
		self.allowAnnouncementsToHostingCSE	= Configuration.get('cse.announcements.allowAnnouncementsToHostingCSE')


	def configUpdate(self, key:Optional[str] = None, value:Optional[Any] = None) -> None:
		"""	Callback for the *configUpdate* event.
			
			Args:
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'cse.announcements.checkInterval', 'cse.announcements.allowAnnouncementsToHostingCSE' ]:
			return

		# assign new values
		self._assignConfig()


	# TODO Test this for a while. And remove it if this fully works as expected.
	# A regular check might be overkill. Just using the events should be enough.


	# #
	# #	Announcement Monitor
	# #

	# # Start the monitor in a thread. 
	# def start(self) -> None:
	# 	L.isInfo and L.log('Starting Announcements monitor')
	# 	BackgroundWorkerPool.newWorker(self.checkInterval, self.announcementMonitorWorker, 'anncMonitor').start()


	# # Stop the monitor
	# def stop(self) -> None:
	# 	L.isInfo and L.log('Stopping Announcements monitor')
	# 	# Stop the worker
	# 	BackgroundWorkerPool.stopWorkers('anncMonitor')


	# def announcementMonitorWorker(self) -> bool:
	# 	L.isDebug and L.logDebug('Checking announcements to remote CSEs')

	# 	# check all CSR
	# 	for csr in CSE.remote.getAllLocalCSRs():
	# 		self.checkResourcesForAnnouncement(csr)
	# 	return True



	#########################################################################
	#
	#	Event Handlers. Listen on remote CSE registrations
	#

	def handleRegisteredToRegistrarCSE(self, remoteCSE:Resource, remoteCSR:Resource) -> None:
		"""	Handle registrations to a registrar CSE.

			Args:
				remoteCSE: The remote `CSEBase` resource.
				remoteCSR: The own CSE's remote `CSR` resource.
		"""
		time.sleep(waitBeforeAnnouncement)	# Give some time until remote CSE fully connected
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleDeRegisteredFromRegistrarCSE(self, remoteCSR:Resource) -> None:
		"""	Handle de-registrations from a registrar CSE.

			Args:
				remoteCSR: The own CSE's remote `CSR` resource.

		"""
		# self.checkResourcesForUnAnnouncement(remoteCSR)	# TODO remove this > 0.11.0 for new Announcement behaviour
		pass


	def handleRegistreeCSEHasRegistered(self, remoteCSR:Resource) -> None:
		"""	Handle registrations when a registree CSE has registered.

			Args:
				remoteCSR: The own CSE's remote `CSR` resource.
		"""
		time.sleep(waitBeforeAnnouncement) 	# Give some time until remote CSE is fully connected
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleRegistreeCSEHasDeregistered(self, remoteCSR:Resource) -> None:
		""" Handle de-registrations when a registree CSE has de-registered.

			Args:
				remoteCSR: The own CSE's remote `CSR` resource.
		"""
		#self.checkResourcesForUnAnnouncement(remoteCSR)	# TODO remove this > 0.11.0 for new Announcement behaviour+
		pass



	#########################################################################
	#
	#	Access Methods to check, announce, unanounce etc
	#

	#
	#	Announcements
	#

	def checkResourcesForAnnouncement(self, remoteCSR:Resource) -> Result:
		"""	Check all resources in the resource tree and announce them if necessary.

			Args:
				remoteCSR: The registree or registrar CSE's `CSR` resource.
			
			Return:
				Result object indicating the success of the operation.
			
			See Also:
				- `announceResource`
				- `searchAnnounceableResourcesForCSI`
		"""
		if not remoteCSR:
			return Result(status = True)

		# get all reources for this specific CSI that are NOT announced to it yet
		resources = self.searchAnnounceableResourcesForCSI(remoteCSR.csi, False) # only return the resources that are *not* announced to this csi yet
		# try to announce all not-announced resources to this csr
		for resource in resources:
			if not (res := self.announceResource(resource)).status:
				return res
		return Result(status = True)


	def announceResource(self, resource:AnnounceableResource) -> Result:
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
			if (at == CSE.cseCsi or at.startswith(CSE.cseCsiSlash)) and not self.allowAnnouncementsToHostingCSE:
				L.isWarn and L.logWarn('Targeting own CSE for announcement. Ignored.')
				self._removeAnnouncementFromResource(resource, at)
				continue
			self.announceResourceToCSI(resource, at)	# ignore result
		return Result(status=True)


	def announceResourceToCSI(self, resource:AnnounceableResource, csi:str) -> Result:
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

		def checkCSEBaseAnnouncement(cseBase:AnnounceableResource) -> Result:
			"""	Check and perform the announcement of a CSE.
			
				Args:
					cseBase: The announceable version of a `CSEBase` (`CSEBaseAnnc`).

			Return:
				Result object indicating the success of the operation.
			"""
			L.isDebug and L.logDebug(f'Check CSEBase announcement')
			if t := self._announcedInfos(cseBase, csi):
				# CSEBase has "old" announcement infos
				remoteRi = t[1] if Utils.isSPRelative(t[1]) else f'{csi}/{t[1]}'
				if CSE.dispatcher.retrieveResource(remoteRi, CSE.cseCsi).rsc != ResponseStatusCode.OK:	# Not a local resource
					L.isDebug and L.logDebug('CSEBase is not announced')
					# No, it's not there anymore -> announce it again.
					self._removeAnnouncementFromResource(cseBase, csi)
					# announce CSE recursively
					if not (res := self.announceResourceToCSI(cseBase, csi)).status:	# Don't ignore result for this one
						return res
			else:

				# No internal announcement infos, try to discover it on the remote CSE.
				# This is done by discovering a CSEBaseAnnc resource with a link to our CSE.

				# Get the remote CSE's resource ID
				if (to := CSE.remote.getRemoteCSEBaseAddress(csi)) is None:
					return Result.errorResult(dbg = f'Cannot find CSR for csi: {csi}')

				dct = RequestUtils.createRawRequest(to = to,
													rcn = ResultContentType.childResourceReferences.value,
													drt = DesiredIdentifierResultType.unstructured.value,
													fc = {	'ty' : ResourceTypes.CSEBaseAnnc.value,
															'lnk' : f'{cseBase.csi}/{cseBase.ri}'
														})

				if not (res := CSE.request.sendRetrieveRequest(to, originator = CSE.cseCsi, content = dct, raw = True)).status:
					return res

				if res.rsc == ResponseStatusCode.OK and res.data:	# Found a remote CSEBaseAnnc
					# Assign to the local CSEBase
					if (remoteRi := Utils.findXPath(cast(dict, res.data), 'm2m:rrl/rrf/{0}/val')):
						atri = remoteRi if Utils.isSPRelative(remoteRi) else f'{csi}/{remoteRi}'
						L.isDebug and L.logDebug(f'CSEBase already announced: {atri}. Updating CSEBase announcement')
						cseBase.addAnnouncementToResource(csi, remoteRi)
						cseBase.dbUpdate()
						return Result(status = True)

				# Not found, so announce it
				L.isDebug and L.logDebug(f'Announcing CSEBase: {cseBase.ri}')
				if not (res := self.announceResourceToCSI(cseBase, csi)).status:	# Don't ignore result for this one
					return res
			return Result(status = True)


		L.isDebug and L.logDebug(f'Announce resource: {resource.ri} to: {csi}')
		if self._isResourceAnnouncedTo(resource, csi):
			L.isDebug and L.logDebug(f'Resource already announced: {resource.ri}')
			return Result(status = True)

		# Create announced resource & type
		dct = resource.createAnnouncedResourceDict(isCreate = True)
		tyAnnc = ResourceTypes(resource.ty).announced()
		targetID = ''

		if resource.ty != ResourceTypes.CSEBase:	# CSEBase is just announced below
			if not (at := resource.at):
				L.isDebug and L.logDebug('at attribute is empty.')
				return Result(status = True)	# Not much to do here

			# Check if parent is announced already to the same remote CSE
			if not (res := CSE.dispatcher.retrieveLocalResource(resource.pi)).status:
				return Result(status = False, rsc = ResponseStatusCode.internalServerError, dbg = L.logErr(f'Cannot retrieve parent. Announcement not possible: {res.dbg}'))
			
			parentResource = res.resource

			# For announcing the CSEBase we want to take some extra care and check whether it really
			# is available at the remote CSE. It could have been removed (expiration, restart, ...) and
			# this may not be reflected
			if parentResource.ty == ResourceTypes.CSEBase:
				if not (res := checkCSEBaseAnnouncement(parentResource)).status:
					return res
				parentResource.dbReload() 	# parent is already the CSEBase, just reload from DB

			else:	# parent is not a CSEBase

				if not self._isResourceAnnouncedTo(parentResource, csi):
					L.isDebug and L.logDebug(f'Parent resource is not announced: {parentResource.ri}')
					# parent resource is not announced -> announce the resource directly under the CSEBaseAnnc

					# Don't allow instances to be announced without their parents
					if resource.ty in [ResourceTypes.CIN, ResourceTypes.FCI, ResourceTypes.TSI]:
						return Result(status = False, rsc = ResponseStatusCode.operationNotAllowed, dbg = L.logDebug('Announcing instances without their parents is not allowed'))

					# Whatever the parent resource is, check whether the CSEBase has been announced. Announce it if necessay
					if not (res := checkCSEBaseAnnouncement(Utils.getCSE().resource)).status:
						return res
					parentResource = Utils.getCSE().resource	# set the announced CSEBase as new parent
					
					# ... then continue with normale announcement of the resource. The parent for the announcement is now the CSEBase
				
			# parent resource is announced -> Announce the resource under the parent resource Annc
			if not (at := self._announcedInfos(parentResource, csi)):
				return Result(status = False, rsc = ResponseStatusCode.badRequest, dbg = L.logWarn(f'No announcement for parent resource: {parentResource.ri} to: {csi}'))
			targetID = at[1]

		# Create the announed resource on the remote CSE
		if targetID:
			csrID = targetID if Utils.isSPRelative(targetID) else f'{csi}/{targetID}'
		else:
			if (to := CSE.remote.getRemoteCSEBaseAddress(csi)) is None:
				return Result.errorResult(dbg = f'Cannot find CSR for csi: {csi}')
			csrID = to
		L.isDebug and L.logDebug(f'Creating announced resource at: {csrID}')
		res = CSE.request.sendCreateRequest(csrID, CSE.cseCsi, ty = tyAnnc, content = dct)
		if res.rsc not in [ ResponseStatusCode.created, ResponseStatusCode.OK ]:
			if res.rsc != ResponseStatusCode.conflict:	# assume that it is ok if the remote resource already exists 
				return Result(status = False, rsc = res.rsc, dbg = L.logDebug(f'Error creating remote announced resource: {int(res.rsc)} ({res.dbg})'))
		else:
			resource.addAnnouncementToResource(csi, Utils.findXPath(cast(JSON, res.data), '{*}/ri'))
		L.isDebug and L.logDebug(f'Announced resource created: {resource.getAnnouncedTo()}')
		resource.dbUpdate()
		return Result(status = True)


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
		res = CSE.request.sendDeleteRequest(csrID, CSE.cseCsi)
		if res.rsc not in [ ResponseStatusCode.deleted, ResponseStatusCode.OK ]:
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

		# Check for removed AT
		# Logging.logErr(set(self._origAT))
		# Logging.logErr(set(self.at))
		# Logging.logErr(set(self.at) == set(self._origAT))


		# get all resources for this specific CSI that are announced to it yet
		CSIsFromAnnounceTo = []
		for announcedResourceID in resource.at:
			if len(sp := announcedResourceID.split('/')) >= 2:
				if (csi := f'/{sp[1]}') == CSE.cseCsi or csi.startswith(f'{CSE.cseCsi}/'):	# Ignore own CSE as target
					continue
				CSIsFromAnnounceTo.append(csi)

		# Update the annoucned remote resources 
		announcedCSIs = []
		remoteRIs = []
		for (csi, remoteRI) in resource.getAnnouncedTo():
			if csi == originator:	# Skip the announced resource at the originator !!
				continue
			announcedCSIs.append(csi)	# build a list of already announced CSIs
			remoteRIs.append(csi) 		# build a list of remote RIs
			self.updateResourceOnCSI(resource, csi, remoteRI)

		# Check for any non-announced csi in at, and possibly announce them 
		for csi in CSIsFromAnnounceTo:
			if csi not in announcedCSIs and csi not in remoteRIs:
				self.announceResourceToCSI(resource, csi)


	def updateResourceOnCSI(self, resource:AnnounceableResource, csi:str, remoteRI:str) -> None:
		"""	Update an announced resource on a specific remote CSE.

			Args:
				resource: The announceable resource to update.
				csi: The CSE-ID of the CSE where the announced resource is hosted.
				remoteRI: The resource ID of the remote announced resource.
		"""
		# TODO doc
		dct = resource.createAnnouncedResourceDict(isCreate = False)
		# Create the announed resource on the remote CSE
		csrID = f'{csi}/{remoteRI}'
		L.isDebug and L.logDebug(f'Updating announced resource at: {csrID}')	
		res = CSE.request.sendUpdateRequest(csrID, CSE.cseCsi, content = dct)
		if res.rsc not in [ ResponseStatusCode.updated, ResponseStatusCode.OK ]:
			L.isDebug and L.logDebug(f'Error updating remote announced resource: {int(res.rsc)}')
			# Ignore and fallthrough
		L.isDebug and L.logDebug('Announced resource updated')


	def _removeAnnouncementFromResource(self, resource:Resource, csi:str) -> None:
		"""	Remove announcement details from a resource.

			Modify the internal *_announcedTo* attribute as well the *at* attribute
			to remove the reference to the remote CSE from announced resource.

			Args:
				resource: The announceable resource to remove.
				csi: The CSE-ID of the CSE where the announced resource is hosted.
		"""
		ats = resource.getAnnouncedTo()
		remoteRI:str = None

		# TODO put this method of AnnounceableResource
		for x in ats:
			if x[0] == csi:
				remoteRI = x[1]
				ats.remove(x)
				resource.setAttribute(Resource._announcedTo, ats)

		# # Modify the at attribute
		if remoteRI:
			atCsi = f'{csi}/{remoteRI}'
			if (at := resource.at) and atCsi in at:
				at.remove(atCsi)
				resource.setAttribute('at', at)


	def _isResourceAnnouncedTo(self, resource:Resource, csi:str) -> bool:
		"""	Check whether a resource is announced to a specific remote CSE.
		
			This is done by looking at the entries in the internal *_announcedTo* 
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
				if ato := r.get(Resource._announcedTo):
					for i in ato:
						if csi == i[0]:	# 0=remote csi,
							return isAnnounced
					return not isAnnounced
			return False

		return cast(List[AnnounceableResource], CSE.storage.searchByFilter(_announcedFilter))


