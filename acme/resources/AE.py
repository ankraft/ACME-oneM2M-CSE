#
#	AE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Application Entity (AE) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, ContentSerializationType, JSON
from ..etc.ResponseStatusCodes import BAD_REQUEST, ORIGINATOR_HAS_NO_PRIVILEGE
from ..etc.IDUtils import uniqueAEI
from ..etc.Constants import Constants
from ..runtime.Logging import Logging as L
from ..runtime import CSE
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class AE(AnnounceableResource):
	""" Application Entity (AE) resource type """

	resourceType = ResourceTypes.AE
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.ACP,
													   ResourceTypes.ACTR,
													   ResourceTypes.CNT,
													   ResourceTypes.CRS,
													   ResourceTypes.FCNT,
													   ResourceTypes.GRP,
													   ResourceTypes.LCP,
													   ResourceTypes.PCH,
													   ResourceTypes.PRMR,
													   ResourceTypes.PRP,
													   ResourceTypes.SMD,
													   ResourceTypes.SUB,
													   ResourceTypes.TS,
													   ResourceTypes.TSB ]
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


	def activate(self, parentResource:Resource, originator:str) -> None:

		# Initialize default values
		if not self.hasAttribute('aei'):
			# small optimization: do not overwrite (and do calculations) the aei if it is already set
			self.setAttribute('aei', uniqueAEI(), overwrite = False)
		self.setAttribute('rr', False, overwrite = False)

		super().activate(parentResource, originator)


	def childWillBeAdded(self, childResource:Resource, originator:str) -> None:
		# Inherited
		super().childWillBeAdded(childResource, originator)

		# Perform checks for <PCH>	
		if childResource.ty == ResourceTypes.PCH:
			# Check correct originator. Even the ADMIN is not allowed that		
			if self.aei != originator:
				raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logDebug(f'Originator must be the parent <AE>'))

			# check that there will only by one PCH as a child
			if CSE.dispatcher.countDirectChildResources(self.ri, ty = ResourceTypes.PCH) > 0:
				raise BAD_REQUEST('only one PCH per AE is allowed')


	def validate(self, originator:Optional[str] = None,
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		# Inherited
		super().validate(originator, dct, parentResource)
		self._normalizeURIAttribute('poa')

		# Update the nl attribute in the hosting node (similar to csebase) in case 
		# the AE is now on a different node. This shouldn't be happen in reality,
		# but technically it is allowed.
		nl = self.nl
		_nl_ = self[Constants.attrNode]
		if nl or _nl_:
			if nl != _nl_:	# if different node
				ri = self.ri

				# Remove from old node first
				if _nl_:
					self._removeAEfromNOD(_nl_)
				self[Constants.attrNode] = nl

				# Add to new node
				if node := CSE.dispatcher.retrieveResource(nl):	# new node
					if not (hael := node.hael):
						node['hael'] = [ ri ]
					else:
						if isinstance(hael, list) and ri not in hael:
							hael.append(ri)
							node['hael'] = hael
					node.dbUpdate(True)
			self[Constants.attrNode] = nl
		
		# check csz attribute
		if csz := self.csz:
			for c in csz:
				if c not in ContentSerializationType.supportedContentSerializations():
					raise BAD_REQUEST('unsupported content serialization: {c}')
		
		# check api attribute
		if not (api := self['api']) or len(api) < 2:	# at least R|N + another char
			raise BAD_REQUEST('missing or empty attribute: "api"')
		
		match api:
			case x if x.startswith('N'):
				pass # simple format
			case x if x.startswith('R'):
				if len(x.split('.')) < 3:
					raise BAD_REQUEST('wrong format for registered ID in attribute "api": to few elements')
			# api must normally begin with a lower-case "r", but it is allowed for release 2a and 3
			case x if x.startswith('r'):
				if (rvi := self.getRVI()) is not None and rvi not in ['2a', '3']:
					raise BAD_REQUEST(L.logWarn('lower case "r" is only allowed for release versions "2a" and "3"'))
			case _:
				raise BAD_REQUEST(L.logWarn(f'wrong format for ID in attribute "api": {api} (must start with "R" or "N")'))


	def deactivate(self, originator:str, parentResource:Resource) -> None:
		# Inherited
		super().deactivate(originator, parentResource)

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
				nodeRi: The hosting node's resource ID.
		"""
		ri = self.ri
		if node := CSE.dispatcher.retrieveResource(nodeRi):
			if (hael := node.hael) and isinstance(hael, list) and ri in hael:
				hael.remove(ri)
				if len(hael) == 0:
					node.delAttribute('hael')
				else:
					node['hael'] = hael
				node.dbUpdate(True)

