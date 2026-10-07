#
#	ACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" AccessControlPolicy (ACP) resource type. """

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from ..helpers.TextTools import findXPath
from ..etc.Types import ResourceTypes, Permission, JSON, CSERequest
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..runtime.Logging import Logging as L
from ..resources.Resource import Resource, addToInternalAttributes
from ..resources.AnnounceableResource import AnnounceableResource
from ..runtime.PluginSupport import requires

if TYPE_CHECKING:
	from ..services.Dispatcher import Dispatcher
	from ..runtime.Storage import Storage

@requires(dispatcher='acmecse.services.Dispatcher')
@requires(storage='acmecse.runtime.Storage')
class ACP(AnnounceableResource):
	""" AccessControlPolicy (ACP) resource type """

	dispatcher: Dispatcher = None
	""" Injected Dispatcher instance. """

	storage:Storage = None
	"""	Injected Storage instance. """


	def activate(self, parentResource:Resource, 
			  		   originator:str, 
					   request: Optional[CSERequest] = None) -> None:

		# Set default permissions
		self.setAttribute('pv/acr', [], overwrite = False)
		self.setAttribute('pvs/acr', [], overwrite = False)

		super().activate(parentResource, originator, request)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		# Inherited
		super().validate(originator, dct, parentResource)

		# Test that the pvs attribute is and will be present and not empty
		if (pvs := self.getFinalResourceAttribute('pvs', dct)) is not None:
			if len(pvs) == 0:
				raise BAD_REQUEST('pvs must not be empty')
		else:
			raise BAD_REQUEST('pvs must not be None')
		

	def deactivate(self, originator:str, parentResource:Resource) -> None:
		# Inherited
		super().deactivate(originator, parentResource)

		# Remove own resourceID from all acpi
		L.isDebug and L.logDebug(f'Removing acp.ri: {self.ri} from assigned resource acpi')
		for r in self.storage.searchByFilter(lambda r: (acpi := r.get('acpi')) is not None and self.ri in acpi):	# search for presence in acpi, not perfect match
			acpi = r.acpi
			if self.ri in acpi:
				acpi.remove(self.ri)
				r['acpi'] = acpi if len(acpi) > 0 else None	# Remove acpi from resource if empty
				r.dbUpdate()


	def validateAnnouncedDict(self, dct:JSON) -> JSON:
		# Inherited
		if acr := findXPath(dct, f'{ResourceTypes.ACPAnnc.typeShortname()}/pvs/acr'):
			acr.append( { 'acor': [ RC.cseCsi ], 'acop': Permission.ALL } )
		return dct


	#########################################################################
	#
	#	Resource specific
	#

	#	Permission handlings

	def addPermission(self, originators:list[str], permission:Permission) -> None:
		"""	Add new general permissions to the ACP resource.
		
			Args:
				originators: List of originator identifiers.
				permission: Bit-field of oneM2M request permissions
		"""
		o = list(set(originators))	# Remove duplicates from list of originators
		if p := self['pv/acr']:
			p.append({'acop' : permission, 'acor': o})


	def removePermissionForOriginator(self, originator:str) -> None:
		"""	Remove the permissions for an originator.
		
			Args:
				originator: The originator for to remove the permissions.
		"""
		if p := self['pv/acr']:
			for acr in p:
				if originator in acr['acor']:
					p.remove(acr)
					

	def addSelfPermission(self, originators:List[str], permission:Permission) -> None:
		"""	Add new **self** - permissions to the ACP resource.
		
			Args:
				originators: List of originator identifiers.
				permission: Bit-field of oneM2M request permissions
		"""
		if p := self['pvs/acr']:
			p.append({'acop' : permission, 'acor': list(set(originators))}) 	# list(set()) : Remove duplicates from list of originators


