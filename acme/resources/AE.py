#
#	AE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Application Entity
#

from Constants import Constants as C
from Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from Validator import constructPolicy, addPolicy
import Utils
from .Resource import *
from Logging import Logging
from .AnnounceableResource import AnnounceableResource
import CSE


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'at', 'aa', 'daci', 'loc', 'st', 'hld',
])
aePolicies = constructPolicy([
	'apn', 'api', 'aei', 'poa', 'nl', 'rr', 'csz', 'esi', 'mei', 'srv', 'regs', 'trps', 'scp', 'tren', 'ape','or'
])
attributePolicies =  addPolicy(attributePolicies, aePolicies)



class AE(AnnounceableResource):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.AE, dct, pi, create=create, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = aePolicies	# only the resource type's own policies

		if self.dict is not None:
			self.setAttribute('aei', Utils.uniqueAEI(), overwrite=False)
			self.setAttribute('rr', False, overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.ACP,
									   T.CNT,
									   T.FCNT,
									   T.GRP,
									   T.PCH,
									   T.SUB
									 ])


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res

		# Perform checks for <PCH>	
		if childResource.ty == T.PCH:
			# Check correct originator. Even the ADMIN is not allowed that		
			if self.aei != originator:
				Logging.logDebug(dbg := f'Originator must be the parent <AE>')
				return Result(status=False, rsc=RC.originatorHasNoPrivilege, dbg=dbg)

			# check that there will only by one PCH as a child
			if CSE.dispatcher.countDirectChildResources(self.ri, ty=T.PCH) > 0:
				return Result(status=False, rsc=RC.badRequest, dbg='Only one PCH per AE is allowed')

		return Result(status=True)


	def validate(self, originator:str=None, create:bool=False, dct:JSON=None) -> Result:
		if not (res := super().validate(originator, create, dct)).status:
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
		
		# check csz attribute
		if (csz := self['csz']) is not None:
			for c in csz:
				if c not in C.supportedContentSerializations:
					return Result(status=False, rsc=RC.badRequest, dbg=f'unsupported content serialization: {c}')
		
		# check api attribute
		if (api := self['api']) is None or len(api) < 2:	# at least R|N + another char
			return Result(status=False, rsc=RC.badRequest, dbg=f'missing or empty attribute: "api"')
		if api.startswith('N'):
			pass # simple format
		elif api.startswith('R'):
			if len((apiElements := api.split('.'))) < 3:
				return Result(status=False, rsc=RC.badRequest, dbg=f'wrong format for registered ID in attribute "api": to few elements')
		else:
			Logging.logDebug('wrong format for ID in attribute "api": must start with "R" or "N"')
			return Result(status=False, rsc=RC.badRequest, dbg=f'wrong format for ID in attribute "api": must start with "R" or "N"')


		return Result(status=True)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)

		# Remove itself from the node link in a hosting <node>
		if (nl := self.nl) is not None:
			self._removeAEfromNOD(nl, self.ri)


	def _removeAEfromNOD(self, nodeRi:str, ri:str) -> None:
		""" Remove AE from hosting Node. """
		if (node := CSE.dispatcher.retrieveResource(nodeRi).resource) is not None:
			if (hael := node['hael']) is not None and isinstance(hael, list) and ri in hael:
				hael.remove(ri)
				if len(hael) == 0:
					node.delAttribute('hael')
				else:
					node['hael'] = hael
				node.dbUpdate()


