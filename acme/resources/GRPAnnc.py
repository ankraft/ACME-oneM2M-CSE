#
#	GRPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	GRP : Announceable variant
#


from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..resources.Resource import *


class GRPAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.ACTR, T.ACTRAnnc, T.SUB ]

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
		'mt': None,
		'spty': None,
		'cnm': None,
		'mnm': None,
		'mid': None,
		'macp': None,
		'mtv': None,
		'csy': None,
		'gn': None,
		'ssi': None,
		'nar': None
	}

	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.GRPAnnc, dct, pi = pi, create = create)

