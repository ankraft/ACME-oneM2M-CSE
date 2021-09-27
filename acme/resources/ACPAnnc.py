#
#	ACPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Acp : Announceable variant
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Permission, JSON
from ..resources.AnnouncedResource import AnnouncedResource
from ..resources.Resource import *


class ACPAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.SUB ]

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
			'lnk': None,
			'ast': None,

			# Resource attributes
			'pv': None,
			'pvs': None,
			'adri': None,
			'apri': None,
			'airi': None
	}


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.ACPAnnc, dct, pi=pi, create=create)


	def checkSelfPermission(self, origin:str, requestedPermission:int) -> bool:
		for p in self['pvs/acr']:
			if requestedPermission & p['acop'] == Permission.NONE:	# permission not fitting at all
				continue
			if 'all' in p['acor'] or origin in p['acor']:
				return True
		return False
