#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

from Logging import Logging
import Utils
from resources.Resource import Resource


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



	# Announce a Resource
	def announceResource(self, resource: Resource) -> None:
		Logging.logDebug('Announce resource')

		if (at := resource['at']) is None or len(at) == 0:
			Logging.logWarn('at attribute is empty')
			return

		# Handle direct URL announcement
		if Utils.isURL(at):
			return self.announceResourceViaDirectURL(resource, at)


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