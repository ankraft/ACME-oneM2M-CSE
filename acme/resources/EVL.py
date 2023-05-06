#
#	EVL.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:EventLog
#

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, Result
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource
from ..helpers.TextTools import findXPath

class EVL(MgmtObj):

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
		'lgt': None,
		'lgd': None,
		'lgst': None,
		'lga': None,
		'lgo': None
	}
	

	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.EVL, create = create)

		self.setAttribute('lga', True)
		self.setAttribute('lgo', True)

	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		# Check for rbo & far updates 
		if findXPath(dct, '{*}/lga') and findXPath(dct, '{*}/lgo'):
			raise BAD_REQUEST('update both lga and lgo to True at the same time is not allowed')

		# Always overwrite with True
		self.setAttribute('lga', True)
		self.setAttribute('lgo', True)
		super().update(dct, originator, doValidateAttributes)
