#
#	PRMI.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ProcessManagement
#

from __future__ import annotations

from ..resources.Resource import Resource

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, ProcessState, ProcessControl, Permission
from ..resources.AnnounceableResource import AnnounceableResource
from ..helpers.TextTools import findXPath
from ..etc.ResponseStatusCodes import ResponseException, OPERATION_NOT_ALLOWED, NOT_FOUND, INVALID_PROCESS_CONFIGURATION
from ..runtime import CSE
from ..runtime.Logging import Logging as L

# TODO annc version
# TODO add to UML diagram
# TODO add to statistics, also in console


class PRMR(AnnounceableResource):

	resourceType = ResourceTypes.PRMR
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.STTE,
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
		'et': None,
		'acpi': None,
		'lbl': None,
		'cr': None,
		'cstn': None,
		'daci': None,

		'at': None,
		'aa': None,
		'ast': None,

		# Resource attributes
		'prst': None,
		'prct': None,
		'cust': None,
		'atcos': None,
		'encos': None,
		'inst': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)

		# Set the initial processStatus to Disabled
		self.setAttribute('prst', ProcessState.Disabled.value)

		# Set the initial processControl to Disable
		self.setAttribute('prct', ProcessControl.Disable.value)

		# EXPERIMENTAL: the currentState (cust) and initialState (inst) are NOT present initially.
		# cust cannot be null. So, it must be "not present" initially. This must be changed in TS-0001 (to 0..1)

	
	def update(self, dct: JSON = None, originator: str | None = None, doValidateAttributes: bool | None = True) -> None:

		# current processState
		prst = self.prst

		# Step 1) Update of initialState, activateCondition or endCondition attributes
		newInst = findXPath(dct, 'm2m:prmr/inst')
		newAtcos = findXPath(dct, 'm2m:prmr/atcos')
		newEncos = findXPath(dct, 'm2m:prmr/encos')
		if any([newInst, newAtcos, newEncos]) and prst != ProcessState.Disabled:
			raise OPERATION_NOT_ALLOWED(L.logDebug('Process state must be "disabled" to update the initialState, activateCondition or endCondition attributes'))

		# Step 2) AND 3):
		# 	Check existence and access for activateCondition and endCondition
		#	Check threshold of the values and operator in the activateCondition and endCondition attributes

		# EXPERIMENTAL use custodian/originator for the followings
		_originator = self.getCurrentOriginator()

		if newAtcos:
			for atco in newAtcos:
				# Check validity of the activateCondition attribute
				try:
					CSE.action.checkEvalCriteria(atco['evc'], atco['sri'], _originator)
				except ResponseException as e:
					raise INVALID_PROCESS_CONFIGURATION(L.logDebug(f'Error in activateCondition: {e}'))

		if newEncos:
			for enco in newEncos:
				# Check validity of the endCondition attribute
				try:
					CSE.action.checkEvalCriteria(enco['evc'], enco['sri'], _originator)
				except ResponseException as e:
					raise INVALID_PROCESS_CONFIGURATION(L.logDebug(f'Error in endCondition: {e}'))
				
	
		# Step 4) Check existence and access to the <state> resource referenced by the (new) initialState attribute
		if newInst:
			# Try to retrieve the new state resource
			try:
				newInstResource = CSE.dispatcher.retrieveResource(newInst, originator)
			except NOT_FOUND:
				raise INVALID_PROCESS_CONFIGURATION(L.logDebug('The referenced state resource does not exist'))
			# Check if the originator has access to the new state resource
			if not CSE.security.hasAccess(originator, newInstResource, Permission.RETRIEVE):	# Check if the originator has RETRIEVE access to the state resource
				raise INVALID_PROCESS_CONFIGURATION(L.logDebug('The originator does not have the necessary privileges to access the referenced state resource'))
			# Check if the new state resource is a child resource of this process resource
			if newInstResource.pi != self.ri:
				raise INVALID_PROCESS_CONFIGURATION(L.logDebug('The referenced state resource is not a child resource of this process resource'))
			# EXPERIMENTAL Check if the new state resource is of the correct resource type
			if newInstResource.ty != ResourceTypes.STTE:
				raise INVALID_PROCESS_CONFIGURATION(L.logDebug('The referenced state resource must be of the resource type "state"'))

		#
		# Check processControl updates
		#
		
		match (newPrct := findXPath(dct, 'm2m:prmr/prct')):
			
			# Failure
			# Step 5)
			case ProcessControl.Enable if prst != ProcessState.Disabled:
				raise OPERATION_NOT_ALLOWED(L.logDebug('Process state must be "disabled" to enable the process'))
				# TODO test for this
			# Step 6)
			case ProcessControl.Disable if prst == ProcessState.Disabled:
				raise OPERATION_NOT_ALLOWED(L.logDebug('Process state must not be "disabled" to disable the process'))
				# TODO test for this

			# Step 7)
			case ProcessControl.Pause if prst != ProcessState.Activated:
				raise OPERATION_NOT_ALLOWED(L.logDebug('Process state must be "activated" to pause the process'))
				# TODO test for this
			# Step 10)
			case ProcessControl.Pause if prst == ProcessState.Activated:
				self.setAttribute('prst', ProcessState.Paused.value)
				CSE.action.enterPauseState(self)
				# TODO test for this


			# Step 8)
			case ProcessControl.Reactivate if prst != ProcessState.Paused:
				raise OPERATION_NOT_ALLOWED(L.logDebug('Process state must be "paused" to reactivate the process'))
			
			# Success
			# Step 9)
			case ProcessControl.Enable if prst == ProcessState.Disabled:
				L.isDebug and L.logDebug('Enabling process')

				# TODO
				# Does the <state> resource referenced by the initialState attribute exist?
				# Is it a child resource of this resource?
				# has the originator retrieve privileges on it?
				
				# Does the originator has proper CRUD privileges for the <state> and <action> resources referenced by this resource and child resources?
				# Are all the referenced resources child resources of this resource?
				# Are all the referenced resources of the correct resource types?

				# If yes: Set processStatus to "enabled"
				# Start the process
				# If no: Return error "INVALID_PROCESS_CONFIGURATION"
				pass
			
			# Step 11)
			case ProcessControl.Reactivate if prst == ProcessState.Paused:
				self.setAttribute('prst', ProcessState.Activated.value)
				CSE.action.enterActiveState(self)
				# TODO continues processing the process
			
			# Step 12)
			case ProcessControl.Disable if prst != ProcessState.Disabled:
				self.setAttribute('prst', ProcessState.Disabled.value)
				# Set the stateActive attribute of the activate <state> resource to false
				try:
					_state = CSE.dispatcher.retrieveResource(self.cust)
					_state.setAttribute('sact', False)
					_state.dbUpdate()
				except:
					# ignore any error here
					pass
				# Remove the current state (cust) attribute
				self.delAttribute('cust')	# EXPERIMENTAL In the spec this sets the cust attribute to Null
				# disable the process
				CSE.action.enterDisabledState(self)




		super().update(dct, originator, doValidateAttributes)	


	# EXPERIMENTAL Don't define a deactivate() method. This would cause problems with deregistering of AEs