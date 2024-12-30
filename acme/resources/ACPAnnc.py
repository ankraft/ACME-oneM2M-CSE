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

	resourceType = ResourceTypes.ACPAnnc
	""" The resource type """

	typeShortname = ResourceTypes.ACPAnnc.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """


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


