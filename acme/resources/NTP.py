 #
#	NTP.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: NotificationTargetPolicy
#

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from ..etc.Types import ResourceTypes, JSON, LogicalOperator
from ..etc.Constants import RuntimeConstants as RC
from ..resources.Resource import Resource
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..runtime.Storage import Storage
	
_defaultPLBL = 'Default'
""" Default policy label for NTP resources. """

@requires(storage='acme.runtime.Storage')
class NTP(Resource):

	storage: Storage =None
	"""	Injected Storage instance. """


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		
		# Check that the creator attribute is not set when the resource is created by the CSE admin
		if self.cr is not None and originator == RC.cseOriginator:
			raise BAD_REQUEST(f'Creator attribute: {self.cr} is not allowed for CSE admin created NTP resources.')


	def validate(self, originator:str=None, dct:Optional[JSON]=None, parentResource:Optional[Resource]=None) -> None:
		super().validate(originator, dct, parentResource)

		# Set a default value for the rrs attribute if not provided
		if self.rrs is None:
			# Set the default value for rrs if not provided
			self.setAttribute('rrs', LogicalOperator.AND.value)	# EXPERIMENTAL Check spec change for default value

		# Validate that only one NTP resource with the same creator and label exists
		res = self.storage.searchByFragment({ 'ty': ResourceTypes.NTP, 'cr': self.cr, 'plbl': self.plbl })
		for r in res:
			if r.ri != self.ri:	# ignore self
				if r.plbl == self.plbl and r.cr == self.cr:
					raise BAD_REQUEST(f'Only one NTP resource with the same creator and policyLabel is allowed. Existing NTP: {r.ri}')

	
	def willBeDeactivated(self, originator:str, parentResource:Resource, parentDelete: bool=False) -> None:
		# Check that the system default policy is not deleted
		if self.plbl == _defaultPLBL and self.getOriginator() == RC.cseOriginator:
			raise BAD_REQUEST(f'The system default NTP resource cannot be deleted.')
		super().willBeDeactivated(originator, parentResource, parentDelete)
	