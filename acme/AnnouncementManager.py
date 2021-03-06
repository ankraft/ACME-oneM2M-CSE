#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

import time, traceback
from copy import deepcopy
from typing import Tuple, List
from Logging import Logging
import Utils, CSE
from Configuration import Configuration
from resources.Resource import Resource
from resources.AnnouncedResource import AnnouncedResource
from resources.AnnounceableResource import AnnounceableResource
from Constants import Constants as C
from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from helpers.BackgroundWorker import BackgroundWorkerPool

# TODO for anounceable resource:
# - update: update resource here

waitBeforeAnnouncement = 3

class AnnouncementManager(object):

	def __init__(self) -> None:
		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.handleRegisteredToRemoteCSE)			# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.handleDeRegisteredFromRemoteCSE)	# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasRegistered, self.handleRemoteCSEHasRegistered)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasDeregistered, self.handleRemoteCSEHasDeregistered)	# type: ignore
		
		# Configuration values
		self.checkInterval			= Configuration.get('cse.announcements.checkInterval')
		self.announcementsEnabled 	= Configuration.get('cse.announcements.enable')

		self.start()
		Logging.log('AnnouncementManager initialized')


	def shutdown(self) -> bool:
		self.stop()
		if CSE.remote is not None:
			for csr in CSE.remote.getAllLocalCSRs():
				if csr is not None:
					self.checkResourcesForUnAnnouncement(csr)
		Logging.log('AnnouncementManager shut down')
		return True

	#
	#	Announcement Monitor
	#

	# Start the monitor in a thread. 
	def start(self) -> None:
		if not self.announcementsEnabled:
			return
		Logging.log('Starting Announcements monitor')
		BackgroundWorkerPool.newWorker(self.checkInterval, self.announcementMonitorWorker, 'anncMonitor').start()


	# Stop the monitor. Also delete the CSR resources on both sides
	def stop(self) -> None:
		if not self.announcementsEnabled:
			return
		Logging.log('Stopping Announcements monitor')
		# Stop the thread
		BackgroundWorkerPool.stopWorkers('anncMonitor')


	def announcementMonitorWorker(self) -> bool:
		Logging.logDebug('Checking announcements to remote CSEs')

		# check all CSR
		for csr in CSE.remote.getAllLocalCSRs():
			self.checkResourcesForAnnouncement(csr)
		return True



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
		self.checkResourcesForUnAnnouncement(remoteCSR)


	def handleRemoteCSEHasRegistered(self, remoteCSR:Resource) -> None:
		"""	Handle registrations when a remote CSE has registered (registree CSE).
		"""
		time.sleep(waitBeforeAnnouncement) 	# Give some time until remote CSE fully connected
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleRemoteCSEHasDeregistered(self, remoteCSR:Resource) -> None:
		""" Handle de-registrations when a remote CSE has de-registered (registree CSE).
		"""
		self.checkResourcesForUnAnnouncement(remoteCSR)





	#########################################################################
	#
	#	Access Methods to check, announce, unanounce etc
	#

	#
	#	Announcements
	#

	def checkResourcesForAnnouncement(self, remoteCSR:Resource) -> None:
		"""	Check all resources and announce them if necessary.
		"""
		if not self.announcementsEnabled:
			return
		if remoteCSR is None:
			return
		csi = remoteCSR.csi

		# get all reources for this specific CSI that are NOT announced to it yet
		resources = CSE.storage.searchAnnounceableResourcesForCSI(csi, False) # only return the resources that are *not* announced to this csi yet
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.announceResource(resource)


	def announceResource(self, resource:AnnounceableResource) -> None:
		"""	Announce a single resource to its announcement targets.
		"""

		if not self.announcementsEnabled:
			return
		Logging.logDebug(f'Announce resource: {resource.ri} to all connected csr')
		for csi in resource.at:
			if csi == CSE.cseCsi or csi.startswith(f'{CSE.cseCsi}/'):
				Logging.logWarn('Targeting own CSE. Ignored.')
				self._removeAnnouncementFromResource(resource, csi)
				continue
			if (csr := Utils.resourceFromCSI(csi)) is None:
				Logging.logWarn('Announcement Target CSE not found. Ignored.')
				self._removeAnnouncementFromResource(resource, csi)
				continue
			# if (remoteCSR := CSE.remote.getCSRForRemoteCSE(csr)) is None:	# not yet registered
			# 	continue
			self.announceResourceToCSR(resource, csr)


	def announceResourceToCSR(self, resource:AnnounceableResource, remoteCSR:Resource) -> None:
		"""	Announce a resource to a specific CSR.
		"""

		# retrieve the csi & poas for the remote CSR
		csi, poas = self._getCsiPoaForRemoteCSR(remoteCSR)


		# TODO: multi-hop announcement

		Logging.logDebug(f'Announce resource: {resource.ri} to: {csi}')

		if (at := resource.at) is None or len(at) == 0:
			Logging.logWarn('at attribute is empty')
			return
		if csi not in at:
			Logging.logWarn(f'CSI: {csi} not found for at: {at}')
			return

		# Create announced resource & type
		data = resource.createAnnouncedResourceDict(remoteCSR, isCreate=True, csi=csi)
		tyAnnc = T(resource.ty).announced()

		# Get target URL for request
		if poas is not None and len(poas) > 0:
			poa = poas[0]						# Only first POA
			url = f'{poa}{CSE.cseCsi}'			# remote CSR is always own csi
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Create the announed resource on the remote CSE
		Logging.logDebug(f'Creating announced resource at: {csi} url: {url}')	
		res = CSE.request.sendCreateRequest(url, CSE.cseCsi, ty=tyAnnc, data=data)
		if res.rsc not in [ RC.created, RC.OK ]:
			if res.rsc != RC.alreadyExists:	# assume that it is ok if the remote resource already exists 
				Logging.logDebug(f'Error creating remote announced resource: {res.rsc:d}')
				if (at := resource.at) is not None and len(at) > 0 and csi in at:
					at.remove(csi)
					if len(at) == 0:
						resource.setAttribute('at', None)
					else:
						resource.setAttribute('at', at)
				return
		else:
			self._addAnnouncementToResource(resource, res.dict, csi)
		Logging.logDebug('Announced resource created')
		resource.dbUpdate()


	#
	#	De-Announcements
	#

	def checkResourcesForUnAnnouncement(self, remoteCSR:Resource) -> None:
		"""	Check whether resources need announcements and initiate announcement
			if they are.
		"""
		if not self.announcementsEnabled:
			return
		csi = remoteCSR.csi
		Logging.logDebug(f'Checking resources for Unannouncement to: {csi}')
		# get all reources for this specific CSI that are NOT announced to it yet
		resources = CSE.storage.searchAnnounceableResourcesForCSI(csi, True)
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.deAnnounceResource(resource)
			self._removeAnnouncementFromResource(resource, csi)
			resource.dbUpdate()



	def deAnnounceResource(self, resource:AnnounceableResource) -> None:
		"""	De-announce a single resource from its announcement targets.
		"""
		if not self.announcementsEnabled:
			return
		Logging.logDebug(f'De-Announce resource: {resource.ri} from all connected csr')

		for (csi, remoteRI) in resource[Resource._announcedTo]:
			if (csr := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			# if (remoteCSR := CSE.remote.getCSRForRemoteCSE(csr)) is None:	# not yet registered
			# 	continue
			self.deAnnounceResourceFromCSR(resource, csr, remoteRI)


	def deAnnounceResourceFromCSR(self, resource:AnnounceableResource, remoteCSR:Resource, resourceRI:str) -> None:
		"""	De-Announce a resource from a specific CSR.
		"""

		# retrieve the cse & poas for the remote CSR
		csi, poas = self._getCsiPoaForRemoteCSR(remoteCSR)

		# TODO: multi-hop announcement

		Logging.logDebug(f'De-Announce remote resource: {resource.ri} from: {csi}')

		# Get target URL for request
		if poas is not None and len(poas) > 0:
			url = f'{poas[0]}/{resourceRI}'	# TODO check all available poas. remote CSR is always own csi
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Delete the announed resource from the remote CSE
		Logging.logDebug(f'Delete announced resource from: %{csi} url: {url}')	
		res = CSE.request.sendDeleteRequest(url, CSE.cseCsi)
		if res.rsc not in [ RC.deleted, RC.OK ]:
			Logging.logDebug(f'Error deleting remote announced resource: {res.rsc}')
			# ignore the fact that we cannot delete the announced resource.
			# fall-through for some house-keeping
		self._removeAnnouncementFromResource(resource, csi)
		Logging.logDebug('Announced resource deleted')
		resource.dbUpdate()


	#
	#	Update Announcements
	#


	def announceUpdatedResource(self, resource:AnnounceableResource) -> None:
		if not self.announcementsEnabled:
			return
		Logging.logDebug(f'Updating announced resource: {resource.ri}')

		# Check for removed AT
		# Logging.logErr(set(self._origAT))
		# Logging.logErr(set(self.at))
		# Logging.logErr(set(self.at) == set(self._origAT))


		# get all reources for this specific CSI that are  announced to it yet
		at = deepcopy(resource.at)
		CSIsFromAnnounceTo = []
		for announcedResource in at:
			if len(sp := announcedResource.split('/')) >= 2:
				if (csi := f'/{sp[1]}') == CSE.cseCsi or csi.startswith(f'{CSE.cseCsi}/'):	# Ignore own CSE as target
					continue
				CSIsFromAnnounceTo.append(csi)

		announcedCSIs = []
		remoteRIs = []
		for (csi, remoteRI) in resource[Resource._announcedTo]:
			announcedCSIs.append(csi) # build a list of already announced CSIs
			remoteRIs.append(csi) # build a list of remote RIs

			# CSR still connected?
			if (csr := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			
			# remote csi still in at? If not then remove it
			if csi not in CSIsFromAnnounceTo:
				self.deAnnounceResourceFromCSR(resource, csr, remoteRI)
				continue

			# if (remoteCSR := CSE.remote.getCSRForRemoteCSE(csr)) is None:	# not yet registered
			# 	continue
			self.updateResourceOnCSR(resource, csr, remoteRI)

		# Check for any non-announced csi in at, and possibly announce them 
		for csi in CSIsFromAnnounceTo:
			if csi not in announcedCSIs and csi not in remoteRIs:
				if (csr := Utils.resourceFromCSI(csi)) is None:
					continue
				self.announceResourceToCSR(resource, csr)


	def updateResourceOnCSR(self, resource:Resource, remoteCSR:Resource, remoteRI:str) -> None:
		"""	Update an announced resource to a specific CSR.
		"""

		# retrieve the cse & poas for the remote CSR
		csi, poas = self._getCsiPoaForRemoteCSR(remoteCSR)


		# TODO: multi-hop announcement

		Logging.logDebug(f'Update announced resource: {resource.ri} to: {csi}')

		data = resource.createAnnouncedResourceDict(remoteCSR, isCreate=False, csi=csi)

		# Get target URL for request
		if poas is not None and len(poas) > 0:
			url = f'{poas[0]}/{remoteRI}'	# TODO check all available poas.
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Create the announed resource on the remote CSE
		Logging.logDebug(f'Updating announced resource at: {csi} url: {url}')	
		res = CSE.request.sendUpdateRequest(url, CSE.cseCsi, data=data)
		if res.rsc not in [ RC.updated, RC.OK ]:
			Logging.logDebug(f'Error updating remote announced resource: {res.rsc:d}')
			# Ignore and fallthrough
		Logging.logDebug('Announced resource updated')


	def _getCsiPoaForRemoteCSR(self, remoteCSR:Resource) -> Tuple[str,List[str]]:
		"""	This function returns the correct csi and poas for the provided remoteCSR
			resource. This is different for getting it for the registrar CSE and for
			the descendant CSE's. In case of a descendant CSR all the information are
			there, but in case of own's CSR we need to get the information from the
			registrar CSE)
		"""
		csi  = remoteCSR.csi
		poas = remoteCSR.poa
		if csi == CSE.cseCsi:	# own registrar
			if CSE.remote.registrarCSE is not None:
				csi = CSE.remote.registrarCSE.csi
				poas = CSE.remote.registrarCSE.poa
		return csi, poas


	def _addAnnouncementToResource(self, resource:Resource, dct:JSON, csi:str) -> None:
		"""	Add anouncement information to the resource. These are a list of tuples of 
			the csi to which the resource is registered as well as the ri of the 
			resource on the remote CSE. Also, add the reference in the at attribute.
		"""
		remoteRI = Utils.findXPath(dct, '{0}/ri')
		ats = resource[Resource._announcedTo]
		ats.append((csi, remoteRI))
		resource.setAttribute(Resource._announcedTo, ats)

		# Modify the at attribute
		if len(at := resource.at) > 0 and csi in at:
			at[at.index(csi)] = f'{csi}/{remoteRI}' # replace the element in at
			resource.setAttribute('at', at)


	def _removeAnnouncementFromResource(self, resource:Resource, csi:str) -> None:
		"""	Remove announcement details from a resource (internal attribute).
			Modify the internal as well the at attributes to remove the reference
			to the remote CSE.
		"""
		ats = resource[Resource._announcedTo]
		remoteRI:str = None
		for x in ats:
			if x[0] == csi:
				remoteRI = x[1]
				ats.remove(x)
				resource.setAttribute(Resource._announcedTo, ats)

		# # Modify the at attribute
		if remoteRI is not None:
			atCsi = f'{csi}/{remoteRI}'
			if (at := resource.at) is not None and len(at) > 0 and atCsi in at:
				at.remove(atCsi)
				resource.setAttribute('at', at)


	def announceResourceViaDirectURL(self, resource: Resource, at: str) -> bool:
		"""	Announce a resource via a direct URL, nit via a csi.
		"""
		Logging.logErr('TODO Direct Announcement')
		return False

