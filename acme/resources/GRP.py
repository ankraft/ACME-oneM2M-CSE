#
#	GRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Group
#

from ..etc.Types import AttributePolicyDict, ResourceTypes as T, Result, ConsistencyStrategy, JSON
from ..services.Logging import Logging as L
from ..services import CSE as CSE
from ..resources import Factory as Factory
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource


class GRP(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ T.ACTR, T.SUB, T.GRP_FOPT ]

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
		'cr': None,

		# Resource attributes
		'mt': None,
		'spty': None,
		'cnm': None,
		'mnm': None,
		'mid': None,
		'macp': None,
		'mtv': None,
		'csy': None,
		'gn': None,
		'ssi': None,
		'nar': None
	}


	def __init__(self, dct:JSON = None, pi:str = None, fcntType:str = None, create:bool = False) -> None:
		super().__init__(T.GRP, dct, pi, create = create)

		self.setAttribute('mt', int(T.MIXED), overwrite = False)
		self.setAttribute('ssi', False, overwrite = True)
		self.setAttribute('cnm', 0, overwrite = False)	# calculated later
		self.setAttribute('mid', [], overwrite = False)			
		self.setAttribute('mtv', False, overwrite = False)
		self.setAttribute('csy', ConsistencyStrategy.abandonMember, overwrite = False)

		# These attributes are not provided by default: mnm (no default), macp (no default)
		# optional set: spty, gn, nar


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		
		# add fanOutPoint
		ri = self.ri
		if L.isDebug: L.logDebug(f'Registering fanOutPoint resource for: {ri}')
		fanOutPointResource = Factory.resourceFromDict({ 'pi' : ri }, ty = T.GRP_FOPT).resource
		if not (res := CSE.dispatcher.createResource(fanOutPointResource, self, originator)).resource:
			return Result(status = False, rsc = res.rsc, dbg = res.dbg)
		return Result.successResult()


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		return CSE.group.validateGroup(self, originator)


