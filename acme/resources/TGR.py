#
#	TGR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: TriggerRequest
#

""" TriggerRequest (TGR) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict,CSEType, EvalMode, ResourceTypes, JSON, TriggerStatus
from ..etc.ResponseStatusCodes import BAD_REQUEST, NOT_FOUND, NOT_IMPLEMENTED
from ..etc.ACMEUtils import riFromID, compareIDs
from ..helpers.TextTools import findXPath
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..runtime.Configuration import Configuration, ConfigurationError
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..etc.Constants import RuntimeConstants as RC


class TGR(AnnounceableResource):
	""" TriggerRequest (TGR) resource type. """

	# resourceType = ResourceTypes.TGR
	# """ The resource type """

	# typeShortname = resourceType.typeShortname()
	# """	The resource's domain and type name. """

	# # Specify the allowed child-resource types
	# _allowedChildResourceTypes:list[ResourceTypes] = [ ResourceTypes.SUB
	# 												 ]
	# """ The allowed child-resource types. """

	# # Attributes and Attribute policies for this Resource Class
	# # Assigned during startup in the Importer
	# _attributes:AttributePolicyDict = {		
	# 	# Common and universal attributes
	# 	'rn': None,
	# 	'ty': None,
	# 	'ri': None,
	# 	'pi': None,
	# 	'ct': None,
	# 	'lt': None,
	# 	'lbl': None,
	# 	'acpi':None,
	# 	'et': None,
	# 	'daci': None,
	# 	'cstn': None,

	# 	# Resource attributes
	# 	'mei': None,
	# 	'tri': None,
	# 	'tpe': None,
	# }
	# """	Attributes and `AttributePolicy` for this resource type. """


	def activate(self, parentResource: Resource, originator: str) -> None:

		# Check whether the TriggerRequestManager plugin is available
		if not (triggerManager := CSE.pluginManager.triggerRequestManager):
			raise NOT_IMPLEMENTED(L.logWarn('TriggerRequestManager plugin not available'))

		# Check whether the CSE is an IN-CSE, otherwise send an error
		if not RC.cseType == CSEType.IN:
			raise BAD_REQUEST(L.logWarn('TriggerRequests can only be created on an IN-CSE'))
		
		# Check whether the target is an AE or a remoteCSE, and the triggerEnable attribute is set to true
		# Otherwise, reject the request with TRIGGERING_DISABLED_FOR_RECIPIENT
		if (tri := self.tri):
			try:
				targetResource = CSE.dispatcher.retrieveResource(tri, originator)
				if (tren := targetResource.tren) is not None and tren == False:
					raise BAD_REQUEST(L.logWarn(f'Triggering is disabled for the target resource: {tri}'))
			except NOT_FOUND:
				targetResource = None



		# TODO If the Originator specifies a Trigger-Recipient-ID value in the Create primitive for a 
		# Registree AE or CSE, and the triggerEnable attribute of the Registree's <AE> or <remoteCSE>
		# resource has a value of false, the Receiver shall generate a Response Status Code indicating "TRIGGERING_DISABLED_FOR_RECIPIENT".

		# TODO Rest of activation process

		# TODO While processing the <triggerRequest> Create primitive the Receiver shall determine which NSE to forward the
		# trigger request to based on locally provisioned information or based on a DNS lookup of the M2M-Ext-ID attribute
		# of the <triggerRequest>. If an NSE cannot be determined, the Receiver shall set the triggerStatus attribute 
		# to ERROR_NSE_NOT_FOUND. Otherwise, the Receiver shall continue to process the trigger request and set the triggerStatus attribute to PROCESSING.



		# TODO scripts to handle the trigger requests. Need to define new script meta tags here.
		# - Determine the NSE to forward the trigger request to
		# - Submit the trigger request to the NSE

		# Determine the NSE to forward the trigger request to. If found, then set the tst attribute to PROCESSING.
		
		# TODO run the script to determine the NSE. Interprete the result to either raise ERROR_NSE_NOT_FOUND or set PROCESSING.
		
		# self.setAttribute('tst', TriggerStatus.PROCESSING)



		super().activate(parentResource, originator)




	def update(self, dct: JSON=None,
					 originator: Optional[str]=None, 
					 doValidateAttributes: Optional[bool]=True) -> None:
		super().update(dct, originator, doValidateAttributes)
	


	def deactivate(self, originator: str, parentResource: Resource) -> None:
		# Unschedule the action
		return super().deactivate(originator, parentResource)


# TODO tests
# - Test TriggerEnabled on target resource
# - Implement test for IN & NON-IN CSE
