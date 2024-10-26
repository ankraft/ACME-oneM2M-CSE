#
#	CRDSAnnc.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CRDS : Announceable variant
#
""" [credentials] announced (CRDSA) `MgmtObjAnnc` specialization. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.MgmtObjAnnc import MgmtObjAnnc

class CRDSAnnc(MgmtObjAnnc):
	""" [credentils] announced (CRDSA) `MgmtObjAnnc` specialization. """

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
			'pur': None,
			'crid': None,
			'crse': None,
			'crtk': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(dct, pi, mgd = ResourceTypes.CRDS, create = create)
