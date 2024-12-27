#
#	ACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" AccessControlPolicy (ACP) resource type. """

from __future__ import annotations
from typing import List, Optional

from ..helpers.TextTools import findXPath
from ..etc.Types import AttributePolicyDict, ResourceTypes, Permission, JSON
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..resources.Resource import Resource, addToInternalAttributes
from ..resources.AnnounceableResource import AnnounceableResource


# Add to internal attributes
addToInternalAttributes(Constants.attrRiTyMapping)


class ACP(AnnounceableResource):
	""" AccessControlPolicy (ACP) resource type """

	resourceType = ResourceTypes.ACP
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """


	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB ] # TODO Transaction to be added
	""" The allowed child-resource types. """

	# Assigned during startup in the Importer.
	_attributes:AttributePolicyDict = {	
			# Common and universal attributes
			'rn': None,
			'ty': None,
			'ri': None,
			'pi': None,
			'ct': None,
			'lt': None,
			'et': None,
			'lbl': None,
			'at': None,
			'aa': None,
			'ast': None,

			# Resource attributes
			'pv': None,
			'pvs': None,
			'adri': None,
			'apri': None,
			'airi': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def activate(self, parentResource:Resource, originator:str) -> None:

		# Set default permissions
		self.setAttribute('pv/acr', [], overwrite = False)
		self.setAttribute('pvs/acr', [], overwrite = False)

		super().activate(parentResource, originator)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		# Inherited
		super().validate(originator, dct, parentResource)
		
		if dct and (pvs := findXPath(dct, f'{ResourceTypes.ACPAnnc.typeShortname()}/pvs')):
			if len(pvs) == 0:
				raise BAD_REQUEST('pvs must not be empty')
		if not self.pvs:
			raise BAD_REQUEST('pvs must not be empty')

		# Get types for the acor members. Ignore if not found
		# This is an optimization used later in case there is a group in acor
		# The dictionary is stored in the ACP resource itself and contains
		# a mapping of resourceID's to resource types.
		# It is later used by the security manager
		riTyDict = {}

		def _getAcorTypes(pv:JSON) -> None:
			""" Get the types of the acor members.
				Args:
					pv: The pv attribute to get the types for.
			"""
			if pv:
				for acr in pv.get('acr', []):
					if (acor := acr.get('acor')):
						for o in acor:
							try:
								r = CSE.dispatcher.retrieveResource(o)
								riTyDict[o] = r.ty		
							except:
								# ignore any errors here. The acor might not be a resource yet
								continue

		_getAcorTypes(self.getFinalResourceAttribute('pv', dct))
		_getAcorTypes(self.getFinalResourceAttribute('pvs', dct))
		self.setAttribute(Constants.attrRiTyMapping, riTyDict)



	def deactivate(self, originator:str, parentResource:Resource) -> None:
		# Inherited
		super().deactivate(originator, parentResource)

		# Remove own resourceID from all acpi
		L.isDebug and L.logDebug(f'Removing acp.ri: {self.ri} from assigned resource acpi')
		for r in CSE.storage.searchByFilter(lambda r: (acpi := r.get('acpi')) is not None and self.ri in acpi):	# search for presence in acpi, not perfect match
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


	def getTypeForRI(self, ri:str) -> Optional[str]:
		""" Get the resource type for a resourceID.
			Args:
				ri: The resourceID to get the type for.
			Return:
				The resource type if found, or *None* otherwise.
		"""
		return self[Constants.attrRiTyMapping].get(ri)

