#
#	FCNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" FlexContainerAnnounced resource class """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.AnnouncedResource import AnnouncedResource


class FCNTAnnc(AnnouncedResource):
	""" FlexContainerAnnounced resource class """

	resourceType = ResourceTypes.FCNTAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [	ResourceTypes.ACTR, 
									ResourceTypes.ACTRAnnc, 
									ResourceTypes.CNT, 
									ResourceTypes.CNTAnnc, 
									ResourceTypes.CIN, 
									ResourceTypes.CINAnnc, 
									ResourceTypes.FCNT, 
									ResourceTypes.FCNTAnnc, 
									ResourceTypes.FCI, 
									ResourceTypes.TS, 
									ResourceTypes.TSAnnc, 
									ResourceTypes.SUB ]
	"""	List of allowed child resource types """

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
		'loc': None,
		'lnk': None,

		# Resource attributes
		'cnd': None,
		'or': None,
		'nl': None,
		'mni': None,
		'mia': None,
		'mbs': None
	}
	"""	List of universal, common, and resource specific attributes """


