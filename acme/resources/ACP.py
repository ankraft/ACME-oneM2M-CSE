#
#	ACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: AccessControlPolicy
#

from Constants import Constants as C
from Validator import constructPolicy
from .Resource import *
import Utils


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'lbl', 'ct', 'lt', 'at', 'aa', 
	'pv', 'pvs', 'adri', 'apri', 'airi'
])

class ACP(Resource):

	def __init__(self, jsn=None, pi=None, rn=None, create=False, createdInternally=None):
		super().__init__(C.tsACP, jsn, pi, C.tACP, create=create, inheritACP=True, rn=rn, attributePolicies=attributePolicies)
		
		if self.json is not None:
			self.setAttribute('pv/acr', [], overwrite=False)
			self.setAttribute('pvs/acr', [], overwrite=False)
			if createdInternally is not None:
				self.setAttribute(self._createdInternally, createdInternally)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource):
		return super()._canHaveChild(resource,	
									 [ C.tSUB # TODO Transaction to be added
									 ])


	def validate(self, originator, create=False):
		if (res := super().validate(originator, create))[0] == False:
			return res

		# add admin originator	
		if Configuration.get('cse.acp.addAdminOrignator'):
			cseOriginator = Configuration.get('cse.originator')
			self.addPermissionOriginator(cseOriginator)
			self.addSelfPermissionOriginator(cseOriginator)
		return True, C.rcOK



	#########################################################################

	def createdInternally(self):
		""" Return the resource.ri for which this ACP was created, or None. """
		return self[self._createdInternally]

	#########################################################################

	#
	#	Permission handlings
	#

	def addPermission(self, originators : list, permission : int):
		o = list(set(originators))	# Remove duplicates from list of originators
		if (p := self['pv/acr']) is not None:
			p.append({'acop' : permission, 'acor': o})

	def removePermissionForOriginator(self, originator : str):
		if (p := self['pv/acr']) is not None:
			for acr in p:
				if originator in acr['acor']:
					p.remove(acr)
					

	def addSelfPermission(self, originators : list, permission : int):
		o = list(set(originators))	 # Remove duplicates from list of originators
		if (p := self['pvs/acr']) is not None:
			p.append({'acop' : permission, 'acor': o})


	def addPermissionOriginator(self, originator):
		for p in self['pv/acr']:
			if originator not in p['acor']:
				p['acor'].append(originator)

	def addSelfPermissionOriginator(self, originator):
		for p in self['pvs/acr']:
			if originator not in p['acor']:
				p['acor'].append(originator)


	def checkPermission(self, origin, requestedPermission):
		for p in self['pv/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor'] or requestedPermission == C.permNOTIFY:
				return True
		return False


	def checkSelfPermission(self, origin, requestedPermission):
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == 0:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor']:
				return True
		return False

