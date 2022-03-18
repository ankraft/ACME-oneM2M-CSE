#
#	ANDI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:areaNwkDeviceInfo
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.MgmtObj import *

defaultDeviceID = ''

class ANDI(MgmtObj):

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
			'cstn': None,
			'acpi':None,
			'at': None,
			'aa': None,
			'ast': None,
			'daci': None,
			
			# MgmtObj attributes
			'mgd': None,
			'obis': None,
			'obps': None,
			'dc': None,
			'mgs': None,
			'cmlk': None,

			# Resource attributes
			'dvd': None,
			'dvt': None,
			'awi': None,
			'sli': None,
			'sld': None,
			'ss': None,
			'lnh': None
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.ANDI, create = create)

		self.setAttribute('dvd', defaultDeviceID, overwrite = False)
		self.setAttribute('dvt', '', overwrite = False)
		self.setAttribute('awi', '', overwrite = False)
