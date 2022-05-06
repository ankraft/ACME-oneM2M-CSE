#
#	TSIAnnc.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TSI : Announceable variant
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.Resource import *
from ..resources.AnnouncedResource import AnnouncedResource

class TSIAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ ]

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


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.TSIAnnc, dct, pi = pi, inheritACP = True, create = create)
		 
