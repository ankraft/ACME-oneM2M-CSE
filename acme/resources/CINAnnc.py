#
#	CINAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	CIN : Announceable variant
#

from __future__ import annotations
from ..etc.Types import ResourceTypes as T, JSON
from ..services.Validator import constructPolicy, addPolicy
from ..resources.AnnouncedResource import AnnouncedResource
from ..resources.Resource import *

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'et', 'acpi', 'lbl','daci', 'loc',
	'lnk'
])
cinAPolicies = constructPolicy([
	'cnf', 'conr', 'con', 'or'
])
attributePolicies =  addPolicy(attributePolicies, cinAPolicies)
# TODO announceSyncType


class CINAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes:list[T] = [ ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CINAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)

