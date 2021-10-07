#
#	ACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: AccessControlPolicy
#

from __future__ import annotations
from typing import List
from ..helpers.TextTools import simpleMatch
from ..etc import Utils as Utils
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ResponseStatusCode as RC, Result, Permission, JSON
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource


class ACP(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.SUB ] # TODO Transaction to be added

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
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


	def __init__(self, dct:JSON=None, pi:str=None, rn:str=None, create:bool=False, createdInternally:str=None) -> None:
		super().__init__(T.ACP, dct, pi, create=create, inheritACP=True, rn=rn)

		self.setAttribute('pv/acr', [], overwrite=False)
		self.setAttribute('pvs/acr', [], overwrite=False)
		if createdInternally:
			self.setCreatedInternally(createdInternally)



	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		
		if dct and (pvs := Utils.findXPath(dct, f'{T.ACPAnnc.tpe()}/pvs')):
			if len(pvs) == 0:
				return Result(status=False, rsc=RC.badRequest, dbg='pvs must not be empty')
		if not self.pvs:
			return Result(status=False, rsc=RC.badRequest, dbg='pvs must not be empty')

		# Check acod
		def _checkAcod(acrs:list) -> Result:
			if not acrs:
				return Result(status=True)
			for acr in acrs:
				if (acod := acr.get('acod')):
					if not (acod := acod.get('chty')) or not isinstance(acod, list):
						return Result(status=False, rsc=RC.badRequest, dbg='chty is mandatory in acod')
			return Result(status=True)

		if not (res := _checkAcod(Utils.findXPath(dct, f'{T.ACPAnnc.tpe()}/pv/acr'))).status:
			return res
		if not (res := _checkAcod(Utils.findXPath(dct, f'{T.ACPAnnc.tpe()}/pvs/acr'))).status:
			return res

		return Result(status=True)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)

		# Remove own resourceID from all acpi
		L.isDebug and L.logDebug(f'Removing acp.ri: {self.ri} from assigned resource acpi')
		for r in CSE.storage.searchByFilter(lambda r: (acpi := r.get('acpi')) is not None and self.ri in acpi):	# search for presence in acpi, not perfect match
			acpi = r.acpi
			if self.ri in acpi:
				acpi.remove(self.ri)
				r['acpi'] = acpi if len(acpi) > 0 else None	# Remove acpi from resource if empty
				r.dbUpdate()


	def validateAnnouncedDict(self, dct:JSON) -> JSON:
		if acr := Utils.findXPath(dct, f'{T.ACPAnnc.tpe()}/pvs/acr'):
			acr.append( { 'acor': [ CSE.cseCsi ], 'acop': Permission.ALL } )
		return dct


	#########################################################################

	#
	#	Permission handlings
	#

	def addPermission(self, originators:list[str], permission:int) -> None:
		o = list(set(originators))	# Remove duplicates from list of originators
		if p := self['pv/acr']:
			p.append({'acop' : permission, 'acor': o})


	def removePermissionForOriginator(self, originator:str) -> None:
		if p := self['pv/acr']:
			for acr in p:
				if originator in acr['acor']:
					p.remove(acr)
					

	def addSelfPermission(self, originators:List[str], permission:int) -> None:
		if p := self['pvs/acr']:
			p.append({'acop' : permission, 'acor': list(set(originators))}) 	# list(set()) : Remove duplicates from list of originators


	def addPermissionOriginator(self, originator:str) -> None:
		for p in self['pv/acr']:
			if originator not in p['acor']:
				p['acor'].append(originator)

	def addSelfPermissionOriginator(self, originator:str) -> None:
		for p in self['pvs/acr']:
			if originator not in p['acor']:
				p['acor'].append(originator)


	def checkPermission(self, originator:str, requestedPermission:int, ty:T) -> bool:
		# L.isDebug and L.logDebug(f'originator: {originator} requestedPermission: {requestedPermission}')
		for p in self['pv/acr']:
			# L.isDebug and L.logDebug(f'p.acor: {p['acor']} requestedPermission: {p['acop']}')

			# Check Permission-to-check first
			if requestedPermission & p['acop'] == Permission.NONE:	# permission not fitting at all
				continue

			# Check acod : chty
			if acod := p.get('acod'):
				if requestedPermission == Permission.CREATE:
					if ty is None or ty not in acod.get('chty'):	# ty is an int
						continue								# for CREATE: type not in chty
				else:
					if ty not in acod.get('ty'):
						continue								# any other Permission type: ty not in chty
				# TODO support acod/specialization

			# Check originator
			if 'all' in p['acor'] or originator in p['acor'] or requestedPermission == Permission.NOTIFY:
				return True
			if any([ simpleMatch(originator, a) for a in p['acor'] ]):	# check whether there is a wildcard match
				return True
		return False


	def checkSelfPermission(self, originator:str, requestedPermission:int) -> bool:
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			# TODO check acod in pvs
			if 'all' in p['acor'] or originator in p['acor']:
				return True
			if any([ simpleMatch(originator, a) for a in p['acor'] ]):	# check whether there is a wildcard match
				return True
		return False

