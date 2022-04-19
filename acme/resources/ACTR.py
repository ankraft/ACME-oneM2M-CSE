#
#	ACTR.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Action
#

from __future__ import annotations
from ..etc.Types import AttributePolicyDict, EvalMode, ResourceTypes as T, Result, JSON
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from ..resources.Resource import *
from ..resources.AnnounceableResource import AnnounceableResource
from ..resources import Factory as Factory


class ACTR(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[T] = [ T.SUB ] # TODO Dependecy
	""" The allowed child-resource types. """

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
		'lbl': None,
		'acpi':None,
		'et': None,
		'daci': None,
		'cstn': None,
		'at': None,
		'aa': None,
		'ast': None,
		'cr': None,

		# Resource attributes
		'apy': None,
		'sri': None,
		'evc': None,
		'evm': None,
		'ecp': None,
		'dep': None,
		'orc': None,
		'apv': None,
		'ipu': None,
		'air': None,
	}


	def __init__(self, dct:JSON = None, pi:str = None, create:bool = False) -> None:
		super().__init__(T.ACTR, dct, pi, create = create)



	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		super().validate(originator=originator, create=create, dct=dct, parentResource=parentResource)

		# check whether all the referenced resources exists: subjectResourceID, objectResourceID
		if self.sri is not None: # sri is optional
			if not (res := CSE.dispatcher.retrieveLocalResource(self.sri)).status:
				L.logDebug(dbg := f'sri - referenced resource not found: {res.dbg})')
				return Result.errorResult(dbg = dbg)
		if not (res := CSE.dispatcher.retrieveLocalResource(self.orc)).status:
			L.logDebug(dbg := f'orc - referenced resource not found: {res.dbg})')
			return Result.errorResult(dbg = dbg)
		




# 2) The Receiver shall check if the From parameter contained in the actionPrimitive attribute of the received <action> resource is equal
# to the Originator of this Create request primitive. If it is not, the receiver shall return a response primitive with a Response Status Code indicating "BAD_REQUEST" error.





# 3) The Receiver shall check that if the value of the evalMode attribute received in the request is “off” or “once”, then the evalControlParam 
# attribute is not present in the request. If present, the receiver shall return a response primitive with a Response Status Code indicating "BAD_REQUEST" error.
		evm = self.evm
		if not (EvalMode.off <= evm <= EvalMode.continous):
			L.logDebug(dbg := f'evm - invalid EvalMode: {evm})')
			return Result.errorResult(dbg = dbg)
		# TODO check above	



# 4) The Receiver shall check that the attribute referenced by the subject element of the evalCriteria attribute is an attribute of the resource type 
# referenced by the subjectResourceID attribute if present or the parent resource type if the subjectResourceID attribute is not present. If it is not, 
# the receiver shall return a response primitive with a Response Status Code indicating "BAD_REQUEST" error.

		# check evalCriteria attribute
		evc = self.evc
		# TODO




# 5) The Receiver shall check that the value provided for the threshold element of the evalCriteria attribute is within the value space (as defined in [3]) 
# of the data type of the subject element of the evalCriteria attribute. The Receiver shall also check that the value provided for the operator element of the 
# evalCriteria attribute is a valid value based on Table 6.3.4.2.86-1. If either check fails, the receiver shall return a response primitive with a Response 
# Status Code indicating "BAD_REQUEST" error.

# 6) If evalMode is not “off” then, the Receiver shall process the <action> resource as described in clause 10.2.21 of oneM2M TS-0001 [6] after Recv-6.7.

		return Result(status = True)
