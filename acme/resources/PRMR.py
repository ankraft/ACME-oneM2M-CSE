#
#	PRMI.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ProcessManagement
#

from __future__ import annotations
from typing import Optional, Any, Union

from ..resources.Resource import Resource

from ..etc.Types import AttributePolicyDict, ResourceTypes, JSON, ProcessState, ProcessControl
from ..resources.AnnounceableResource import AnnounceableResource
from ..helpers.TextTools import findXPath
from ..etc.ResponseStatusCodes import OPERATION_NOT_ALLOWED

# TODO annc version
# TODO add to UML diagram
# TODO add to statistics, also in console


class PRMR(AnnounceableResource):

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.STTE,
							   	   ResourceTypes.SUB
								 ]

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

	def __init__(self, dct:Optional[JSON] = None, 
					   pi:Optional[str] = None, 
					   create:Optional[bool] = False) -> None:
		super().__init__(ResourceTypes.PRMR, dct, pi, create = create)


	def activate(self, parentResource: Resource, originator: str) -> None:
		super().activate(parentResource, originator)

		# Set the initial processStatus to Disabled
		self.setAttribute('prst', ProcessState.Disabled.value)

		# Set the initial processControl to Disable
		self.setAttribute('prct', ProcessControl.Disable.value)

	
	def update(self, dct: JSON = None, originator: str | None = None, doValidateAttributes: bool | None = True) -> None:


		#
		# Check processControl updates
		#
		
		prst = self.prst
		match (newPrct := findXPath(dct, f'm2m:prmr/prct')):
			
			# Failure
			case ProcessControl.Enable if prst != ProcessState.Disabled:
				raise OPERATION_NOT_ALLOWED('Process state must be "disabled" to enable the process')
			case ProcessControl.Disable if prst == ProcessState.Disabled:
				raise OPERATION_NOT_ALLOWED('Process state must not be "disabled" to disable the process')
			case ProcessControl.Pause if prst != ProcessState.Activated:
				raise OPERATION_NOT_ALLOWED('Process state must be "activated" to pause the process')
			
			# Success
			case ProcessControl.Pause if prst == ProcessState.Activated:
				self.setAttribute('prst', ProcessState.Paused.value)
				# TODO pause the process
			
			case ProcessControl.Reactivate if prst == ProcessState.Paused:
				self.setAttribute('prst', ProcessState.Activated.value)
				# TODO reactivate the process
			
			case ProcessControl.Disable if prst != ProcessState.Disabled:
				self.setAttribute('prst', ProcessState.Disabled.value)
				self.delAttribute('cust')
				# TODO disable the process

			# TODO continue with step 9)


		super().update(dct, originator, doValidateAttributes)	
