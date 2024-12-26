#
#	NODAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	NODAnnc : Announceable variant
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.AnnouncedResource import AnnouncedResource


class NODAnnc(AnnouncedResource):

	resourceType = ResourceTypes.NODAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR, 
								   ResourceTypes.ACTRAnnc, 
								   ResourceTypes.MGMTOBJAnnc, 
								   ResourceTypes.SCHAnnc,
								   ResourceTypes.SUB ]

	# Attributes and Attribute policies for this Resource Class
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
		'ast': None,
		'lnk': None,

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
