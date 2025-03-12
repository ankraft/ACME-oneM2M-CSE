#
#	CINAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CIN : Announceable variant
#
"""  ContentInstance announced (CINA) resource type."""

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes
from ..resources.AnnouncedResource import AnnouncedResource


class CINAnnc(AnnouncedResource):
	""" ContentInstance announced (CINA) resource type. """

	resourceType = ResourceTypes.CINAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]
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
		'ast': None,
		'loc': None,
		'lnk': None,

		# Resource attributes
		'cnf': None,
		'conr': None,
		'con': None,
		'or': None,
		'conr': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """

