#
#	PCH.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PollingChannel
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, JSON
from ..resources.Resource import *
from ..resources import Factory as Factory
from ..services import CSE as CSE
from ..services.Logging import Logging as L


class PCH(Resource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.PCH_PCU ]

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

		# Resource attributes

		# TODO requestAggregation attribute as soon as it has been specified in TS-0004

	}


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		# PCH inherits from its parent, the <AE>
		super().__init__(T.PCH, dct, pi, create=create, inheritACP=True)


# TODO test Retrieve by AE only! Add new willBeRetrieved() function
# TODO continue with 10.2.5.14 Retrieve <pollingChannel>

	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# NOTE Check for uniqueness is done in <AE>.childWillBeAdded()
		# TODO the same for CSR
			
		
		# register pollingChannelURI virtual resource
		if L.isDebug: L.logDebug(f'Registering <PCU> for: {self.ri}')
		pcu = Factory.resourceFromDict(pi=self.ri, ty=T.PCH_PCU).resource	# rn is assigned by resource itself
		if not (res := CSE.dispatcher.createResource(pcu)).resource:
			return Result(status=False, rsc=res.rsc, dbg=res.dbg)

		return Result(status=True)

