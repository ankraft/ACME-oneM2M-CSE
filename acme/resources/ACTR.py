#
#	ACTR.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Action
#

from __future__ import annotations
from typing import Optional, Tuple, Any, cast

from ..etc.Types import AttributePolicyDict, EvalMode, ResourceTypes, Result, JSON, Permission, EvalCriteriaOperator
from ..etc.Types import BasicType
from ..etc.Utils import riFromID
from ..helpers.TextTools import findXPath
from ..services import CSE
from ..services.Logging import Logging as L
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class ACTR(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.DEPR,
													   ResourceTypes.SUB
													 ]
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


	def __init__(self, dct:Optional[JSON] = None, pi:Optional[str] = None, create:Optional[bool] = False) -> None:
		# the following two lines are needed bc mypy cannot determine the type otherwise
		self.sri:str
		self.orc:str
		super().__init__(ResourceTypes.ACTR, dct, pi, create = create)


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# Check referenced resources
		if not (res := self._checkReferencedResources(originator, self.sri, self.orc)).status:
			return res
		sriResource = cast(Resource, cast(Tuple, res.data)[0])
		orcResource = cast(Resource, cast(Tuple, res.data)[1])
		self.sri = riFromID(self.sri)
		self.orc = riFromID(self.orc)

		#	Check that the from parameter of the actionPrimitive is the originator
		if not (res := self._checkApvFrom(originator)).status:
			return res

		# Check evalmode and control parameters
		evm = self.evm
		if evm in [EvalMode.off, EvalMode.once] and self.hasAttribute('ecp'):
			return Result.errorResult(dbg = L.logDebug(f'ecp - must not be present for evm: {evm}'))

		#	Check that the attribute referenced by the evalCriteria does exist
		checkResource = parentResource \
						if self.sri is None \
						else sriResource
		sbjt = self.evc['sbjt']
		if not checkResource.hasAttributeDefined(sbjt):
			return Result.errorResult(dbg = L.logDebug(f'sbjt - subject resource hasn\'t the attribute: {sbjt} defined: {checkResource.ri}'))

		#	Check evalCriteria threshold attribute's value type and operation validity
		if not (res := self._checkThreshold(sbjt, (thld := self.evc['thld']))).status:
			return res
		dataType = cast(BasicType, res.data)

		#	Check evalCriteria operator
		if not (res := self._checkOperator(EvalCriteriaOperator(self.evc['optr']), dataType, sbjt)).status:
			return res

		# Schedule and process the <action> resource
		CSE.action.scheduleAction(self)

		return Result.successResult()


	def update(self, dct:JSON = None, originator:Optional[str] = None, doValidateAttributes:Optional[bool] = True) -> Result:
		
		# Check referenced resources
		sri = riFromID(findXPath(dct, 'm2m:actr/sri'))
		orc = riFromID(findXPath(dct, 'm2m:actr/orc'))
		if not (res := self._checkReferencedResources(originator, sri, orc)).status:
			return res

		# Check not-NULL orc
		if 'orc' in dct['m2m:actr'] and findXPath(dct, 'm2m:actr/orc') is None:
			return Result.errorResult(dbg = L.logDebug(f'orc - must not be NULL in an UPDATE request'))

		# TODO check existence of dependencies

		# TODO The Receiver shall check that any <dependency> resources referenced by the dependencies attribute
		#  are child resources of the <action> resource. If any are not child resources, then the Receiver shall 
		# return a response primitive with a Response Status Code indicating "BAD_REQUEST" error.

		#	Check that the from parameter of the actionPrimitive is the originator
		if not (res := self._checkApvFrom(originator)).status:
			return res

		# Check that ecp is not set in the request or resource if new evalmode is off or once
		if (dctEvm := findXPath(dct, 'm2m:actr/evm')) in [ EvalMode.off, EvalMode.once ]:
			if findXPath(dct, 'm2m:actr/ecp'):
				return Result.errorResult(dbg = L.logDebug(f'ecp - must not be present in the UPDATE request if evm is: {dctEvm} in the request'))
			if self.ecp:
				return Result.errorResult(dbg = L.logDebug(f'ecp - must not be present in the UPDATE request if evm is : {dctEvm} in the <actr> resource'))


		# Determine newSri. Might be the parent RI if not present at all
		dctSri = findXPath(dct, 'm2m:actr/sri') 
		newSri = dctSri if dctSri else self.sri	
		newSri = newSri if newSri else self.pi
		dctEvc = findXPath(dct, 'm2m:actr/evc')
		newEvc = dctEvc if dctEvc else self.evc

		# Check that a new sbjt attribute exists in the (potentially new) subject target
		# Also check when only the subject target changes
		if dctEvc or dctSri:
			if not (res := CSE.dispatcher.retrieveResource(newSri, originator = self.getOriginator())).status:
				return res
			sriResource = res.resource
			sbjt = newEvc['sbjt']
			if not sriResource.hasAttributeDefined(sbjt):
				return Result.errorResult(dbg = L.logDebug(f'sbjt - subject resource hasn\'t the attribute: {sbjt} defined: {sriResource.ri}'))

		#	Check evalCriteria threshold attribute's value type and operation validity
		if dctEvc:
			if not (res := self._checkThreshold(sbjt, (thld := dctEvc['thld']))).status:
				return res
			dataType = cast(BasicType, res.data)

			#	Check evalCriteria operator
			if not (res := self._checkOperator(EvalCriteriaOperator(dctEvc['optr']), dataType, sbjt)).status:
				return res

		# Store some attributes for later evaluation
		newEcp = findXPath(dct, 'm2m:actr/ecp')
		origEvm = self.evm

		# Now, apply all changes
		if not (res := super().update(dct, originator)).status:
			return res

		# Restart the monitoring (unschedule and restart later) when new evm is given
		doScheduleAction = False
		if dctEvm is not None:
			CSE.action.unscheduleAction(self)
			# don't restart when new evm == off
			if dctEvm in [ EvalMode.once, EvalMode.periodic, EvalMode.continous ]:
				doScheduleAction = True
		
		# Restart periodic and continious when new ecp (only) was set
		if newEcp is not None and dctEvm is None and origEvm in [ EvalMode.periodic, EvalMode.continous ]:
			CSE.action.unscheduleAction(self)
			doScheduleAction = True

		# Restart monitoring if necessary
		if doScheduleAction:
			CSE.action.scheduleAction(self)

		# Call this last
		return Result.successResult()


	def deactivate(self, originator:str) -> None:
		# Unschedule the action
		CSE.action.unscheduleAction(self)
		return super().deactivate(originator)


	###########################################################################
	#
	#	Internals
	#

	def _checkReferencedResources(self, originator:str, sri:str, orc:str) -> Result:
		"""	Check whether all the referenced resources exists and we have access: subjectResourceID, objectResourceID
		"""
		# TODO doc

		resSri = None
		resOrc = None
		if sri is not None: # sri is optional
			
			if not (resSri := CSE.dispatcher.retrieveResource(riFromID(sri), originator)).status:
				return Result.errorResult(dbg = L.logDebug(f'sri - referenced resource: {sri} not found: {resSri.dbg})'))
			if not CSE.security.hasAccess(originator, resSri.resource, Permission.RETRIEVE):
				return Result.errorResult(dbg = L.logDebug(f'sri - originator has no access to the referenced resource: {sri}'))

		if orc is not None:
			if not (resOrc := CSE.dispatcher.retrieveLocalResource(riFromID(orc), originator = originator)).status:
				return Result.errorResult(dbg = L.logDebug(f'orc - referenced resource: {orc} not found: {resOrc.dbg})'))
			if not CSE.security.hasAccess(originator, resOrc.resource, Permission.RETRIEVE):
				return Result.errorResult(dbg = L.logDebug(f'orc - originator has no access to the referenced resource: {orc}'))
			
		return Result(status = True, 
					  data = (resSri.resource if resSri else None, 
							  resOrc.resource if resOrc else None))


	def _checkApvFrom(self, originator:str) -> Result:
		"""	Check that the from parameter of the actionPrimitive is the originator
		"""
		# TODO doc
		if (apvFr := findXPath(self.apv, 'fr')) != originator:
			return Result.errorResult(dbg = L.logDebug(f'invalid "apv.from": {apvFr}. Must be: {originator}'))
		return Result.successResult()


	def _checkThreshold(self, sbjt:str, thld:Any) -> Result:
		# TODO doc
		#	Check evalCriteria threshold attribute's value type and operation validity
		if not (res := CSE.validator.validateAttribute(sbjt, thld)).status:
			return Result.errorResult(dbg = L.logDebug(f'thld - invalid threshold value: {thld} for attribute: {sbjt}'))
		# the result "res" contains the attribute's data type in a tuple
		return Result(status = True, data = cast(Tuple, res.data)[0])


	def _checkOperator(self, optr:EvalCriteriaOperator, dataType:BasicType, sbjt:str) -> Result:
		# TODO doc
		if not optr.isAllowedType(dataType):
			return Result.errorResult(dbg = L.logDebug(f'optr - invalid data type: {dataType} and operator: {optr} for attribute: {sbjt}'))
		return Result.successResult()

