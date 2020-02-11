#
#	AnnouncementManager.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing entity for resource announcements
#

from Logging import Logging

# TODO: This manager will be implemented in the future.
#
#
# Table 9.6.26.1-1: Announced Resource Types
# 9.6.26 Resource Announcement
# Update to the announcedAttribute attribute in the original resource will trigger new attribute announcement or the de-announcement of the announced attribute(s).
# the announced resource shall be created as a direct child of the Hosting CSE’s <remoteCSE> hosted by the announcement target CSE.

class AnnouncementManager(object):

	def __init__(self):
		Logging.log('AnnouncementManager initialized')


	def shutdown(self):
		Logging.log('AnnouncementManager shut down')