#
#	TSAnnc.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	TS : Announceable variant
#

from __future__ import annotations
from .AnnouncedResource import AnnouncedResource
from .Resource import *
from Types import ResourceTypes as T, JSON
from Validator import constructPolicy, addPolicy

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'et', 'acpi', 'lbl','daci', 'loc',
	'lnk' 
])
tsAPolicies = constructPolicy([
	'mni', 'mbs', 'mia', 'cni', 'cbs', 'pei', 'peid', 'mdd', 'mdn', 'mdlt', 'mdc', 'mdt', 'cnf',
	'or'
])

attributePolicies =  addPolicy(attributePolicies, tsAPolicies)


class TSAnnc(AnnouncedResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.SUB, T.TSI,	T.TSIAnnc ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.TSAnnc, dct, pi=pi, create=create, attributePolicies=attributePolicies)

