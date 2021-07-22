#
#	GRPAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	GRP : Announceable variant
#


from .AnnouncedResource import AnnouncedResource
from .Resource import *
from Types import ResourceTypes as T, JSON
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'et', 'acpi', 'lbl','daci', 'loc',
	'lnk' 
])
nodAPolicies = constructPolicy([
		'ni', 'hcl', 'hael', 'hsl', 'mgca', 'rms', 'nid', 'nty'
])
attributePolicies =  addPolicy(attributePolicies, nodAPolicies)
# TODO announceSyncType


class NODAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.MGMTOBJAnnc, T.SUB ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.NODAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)

