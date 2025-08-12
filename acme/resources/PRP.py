#
#	PRP.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: PrimitiveProfile
#

from __future__ import annotations

from ..resources.Resource import Resource

from ..etc.Types import AttributePolicyDict, AttributePolicyDictList, ResourceTypes, Cardinality, BasicType
from ..resources.AnnounceableResource import AnnounceableResource
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..runtime.Logging import Logging as L
from ..runtime import CSE

# TODO annc version
# TODO add to UML diagram
# TODO add to statistics, also in console


notAllowedAttributes = [ 'op', 'to', 'fr', 'rqi', 'rvi', 'rsc', 'fc', 'ot', 'gid', 'tkns', 'ati' ]
""" Attributes that are not allowed in the PRP resource (adds and dels attribute). """

class PRP(AnnounceableResource):

	resourceType = ResourceTypes.PRP
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [	ResourceTypes.SUB
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
		'lbl': None,
		'acpi': None,
		'daci': None,
		'cstn': None,
		'cr': None,

		'at': None,
		'aa': None,
		'ast': None,

		# Resource attributes
		'idl': None,
		'rtys': None,
		'ops': None,
		'rsds': None,
		'rvs': None,
		'adds': None,
		'dels': None,
		'appl': None,
	}
	"""	Attributes and `AttributePolicy` for this resource type. """


	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)

		# TODO resourceIDs are not supported yet. Perhaps we should remove this attribute? Problem: How to handle resourceIDs with wildcards.

		additions = self.adds							# listOfAttributes
		deletions = self.dels							# m2m:attributelist
		resourceTypes:list[ResourceTypes] = self.rtys	# m2m:resourceTypeList

		# check if attributes in additions are not present in deletions
		# TODO move to separate function also for Update
		if additions and deletions:
			for attr in additions:
				nm:str = attr.get('nm')
				if nm in deletions:
					raise BAD_REQUEST(L.logDebug(f'Attributes in adds must not be present in dels: {nm}'))

		# Check that certain attributes are neither present in additions and deletions
		# TODO move to separate function also for Update
		if additions:
			for attr in additions:
				nm = attr.get('nm')
				if nm in notAllowedAttributes:
					raise BAD_REQUEST(L.logDebug(f'Attribute must not be present in adds: {nm}'))
		if deletions:
			for del_ in deletions:
				if del_ in notAllowedAttributes:
					raise BAD_REQUEST(L.logDebug(f'Attribute must not be present in dels: {del_}'))

		# Check that the attributes in additions are allowed for the resourceTypes
		if additions:

			# First, sort the attributes in additions into two lists: non-resource attributes and resource attributes
			for attr in additions:
				nm = attr.get('nm')
				val = attr.get('val')

				nonResourceAttributes:AttributePolicyDict = {}
				resourceAttributes:AttributePolicyDictList = {}
				if (policyList := CSE.validator.getAttributePoliciesByName(nm)):
					resourceAttributes[nm] = policyList
				elif (policy := CSE.validator.getAttributePolicy(ResourceTypes.REQUEST, nm, True)):
					nonResourceAttributes[nm] = policy
				elif (policy := CSE.validator.getAttributePolicy(ResourceTypes.RESPONSE, nm, True)):
					nonResourceAttributes[nm] = policy
				else:
					raise BAD_REQUEST(L.logDebug(f'Attribute: {nm} not found or not supported'))
			
			# Then check the values of the provided attributes in both lists

			# Non-resource attributes ie. Request and Response attributes
			for nm, policy in nonResourceAttributes.items():
				# Check for non-complex type
				if policy.type == BasicType.complex:
					raise BAD_REQUEST(L.logDebug(f'Complex attribute not allowed in adds: {nm}'))

				# Check the value and type
				try:
					CSE.validator.validateAttribute(nm, val, policy.type)
				except BAD_REQUEST as e:
					raise BAD_REQUEST(L.logDebug(f'Attribute: {nm} failed validation: {e.dbg}'))

			# Checks for Resource attributes
			for nm, policyList in resourceAttributes.items():

				for policy in policyList:	# This could be a list of policies for the same attribute
					# Check for non-complex type
					if policy.type == BasicType.complex:
						raise BAD_REQUEST(L.logDebug(f'Complex attribute not allowed in adds: {nm}'))
				
					# TODO check for NP

					# Check the value and type
					try:
						CSE.validator.validateAttribute(nm, val, policy.type)
					except BAD_REQUEST as e:
						raise BAD_REQUEST(L.logDebug(f'Attribute: {nm} failed validation: {e.dbg}'))
							
				if resourceTypes:
					# Test all entries in the rtys attribute
					for rtype in resourceTypes:
						# if the resource type is found in any of the policies, then the attribute is allowed
						# Otherwise, raise a BAD_REQUEST exception at the end of the loop
						for policy in policyList:
							if rtype in policy.rtypes:
								break
						else:
							raise BAD_REQUEST(L.logDebug(f'Attribute: {nm} not allowed for resource type: {rtype}'))
					
			
			# 
			

			# TODO get a list of resources from the resourceID attribute and check 
			

			# 	# Check all resource types for this attribute
			# 	for rtype in resourceTypes:
			# 		if (policy := CSE.validator.getAttributePolicy(rtype, nm, True)):
			# 			# The following might raise a BAD_REQUEST exception if the attribute is not allowed for the resource type etc
			# 			CSE.validator.validateAttribute(nm, val, policy.type, rtype)
			# 		else:
			# 			# If the attribute is not a resource attribute, add it to the list of non-resource attributes
			# 			listOfNonResourceAttributes.append(nm)

			# L.inspect(listOfNonResourceAttributes)
			# # Now check the non-resource attributes - are they Request
			# for nonResourceAttr in listOfNonResourceAttributes:
			# 	if policy := CSE.validator.getAttributePolicy(ResourceTypes.REQUEST, nonResourceAttr):
			# 		L.inspect(policy)
			# 		# The following might raise a BAD_REQUEST exception if the attribute is not allowed for the resource type etc
			# 		CSE.validator.validateAttribute(nm, val, policy.type, ResourceTypes.REQRESP)
			# 	else:
			# 		raise BAD_REQUEST(L.logDebug(f'Attribute: {nonResourceAttr} not found in attribute policies'))

				# TODO test with rcn
	
				# for del_ in deletions:
				# 		raise BAD_REQUEST(L.logDebug(f'Attribute: {del_} not allowed for resource type: {rtype}'))
					# if Cardinality.isMandatory(policy.cardinality)
					# 	raise BAD_REQUEST(L.logDebug(f'Attribute: {del_} is mandatory for resource type: {rtype}'))


		# 4) check that the attributes values in deletions are allowed for the resource(s) referenced by the resourceID attribute

		# 5) Check that the attributes in additions are NOT complex attributes	

		# 6) check that the values in additions are of the correct data type

