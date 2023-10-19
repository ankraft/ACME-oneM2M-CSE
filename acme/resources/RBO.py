#
#	RBO.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Reboot
#
""" MgmtObj:Reboot (RBO) resource type."""

from __future__ import annotations
from typing import Optional

from ..resources.MgmtObj import MgmtObj
from ..resources.Resource import Resource
from ..etc.Types import AttributePolicyDict, ResourceTypes, Result, JSON
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..helpers.TextTools import findXPath

class RBO(MgmtObj):
	""" MgmtObj:Reboot (RBO) resource type. """

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
		'rbo': None,
		'far': None
	}
	""" The allowed attributes and their policy for this resource type."""
	
	
	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.RBO, create = create)

		self.setAttribute('rbo', False, overwrite = True)	# always False
		self.setAttribute('far', False, overwrite = True)	# always False


	#
	#	Handling the special behaviour for rbo and far attributes in 
	#	validate() and update()
	#

	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		self.setAttribute('rbo', False, overwrite = True)	# always set (back) to False
		self.setAttribute('far', False, overwrite = True)	# always set (back) to False


	def update(self, dct:Optional[JSON] = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		# Check for rbo & far updates 
		rbo = findXPath(dct, '{*}/rbo')
		far = findXPath(dct, '{*}/far')
		if rbo and far:
			raise BAD_REQUEST('update both rbo and far to True is not allowed')

		super().update(dct, originator, doValidateAttributes)
