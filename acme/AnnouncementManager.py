#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

import json, time, traceback
from typing import Tuple, List
from Logging import Logging
import Utils, CSE
from Configuration import Configuration
from resources.Resource import Resource
from resources.AnnouncedResource import AnnouncedResource
from Constants import Constants as C
from Types import ResourceTypes as T
from helpers.BackgroundWorker import BackgroundWorker

# TODO for anounceable resource:
# - update: update resource here

waitBeforeAnnouncement = 3

class AnnouncementManager(object):

	def __init__(self) -> None:
		self.worker:BackgroundWorker			= None

		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.handleRegisteredToRemoteCSE)			# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.handleDeRegisteredFromRemoteCSE)	# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasRegistered, self.handleRemoteCSEHasRegistered)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasDeregistered, self.handleRemoteCSEHasDeregistered)	# type: ignore
		
		# TODO self.checkInterval						= Configuration.get('cse.announcements.checkInterval')
		self.checkInterval			= Configuration.get('cse.announcements.checkInterval')
		self.announcementsEnabled 	= Configuration.get('cse.announcements.enable')

		self.start()
		Logging.log('AnnouncementManager initialized')


	def shutdown(self) -> None:
		self.stop()
		if CSE.remote is not None:
			for csr in CSE.remote.getAllLocalCSRs():
				if csr is not None:
					self.checkResourcesForUnAnnouncement(csr)
		Logging.log('AnnouncementManager shut down')

	#
	#	Announcement Monitor
	#

	# Start the monitor in a thread. 
	def start(self) -> None:
		if not self.announcementsEnabled:
			return
		Logging.log('Starting Announcements monitor')
		self.worker = BackgroundWorker(self.checkInterval, self.announcementMonitorWorker, 'anncMonitor')
		self.worker.start()


	# Stop the monitor. Also delete the CSR resources on both sides
	def stop(self) -> None:
		if not self.announcementsEnabled:
			return
		Logging.log('Stopping Announcements monitor')
		# Stop the thread
		if self.worker is not None:
			self.worker.stop()


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

	def handleRegisteredToRemoteCSE(self, remoteCSE:Resource, remoteCSR: Resource) -> None:
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



		# Logging.logDebug('Checking resources for Announcement to: %s' % csi)
		# # get all reources for this specific CSI that are NOT announced to it yet
		# resources = CSE.storage.searchAnnounceableResourcesForCSI(csi, False) # only return the resources that are *not* announced to this csi yet
		# # try to announce all not-announced resources to this csr
		# for resource in resources:
		# 	self.announceResourceToCSR(resource, remoteCSR)


	def announceResource(self, resource:Resource) -> None:
		"""	Announce a single resource to its announcement targets.
		"""
		if not self.announcementsEnabled:
			return
		Logging.logDebug('Announce resource: %s to all connected csr' % resource.ri)
		for csi in resource.at:
			if csi == CSE.remote.cseCsi or csi.startswith('%s/' % CSE.remote.cseCsi):
				Logging.logWarn('Targeting own CSE. Ignored.')
				continue
			if (csr := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			# if (remoteCSR := CSE.remote.getCSRForRemoteCSE(csr)) is None:	# not yet registered
			# 	continue
			self.announceResourceToCSR(resource, csr)


	def announceResourceToCSR(self, resource:Resource, remoteCSR:Resource) -> None:
		"""	Announce a resource to a specific CSR.
		"""

		# retrieve the csi & poas for the remote CSR
		csi, poas = self._getCsiPoaForRemoteCSR(remoteCSR)


		# TODO: multi-hop announcement

		Logging.logDebug('Announce resource: %s to: %s' % (resource.ri, csi))

		if (at := resource.at) is None or len(at) == 0:
			Logging.logWarn('at attribute is empty')
			return
		if csi not in at:
			Logging.logWarn('CSI: %s not found for at: %s' % (csi,at))
			return

		# Create announced json & type
		data = resource.createAnnouncedResourceJSON(remoteCSR, isCreate=True, csi=csi)
		tyAnnc = T(resource.ty).announced()

		# Get target URL for request
		if poas is not None and len(poas) > 0:
			poa = poas[0]												# Only first POA
			#url = '%s/~%s%s' % (poa, csi, CSE.remote.cseCsi)			# remote CSR is always own csi
			url = '%s%s' % (poa, CSE.remote.cseCsi)			# remote CSR is always own csi
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Create the announed resource on the remote CSE
		Logging.logDebug('Creating announced resource at: %s url: %s' % (csi, url))	
		jsn, rc, msg = CSE.httpServer.sendCreateRequest(url, CSE.remote.originator, ty=tyAnnc, data=json.dumps(data))
		if rc not in [C.rcCreated, C.rcOK]:
			if rc != C.rcAlreadyExists:
				Logging.logDebug('Error creating remote announced resource: %d' % rc)
				return
		else:
			self._addAnnouncementToResource(resource, jsn, csi)
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
		Logging.logDebug('Checking resources for Unannouncement to: %s' % csi)
		# get all reources for this specific CSI that are NOT announced to it yet
		resources = CSE.storage.searchAnnounceableResourcesForCSI(csi, True)
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.deAnnounceResource(resource)
			self._removeAnnouncementFromResource(resource, csi)
			resource.dbUpdate()



	def deAnnounceResource(self, resource:Resource) -> None:
		"""	De-announce a single resource from its announcement targets.
		"""
		if not self.announcementsEnabled:
			return
		Logging.logDebug('De-Announce resource: %s from all connected csr' % resource.ri)

		for (csi, remoteRI) in resource[Resource._announcedTo]:
			if (csr := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			# if (remoteCSR := CSE.remote.getCSRForRemoteCSE(csr)) is None:	# not yet registered
			# 	continue
			self.deAnnounceResourceFromCSR(resource, csr, remoteRI)



	def deAnnounceResourceFromCSR(self, resource:Resource, remoteCSR:Resource, resourceRI:str) -> None:
		"""	De-Announce a resource from a specific CSR.
		"""

		# retrieve the cse & poas for the remote CSR
		csi, poas = self._getCsiPoaForRemoteCSR(remoteCSR)

		# TODO: multi-hop announcement

		Logging.logDebug('De-Announce remote resource: %s from: %s' % (resource.ri, csi))

		# Get target URL for request
		if poas is not None and len(poas) > 0:
			# url = '%s/~%s/%s' % (poa, csi, resourceRI)	# TODO check all available poas. remote CSR is always own csi
			url = '%s/%s' % (poas[0],resourceRI)	# TODO check all available poas. remote CSR is always own csi
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Delete the announed resource from the remote CSE
		Logging.logDebug('Delete announced resource from: %s url: %s' % (csi, url))	
		jsn, rc, msg = CSE.httpServer.sendDeleteRequest(url, CSE.remote.originator)
		if rc not in [C.rcDeleted, C.rcOK]:
			if rc != C.rcAlreadyExists:
				Logging.logDebug('Error deleting remote announced resource: %d' % rc)
				# ignore the fact that we cannot delete the announced resource.
				# fall-through for some house-keeping
		self._removeAnnouncementFromResource(resource, csi)
		Logging.logDebug('Announced resource deleted')
		resource.dbUpdate()


	#
	#	Update Announcements
	#


	def announceUpdatedResource(self, resource:Resource) -> None:
		if not self.announcementsEnabled:
			return
		Logging.logDebug('Updating announced resource: %s' % resource.ri)
		# get all reources for this specific CSI that are  announced to it yet

		for (csi, remoteRI) in resource[Resource._announcedTo]:
			if (csr := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			# if (remoteCSR := CSE.remote.getCSRForRemoteCSE(csr)) is None:	# not yet registered
			# 	continue
			self.updateResourceOnCSR(resource, csr, remoteRI)


	def updateResourceOnCSR(self, resource:Resource, remoteCSR:Resource, remoteRI:str) -> None:
		"""	Update an announced resource to a specific CSR.
		"""

		# retrieve the cse & poas for the remote CSR
		csi, poas = self._getCsiPoaForRemoteCSR(remoteCSR)


		# TODO: multi-hop announcement

		Logging.logDebug('Update announced resource: %s to: %s' % (resource.ri, csi))

		data = resource.createAnnouncedResourceJSON(remoteCSR, isCreate=False, csi=csi)
		tyAnnc = T(resource.ty).announced()

		# Get target URL for request
		if poas is not None and len(poas) > 0:
			# url = '%s/~%s/%s' % (poas[0], csi, remoteRI)	# TODO check all available poas.
			url = '%s/%s' % (poas[0], remoteRI)	# TODO check all available poas.
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Create the announed resource on the remote CSE
		Logging.logDebug('Updating announced resource at: %s url: %s' % (csi, url))	
		jsn, rc, msg = CSE.httpServer.sendUpdateRequest(url, CSE.remote.originator, data=json.dumps(data))
		if rc not in [C.rcUpdated, C.rcOK]:
			if rc != C.rcAlreadyExists:
				Logging.logDebug('Error updating remote announced resource: %d' % rc)

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
		if csi == CSE.remote.cseCsi:	# own registrar
			if CSE.remote.registrarCSE is not None:
				csi = CSE.remote.registrarCSE.csi
				poas = CSE.remote.registrarCSE.poa
		return csi, poas


	def _addAnnouncementToResource(self, resource:Resource, jsn:dict, csi:str) -> None:
		"""	Add anouncement information to the resource. These are a list of tuples of 
			the csi to which the resource is registered as well as the ri of the 
			resource on the remote CSE. Also, add the reference in the at attribute.
		"""
		remoteRI = Utils.findXPath(jsn, '{0}/ri')
		ats = resource[Resource._announcedTo]
		ats.append((csi, remoteRI))
		resource.setAttribute(Resource._announcedTo, ats)

		# Modify the at attribute
		if len(at := resource.at) > 0 and csi in at:
			at.append('%s/%s' %(csi, remoteRI))
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
			atCsi = '%s/%s' %(csi, remoteRI)
			if len(at := resource.at) > 0 and atCsi in at:
				at.remove(atCsi)
				resource.setAttribute('at', at)


	def announceResourceViaDirectURL(self, resource: Resource, at: str) -> bool:
		"""	Announce a resource via a direct URL, nit via a csi.
		"""
		Logging.logErr('TODO Direct Announcement')
		return False

