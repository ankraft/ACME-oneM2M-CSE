#
#	CSEBaseAnnc.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CNT : Announceable variant
#
""" CSEBase announced (CSEBaseA) resource type. """

from __future__ import annotations

from ..etc.Types import AttributePolicyDict, ResourceTypes
from ..resources.AnnouncedResource import AnnouncedResource


class CSEBaseAnnc(AnnouncedResource):

	resourceType = ResourceTypes.CSEBaseAnnc
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [	ResourceTypes.ACPAnnc, 
									ResourceTypes.ACTRAnnc, 
									ResourceTypes.AEAnnc, 
									ResourceTypes.CNTAnnc, 
									ResourceTypes.FCNTAnnc, 
									ResourceTypes.GRPAnnc,
									ResourceTypes.LCPAnnc,
									ResourceTypes.NODAnnc, 
								    ResourceTypes.PRMRAnnc,
									ResourceTypes.SCHAnnc,
									ResourceTypes.SUB, 
									ResourceTypes.TSAnnc, 
									ResourceTypes.TSBAnnc ]


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
		'loc': None,	
		'cstn': None,
		'acpi': None,
		'daci': None,
		'lnk': None,

		# Resource attributes
		'esi': None,
		'srv': None,
		# TODO no CSI?
	}


