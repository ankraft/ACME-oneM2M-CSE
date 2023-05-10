#
#	ContainerResource.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all container resources
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import ResourceTypes, JSON
from ..etc.DateUtils import getResourceDate
from ..etc.Constants import Constants
from .AnnounceableResource import AnnounceableResource
from .Resource import Resource
from ..services import CSE
from ..services.Logging import Logging as L


class ContainerResource(AnnounceableResource):

	_lari = Constants.attrLaRi
	_olri = Constants.attrOlRi

	def __init__(self, ty:ResourceTypes, 
					   dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   tpe:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ty, dct, pi, tpe = tpe, create = create)
		self._addToInternalAttributes(self._lari)
		self._addToInternalAttributes(self._olri)


	def getOldestRI(self) -> str:
		"""	Retrieve a *oldest* resource's resource ID.

			Return:
				The resource ID.
		"""
		return self[self._olri]
	

	def setOldestRI(self, ri:str) -> None:
		"""	Assign a resource ID to the *oldest* resource ID.

			Args:
				ri: The resource ID of an *oldest* resource.
		"""
		self.setAttribute(self._olri, ri, overwrite = True)


	def getLatestRI(self) -> str:
		"""	Retrieve a *latest* resource's resource ID.

			Return:
				The resource ID.
		"""
		return self[self._lari]
	

	def setLatestRI(self, ri:str) -> None:
		"""	Assign a resource ID to the *latest* resource ID.

			Args:
				ri: The resource ID of an *latest* resource.
		"""
		self.setAttribute(self._lari, ri, overwrite = True)


	def updateLaOlLatestTimestamp(self) -> None:
		"""	Update the *lt* attribute of the *latest* and *oldest* virtual child-resources.
		"""
		# Update latest
		lt = getResourceDate()
		resource = CSE.dispatcher.retrieveLocalResource(self.getLatestRI())
		resource.setAttribute('lt', lt)
		resource.dbUpdate(True)

		# Update oldest
		resource = CSE.dispatcher.retrieveLocalResource(self.getOldestRI())
		resource.setAttribute('lt', lt)
		resource.dbUpdate(True)

	
	def instanceAdded(self, instance:Resource) -> None:
		L.logDebug('Adding instance')
		self.setAttribute('cni', self.cni + 1)	# Increment cni because an instance is added
		self.setAttribute('cbs', self.cbs + instance.cs) # Add to sum of cbs
		self.dbUpdate(True)



	def instanceRemoved(self, instance:Resource) -> None:
		L.logDebug('Removing instance')
		self.setAttribute('cni', self.cni - 1)	# Decrement cni because an instance is added
		self.setAttribute('cbs', self.cbs - instance.cs) # Substract from sum of cbs
		self.dbUpdate(True)

