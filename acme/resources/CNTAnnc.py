#
#	CNTAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CNT : Announceable variant
#
""" Container announced (CNTA) resource type."""

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.AnnouncedResource import AnnouncedResource


class CNTAnnc(AnnouncedResource):
	""" Container announced (CNTA) resource type. """

	resourceType = ResourceTypes.CNTAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACTR, 
								   ResourceTypes.ACTRAnnc,
								   ResourceTypes.CNT, 
								   ResourceTypes.CNTAnnc, 
								   ResourceTypes.CIN, 
								   ResourceTypes.CINAnnc, 
								   ResourceTypes.FCNT, 
								   ResourceTypes.FCNTAnnc, 
								   ResourceTypes.SUB, 
								   ResourceTypes.TS, 
								   ResourceTypes.TSAnnc ]
	""" The allowed child-resource types. """

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
		'mni': None,
		'mbs': None,
		'mia': None,
		'li': None,
		'or': None,
		'disr': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """

