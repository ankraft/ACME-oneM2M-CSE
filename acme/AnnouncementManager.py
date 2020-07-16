#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

import json, time, traceback
from Logging import Logging
import Utils, CSE
from resources.Resource import Resource
from resources.AnnouncedResource import AnnouncedResource
from Constants import Constants as C
from Types import ResourceTypes as T
from helpers.BackgroundWorker import BackgroundWorker

# TODO for anounceable resource:
# - update: update resource here



class AnnouncementManager(object):

	def __init__(self) -> None:
		self.worker:BackgroundWorker			= None

		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.handleRegisteredToRemoteCSE)			# type: ignore
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.handleDeRegisteredFromRemoteCSE)	# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasRegistered, self.handleRemoteCSEHasRegistered)			# type: ignore
		CSE.event.addHandler(CSE.event.remoteCSEHasDeregistered, self.handleRemoteCSEHasDeregistered)	# type: ignore
		
		# TODO self.checkInterval						= Configuration.get('cse.announcements.checkInterval')
		self.checkInterval	= 10
		self.start()
		Logging.log('AnnouncementManager initialized')


	def shutdown(self) -> None:
		self.stop()
		if CSE.remote is not None:
			for csr in CSE.remote.getAllLocalCSRs():
				if csr is not None:
					self.checkResourcesForDeAnnouncement(csr)
		Logging.log('AnnouncementManager shut down')

	#
	#	Announcement Monitor
	#

	# Start the monitor in a thread. 
	def start(self) -> None:
		# TODO
		#if not Configuration.get('cse.enableAnnouncements'):
		#	return;
		Logging.log('Starting Announcements monitor')
		self.worker = BackgroundWorker(self.checkInterval, self.announcementMonitorWorker, 'anncMonitor')
		self.worker.start()


	# Stop the monitor. Also delete the CSR resources on both sides
	def stop(self) -> None:
		# TODO
		# if not Configuration.get('cse.enableAnnouncements'):
		# 	return;
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
		#time.sleep(5) # TODO configurable? Or wait for something?
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleDeRegisteredFromRemoteCSE(self, remoteCSR:Resource) -> None:
		self.checkResourcesForDeAnnouncement(remoteCSR)


	def handleRemoteCSEHasRegistered(self, remoteCSR:Resource) -> None:
		self.checkResourcesForAnnouncement(remoteCSR)


	def handleRemoteCSEHasDeregistered(self, remoteCSR:Resource) -> None:
		self.checkResourcesForDeAnnouncement(remoteCSR)





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
		if remoteCSR is None:
			return
		csi = remoteCSR.csi
		Logging.logDebug('Checking resources for Announcement to: %s' % csi)
		# get all reources for this specific CSI that are NOT announced to it yet
		resources = CSE.storage.searchAnnounceableResourcesForCSI(csi, False) # only return the resources that are *not* announced to this csi yet
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.announceResourceToCSR(resource, remoteCSR)


	def announceResource(self, resource:Resource) -> None:
		"""	Announce a single resource to its announcement targets.
		"""
		Logging.logDebug('Announce resource: %s to all connected csr' % resource.ri)
		for csi in resource.at:
			if (remoteCSE := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			if (remoteCSR := CSE.remote.getCSRForRemoteCSE(remoteCSE)) is None:	# not yet registered
				continue
			self.announceResourceToCSR(resource, remoteCSR)


	def announceResourceToCSR(self, resource:Resource, remoteCSR:Resource) -> None:
		"""	Announce a resource to a specific CSR.
		"""
		csi  = remoteCSR.csi
		poas = remoteCSR.poa

		# TODO: multi-hop announcement

		Logging.logDebug('Announce resource: %s to: %s' % (resource.ri, csi))

		if (at := resource.at) is None or len(at) == 0:
			Logging.logWarn('at attribute is empty')
			return
		if csi not in at:
			Logging.logWarn('CSI: %s not found for at: %s' % (csi,at))
			return

		# Create announced json & type
		data = resource.createAnnouncedResourceJSON()
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
		else:
			ats = resource[Resource._announcedTo]
			ats.append((csi, Utils.findXPath(jsn, '{0}/ri')))
			resource.setAttribute(Resource._announcedTo, ats)
		Logging.logDebug('Announced resource created')
		resource.dbUpdate()


	#
	#	De-Announcements
	#

	def checkResourcesForDeAnnouncement(self, remoteCSR:Resource) -> None:
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
		Logging.logDebug('De-Announce resource: %s from all connected csr' % resource.ri)

		for (csi, remoteRI) in resource[Resource._announcedTo]:
			if (remoteCSE := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			if (remoteCSR := CSE.remote.getCSRForRemoteCSE(remoteCSE)) is None:	# not yet registered
				continue
			self.deAnnounceResourceFromCSR(resource, remoteCSR, remoteRI)



	def deAnnounceResourceFromCSR(self, resource:Resource, remoteCSR:Resource, resourceRI:str) -> None:
		"""	De-Announce a resource from a specific CSR.
		"""
		csi  = remoteCSR.csi
		poas = remoteCSR.poa
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
		self._removeAnnouncementFromResource(resource, csi)
		Logging.logDebug('Announced resource deleted')
		resource.dbUpdate()


	#
	#	Update Announcements
	#


	def announceUpdatedResource(self, resource:Resource) -> None:
		Logging.logDebug('Updating announced resource: %s' % resource.ri)
		# get all reources for this specific CSI that are  announced to it yet

		for (csi, remoteRI) in resource[Resource._announcedTo]:
			if (remoteCSE := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			if (remoteCSR := CSE.remote.getCSRForRemoteCSE(remoteCSE)) is None:	# not yet registered
				continue
			self.updateResourceOnCSR(resource, remoteCSR, remoteRI)


	def updateResourceOnCSR(self, resource:Resource, remoteCSR:Resource, remoteRI:str) -> None:
		"""	Update an announced resource to a specific CSR.
		"""
		csi  = remoteCSR.csi
		poas = remoteCSR.poa

		# TODO: multi-hop announcement

		Logging.logDebug('Update announced resource: %s to: %s' % (resource.ri, csi))

		data = resource.createAnnouncedResourceJSON()
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


	def _removeAnnouncementFromResource(self, resource:Resource, csi:str) -> None:
		ats = resource[Resource._announcedTo]
		for x in ats:
			if x[0] == csi:
				ats.remove(x)
				resource.setAttribute(Resource._announcedTo, ats)


	def announceResourceViaDirectURL(self, resource: Resource, at: str) -> bool:
		Logging.logErr('TODO Direct Announcement')
		return False

