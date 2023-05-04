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
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST
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


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# Check referenced resources
		sriResource, orcResource = self._checkReferencedResources(originator, self.sri, self.orc)
		self.sri = riFromID(self.sri)
		self.orc = riFromID(self.orc)

		#	Check that the from parameter of the actionPrimitive is the originator
		self._checkApvFrom(originator)

		# Check evalmode and control parameters
		evm = self.evm
		if evm in [EvalMode.off, EvalMode.once] and self.hasAttribute('ecp'):
			raise BAD_REQUEST(L.logDebug(f'ecp - must not be present for evm: {evm}'))

		#	Check that the attribute referenced by the evalCriteria does exist
		checkResource = parentResource \
						if self.sri is None \
						else sriResource
		sbjt = self.evc['sbjt']
		if not checkResource.hasAttributeDefined(sbjt):
			raise BAD_REQUEST(L.logDebug(f'sbjt - subject resource hasn\'t the attribute: {sbjt} defined: {checkResource.ri}'))

		#	Check evalCriteria threshold attribute's value type and operation validity
		dataType = self._checkThreshold(sbjt, (thld := self.evc['thld']))

		#	Check evalCriteria operator
		self._checkOperator(EvalCriteriaOperator(self.evc['optr']), dataType, sbjt)

		# Schedule and process the <action> resource
		CSE.action.scheduleAction(self)


	def update(self, dct:JSON = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		
		# Check referenced resources
		sri = riFromID(findXPath(dct, 'm2m:actr/sri'))
		orc = riFromID(findXPath(dct, 'm2m:actr/orc'))
		self._checkReferencedResources(originator, sri, orc)

		# Check not-NULL orc
		if 'orc' in dct['m2m:actr'] and findXPath(dct, 'm2m:actr/orc') is None:
			raise BAD_REQUEST(L.logDebug(f'orc - must not be NULL in an UPDATE request'))

		# TODO check existence of dependencies

		# TODO The Receiver shall check that any <dependency> resources referenced by the dependencies attribute
		#  are child resources of the <action> resource. If any are not child resources, then the Receiver shall 
		# return a response primitive with a Response Status Code indicating "BAD_REQUEST" error.

		#	Check that the from parameter of the actionPrimitive is the originator
		self._checkApvFrom(originator)

		# Check that ecp is not set in the request or resource if new evalmode is off or once
		if (dctEvm := findXPath(dct, 'm2m:actr/evm')) in [ EvalMode.off, EvalMode.once ]:
			if findXPath(dct, 'm2m:actr/ecp'):
				raise BAD_REQUEST(L.logDebug(f'ecp - must not be present in the UPDATE request if evm is: {dctEvm} in the request'))
			if self.ecp:
				raise BAD_REQUEST(L.logDebug(f'ecp - must not be present in the UPDATE request if evm is : {dctEvm} in the <actr> resource'))


		# Determine newSri. Might be the parent RI if not present at all
		dctSri = findXPath(dct, 'm2m:actr/sri') 
		newSri = dctSri if dctSri else self.sri	
		newSri = newSri if newSri else self.pi
		dctEvc = findXPath(dct, 'm2m:actr/evc')
		newEvc = dctEvc if dctEvc else self.evc

		# Check that a new sbjt attribute exists in the (potentially new) subject target
		# Also check when only the subject target changes
		if dctEvc or dctSri:
			sriResource = CSE.dispatcher.retrieveResource(newSri, originator = self.getOriginator())
			sbjt = newEvc['sbjt']
			if not sriResource.hasAttributeDefined(sbjt):
				raise BAD_REQUEST(L.logDebug(f'sbjt - subject resource hasn\'t the attribute: {sbjt} defined: {sriResource.ri}'))

		#	Check evalCriteria threshold attribute's value type and operation validity
		if dctEvc:
			dataType = self._checkThreshold(sbjt, (thld := dctEvc['thld']))

			#	Check evalCriteria operator
			self._checkOperator(EvalCriteriaOperator(dctEvc['optr']), dataType, sbjt)

		# Store some attributes for later evaluation
		newEcp = findXPath(dct, 'm2m:actr/ecp')
		origEvm = self.evm

		# Now, apply all changes
		super().update(dct, originator, doValidateAttributes)

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


	def deactivate(self, originator:str) -> None:
		# Unschedule the action
		CSE.action.unscheduleAction(self)
		return super().deactivate(originator)


	###########################################################################
	#
	#	Internals
	#

	def _checkReferencedResources(self, originator:str, sri:str, orc:str) -> Tuple[Resource, Resource]:
		"""	Check whether all the referenced resources exists and we have access: subjectResourceID, objectResourceID
		"""
		# TODO doc

		resSri = None
		resOrc = None
		if sri is not None: # sri is optional
			try:
				resSri = CSE.dispatcher.retrieveResourceWithPermission(sri, originator, Permission.RETRIEVE)
			except ResponseException as e:
				raise BAD_REQUEST(dbg = e.dbg)

			# try:
			# 	resSri = CSE.dispatcher.retrieveResource(riFromID(sri), originator)
			# except ResponseException as e:
			# 	raise BAD_REQUEST(L.logDebug(f'sri - referenced resource: {sri} not found: {e.dbg})'))
			# if not CSE.security.hasAccess(originator, resSri, Permission.RETRIEVE):
			# 	raise BAD_REQUEST(L.logDebug(f'sri - originator has no access to the referenced resource: {sri}'))

		if orc is not None:
			try:
				resOrc = CSE.dispatcher.retrieveResourceWithPermission(orc, originator, Permission.RETRIEVE)
			except ResponseException as e:
				raise BAD_REQUEST(dbg = e.dbg)

			# try:
			# 	resOrc = CSE.dispatcher.retrieveLocalResource(riFromID(orc), originator = originator)
			# except ResponseException as e:
			# 	raise BAD_REQUEST(L.logDebug(f'orc - referenced resource: {orc} not found: {e.dbg})'))
			# if not CSE.security.hasAccess(originator, resOrc, Permission.RETRIEVE):
			# 	raise BAD_REQUEST(L.logDebug(f'orc - originator has no access to the referenced resource: {orc}'))
			
		return (resSri, resOrc)


	def _checkApvFrom(self, originator:str) -> None:
		"""	Check that the from parameter of the actionPrimitive is the originator
		"""
		# TODO doc
		if (apvFr := findXPath(self.apv, 'fr')) != originator:
			raise BAD_REQUEST(L.logDebug(f'invalid "apv.from": {apvFr}. Must be: {originator}'))


	def _checkThreshold(self, sbjt:str, thld:Any) -> BasicType:
		# TODO doc
		#	Check evalCriteria threshold attribute's value type and operation validity
		try:
			typ, value = CSE.validator.validateAttribute(sbjt, thld)
		except ResponseException as e:
			raise BAD_REQUEST(L.logDebug(f'thld - invalid threshold value: {thld} for attribute: {sbjt} : {e.dbg}'))
		# the result "res" contains the attribute's data type in a tuple
		return typ


	def _checkOperator(self, optr:EvalCriteriaOperator, dataType:BasicType, sbjt:str) -> None:
		# TODO doc
		if not optr.isAllowedType(dataType):
			raise BAD_REQUEST(L.logDebug(f'optr - invalid data type: {dataType} and operator: {optr} for attribute: {sbjt}'))

