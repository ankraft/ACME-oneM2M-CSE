#
#	TSIAnnc.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TSI : Announceable variant
#

from __future__ import annotations

from ..etc.Types import AttributePolicyDict, ResourceTypes
from ..resources.AnnouncedResource import AnnouncedResource

class TSIAnnc(AnnouncedResource):

	resourceType = ResourceTypes.TSIAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	inheritACP = True
	"""	Flag to indicate if the resource type inherits the ACP from the parent resource. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ]

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
    	'dgt': None,
		'con': None,
		'cs': None,
		'snr': None
	}
