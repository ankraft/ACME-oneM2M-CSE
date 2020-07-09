#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

from Logging import Logging
import Utils, CSE
from resources.Resource import Resource
from resources.AnnouncedResource import AnnouncedResource



# TODO: This manager will be implemented in the future.
#
#
# Table 9.6.26.1-1: Announced Resource Types
# 9.6.26 Resource Announcement
# Update to the announcedAttribute attribute in the original resource will trigger new attribute announcement or the de-announcement of the announced attribute(s).
# the announced resource shall be created as a direct child of the Hosting CSE’s <remoteCSE> hosted by the announcement target CSE.

class AnnouncementManager(object):

	def __init__(self) -> None:
		Logging.log('AnnouncementManager initialized')


	def shutdown(self) -> None:
		Logging.log('AnnouncementManager shut down')



	def announceResource(self, resource: Resource) -> None:
		"""	Announce a single resource.
		"""
		Logging.logDebug('Announce resource')

		if (at := resource['at']) is None or len(at) == 0:
			Logging.logWarn('at attribute is empty')
			return

		# Handle direct URL announcement
		if Utils.isURL(at):
			self.announceResourceViaDirectURL(resource, at)
			return


# TODO create annc resource



		# Check simple case: The announcement target is a directly registered CSR
		if at == CSE.remote.remoteCsi and CSE.remote.isConnected:
			# TODO Create the Annc resource under remote remoteCSR
			pass 
		if at == CSE.remote.remoteCsi and not CSE.remote.isConnected:
			# TODO Create the Annc resource under the remote CSEBase. get URL of remote CSEBase
			pass

		# TODO: if self CSE is announced itself



# - The link attribute is set to the URI of the original resource.

# - If the accessControlPolicyIDs attribute of the original resource is not present, the accessControlPolicyIDs attribute is set to the same value as the parent resource or is set using the local policy of the original resource.

# - Attributes marked with MA in oneM2M TS-0001 [6]. Such attributes shall be included if present in the original resource and set to same value as in the original resource.

# - Attributes marked with OA that are included in the announcedAttribute attribute. Such attributes shall be included if present in the original resource and set to same value as in the original resource.

# - The resourceType attribute is set to the announced variant of the original resource (see Table 6.3.4.2.1-1).


		# TODO more complicated, indirect announcements



	def announceResourceViaDirectURL(self, resource: Resource, at: str) -> bool:
		Logging.logErr('TODO Direct Announcement')
		return False



	def checkResourceReanncements(self) -> None:
		"""	Re-Announce reesource, e.g. after a CSE re-connect.
		"""
		pass


	def createAnnounceableResource(self, resource: Resource) -> AnnouncedResource:
		# check if correct type
		# Create correct resource type.
		# copy / set attributes from TS-0001 9.6.26.2
		# copy all other attributes that are MA in that resource (ask validator)
		# copy all other attributes that are in AA attribute
		return None


