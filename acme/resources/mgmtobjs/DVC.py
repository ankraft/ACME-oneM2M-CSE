#
#	DVC.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:DeviceCapability
#
""" [DVC] (DeviceCapability) management object specialization. """

from __future__ import annotations
from typing import Optional

from ...etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ...helpers.TextTools import findXPath
from ..MgmtObj import MgmtObj
from ..Resource import Resource



class DVC(MgmtObj):
	""" [DeviceCapability] (DVC) management object specialization """

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	mgmtType = ResourceTypes.DVC
	""" The management object type """

	typeShortname = mgmtType.typeShortname()
	"""	The resource's domain and type name. """

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
		'can': None,
		'att': None,
		'cas': None,
		'ena': None,
		'dis': None,
		'cus': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('can', 'unknown', overwrite = False)
		self.setAttribute('att', False, overwrite = False)
		self.setAttribute('cas', {	"acn" : "unknown", "sus" : 0 }, overwrite = False)
		self.setAttribute('cus', False, overwrite = False)
		self.setAttribute('ena', True, overwrite = True)	# always True
		self.setAttribute('dis', True, overwrite = True)	# always True
		super().initialize(pi, originator)

	#
	#	Handling the special behaviour for ena and dis attributes in 
	#	validate() and update()
	#

	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		self.setAttribute('ena', True, overwrite = True)	# always set (back) to True
		self.setAttribute('dis', True, overwrite = True)	# always set (back) to True


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		# Check for ena & dis updates 
		ena = findXPath(dct, '{*}/ena')
		dis = findXPath(dct, '{*}/dis')
		if ena and dis:
			raise BAD_REQUEST('updating both ena and dis to True is not allowed')

		super().update(dct, originator, doValidateAttributes)


