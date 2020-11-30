#
#	ACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: AccessControlPolicy
#

from typing import List
from Constants import Constants as C
from Types import ResourceTypes as T, Result, Permission
from Validator import constructPolicy, addPolicy
from .Resource import *
from .AnnounceableResource import AnnounceableResource
import Utils


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'lbl', 'ct', 'lt', 'at', 'aa'
])
acpPolicies = constructPolicy([
	'pv', 'pvs', 'adri', 'apri', 'airi'
])
attributePolicies =  addPolicy(attributePolicies, acpPolicies)


class ACP(AnnounceableResource):

	def __init__(self, dct:dict=None, pi:str=None, rn:str=None, create:bool=False, createdInternally:str=None) -> None:
		super().__init__(T.ACP, dct, pi, create=create, inheritACP=True, rn=rn, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = acpPolicies	# only the resource type's own policies
		
		if self.dict is not None:
			self.setAttribute('pv/acr', [], overwrite=False)
			self.setAttribute('pvs/acr', [], overwrite=False)
			if createdInternally is not None:
				self.setCreatedInternally(createdInternally)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.SUB # TODO Transaction to be added
									 ])


	def validate(self, originator:str=None, create:bool=False) -> Result:
		if not (res := super().validate(originator, create)).status:
			return res

		# add admin originator	
		if Configuration.get('cse.acp.addAdminOrignator'):
			cseOriginator = Configuration.get('cse.originator')
			self.addPermissionOriginator(cseOriginator)
			self.addSelfPermissionOriginator(cseOriginator)
		return Result(status=True)


	def deactivate(self, originator: str) -> None:
		super().deactivate(originator)

		# Remove own resourceID from all acpi
		Logging.logDebug(f'Removing acp.ri: {self.ri} from assigned resource acpi')
		for r in CSE.storage.searchByValueInField('acpi', self.ri):
			acpi = r.acpi
			if self.ri in acpi:
				acpi.remove(self.ri)
				r['acpi'] = acpi
				r.dbUpdate()


	def validateAnnouncedDict(self, dct:dict) -> dict:
		if (acr := Utils.findXPath(dct, f'{T.ACPAnnc.tpe()}/pvs/acr')) is not None:
			acr.append( { 'acor': [ CSE.remote.cseCsi ], 'acop': Permission.ALL } )
		return dct


	#########################################################################

	#
	#	Permission handlings
	#

	def addPermission(self, originators:list, permission:int) -> None:
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


	def checkPermission(self, origin:str, requestedPermission:int) -> bool:
		# Logging.logDebug(f'origin: {origin} requestedPermission: {requestedPermission}')
		for p in self['pv/acr']:
			# Logging.logDebug(f'p.acor: {p['acor']} requestedPermission: {p['acop']}')
			if requestedPermission & p['acop'] == Permission.NONE:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor'] or requestedPermission == Permission.NOTIFY:
				return True
		return False


	def checkSelfPermission(self, origin:str, requestedPermission:int) -> bool:
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor']:
				return True
		return False

