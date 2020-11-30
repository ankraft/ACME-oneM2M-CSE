#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#

from Constants import Constants as C
from Types import ResourceTypes as T, Result
from Validator import constructPolicy, addPolicy
import Utils
from .Resource import *
from .AnnounceableResource import AnnounceableResource


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'ty', 'ri', 'rn', 'pi', 'acpi', 'ct', 'lt', 'et', 'lbl', 'daci', 
])
reqPolicies = constructPolicy([
])
attributePolicies = addPolicy(attributePolicies, reqPolicies)


class PCH(Resource):

	def __init__(self, dct:dict=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.PCH, dct, pi, create=create, attributePolicies=attributePolicies)

		# TODO attribute requestAggregation


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource, [ T.PCH_PCU ])


