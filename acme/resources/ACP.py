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
from Logging import Logging as L
from Types import ResourceTypes as T, ResponseCode as RC, Result, Permission, JSON
from Validator import constructPolicy, addPolicy
from .Resource import *
from .AnnounceableResource import AnnounceableResource
import Utils, CSE


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'lbl', 'ct', 'lt', 'at', 'aa'
])
acpPolicies = constructPolicy([
	'pv', 'pvs', 'adri', 'apri', 'airi'
])
attributePolicies =  addPolicy(attributePolicies, acpPolicies)


class ACP(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.SUB ] # TODO Transaction to be added


	def __init__(self, dct:JSON=None, pi:str=None, rn:str=None, create:bool=False, createdInternally:str=None, isRemote:bool=False) -> None:
		super().__init__(T.ACP, dct, pi, create=create, inheritACP=True, rn=rn, attributePolicies=attributePolicies, isRemote=isRemote)

		self.resourceAttributePolicies = acpPolicies	# only the resource type's own policies
		
		if self.dict is not None:
			self.setAttribute('pv/acr', [], overwrite=False)
			self.setAttribute('pvs/acr', [], overwrite=False)
			if createdInternally is not None:
				self.setCreatedInternally(createdInternally)



	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		
		if dct is not None and (pvs := Utils.findXPath(dct, f'{T.ACPAnnc.tpe()}/pvs')) is not None:
			if len(pvs) == 0:
				return Result(status=False, rsc=RC.badRequest, dbg='pvs must not be empty')
		if self.pvs is None or len(self.pvs) == 0:
			return Result(status=False, rsc=RC.badRequest, dbg='pvs must not be empty')

		# Check acod
		def _checkAcod(acrs:list) -> Result:
			if acrs is None:
				return Result(status=True)
			for acr in acrs:
				if (acod := acr.get('acod')) is not None:
					if (acod := acod.get('chty')) is None or not isinstance(acod, list):
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
				if len(acpi) > 0:
					r['acpi'] = acpi
				else:
					r['acpi'] = None	# Remove acpi from resource if empty
				r.dbUpdate()


	def validateAnnouncedDict(self, dct:JSON) -> JSON:
		if (acr := Utils.findXPath(dct, f'{T.ACPAnnc.tpe()}/pvs/acr')) is not None:
			acr.append( { 'acor': [ CSE.cseCsi ], 'acop': Permission.ALL } )
		return dct


	#########################################################################

	#
	#	Permission handlings
	#

	def addPermission(self, originators:list[str], permission:int) -> None:
		o = list(set(originators))	# Remove duplicates from list of originators
		if (p := self['pv/acr']) is not None:
			p.append({'acop' : permission, 'acor': o})


	def removePermissionForOriginator(self, originator:str) -> None:
		if (p := self['pv/acr']) is not None:
			for acr in p:
				if originator in acr['acor']:
					p.remove(acr)
					

	def addSelfPermission(self, originators:List[str], permission:int) -> None:
		o = list(set(originators))	 # Remove duplicates from list of originators
		if (p := self['pvs/acr']) is not None:
			p.append({'acop' : permission, 'acor': o})


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
			if (acod := p.get('acod')) is not None:
				if requestedPermission == Permission.CREATE:
					if ty is None or ty not in acod.get('chty'):
						continue								# for CREATE: type not in chty
				else:
					if ty not in acod.get('ty'):
						continue								# any other Permission type: ty not in chty
				# TODO support acod/specialization

			# Check originator
			if 'all' in p['acor'] or originator in p['acor'] or requestedPermission == Permission.NOTIFY:
				return True
			if any([ Utils.simpleMatch(originator, a) for a in p['acor'] ]):	# check whether there is a wildcard match
				return True
		return False


	def checkSelfPermission(self, originator:str, requestedPermission:int) -> bool:
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			# TODO check acod in pvs
			if 'all' in p['acor'] or originator in p['acor']:
				return True
			if any([ Utils.simpleMatch(originator, a) for a in p['acor'] ]):	# check whether there is a wildcard match
				return True
		return False

