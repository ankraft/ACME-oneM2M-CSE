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
from Types import ResourceTypes as T, Result
from Validator import constructPolicy, addPolicy
from .Resource import *
import Utils


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'lbl', 'ct', 'lt', 'at', 'aa'
])
acpPolicies = constructPolicy([
	'pv', 'pvs', 'adri', 'apri', 'airi'
])
attributePolicies =  addPolicy(attributePolicies, acpPolicies)


class ACP(Resource):

	def __init__(self, jsn:dict=None, pi:str=None, rn:str=None, create:bool=False, createdInternally:str=None) -> None:
		super().__init__(T.ACP, jsn, pi, create=create, inheritACP=True, rn=rn, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = acpPolicies	# only the resource type's own policies
		
		if self.json is not None:
			self.setAttribute('pv/acr', [], overwrite=False)
			self.setAttribute('pvs/acr', [], overwrite=False)
			if createdInternally is not None:
				self.setAttribute(self._createdInternally, createdInternally)


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
		Logging.logDebug('Removing acp.ri: %s from assigned resource acpi' % self.ri)
		for r in CSE.storage.searchByValueInField('acpi', self.ri):
			acpi = r.acpi
			if self.ri in acpi:
				acpi.remove(self.ri)
				r['acpi'] = acpi
				r.dbUpdate()




	#########################################################################

	def createdInternally(self) -> str:
		""" Return the resource.ri for which this ACP was created, or None. """
		return self[self._createdInternally]

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
		# Logging.logDebug('origin: %s requestedPermission: %s' % (origin, requestedPermission))
		for p in self['pv/acr']:
			# Logging.logDebug('p.acor: %s requestedPermission: %s' % (p['acor'], p['acop']))
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor'] or requestedPermission == C.permNOTIFY:
				return True
		return False


	def checkSelfPermission(self, origin:str, requestedPermission:int) -> bool:
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor']:
				return True
		return False

