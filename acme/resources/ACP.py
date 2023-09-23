#
#	ACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" AccessControlPolicy (ACP) resource type. """

from __future__ import annotations
from typing import List, Optional

from ..helpers.TextTools import simpleMatch
from ..helpers.TextTools import findXPath
from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, Permission, JSON
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.Constants import Constants
from ..services import CSE
from ..services.Logging import Logging as L
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class ACP(AnnounceableResource):
	""" AccessControlPolicy (ACP) resource type """

	_riTyMapping = Constants.attrRiTyMapping

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


	def __init__(self, dct:JSON, 
					   pi:Optional[str] = None, 
					   rn:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.ACP, dct, pi, create = create, inheritACP = True, rn = rn)

		self._addToInternalAttributes(self._riTyMapping)

		self.setAttribute('pv/acr', [], overwrite = False)
		self.setAttribute('pvs/acr', [], overwrite = False)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		# Inherited
		super().validate(originator, dct, parentResource)
		
		if dct and (pvs := findXPath(dct, f'{ResourceTypes.ACPAnnc.tpe()}/pvs')):
			if len(pvs) == 0:
				raise BAD_REQUEST('pvs must not be empty')
		if not self.pvs:
			raise BAD_REQUEST('pvs must not be empty')

		# Check acod
		# TODO Is this still necessary? Check in resource validation?
		def _checkAcod(acrs:list) -> None:
			if acrs:
				for acr in acrs:
					if (acod := acr.get('acod')):
						for each in acod:
							if not (chty := each.get('chty')) or not isinstance(chty, list):
								raise BAD_REQUEST('chty is mandatory in acod')

		_checkAcod(findXPath(dct, f'{ResourceTypes.ACPAnnc.tpe()}/pv/acr'))
		_checkAcod(findXPath(dct, f'{ResourceTypes.ACPAnnc.tpe()}/pvs/acr'))

		# Get types for the acor members. Ignore if not found
		# This is an optimization used later in case there is a group in acor
		riTyDict = {}

		def _getAcorTypes(pv:JSON) -> None:
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
		self.setAttribute(ACP._riTyMapping, riTyDict)



	def deactivate(self, originator:str) -> None:
		# Inherited
		super().deactivate(originator)

		# Remove own resourceID from all acpi
		L.isDebug and L.logDebug(f'Removing acp.ri: {self.ri} from assigned resource acpi')
		l_acpi = []
  		
		# search for presence in acpi, not perfect match
		if CSE.storage.isMongoDB():
			l_acpi = CSE.storage.retrieveResourcesByContain(field='acpi', contain=self.ri)
		else:
			l_acpi = CSE.storage.searchByFilter(lambda r: (acpi := r.get('acpi')) is not None and self.ri in acpi)

		for r in l_acpi:	
			acpi = r.acpi
			if self.ri in acpi:
				acpi.remove(self.ri)
				r['acpi'] = acpi if len(acpi) > 0 else None	# Remove acpi from resource if empty
				r.dbUpdate()


	def validateAnnouncedDict(self, dct:JSON) -> JSON:
		# Inherited
		if acr := findXPath(dct, f'{ResourceTypes.ACPAnnc.tpe()}/pvs/acr'):
			acr.append( { 'acor': [ CSE.cseCsi ], 'acop': Permission.ALL } )
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


	def checkPermission(self, originator:str, requestedPermission:Permission, ty:ResourceTypes) -> bool:
		"""	Check whether an *originator* has the requested permissions.

			Args:
				originator: The originator to test the permissions for.
				requestedPermission: The permissions to test.
				ty: If the resource type is given then it is checked for CREATE (as an allowed child resource type), otherwise as an allowed resource type.
			Return:
				If any of the configured *accessControlRules* of the ACP resource matches, then the originatorhas access, and *True* is returned, or *False* otherwise.
		"""
		# L.isDebug and L.logDebug(f'originator: {originator} requestedPermission: {requestedPermission}')
		for acr in self['pv/acr']:
			# L.isDebug and L.logDebug(f'p.acor: {p['acor']} requestedPermission: {p['acop']}')

			# Check Permission-to-check first
			if requestedPermission & acr['acop'] == Permission.NONE:	# permission not fitting at all
				continue

			# Check acod : chty
			if acod := acr.get('acod'):
				for eachAcod in acod:
					if requestedPermission == Permission.CREATE:
						if ty is None or ty not in eachAcod.get('chty'):	# ty is an int
							continue										# for CREATE: type not in chty
					else:
						if ty is not None and ty != eachAcod.get('ty'):
							continue								# any other Permission type: ty not in chty
					break # found one, so apply the next checks further down
				else:
					continue	# NOT found, so continue the overall search

				# TODO support acod/specialization

			# Check originator
			if self._checkAcor(acr['acor'], originator):
				return True

		return False


	def checkSelfPermission(self, originator:str, requestedPermission:Permission) -> bool:
		"""	Check whether an *originator* has the requested permissions to the `ACP` resource itself.

			Args:
				originator: The originator to test the permissions for.
				requestedPermission: The permissions to test.
			Return:
				If any of the configured *accessControlRules* of the ACP resource matches, then the originatorhas access, and *True* is returned, or *False* otherwise.
		"""
		# NOTE The same function also exists in ACPAnnc.py

		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue

			# Check originator
			if self._checkAcor(p['acor'], originator):
				return True

		return False


	def _checkAcor(self, acor:list[str], originator:str) -> bool:

		# Check originator
		if 'all' in acor or \
			originator in acor:
			# or requestedPermission == Permission.NOTIFY:	# TODO not sure whether this is correct
			return True
		
		# Iterrate over all acor entries for either a group check or a wildcard check
		_riTypes = self.attribute(ACP._riTyMapping)
		for a in acor:

			# Check for group. If the originator is a member of a group, then the originator has access
			if _riTypes.get(a) == ResourceTypes.GRP:
				try:
					if originator in CSE.dispatcher.retrieveResource(a).mid:
						L.isDebug and L.logDebug(f'Originator found in group member')
						return True
				except Exception as e:
					L.logErr(f'GRP resource not found for ACP check: {a}', exc = e)
					continue # Not much that we can do here

			# Otherwise Check for wildcard match
			if simpleMatch(originator, a):
				return True
		
		return False
