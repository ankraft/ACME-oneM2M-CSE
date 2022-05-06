#
#	BAT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Battery
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.MgmtObj import *


btsNORMAL			 = 1
btsCHARGING			 = 2
btsCHARGING_COMPLETE = 3
btsDAMAGED			 = 4
btsLOW_BATTERY		 = 5
btsNOT_INSTALLED	 = 6
btsUNKNOWN			 = 7


defaultBatteryLevel  = 100
defaultBatteryStatus = btsUNKNOWN

class BAT(MgmtObj):

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
			'btl': None,
			'bts': None
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.BAT, create = create)

		self.setAttribute('btl', defaultBatteryLevel, overwrite = False)
		self.setAttribute('bts', defaultBatteryStatus, overwrite = False)

