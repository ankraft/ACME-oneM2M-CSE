#
#	FWRAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	FWR : Announceable variant
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.MgmtObjAnnc import *


class FWRAnnc(MgmtObjAnnc):

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
		'vr': None,
		'fwn': None,
		'url': None,
		'uds': None,
		'ud': None
	}

	
	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.FWR, create = create)

