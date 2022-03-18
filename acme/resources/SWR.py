#
#	SWR.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Software
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, JSON
from ..resources.MgmtObj import *

statusUninitialized = 0
statusSuccessful = 1
statusFailure = 2
statusInProcess = 3

defaultSoftwareName = 'unknown'
defaultVersion = '0.0'
defaultURL = 'unknown'
defaultStatus = { 'acn' : '', 'sus' : statusUninitialized }


class SWR(MgmtObj):

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
		'vr': None,
		'swn': None,
		'url': None,
		'ins': None,
		'acts': None,
		'in': None,
		'un': None,
		'act': None,
		'dea': None
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(dct, pi, mgd = T.SWR, create = create)

		self.setAttribute('vr', defaultVersion, overwrite = False)
		self.setAttribute('swn', defaultSoftwareName, overwrite = False)
		self.setAttribute('url', defaultURL, overwrite = False)
		self.setAttribute('ins', defaultStatus, overwrite = False)
		self.setAttribute('acts', defaultStatus, overwrite = False)
		self.setAttribute('in', False, overwrite = False)
		self.setAttribute('un', False, overwrite = False)
		self.setAttribute('act', False, overwrite = False)
		self.setAttribute('dea', False, overwrite = False)

