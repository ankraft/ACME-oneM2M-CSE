#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

from __future__ import annotations
import time
from typing import Optional, Tuple, List, cast
from ..etc import Utils
from ..etc import RequestUtils
from ..etc.Types import DesiredIdentifierResultType, ResourceTypes as T, ResponseStatusCode as RC, JSON, Result, ResultContentType
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from . import CSE
from .Logging import Logging as L
from .Configuration import Configuration

# TODO for anounceable resource:
# - update: update resource here

waitBeforeAnnouncement = 3	# seconds # TODO configurable

class AnnouncementManager(object):

	def __init__(self) -> None:
		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.handleRegisteredToRemoteCSE)			# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.handleDeRegisteredFromRemoteCSE)	# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasRegistered, self.handleRemoteCSEHasRegistered)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasDeregistered, self.handleRemoteCSEHasDeregistered)	# type: ignore
		
		# Configuration values
		self.checkInterval			= Configuration.get('cse.announcements.checkInterval')

		# self.start()	# TODO remove after 0.10.0
		L.isInfo and L.log('AnnouncementManager initialized')


	def shutdown(self) -> bool:
		# self.stop()	# TODO remove after 0.10.0
		if CSE.remote:
			for csr in CSE.remote.getAllLocalCSRs():
				if csr:
					self.checkResourcesForUnAnnouncement(csr)
		L.isInfo and L.log('AnnouncementManager shut down')
		return True


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

	def handleRegisteredToRemoteCSE(self, remoteCSE:Resource, remoteCSR:Resource) -> None:
		"""	Handle registrations to a remote CSE (Registrar CSE).
		"""
		time.sleep(waitBeforeAnnouncement)	# Give some time until remote CSE fully connected
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleDeRegisteredFromRemoteCSE(self, remoteCSR:Resource) -> None:
		"""	Handle de-registrations from a remote CSE (registrar CSE).
		"""
		# self.checkResourcesForUnAnnouncement(remoteCSR)	# TODO remove this for new Announcement behaviour
		pass


	def handleRemoteCSEHasRegistered(self, remoteCSR:Resource) -> None:
		"""	Handle registrations when a remote CSE has registered (registree CSE).
		"""
		time.sleep(waitBeforeAnnouncement) 	# Give some time until remote CSE fully connected
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleRemoteCSEHasDeregistered(self, remoteCSR:Resource) -> None:
		""" Handle de-registrations when a remote CSE has de-registered (registree CSE).
		"""
		#self.checkResourcesForUnAnnouncement(remoteCSR)	# TODO remove this for new Announcement behaviour+
		pass



	#########################################################################
	#
	#	Access Methods to check, announce, unanounce etc
	#

	#
	#	Announcements
	#

	def checkResourcesForAnnouncement(self, remoteCSR:Resource) -> Result:
		"""	Check all resources and announce them if necessary.
		"""
		if not remoteCSR:
			return Result(status=True)

		# get all reources for this specific CSI that are NOT announced to it yet
		resources = self.searchAnnounceableResourcesForCSI(remoteCSR.csi, False) # only return the resources that are *not* announced to this csi yet
		# try to announce all not-announced resources to this csr
		for resource in resources:
			if not (res := self.announceResource(resource)).status:
				return res
		return Result(status=True)


	def announceResource(self, resource:AnnounceableResource) -> Result:
		"""	Announce a single resource to its announcement targets.
		"""
		L.isDebug and L.logDebug(f'Announce resource: {resource.ri} to all connected csr')
		for at in resource.at:
			if at == CSE.cseCsi or at.startswith(CSE.cseCsiSlash):
				L.isWarn and L.logWarn('Targeting own CSE. Ignored.')
				self._removeAnnouncementFromResource(resource, at)
				continue
			self.announceResourceToCSI(resource, at)	# ignore result
		return Result(status=True)


	def announceResourceToCSI(self, resource:AnnounceableResource, csi:str) -> Result:
		"""	Announce a resource to a specific CSR.
		"""
		# TODO direct URL

		def checkCSEBaseAnnouncement(cseBase:AnnounceableResource) -> Result:
			if t := self._announcedInfos(cseBase, csi):
				# CSEBase has "old" announcement infos
				if CSE.dispatcher.retrieveResource(f'{csi}/{t[1]}', CSE.cseCsi).rsc != RC.OK:	# Not a local resource
					# No, it's not there anymore -> announce it again.
					self._removeAnnouncementFromResource(cseBase, csi)
					# announce CSE recursively
					if not (res := self.announceResourceToCSI(cseBase, csi)).status:	# Don't ignore result for this one
						return res
			else:

				# No internal announcement infos, try to discover it on the remote CSE.
				# This is done by discovering a CSEBaseAnnc resource with a link to our CSE.
				req = RequestUtils.createRawRequest(
						to = csi,
						rcn = ResultContentType.childResourceReferences.value,
						drt = DesiredIdentifierResultType.unstructured.value,
						fc = {	'ty' : T.CSEBaseAnnc.value,
								'lnk' : f'{cseBase.csi}/{cseBase.ri}'
							 }
						)
				if not (res := CSE.request.sendRetrieveRequest(csi, originator = CSE.cseCsi, data = req, raw = True)).status:
					return res
				if res.rsc == RC.OK and res.data:	# Found a remote CSEBaseAnnc
					# Assign to the local CSEBase
					if (ri := Utils.findXPath(cast(dict, res.data), 'm2m:rrl/rrf/{0}/val')):
						atri = f'{csi}/{ri}'
						L.isDebug and L.logDebug(f'CSEBase already announced: {atri}. Updating CSEBase announcement')
						cseBase.addAnnouncementToResource(csi, ri)
						# !! CSEBase has no (exposed) at attribute, therefore the following code shall not
						# !! be run for the CSEBase. Only the internal attribute is updated (previous code line).
						# at:list[str] = cseBase.attribute('at', [])
						# at.append(atri)
						# cseBase.setAttribute('at', at)
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
			return Result(status=True)

		# Create announced resource & type
		data = resource.createAnnouncedResourceDict(isCreate = True)
		tyAnnc = T(resource.ty).announced()
		targetID = ''

		if resource.ty != T.CSEBase:	# CSEBase is just announced below
			if not (at := resource.at):
				L.isDebug and L.logDebug('at attribute is empty.')
				return Result(status=True)	# Not much to do here

			# Check if parent is announced already to the same remote CSE
			if not (res := CSE.dispatcher.retrieveLocalResource(resource.pi)).status:
				L.logErr(dbg := f'Cannot retrieve parent. Announcement not possible: {res.dbg}')
				return Result(status=False, rsc=RC.internalServerError, dbg=dbg)
			
			parentResource = res.resource

			# For announcing the CSEBase we want to take some extra care and check whether it really
			# is available at the remote CSE. It could have been removed (expiration, restart, ...) and
			# this may not be reflected
			if parentResource.ty == T.CSEBase:
				if not (res := checkCSEBaseAnnouncement(parentResource)).status:
					return res
				parentResource.dbReload() 	# parent is already the CSEBase, just reload from DB

			else:	# parent is not a CSEBase
				if not self._isResourceAnnouncedTo(parentResource, csi):
					L.isDebug and L.logDebug(f'Parent resource is not announced: {parentResource.ri}')
					# parent resource is not announced -> announce the resource directly under the CSEBaseAnnc

					# Don't allow instances to be announced without their parents
					if resource.ty in [T.CIN, T.FCI, T.TSI]:
						L.logDebug(dbg := 'Announcing instances without their parents is not allowed')
						return Result(status=False, rsc=RC.operationNotAllowed, dbg=dbg)

					# Whatever the parent resource is, check whether the CSEBase has been announced. Announce it if necessay
					if not (res := checkCSEBaseAnnouncement(Utils.getCSE().resource)).status:
						return res
					parentResource = Utils.getCSE().resource	# set the announced CSEBase as new parent
					
					# ... then continue with normale announcement of the resource. The parent for the announcement is now the CSEBase
				
			# parent resource is announced -> Announce the resource under the parent resource Annc
			if not (at := self._announcedInfos(parentResource, csi)):
				L.logWarn(dbg := f'No announcement for parent resource: {parentResource.ri} to: {csi}')
				return Result(status=False, rsc=RC.badRequest, dbg=dbg)
			targetID = f'/{at[1]}'

		# Create the announed resource on the remote CSE
		spRi = f'{csi}{targetID}'
		L.isDebug and L.logDebug(f'Creating announced resource at: {csi} ID: {spRi}')	
		res = CSE.request.sendCreateRequest(csi, CSE.cseCsi, appendID = spRi, ty = tyAnnc, data = data)
		if res.rsc not in [ RC.created, RC.OK ]:
			if res.rsc != RC.conflict:	# assume that it is ok if the remote resource already exists 
				L.logDebug(dbg := f'Error creating remote announced resource: {int(res.rsc)} ({res.dbg})')
				return Result(status = False, rsc = res.rsc, dbg = dbg)
		else:
			resource.addAnnouncementToResource(csi, Utils.findXPath(cast(JSON, res.data), '{0}/ri'))
		L.isDebug and L.logDebug(f'Announced resource created: {resource.getAnnouncedTo()}')
		resource.dbUpdate()
		return Result(status=True)


	#
	#	De-Announcements
	#

	def checkResourcesForUnAnnouncement(self, remoteCSR:Resource) -> None:
		"""	Check whether resources need announcements and initiate announcement
			if they are.
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
		"""	De-announce a single resource from its announcement targets.
		"""
		L.isDebug and L.logDebug(f'De-Announce resource: {resource.ri} from all connected csr')

		for (csi, remoteRI) in resource.getAnnouncedTo():
			self.deAnnounceResourceFromCSI(resource, csi, remoteRI)


	def deAnnounceResourceFromCSI(self, resource:AnnounceableResource, csi:str, remoteRI:str) -> None:
		"""	De-Announce a resource from a specific CSR.
		"""

		spRi = f'{csi}/{remoteRI}'
		# Delete the announed resource from the remote CSE
		L.isDebug and L.logDebug(f'Delete announced resource: {spRi}')	
		res = CSE.request.sendDeleteRequest(csi, CSE.cseCsi, appendID = spRi)
		if res.rsc not in [ RC.deleted, RC.OK ]:
			L.isDebug and L.logDebug(f'Error deleting remote announced resource: {res.rsc}')
			# ignore the fact that we cannot delete the announced resource.
			# fall-through for some house-keeping
		self._removeAnnouncementFromResource(resource, csi)
		L.isDebug and L.logDebug('Announced resource deleted')
		resource.dbUpdate()


	#
	#	Update Announcements
	#


	def announceUpdatedResource(self, resource:AnnounceableResource, originator:str) -> None:
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
		ot = f'{originator}/'
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


	def updateResourceOnCSI(self, resource:Resource, csi:str, remoteRI:str) -> None:
		"""	Update an announced resource to a specific CSR.
		"""
		data = resource.createAnnouncedResourceDict(isCreate = False)
		spRi = f'{csi}/{remoteRI}'

		# Create the announed resource on the remote CSE
		L.isDebug and L.logDebug(f'Updating announced resource at: {spRi}')	
		res = CSE.request.sendUpdateRequest(csi, CSE.cseCsi, data = data, appendID = spRi)
		if res.rsc not in [ RC.updated, RC.OK ]:
			L.isDebug and L.logDebug(f'Error updating remote announced resource: {int(res.rsc)}')
			# Ignore and fallthrough
		L.isDebug and L.logDebug('Announced resource updated')


	def _removeAnnouncementFromResource(self, resource:Resource, csi:str) -> None:
		"""	Remove announcement details from a resource (internal attribute).
			Modify the internal as well the at attributes to remove the reference
			to the remote CSE.
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
		"""	Check whether a resource is announced. This is done by looking at the entries in the
			internal "__announcedTo__" attribute, ie. whether they will contain the `csi`.
			"""
		return (at := resource.getAnnouncedTo()) is not None and any(csi == _csi for (_csi, _) in at)
	

	def _announcedInfos(self, resource:Resource, csi:str) -> Optional[Tuple[str, str]]:
		"""	Return the matching tuple for the given `csi` of a resource announcement,
			or None if none is set.
		"""
		if at := resource.getAnnouncedTo():
			for _at in at:
				if _at[0] == csi:
					return _at
		return None


	def announceResourceViaDirectURL(self, resource: Resource, at: str) -> bool:
		"""	Announce a resource via a direct URL, nit via a csi.
		"""
		L.logErr('TODO Direct Announcement')
		return False


	#########################################################################
	#
	#	Utilities
	#

	def searchAnnounceableResourcesForCSI(self, csi:str, isAnnounced:bool) -> list[AnnounceableResource]:
		""" Search and retrieve all resources that have the provided CSI in their 
			'at' attribute. Also, distinguish between announced and not announced resources in the filter.
		"""

		mcsi = f'{csi}/'
		def _announcedFilter(r:JSON) -> bool:
			if (at := r.get('at')) and len(list(filter(lambda x: x.startswith(mcsi), at))) > 0:	# check whether any entry in 'at' startswith mcsi
				if ato := r.get(Resource._announcedTo):
					for i in ato:
						if csi == i[0]:	# 0=remote csi,
							return isAnnounced
					return not isAnnounced
			return False

		return cast(List[AnnounceableResource], CSE.storage.searchByFilter(_announcedFilter))


