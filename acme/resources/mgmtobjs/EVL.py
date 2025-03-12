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

from ...etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ..MgmtObj import MgmtObj
from ...helpers.TextTools import findXPath

class EVL(MgmtObj):

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	mgmtType = ResourceTypes.EVL
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
		'lgt': None,
		'lgd': None,
		'lgst': None,
		'lga': None,
		'lgo': None
	}
	


	def initialize(self, pi:str, originator:str) -> None:
		self.setAttribute('lga', True)
		self.setAttribute('lgo', True)
		super().initialize(pi, originator)


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
