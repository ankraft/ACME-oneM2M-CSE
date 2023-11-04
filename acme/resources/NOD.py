#
#	NOD.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Node
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..etc.Utils import uniqueID
from ..services import CSE
from ..resources.AnnounceableResource import AnnounceableResource


# TODO Support cmdhPolicy
# TODO Support storage


class NOD(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR,
								   ResourceTypes.MGMTOBJ, 
								   ResourceTypes.SCH,
								   ResourceTypes.SMD, 
								   ResourceTypes.FCNT,
								   ResourceTypes.SUB ]


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
		'cstn': None,
		'acpi':None,
		'at': None,
		'aa': None,
		'ast': None,
		'daci': None,

		# Resource attributes
		'ni': None,
		'hcl': None,
		'hael': None,
		'hsl': None,
		'mgca': None,
		'rms': None,
		'nid': None,
		'nty': None
	}


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.NOD, dct, pi, create = create)
		self.setAttribute('ni', uniqueID(), overwrite = False)


	def deactivate(self, originator:str) -> None:
		super().deactivate(originator)

		# Remove self from all hosted AE's (their node links)
		if not (hael := self['hael']):
			return
		ri = self['ri']
		for ae in self['hael']:
			self._removeNODfromAE(ae, ri)


	def _removeNODfromAE(self, aeRI:str, ri:str) -> None:
		""" Remove NOD.ri from AE node link. """
		if aeResource := CSE.dispatcher.retrieveResource(aeRI):
			if (nl := aeResource.nl) and isinstance(nl, str) and ri == nl:
				aeResource.delAttribute('nl')
				aeResource.dbUpdate(True)

