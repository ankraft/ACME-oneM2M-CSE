#
#	ACTR.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: Action
#

""" Action (ACTR) resource type. """

from __future__ import annotations
from typing import Optional, Tuple

from configparser import ConfigParser

from ..etc.Types import AttributePolicyDict, EvalMode, ResourceTypes, JSON, Permission, EvalCriteriaOperator, Operation
from ..etc.ResponseStatusCodes import ResponseException, BAD_REQUEST
from ..etc.ACMEUtils import riFromID, compareIDs
from ..helpers.TextTools import findXPath
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration, ConfigurationError
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource


class ACTR(AnnounceableResource):
	""" Action (ACTR) resource type. """

	resourceType = ResourceTypes.ACTR
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

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
	"""	Attributes and `AttributePolicy` for this resource type. """


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)

		# Check referenced resources
		sriResource, orcResource = self._checkReferencedResources(originator, 
																  self.sri, 	# type: ignore[has-type]
																  self.orc, 	# type: ignore[has-type]
																  self._getApvOperation())
		self.sri = riFromID(self.sri)	# type: ignore[has-type]
		self.orc = riFromID(self.orc)	# type: ignore[has-type]

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

		# Check that the evalCriteria is correct
		try:
			CSE.action.checkEvalCriteria(self.evc, checkResource, originator)
		except ResponseException as e:
			raise BAD_REQUEST(e.dbg)

		# Schedule and process the <action> resource
		CSE.action.scheduleAction(self)


	def update(self, dct:JSON = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		
		# Preliminary update check before working with the update dictionary
		CSE.validator.validateResourceUpdate(self, dct, doValidateAttributes)

		# Check referenced resources
		sri = riFromID(findXPath(dct, 'm2m:actr/sri'))
		orc = riFromID(findXPath(dct, 'm2m:actr/orc'))
		apvOperation = self.getFinalResourceAttribute('apv/op', dct)
		self._checkReferencedResources(originator, sri, orc, apvOperation)

		# Check not-NULL orc
		if 'orc' in dct['m2m:actr'] and findXPath(dct, 'm2m:actr/orc') is None:
			raise BAD_REQUEST(L.logDebug(f'orc - must not be NULL in an UPDATE request'))


		# Check dependency resources

		dep = findXPath(dct, 'm2m:actr/dep')
		if dep is not None:
			for d in dep:
				_d = riFromID(d)
				if not CSE.dispatcher.hasDirectChildResource(self.ri, _d):
					raise BAD_REQUEST(L.logDebug(f'dep - must be a direct child resources of the <action> resource: {d}'))

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
		sriResource:Resource = None
		if dctEvc or dctSri:	# only if there is a new evalCriteria or a new subject resource
			try:
				sriResource = CSE.dispatcher.retrieveResource(newSri, originator = self.getOriginator())
			except ResponseException as e:
				raise BAD_REQUEST(L.logDebug(f'sri - subject resource not found: {newSri}'))
			# Actual check of the sbjt attribute is done in the checkEvalCriteria method below
		
		# Else use the current subject resource
		elif self.sri:
			sriResource = CSE.dispatcher.retrieveResource(self.sri)

		#	Check evalCriteria threshold attribute's value type and operation validity
		if dctEvc or dctSri:	# If we have a evalCriteria at all or a subject resource

			# Check that the evalCriteria is correct
			try:
				CSE.action.checkEvalCriteria(newEvc, sriResource, originator)
			except ResponseException as e:
				raise BAD_REQUEST(e.dbg)

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
		
		# Update other attributes if necessary
		if dep:
			CSE.action.updateAction(self)


	def deactivate(self, originator:str, parentResource:Resource) -> None:
		# Unschedule the action
		CSE.action.unscheduleAction(self)
		return super().deactivate(originator, parentResource)


	###########################################################################
	#
	#	Internals
	#

	def _checkReferencedResources(self, originator:str, sri:str, orc:str, apvOperation:Operation|int) -> Tuple[Resource, Resource]:
		"""	Check whether all the referenced resources exists and we have access: subjectResourceID, objectResourceID
		"""
		# TODO doc

		resSri = None
		resOrc = None
		if sri is not None: # sri is optional
			try:
				resSri = CSE.dispatcher.retrieveResourceWithPermission(sri, originator, Permission.RETRIEVE)
				L.isDebug and L.logDebug(f'Found subject resource sri: {resSri.ri}')
			except ResponseException as e:
				raise BAD_REQUEST(e.dbg)

		if orc is not None:
			try:
				apvOperation = Operation(apvOperation) if isinstance(apvOperation, int) else apvOperation
				resOrc = CSE.dispatcher.retrieveResourceWithPermission(orc, originator, apvOperation.permission())
				L.isDebug and L.logDebug(f'Found object resource orc: {resOrc.ri}')
			except ResponseException as e:
				raise BAD_REQUEST(e.dbg)

		return (resSri, resOrc)


	def _checkApvFrom(self, originator:str) -> None:
		"""	Check that the *from* parameter of the *actionPrimitive* is the originator.

			Args:
				originator:	The originator to check against.

			Raises:
				BAD_REQUEST: If the originator in the *actionPrimitive* does not match the *from* parameter.
		"""
		if not compareIDs(apvFr := findXPath(self.apv, 'fr'), originator):
			raise BAD_REQUEST(L.logDebug(f'invalid "apv.from": {apvFr}. Must be: {originator}'))


	def _getApvOperation(self) -> Operation:
		"""	Get the operation from the *actionPrimitive* attribute.

			Returns:
				The operation.
		"""
		return Operation(findXPath(self.apv, 'op'))
