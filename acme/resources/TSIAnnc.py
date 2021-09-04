#
#	TSIAnnc.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TSI : Announceable variant
#

from __future__ import annotations
from ..etc.Types import ResourceTypes as T, JSON
from ..services.Validator import constructPolicy, addPolicy
from ..resources.Resource import *
from ..resources.AnnouncedResource import AnnouncedResource

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'et', 'acpi', 'lbl','daci', 'loc',
	'lnk' 
])
tsiAPolicies = constructPolicy([
    'dgt', 'con', 'cs', 'snr'
])

attributePolicies =  addPolicy(attributePolicies, tsiAPolicies)

class TSIAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes:list[T] = [ ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.TSIAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)
		 