# 		# Set the initial processStatus to Disabled
# 		self.setAttribute('prst', ProcessState.Disabled.value)

# 		# Set the initial processControl to Disable
# 		self.setAttribute('prct', ProcessControl.Disable.value)

# 		# EXPERIMENTAL: the currentState (cust) and initialState (inst) are NOT present initially

	
# 	def update(self, dct: JSON = None, originator: str | None = None, doValidateAttributes: bool | None = True) -> None:

# 		# current processState
# 		prst = self.prst

# 		# Step 1) Update of initialState, activateCondition or endCondition attributes
# 		newInst = findXPath(dct, 'm2m:prmr/inst')
# 		newAtcos = findXPath(dct, 'm2m:prmr/atcos')
# 		newEncos = findXPath(dct, 'm2m:prmr/encos')
# 		if any([newInst, newAtcos, newEncos]) and prst != ProcessState.Disabled:
# 			raise OPERATION_NOT_ALLOWED('Process state must be "disabled" to update the initialState, activateCondition or endCondition attributes')	

# 		# Step 2) Check existence and access for activateCondition and endCondition
# 		if newAtcos:
# 			# TODO check existence if and access to resources and attributes referenced by the subject element of the evalCriteria element
# 			# Check <action> code to reuse the code from the <action> resource
# 			# If not: Return error "INVALID_PROCESS_CONFIGURATION"
# 			pass
# 		if newEncos:
# 			# TODO check existence if and access to resources and attributes referenced by the subject element of the evalCriteria element
# 			# Check <action> code to reuse the code from the <action> resource
# 			# If not: Return error "INVALID_PROCESS_CONFIGURATION"
# 			pass
	

