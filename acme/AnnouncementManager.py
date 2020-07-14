#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

import json, time
from Logging import Logging
import Utils, CSE
from resources.Resource import Resource
from resources.AnnouncedResource import AnnouncedResource
from Constants import Constants as C
from Types import ResourceTypes as T

# TODO for anounceable resource:
# - update: update resource here



class AnnouncementManager(object):

	def __init__(self) -> None:
		CSE.event.addHandler(CSE.event.deregisteredFromRemoteCSE, self.deRegisteredFromRemoteCSE)			# type: ignore
		CSE.event.addHandler(CSE.event.registeredToRemoteCSE, self.registeredToRemoteCSE)			# type: ignore
		Logging.log('AnnouncementManager initialized')


	def shutdown(self) -> None:
		for remoteCSE in CSE.remote.getAllRemoteCSEs():
			self.checkResourcesForDeAnnouncement(remoteCSE)
		Logging.log('AnnouncementManager shut down')


	#########################################################################
	#
	#	Event Handlers. Listen on remote CSE registrations
	#

	def registeredToRemoteCSE(self, remoteCSE:Resource, remoteCSR: Resource) -> None:
		#time.sleep(5) # TODO configurable? Or wait for something?
		self.checkResourcesForAnnouncement(remoteCSE, remoteCSR)


	def deRegisteredFromRemoteCSE(self, remoteCSE:Resource) -> None:
		self.checkResourcesForDeAnnouncement(remoteCSE)




	#########################################################################
	#
	#	Access Methods to check, announce, unanounce etc
	#

	#
	#	Announcements
	#

	def checkResourcesForAnnouncement(self, remoteCSE:Resource, remoteCSR:Resource) -> None:
		"""	Check all resources and announce them if necessary.
		"""
		Logging.logDebug('Checking resources for Announcement to: %s' % remoteCSE.csi)
		# get all reources for this specific CSI that are NOT announced to it yet
		resources = CSE.storage.searchAnnounceableResourcesForCSI(remoteCSE.csi, False)
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.announceResourceToCSR(resource, remoteCSE, remoteCSR)


	def announceResource(self, resource:Resource) -> None:
		"""	Announce a single resource to its announcement targets.
		"""
		Logging.logDebug('Announce resource: %s to all connected csr' % resource.ri)
		for csi in resource.at:
			if (remoteCSE := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			if (remoteCSR := CSE.remote.getRemoteCSRForRemoteCSE(remoteCSE)) is None:	# not yet registered
				continue
			self.announceResourceToCSR(resource, remoteCSE, remoteCSR)


	def announceResourceToCSR(self, resource:Resource, remoteCSE:Resource, remoteCSR:Resource) -> None:
		"""	Announce a resource to a specific CSR.
		"""

		# TODO: multi-hop announcement

		Logging.logDebug('Announce resource: %s to: %s' % (resource.ri, remoteCSE.csi))

		if (at := resource.at) is None or len(at) == 0:
			Logging.logWarn('at attribute is empty')
			return
		if remoteCSE.csi not in at:
			Logging.logWarn('CSI not found in at: %s' % at)

		# Create announced json & type
		data = resource.createAnnouncedResourceJSON()
		tyAnnc = T(resource.ty).announced()

		# Get target URL for request
		if (poas := remoteCSE.poa) is not None and len(poas) > 0:
			poa = poas[0]												# Only first POA
			url = '%s/~%s/%s' % (poa, remoteCSE.csi, remoteCSR.ri)
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Create the announed resource on the remote CSE
		Logging.logDebug('Creating announced resource at: %s url: %s' % (remoteCSE.csi, url))	
		jsn, rc, msg = CSE.httpServer.sendCreateRequest(url, remoteCSR.csi, ty=tyAnnc, data=json.dumps(data))
		if rc not in [C.rcCreated, C.rcOK]:
			if rc != C.rcAlreadyExists:
				Logging.logDebug('Error creating remote announced resource: %d' % rc)
		else:
			ats = resource[Resource._announcedTo]
			ats.append((remoteCSE.csi, Utils.findXPath(jsn, '{0}/ri')))
			resource.setAttribute(Resource._announcedTo, ats)
		Logging.logDebug('Announced resource created')
		resource.dbUpdate()


	#
	#	De-Announcements
	#

	def checkResourcesForDeAnnouncement(self, remoteCSE:Resource) -> None:
		Logging.logDebug('Checking resources for Unannouncement to: %s' % remoteCSE.csi)
		# get all reources for this specific CSI that are NOT announced to it yet
		resources = CSE.storage.searchAnnounceableResourcesForCSI(remoteCSE.csi, True)
		# try to announce all not-announced resources to this csr
		for resource in resources:
			self.deAnnounceResource(resource)
			self._removeAnnouncementFromResource(resource, remoteCSE.csi)
			resource.dbUpdate()



	def deAnnounceResource(self, resource:Resource) -> None:
		"""	De-announce a single resource from its announcement targets.
		"""
		Logging.logDebug('De-Announce resource: %s from all connected csr' % resource.ri)

		for (csi, ri) in resource[Resource._announcedTo]:
			if (remoteCSE := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			if (remoteCSR := CSE.remote.getRemoteCSRForRemoteCSE(remoteCSE)) is None:	# not yet registered
				continue
			self.deAnnounceResourceFromCSR(resource, remoteCSE, ri)



	def deAnnounceResourceFromCSR(self, resource:Resource, remoteCSE:Resource, ri:str) -> None:
		"""	De-Announce a resource from a specific CSR.
		"""

		# TODO: multi-hop announcement

		Logging.logDebug('De-Announce resource: %s from: %s' % (resource.ri, remoteCSE.csi))

		# Get target URL for request
		if (poas := remoteCSE.poa) is not None and len(poas) > 0:
			poa = poas[0]
			url = '%s/~%s/%s' % (poa, remoteCSE.csi, ri)	# TODO check all available poas.
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Delete the announed resource from the remote CSE
		Logging.logDebug('Delete announced resource from: %s url: %s' % (remoteCSE.csi, url))	
		jsn, rc, msg = CSE.httpServer.sendDeleteRequest(url, CSE.remote.originator)
		if rc not in [C.rcDeleted, C.rcOK]:
			if rc != C.rcAlreadyExists:
				Logging.logDebug('Error deleting remote announced resource: %d' % rc)
		self._removeAnnouncementFromResource(resource, remoteCSE.csi)
		Logging.logDebug('Announced resource deleted')
		resource.dbUpdate()




	#
	#	Update Announcements
	#


	def announceUpdatedResource(self, resource:Resource) -> None:
		Logging.logDebug('Updating announced resource: %s' % resource.ri)
		# get all reources for this specific CSI that are  announced to it yet
		for (csi, ri) in resource[Resource._announcedTo]:
			if (remoteCSE := Utils.resourceFromCSI(csi)) is None:
				self._removeAnnouncementFromResource(resource, csi)
				continue
			if (remoteCSR := CSE.remote.getRemoteCSRForRemoteCSE(remoteCSE)) is None:	# not yet registered
				continue
			self.updateResourceOnCSR(resource, remoteCSE, ri)


	def updateResourceOnCSR(self, resource:Resource, remoteCSE:Resource, ri:str) -> None:
		"""	Update an announced resource to a specific CSR.
		"""

		# TODO: multi-hop announcement

		Logging.logDebug('Update announced resource: %s to: %s' % (resource.ri, remoteCSE.csi))

		data = resource.createAnnouncedResourceJSON()
		tyAnnc = T(resource.ty).announced()

		# Get target URL for request
		if (poas := remoteCSE.poa) is not None and len(poas) > 0:
			url = '%s/~%s/%s' % (poas[0], remoteCSE.csi, ri)	# TODO check all available poas.
		else:
			Logging.logWarn('Cannot get URL')
			return

		# Create the announed resource on the remote CSE
		Logging.logDebug('Updating announced resource at: %s url: %s' % (remoteCSE.csi, url))	
		jsn, rc, msg = CSE.httpServer.sendUpdateRequest(url, CSE.remote.originator, data=json.dumps(data))
		if rc not in [C.rcUpdated, C.rcOK]:
			if rc != C.rcAlreadyExists:
				Logging.logDebug('Error updating remote announced resource: %d' % rc)

		Logging.logDebug('Announced resource updated')


	def _removeAnnouncementFromResource(self, resource:Resource, csi:str):
		ats = resource[Resource._announcedTo]
		for x in ats:
			if x[0] == csi:
				ats.remove(x)
				resource.setAttribute(Resource._announcedTo, ats)


	def announceResourceViaDirectURL(self, resource: Resource, at: str) -> bool:
		Logging.logErr('TODO Direct Announcement')
		return False

