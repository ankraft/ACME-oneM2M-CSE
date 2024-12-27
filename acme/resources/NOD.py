#
#	NOD.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Node
#

from __future__ import annotations

from ..etc.Types import AttributePolicyDict, ResourceTypes
from ..etc.IDUtils import uniqueID
from ..runtime import CSE
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources.Resource import Resource


# TODO Support cmdhPolicy
# TODO Support storage


class NOD(AnnounceableResource):

	resourceType = ResourceTypes.NOD
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

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


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('ni', uniqueID(), overwrite = False)
		super().initialize(pi, originator)


	def deactivate(self, originator:str, parentResource:Resource) -> None:
		super().deactivate(originator, parentResource)

		# Remove self from all hosted AE's (their node links)
		if not self['hael']:
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

