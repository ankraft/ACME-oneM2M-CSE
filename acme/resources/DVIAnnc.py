#
#	DVIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVI : Announceable variant
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..etc import Utils as Utils
from ..resources.MgmtObjAnnc import *

class DVIAnnc(MgmtObjAnnc):

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

		# MgmtObj attributes
		'mgd': None,
		'obis': None,
		'obps': None,
		'dc': None,
		'mgs': None,
		'cmlk': None,

		# Resource attributes
		'dlb': None,
		'man': None,
		'mfdl': None,
		'mfd': None,
		'mod': None,
		'smod': None,
		'dty': None,
		'dvnm': None,
		'fwv': None,
		'swv': None,
		'hwv': None,
		'osv': None,
		'cnty': None,
		'loc': None,
		'syst': None,
		'spur': None,
		'purl': None,
		'ptl': None
	}

	
	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.DVI, create = create)