# 		# Step 3) Check threshold of the values and operator in the activateCondition and endCondition attributes
# 		if newAtcos:
# 			# TODO check threshold of the values and operator in the activateCondition attribute
# 			# Check <action> code to reuse the code from the <action> resource
# 			# If not: Return error "INVALID_PROCESS_CONFIGURATION"
# 			pass
# 		if newEncos:
# 			# TODO check threshold of the values and operator in the endCondition attribute
# 			# Check <action> code to reuse the code from the <action> resource
# 			# If not: Return error "INVALID_PROCESS_CONFIGURATION"
# 			pass
	
# 		# Step 4) Check existence and access to the <state> resource referenced by the (new) initialState attribute
# 		if newInst:
# 			# TODO check existence access to the <state> resource referenced by the (new) initialState attribute, and RETRIEVE privileges for the originator
# 			# If not: Return error "INVALID_PROCESS_CONFIGURATION"
# 			pass

# 		#
# 		# Check processControl updates
# 		#
		
# 		match (newPrct := findXPath(dct, 'm2m:prmr/prct')):
			
# 			# Failure
# 			# Step 5)
# 			case ProcessControl.Enable if prst != ProcessState.Disabled:
# 				raise OPERATION_NOT_ALLOWED('Process state must be "disabled" to enable the process')
# 			# Step 6)
# 			case ProcessControl.Disable if prst == ProcessState.Disabled:
# 				raise OPERATION_NOT_ALLOWED('Process state must not be "disabled" to disable the process')
# 			# Step 7)
# 			case ProcessControl.Pause if prst != ProcessState.Activated:
# 				raise OPERATION_NOT_ALLOWED('Process state must be "activated" to pause the process')
# 			# Step 8)
# 			case ProcessControl.Reactivate if prst != ProcessState.Paused:
# 				raise OPERATION_NOT_ALLOWED('Process state must be "paused" to reactivate the process')
			
# 			# Success
# 			# Step 9)
# 			case ProcessControl.Enable if prst == ProcessState.Disabled:

# 				# Does the <state> resource referenced by the initialState attribute exist?
# 				# Is it a child resource of this resource?
# 				# has the originator retrieve privileges on it?
				
# 				# Does the originator has proper CRUD privileges for the <state> and <action> resources referenced by this resource and child resources?
# 				# Are all the referenced resources child resources of this resource?
# 				# Are all the referenced resources of the correct resource types?

# 				# If yes: Set processStatus to "enabled"
# 				# Start the process
# 				# If no: Return error "INVALID_PROCESS_CONFIGURATION"
# 				pass
# 			# Step 10)
# 			case ProcessControl.Pause if prst == ProcessState.Activated:
# 				self.setAttribute('prst', ProcessState.Paused.value)
# 				# TODO pause the process
			
# 			# Step 11)
# 			case ProcessControl.Reactivate if prst == ProcessState.Paused:
# 				self.setAttribute('prst', ProcessState.Activated.value)
# 				# TODO continues processing the process
			
# 			# Step 12)
# 			case ProcessControl.Disable if prst != ProcessState.Disabled:
# 				self.setAttribute('prst', ProcessState.Disabled.value)
# 				self.delAttribute('cust')	# EXPERIMENTAL
# 				# TODO set the stateActive attribute of the current <state> resource to false
# 				# TODO disable the process



# 		super().update(dct, originator, doValidateAttributes)	


# 	# EXPERIMENTAL Don't define a deactivate() method. This would cause problems with deregistering of AEs