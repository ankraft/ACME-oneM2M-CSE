#
#	ActionManager.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	This module implements an action manager service functionality for the CSE.
"""

from __future__ import annotations
from typing import Optional, Any, cast

import sys, copy

from ..etc.Types import EvalMode, EvalCriteriaOperator, JSON, CSERequest, BasicType, ResourceTypes, Permission
from ..etc.ResponseStatusCodes import ResponseException, INTERNAL_SERVER_ERROR, BAD_REQUEST, NOT_FOUND
from ..helpers.TextTools import setXPath
from ..etc.DateUtils import utcTime
from ..etc.RequestUtils import responseFromResult
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..runtime.Logging import Logging as L
from ..resources.Resource import Resource
from ..resources.ACTR import ACTR
from ..helpers.ResourceSemaphore import CriticalSection


# TODO implement support for input attribute when the procedure is clear

class ActionManager(object):
	"""	This class defines functionalities to handle action triggerings, 
		dependancies and other action related functionalities

		Attributes:
	"""

	
	# Imported here because of circular import
	from ..resources.Resource import Resource


	def __init__(self) -> None:
		"""	Initialization of an *ActionManager* instance.
		"""

		# Add handler for any resource change event
		CSE.event.addHandler(CSE.event.changeResource, self.evaluateActions)	# type: ignore

		CSE.event.addHandler(CSE.event.cseReset, self.restart)		# type: ignore
		L.isInfo and L.log('ActionManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the Action Manager.
		
			Returns:
				Boolean that indicates the success of the operation
		"""
		L.isInfo and L.log('ActionManager shut down')
		return True


	def restart(self, name:str) -> None:
		"""	Restart the ActionManager service.
		"""
		L.isDebug and L.logDebug('ActionManager restarted')


	###############################################################################################


	def evaluateActions(self, name:str, resource:Resource, realRi:Optional[str] = None) -> None:

		if resource.isVirtual():
			return
		
		_ri = realRi if realRi else resource.ri
		_now = utcTime()
		L.isDebug and L.logDebug(f'Looking for resource actions for resource: {_ri}')

		# Get actions. Remember, these are NOT <action> resources
		actions = CSE.storage.searchActionReprsForSubject(_ri)		
		# sort by action priority
		actions = sorted(actions, key = lambda x: x['apy'] if x['apy'] is not None else sys.maxsize)
		L.isDebug and L.logDebug(f'Found {len(actions)} actions for resource: {_ri}')

		for action in actions:

			# Some explanation why this is done in a critical section:
			# It might be that an action is triggered multiple times for a single resource change.
			# to prevent sending multiple requests, the section is locked for a particular action
			# while it is being executed. Other actions for the same or other resources are not affected.
			# When the next action is allowed to execute, it is checked if the action is still valid
			# and is allowed to execute (e.g. in the same period). If not, it is skipped.
			with CriticalSection(ri := action['ri'], 'execution'):
				# L.logWarn(f'Enter {ri}')
				
				# re-read the action document because it might have changed while waiting for the lock
				# However, it might be under rare circumstances that the action is deleted while waiting
				if not (action := CSE.storage.getActionRepr(ri)):
					L.logWarn(f'Action {ri} not found anymore. Skipping')
					continue

				# Check if the action is still valid to execute
				if self.evaluateSingleAction(resource, action, _now) and self.evaluateDependencies(action):
					L.isDebug and L.logDebug(f'Action: conditions {ri} evaluated to True and the action is executed')

					# retrieve the real action resource
					try:
						actr = cast(ACTR, CSE.dispatcher.retrieveLocalResource(ri))
					except ResponseException as e:
						L.logErr(e.dbg)
						raise e

					# Assign a new to (ie. the objectRecourceID)
					apv = copy.deepcopy(actr.apv)
					setXPath(apv, 'to', actr.orc)

					# build request
					try:
						resReq = CSE.request.fillAndValidateCSERequest(request := CSERequest(originalRequest = apv))
					except ResponseException as e:
						L.logWarn(f'Error handling request: {request.originalRequest} : {e.dbg}')
						continue

					# Send request
					L.isDebug and L.logDebug(f'Sending request: {resReq.originalRequest}')
					res = CSE.request.handleRequest(resReq)

					# Store response in the <actr>
					res.request = request
					actr.setAttribute('air', responseFromResult(res).data)	# type: ignore[attr-defined]
					try:
						actr.dbUpdate()
					except ResponseException as e:
						L.logWarn(f'Error updating <actr>: {e.dbg}')
						continue

					# Update according to evalMode
					evm = action['evm']
					if evm == EvalMode.once:			# remove if only once
						L.isDebug and L.logDebug(f'Removing "once" action: {ri}')
						CSE.storage.removeActionRepr(ri)
						continue
					if evm == EvalMode.continous:		# remove from action DB if count reaches 0
						count = action['count']
						if (count := count - 1) == 0:
							L.isDebug and L.logDebug(f'Removing "continuous" action: {ri} (count: {actr.ecp} reached)')
							CSE.storage.removeActionRepr(ri)
						else:
							action['count'] = count
							CSE.storage.updateActionRepr(action)
						continue
					if evm == EvalMode.periodic:
						_ecp = action['ecp'] / 1000.0
						action['periodTS'] = _now + ((action['periodTS'] - _now) % _ecp)
						L.isDebug and L.logDebug(f'Setting next period start to: {action["periodTS"]} for "periodic" action: {ri}')
						CSE.storage.updateActionRepr(action)
				else:
					L.isDebug and L.logDebug(f'Action: {ri} - conditions evaluated to False')

				# L.logWarn(f'Leave {action["ri"]}')


	def _evaluateEVC(self, resource:Resource, evc:JSON) -> bool:
		"""	Evaluate a single evaluation criteria.

			Args:
				resource:		The resource to evaluate against.
				evc:			The evaluation criteria to evaluate.

			Returns:
				Boolean that indicates the success of the evaluation.
		"""
		sbjt = evc['sbjt']
		if (attr := resource.attribute(sbjt)) is None:
			return False
		optr = evc['optr']
		thld = evc['thld']

		if optr == EvalCriteriaOperator.equal:
			return attr == thld
		if optr == EvalCriteriaOperator.notEqual:
			return attr != thld
		if optr == EvalCriteriaOperator.lessThan:
			return attr < thld
		if optr == EvalCriteriaOperator.lessThanEqual:
			return attr <= thld
		if optr == EvalCriteriaOperator.greaterThan:
			return attr > thld
		if optr == EvalCriteriaOperator.greaterThanEqual:
			return attr >= thld
		return False


	def evaluateSingleAction(self, resource:Resource, action:JSON, nowTS:float) -> bool:
		# TODO doc

		L.isDebug and L.logDebug(f'Evaluate action: {action["ri"]}')
		# If the mode is periodic, and the next timestamp for the action is greater then now,
		# then the action is not yet available.
		if action['evm'] == EvalMode.periodic:
			L.isDebug and L.logDebug(f'next action TS: {action["periodTS"]} - now: {nowTS}')
			if action['periodTS'] > nowTS:
				return False
		
		return self._evaluateEVC(resource, action['evc'])
			


	def evaluateDependencies(self, action:JSON) -> bool:
		# TODO doc
		
		if not (dependencies := action.get('dep')):
			return True
		
		dependencySatisified = False
		for idx, dep in enumerate(dependencies):
			L.isDebug and L.logDebug(f'Evaluate dependency: {dep}')

			# Get the dependency resource
			try:
				dependency = CSE.dispatcher.retrieveLocalResource(dep)
			except NOT_FOUND:
				L.isDebug and L.logDebug(f'Dependency evaluation: {dep} not found. Skipping resource evaluation.')
				continue
			except ResponseException as e:
				L.logErr(f'Dependency evaluation: {e.dbg}. Skipping resource evaluation.')
				return False

			# Evaluate the dependency
			sfc = dependency.sfc	# sufficient condition

			# Retrieve the referenced resource
			try:
				resource = CSE.dispatcher.retrieveLocalResource(dependency['rri'])
			except ResponseException as e:
				L.logErr(f'Dependency evaluation: {e.dbg}. Skipping resource evaluation.')
				continue
			
			# Check criteria
			if self._evaluateEVC(resource, dependency.evc):	# evaluation criteria met
				dependencySatisified = True
				if sfc:
					break	# sufficient condition met, no need to check other dependencies
				else:
					if idx == len(dependencies) - 1:	# last dependency, but still True
						break 	# Last one anyway
					continue	# check next dependency
			
			# Evaluation criteria not met
			else:
				if sfc:
					if idx == len(dependencies) - 1:	# last dependency
						break		# Return current value of dependencySatisified
					continue	# check next dependency
				else:
					dependencySatisified = False
					break

		L.isDebug and L.logDebug(f'Dependency evaluation: {dependencySatisified}')
		return dependencySatisified


	def scheduleAction(self, action:ACTR) -> None:
		evm = action.evm
		if evm == EvalMode.off:
			L.isDebug and L.logDebug(f'evm: off for action: {action.ri} - Action inactive.')
			CSE.storage.removeActionRepr(action.ri)	# just remove, ignore result
			return
		if evm == EvalMode.once:
			L.isDebug and L.logDebug(f'evm: once for action: {action.ri}.')
			CSE.storage.upsertAction(action, 0, 0)
			return
		if evm == EvalMode.periodic:
			ecp = action.ecp if action.ecp else Configuration.resource_actr_ecpPeriodic
			L.isDebug and L.logDebug(f'evm: periodic for action: {action.ri}, period: {ecp}.')
			CSE.storage.upsertAction(action, utcTime(), 0)
			return
		if evm == EvalMode.continous:
			ecp = action.ecp if action.ecp else Configuration.resource_actr_ecpContinuous
			L.isDebug and L.logDebug(f'evm: continuous for action: {action.ri}, counter: {ecp}')
			CSE.storage.upsertAction(action, 0, ecp)
			return
		raise INTERNAL_SERVER_ERROR(f'unknown EvalMode: {evm}. This should not happen.')
		

	def unscheduleAction(self, action:ACTR) -> None:
		CSE.storage.removeActionRepr(action.ri)

	
	def updateAction(self, actr:ACTR) -> None:
		# TODO  doc
		# hack, only update the dep attribute
		if action := CSE.storage.getActionRepr(actr.ri):
			action['dep'] = actr.dep
			CSE.storage.updateActionRepr(action)


	#######################################################################
	#
	#	Process Statue Management
	#	See TS-0001 10.2.27
	#

	def enterActiveState(self, resource:Resource) -> None:
		"""	Enter the active state for a resource.

			Args:
				resource: The resource to enter the active state.
		"""
		L.isDebug and L.logDebug(f'Entering active state for resource: {resource.ri}')
		# TODO implement
		pass

	
	def enterDisabledState(self, resource:Resource) -> None:
		"""	Enter the disabled state for a resource.

			Args:
				resource: The resource to enter the disabled state.
		"""
		L.isDebug and L.logDebug(f'Entering disabled state for resource: {resource.ri}')
		# TODO stop monitoring for endCondition
		# TODO implement
		pass


	def enterPauseState(self, resource:Resource) -> None:
		"""	Enter the pause state for a resource.

			Args:
				resource: The resource to enter the pause state.
		"""
		L.isDebug and L.logDebug(f'Entering pause state for resource: {resource.ri}')
		# TODO implement
		pass



	#######################################################################
	#
	#	Helper 
	#

	def checkEvalCriteria(self, evc:JSON, subject:str|Resource, originator:str, checkEvc:bool = True) -> None:
		"""	Check the evaluation criteria for a given subject resource.

			Args:
				evc: The evaluation criteria to check.
				subject: The subject resource ID or the subject resource itself.
				originator: The originator of the request.
				checkEvc: Check the evaluation criteria. Default is *True*.

			Returns:
				A tuple with a boolean indicating the success of the check and a possible error message.

			Raises:
				BAD_REQUEST: If the evaluation criteria is invalid.
				Originator_HAS_NO_PRIVILEGE: If the originator has no access to the subject resource.
				NOT_FOUND: If the subject resource does not exist.
		"""

		# Check if the subject resource exists and is accessible
		match subject:
			case str():
				subjectResource = CSE.dispatcher.retrieveResourceWithPermission(subject, originator, Permission.RETRIEVE)
			case _:
				subjectResource = cast(Resource, subject)

		# Check the evaluation criteria if requested
		if checkEvc:
			# Check whether the subject resource has the subject attribute defined
			if (sbjt := evc.get('sbjt')) is None:
				raise BAD_REQUEST('Subject attribute not defined in evalCriteria')
			if not subjectResource.hasAttributeDefined(sbjt):
				raise BAD_REQUEST('Subject attribute not defined')

			#	Check evalCriteria threshold attribute's value type and operation validity
			if (thld := evc.get('thld')) is None:
				raise BAD_REQUEST('Threshold value not defined in evalCriteria')
			dataType = self.checkAttributeThreshold(sbjt, thld, subjectResource.ty)

			#	Check evalCriteria operator
			if (optr := evc.get('optr')) is None:
				BAD_REQUEST('Operator not defined in evalCriteria')
			CSE.action.checkAttributeOperator(EvalCriteriaOperator(optr), dataType, sbjt)


	def checkAttributeThreshold(self, sbjt:str, thld:Any, rtype:ResourceTypes) -> BasicType:
		""" Check the threshold value for the given subject attribute.

			Args:
				sbjt: The subject attribute name
				thld: The threshold value.
				rtype: The resource type of the subject attribute.

			Return:
				The basic type of the attribute value.

			Raises:
				BAD_REQUEST: If the threshold value is invalid.
		"""
		# TODO doc
		
		#	Check evalCriteria threshold attribute's value type and operation validity
		try:
			typ, _ = CSE.validator.validateAttribute(sbjt, thld, rtype = rtype)
		except ResponseException as e:
			raise BAD_REQUEST(L.logDebug(f'thld - invalid threshold value: {thld} for attribute: {sbjt} : {e.dbg}'))
		return typ


	def checkAttributeOperator(self, optr:EvalCriteriaOperator, dataType:BasicType, sbjt:str) -> None:
		""" Check the operator for the given subject attribute.

			Args:
				optr: The operator.
				dataType: The basic type of the attribute value.
				sbjt: The subject attribute name.

			Raises:
				BAD_REQUEST: If the operator is not allowed for the given data type.
		"""
		if not optr.isAllowedType(dataType):
			raise BAD_REQUEST(L.logDebug(f'optr - invalid data type: {dataType} and operator: {optr} for attribute: {sbjt}'))
