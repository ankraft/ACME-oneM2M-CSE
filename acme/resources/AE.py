#
#	AE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Application Entity
#

from Constants import Constants as C
from Types import ResourceTypes as T
from Validator import constructPolicy
import Utils
from .Resource import *


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'loc',
	'apn', 'api', 'aei', 'poa', 'nl', 'rr', 'csz', 'esi', 'mei', 'srv', 'regs', 'trps', 'scp', 'tren', 'ape','or'
])


class AE(Resource):

	def __init__(self, jsn: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(T.AE, jsn, pi, create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('aei', Utils.uniqueAEI(), overwrite=False)
			self.setAttribute('rr', False, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource: Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.ACP,
									   T.CNT,
									   T.FCNT,
									   T.GRP,
									   T.SUB
									 ])


	def validate(self, originator: str = None, create: bool = False) -> Tuple[bool, int, str]:
		if (res := super().validate(originator), create)[0] == False:
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
				node, _, _ = CSE.dispatcher.retrieveResource(nl) # new node
				if node is not None:
					hael = node['hael']
					if hael is None:
						node['hael'] = [ ri ]
					else:
						if isinstance(hael, list):
							hael.append(ri)
							node['hael'] = hael
					node.dbUpdate()
			self[Resource._node] = nl

		return True, C.rcOK, None


	def deactivate(self, originator : str) -> None:
		super().deactivate(originator)
		if (nl := self['nl']) is None:
			return
		self._removeAEfromNOD(nl, self['ri'])


	def _removeAEfromNOD(self, nodeRi: str, ri: str) -> None:
		""" Remove AE from hosting Node. """

		node, _, _ = CSE.dispatcher.retrieveResource(nodeRi)
		if node is not None:
			hael = node['hael']
			if hael is not None and isinstance(hael, list) and ri in hael:
				hael.remove(ri)
				if len(hael) == 0:
					node.delAttribute('hael')
				else:
					node['hael'] = hael
				node.dbUpdate()

