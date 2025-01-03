#
#	DATC.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:dataCollection
#

from __future__ import annotations
from typing import Optional

from ...etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ...etc.ResponseStatusCodes import BAD_REQUEST
from ...helpers.TextTools import findXPath
from ..MgmtObj import MgmtObj
from ..Resource import Resource
from ...runtime.Logging import Logging as L


class DATC(MgmtObj):

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	mgmtType = ResourceTypes.DATC
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
		'cntp': None,
		'rpsc': None,
		'mesc': None,
		'rpil': None,
		'meil': None,
		'cmlk': None,
	}

	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		L.isDebug and L.logDebug(f'Validating semanticDescriptor: {self.ri}')
		super().validate(originator, dct, parentResource)

		# Test for unique occurence of either rpsc and rpil		
		rpscNew = findXPath(dct, '{*}/rpsc')
		rpilNew = findXPath(dct, '{*}/rpil')
		if (rpscNew or self.rpsc) and (rpilNew or self.rpil):
			raise BAD_REQUEST(L.logDebug(f'rpsc and rpil shall not be set together'))

		# Test for unique occurence of either mesc and meil
		mescNew = findXPath(dct, '{*}/mesc')		
		meilNew = findXPath(dct, '{*}/meil')		
		if (mescNew or self.mesc) and (meilNew or self.meil):
			raise BAD_REQUEST(L.logDebug(f'mesc and meil shall not be set together'))
	
