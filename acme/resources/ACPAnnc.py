#
#	ACPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" AccessControlPolicy announced (ACPA) resource type. """

from __future__ import annotations
from typing import Optional

from ..helpers.TextTools import simpleMatch
from ..etc.Types import AttributePolicyDict, ResourceTypes, Permission, JSON
from ..resources.AnnouncedResource import AnnouncedResource


class ACPAnnc(AnnouncedResource):
	""" AccessControlPolicy announced (ACPA) resource type """

	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB ]
	""" The allowed child-resource types. """

	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {	
			# Common and universal attributes for announced resources
			'rn': None,
		 	'ty': None,
			'ri': None,
			'pi': None,
			'ct': None,
			'lt': None,
			'et': None,
			'lbl': None,
			'acpi':None,
			'daci': None,
			'lnk': None,
			'ast': None,

			# Resource attributes
			'pv': None,
			'pvs': None,
			'adri': None,
			'apri': None,
			'airi': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:JSON, pi:Optional[str] = None, create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.ACPAnnc, dct, pi = pi, create = create)

