#
#	SCHAnnc.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Schedule Announced
#

""" Schedule Announced(SCHA) resource type. """

from __future__ import annotations

from ..etc.Types import AttributePolicyDict, ResourceTypes
from ..resources.AnnouncedResource import AnnouncedResource


class SCHAnnc(AnnouncedResource):
	""" Schedule Announced (SCHA) resource type. """

	resourceType = ResourceTypes.SCHAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]
	""" The allowed child-resource types. """

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
		'acpi':None,
		'daci': None,
		'lnk': None,
		'ast': None,

		# Resource attributes
		'se': None,
		'nco': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """

