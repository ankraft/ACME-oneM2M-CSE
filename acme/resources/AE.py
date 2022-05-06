#
#	AE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Application Entity (AE) resource type """

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, ContentSerializationType as CST, Result, ResponseStatusCode as RC, JSON
from ..etc import Utils as Utils
from ..services.Logging import Logging as L
from ..services import CSE as CSE
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource


class AE(AnnounceableResource):
	""" Application Entity (AE) resource type """

	_allowedChildResourceTypes:list[T] = [ T.ACP, T.ACTR, T.CNT, T.FCNT, T.GRP, T.PCH, T.SUB, T.TS, T.TSB ]
	""" The allowed child-resource types. """

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
			'cstn': None,
			'acpi':None,
			'at': None,
			'aa': None,
			'daci': None,
			'ast': None,
			'loc': None,	

			# Resource attributes
			'apn': None,
			'api': None,
			'aei': None,
			'poa': None,
			'nl': None,
			'rr': None,
			'csz': None,
			'esi': None,
			'mei': None,
			'srv': None,
			'regs': None,
			'trps': None,
			'scp': None,
			'tren': None,
			'ape': None,
			'or': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.AE, dct, pi, create = create)

		self.setAttribute('aei', Utils.uniqueAEI(), overwrite = False)
		self.setAttribute('rr', False, overwrite = False)


	def childWillBeAdded(self, childResource:Resource, originator:str) -> Result:
		# Inherited
		if not (res := super().childWillBeAdded(childResource, originator)).status:
			return res

		# Perform checks for <PCH>	
		if childResource.ty == T.PCH:
			# Check correct originator. Even the ADMIN is not allowed that		
			if self.aei != originator:
				L.logDebug(dbg := f'Originator must be the parent <AE>')
				return Result.errorResult(rsc = RC.originatorHasNoPrivilege, dbg = dbg)

			# check that there will only by one PCH as a child
			if CSE.dispatcher.countDirectChildResources(self.ri, ty=T.PCH) > 0:
				return Result.errorResult(rsc = RC.badRequest, dbg = 'Only one PCH per AE is allowed')

		return Result.successResult()


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		# Inherited
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res

		self._normalizeURIAttribute('poa')

		# Update the nl attribute in the hosting node (similar to csebase) in case 
		# the AE is now on a different node. This shouldn't be happen in reality,
		# but technically it is allowed.
		nl = self.nl
		_nl_ = self.__node__
		if nl or _nl_:
			if nl != _nl_:	# if different node
				ri = self.ri

				# Remove from old node first
				if _nl_:
					self._removeAEfromNOD(_nl_)
				self[Resource._node] = nl

				# Add to new node
				if node := CSE.dispatcher.retrieveResource(nl).resource:	# new node
					if not (hael := node.hael):
						node['hael'] = [ ri ]
					else:
						if isinstance(hael, list):
							hael.append(ri)
							node['hael'] = hael
					node.dbUpdate()
			self[Resource._node] = nl
		
		# check csz attribute
		if csz := self.csz:
			for c in csz:
				if c not in CST.supportedContentSerializations():
					return Result.errorResult(dbg  = 'unsupported content serialization: {c}')
		
		# check api attribute
		if not (api := self['api']) or len(api) < 2:	# at least R|N + another char
			return Result.errorResult(dbg = 'missing or empty attribute: "api"')
		if api.startswith('N'):
			pass # simple format
		elif api.startswith('R'):
			if len((apiElements := api.split('.'))) < 3:
				return Result.errorResult(dbg = 'wrong format for registered ID in attribute "api": to few elements')
		else:
			L.logWarn(dbg := f'wrong format for ID in attribute "api": {api} (must start with "R" or "N")')
			return Result.errorResult(dbg = dbg)

		return Result.successResult()


	def deactivate(self, originator:str) -> None:
		# Inherited
		super().deactivate(originator)

		# Remove itself from the node link in a hosting <node>
		if nl := self.nl:
			self._removeAEfromNOD(nl)


	#########################################################################
	#
	#	Resource specific
	#

	def _removeAEfromNOD(self, nodeRi:str) -> None:
		""" Remove AE from hosting Node. 

			Args:
				nodeRI: The hosting node's resource ID.
		"""
		ri = self.ri
		if node := CSE.dispatcher.retrieveResource(nodeRi).resource:
			if (hael := node.hael) and isinstance(hael, list) and ri in hael:
				hael.remove(ri)
				if len(hael) == 0:
					node.delAttribute('hael')
				else:
					node['hael'] = hael
				node.dbUpdate()


