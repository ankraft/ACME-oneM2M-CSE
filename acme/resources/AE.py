#
#	AE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Application Entity
#

from Constants import Constants as C
from Types import ResourceTypes as T, Result
from Validator import constructPolicy, addPolicy
import Utils
from .Resource import *
from .AnnounceableResource import AnnounceableResource


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'loc'
])
aePolicies = constructPolicy([
	'apn', 'api', 'aei', 'poa', 'nl', 'rr', 'csz', 'esi', 'mei', 'srv', 'regs', 'trps', 'scp', 'tren', 'ape','or'
])
attributePolicies =  addPolicy(attributePolicies, aePolicies)



class AE(AnnounceableResource):

	def __init__(self, jsn:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.AE, jsn, pi, create=create, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = aePolicies	# only the resource type's own policies

		if self.json is not None:
			self.setAttribute('aei', Utils.uniqueAEI(), overwrite=False)
			self.setAttribute('rr', False, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.ACP,
									   T.CNT,
									   T.FCNT,
									   T.GRP,
									   T.SUB
									 ])


	def validate(self, originator:str=None, create:bool=False) -> Result:
		if not (res := super().validate(originator, create)).status:
			return res

		self.normalizeURIAttribute('poa')

		# Update the nl attribute in the hosting node (similar to csebase) in case 
		# the AE is now on a different node. This shouldn't be happen in reality,
		# but technically it is allowed.
		nl = self['nl']
		_nl_ = self.__node__
		if nl is not None or _nl_ is not None:
			if nl != _nl_:	# if different node
				ri = self['ri']

				# Remove from old node first
				if _nl_ is not None:
					self._removeAEfromNOD(_nl_, ri)
				self[Resource._node] = nl

				# Add to new node
				if (node := CSE.dispatcher.retrieveResource(nl).resource) is not None:	# new node
					if (hael := node['hael']) is None:
						node['hael'] = [ ri ]
					else:
						if isinstance(hael, list):
							hael.append(ri)
							node['hael'] = hael
					node.dbUpdate()
			self[Resource._node] = nl

		return Result(status=True)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)
		if (nl := self['nl']) is None:
			return
		self._removeAEfromNOD(nl, self['ri'])


	def _removeAEfromNOD(self, nodeRi: str, ri: str) -> None:
		""" Remove AE from hosting Node. """


		if (node := CSE.dispatcher.retrieveResource(nodeRi).resource) is not None:
			if (hael := node['hael']) is not None and isinstance(hael, list) and ri in hael:
				hael.remove(ri)
				if len(hael) == 0:
					node.delAttribute('hael')
				else:
					node['hael'] = hael
				node.dbUpdate()

