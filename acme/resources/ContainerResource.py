#
#	ContainerResource.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all container resources
#
"""	This module implements the *ContainerResource* class. *ContainerResource* is the base class for all container resources.
"""

from __future__ import annotations

from ..etc.DateUtils import getResourceDate
from ..etc.Constants import Constants
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources.Resource import Resource, addToInternalAttributes
from ..runtime import CSE


# Add to internal attributes
addToInternalAttributes(Constants.attrLaRi)
addToInternalAttributes(Constants.attrOlRi)

class ContainerResource(AnnounceableResource):
	"""	The *ContainerResource* class is the base class for all container resources.
	"""


	def getOldestRI(self) -> str:
		"""	Retrieve a *oldest* resource's resource ID.

			Return:
				The resource ID.
		"""
		return self[Constants.attrOlRi]
	

	def setOldestRI(self, ri:str) -> None:
		"""	Assign a resource ID to the *oldest* resource ID.

			Args:
				ri: The resource ID of an *oldest* resource.
		"""
		self.setAttribute(Constants.attrOlRi, ri, overwrite = True)


	def getLatestRI(self) -> str:
		"""	Retrieve a *latest* resource's resource ID.

			Return:
				The resource ID.
		"""
		return self[Constants.attrLaRi]
	

	def setLatestRI(self, ri:str) -> None:
		"""	Assign a resource ID to the *latest* resource ID.

			Args:
				ri: The resource ID of an *latest* resource.
		"""
		self.setAttribute(Constants.attrLaRi, ri, overwrite = True)


	def updateLaOlLatestTimestamp(self) -> None:
		"""	Update the *lt* attribute of the *latest* and *oldest* virtual child-resources.
		"""
		lt = getResourceDate()
		# Update latest
		resource = CSE.dispatcher.retrieveLocalResource(self.getLatestRI())
		resource.setAttribute('lt', lt)
		resource.dbUpdate(True)

		# Update oldest
		resource = CSE.dispatcher.retrieveLocalResource(self.getOldestRI())
		resource.setAttribute('lt', lt)
		resource.dbUpdate(True)

	
	def instanceAdded(self, instance:Resource) -> None:
		"""	An instance was added to the container. Update the *cni* and *cbs* attributes.
		
			Args:
				instance: The instance that was added.
		"""
		try:
			self.setAttribute('cni', self.cni + 1)	# Increment cni because an instance is added
			self.setAttribute('cbs', self.cbs + instance.cs) # Add to sum of cbs
			self.dbUpdate(True)
		except TypeError:
			pass # Ignore if cni or cbs is not set


	def instanceRemoved(self, instance:Resource) -> None:
		"""	An instance was removed from the container. Update the *cni* and *cbs* attributes.
		
			Args:
				instance: The instance that was removed.
		"""
		try:
			self.setAttribute('cni', self.cni - 1)	# Decrement cni because an instance is added
			self.setAttribute('cbs', self.cbs - instance.cs) # Substract from sum of cbs
			self.dbUpdate(True)
		except TypeError:
			pass # Ignore if cni or cbs is not set

