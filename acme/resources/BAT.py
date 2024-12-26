#
#	BAT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: mgmtObj:Battery
#
""" [Battery] (BAT) management object specialization """
from typing import Optional
from ..helpers.ACMEIntEnum import ACMEIntEnum
from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON
from ..resources.MgmtObj import MgmtObj


class BatteryStatus(ACMEIntEnum):
	NORMAL = 1
	CHARGING =  2
	CHARGING_COMPLETE = 3
	DAMAGED = 4
	LOW_BATTERY = 5
	NOT_INSTALLED = 6
	UNKNOWN = 7
	
	
class BAT(MgmtObj):
	""" [battery] (bat) management object specialization """

	resourceType = ResourceTypes.MGMTOBJ
	""" The resource type """

	typeShortname = resourceType.typeShortname()
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
			'btl': None,
			'bts': None
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None) -> None:
		""" Create a new Battery object. 

			Args:
				dct: The resource dictionary.
				pi: The parent resource ID.
		"""
		super().__init__(dct, pi, mgd = ResourceTypes.BAT)

