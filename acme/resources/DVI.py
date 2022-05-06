#
#	DVI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceInfo
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.MgmtObj import *


defaultDeviceType = 'unknown'
defaultModel = "unknown"
defaultManufacturer = "unknown"
defaultDeviceLabel = "unknown serial id"

class DVI(MgmtObj):

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

		self.setAttribute('dty', defaultDeviceType, overwrite = False)
		self.setAttribute('mod', defaultModel, overwrite = False)
		self.setAttribute('man', defaultManufacturer, overwrite = False)
		self.setAttribute('dlb', defaultDeviceLabel, overwrite = False)

