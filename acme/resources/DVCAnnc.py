#
#	DVCAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVC : Announceable variant
#
""" [DVCAnnc] (DeviceCapabilityAnnc) management object specialization """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.MgmtObjAnnc import MgmtObjAnnc


class DVCAnnc(MgmtObjAnnc):
	""" [DeviceCapabilityAnnc] (DVCAnnc) management object specialization """

	# Attributes and Attribute policies for this Resource Class
	# Assigned during startup in the Importer
	_attributes:AttributePolicyDict = {		
		# Common and universal attributes for announced resources
		'rn': None,
		'ty': None,
		'ri': None,
		'pi': None,
		'ct': None,
		'lt': None,
		'et': None,
		'lbl': None,
		'acpi':None,
		'daci': None,
		'ast': None,
		'lnk': None,

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


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		""" Initialize the DVCAnnc instance.

			Args:
				dct: The JSON dictionary to create the DVCAnnc from.
				pi: The parent's resource ID.
				create: Indicates creation of the resource. Defaults to False.
		"""
		super().__init__(dct, pi, mgd = ResourceTypes.DVC, create = create)

