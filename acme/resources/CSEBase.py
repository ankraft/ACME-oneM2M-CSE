#
#	CSEBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CSEBase
#
""" CSEBase (CSEBase) resource type. """

from __future__ import annotations
from typing import Optional

from ..etc.Types import AttributePolicyDict, CSERequest, ResourceTypes, ContentSerializationType, JSON
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.IDUtils import isValidCSI
from ..etc.ACMEUtils import resourceFromCSI
from ..etc.Constants import Constants
from ..resources.Resource import Resource
from ..resources.AnnounceableResource import AnnounceableResource
from ..runtime import CSE
from ..etc.Constants import RuntimeConstants as RC

# TODO notificationCongestionPolicy

class CSEBase(AnnounceableResource):
	""" CSEBase (CSEBase) resource type. """

	resourceType = ResourceTypes.CSEBase
	""" The resource type """

	typeShortname = resourceType.typeShortname()
	"""	The resource's domain and type name. """

	# Specify the allowed child-resource types
	_allowedChildResourceTypes = [ ResourceTypes.ACP,
								   ResourceTypes.ACTR, 
								   ResourceTypes.AE, 
								   ResourceTypes.CRS, 
								   ResourceTypes.CSR, 
								   ResourceTypes.CNT, 
								   ResourceTypes.FCNT, 
								   ResourceTypes.GRP, 
								   ResourceTypes.LCP,
								   ResourceTypes.NOD,
								   ResourceTypes.PRMR,
								   ResourceTypes.PRP,
								   ResourceTypes.REQ, 
								   ResourceTypes.SCH,
								   ResourceTypes.SUB, 
								   ResourceTypes.TS, 
								   ResourceTypes.TSB, 
								   ResourceTypes.CSEBaseAnnc ]
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
			'loc': None,	
			'cstn': None,
			'acpi': None,

			# Resource attributes
			'poa': None,
			'nl': None,
			'daci': None,
			'esi': None,
			'srv': None,
			'cst': None,
			'csi': None,
			'csz': None,
			'ctm': None,
	}
	"""	Represent a dictionary of attribute policies used in validation. """


	def initialize(self, pi:str, originator:str) -> None:

		self.setAttribute('ri', 'cseid', overwrite = False)
		self.setAttribute('rn', 'cse', overwrite = False)
		self.setAttribute('csi', '/cse', overwrite = False)

		self.setAttribute('poa', RC.csePOA, overwrite = False)	
		self.setAttribute('cst', RC.cseType, overwrite = False)
		self.setAttribute('srt', ResourceTypes.supportedResourceTypes())			#  type: ignore
		self.setAttribute('csz', ContentSerializationType.supportedContentSerializations())
		self.setAttribute('srv', RC.supportedReleaseVersions)			# This must be a list

		# remove the et attribute that was set by the parent. The CSEBase doesn't have one	
		self.delAttribute('et', setNone = False)	

		super().initialize(pi, originator)


	def activate(self, parentResource:Resource, originator:str) -> None:
		super().activate(parentResource, originator)
		if not isValidCSI(self.csi):
			raise BAD_REQUEST(f'Wrong format for CSEBase.csi: {self.csi}')


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		super().validate(originator, dct, parentResource)
		self._normalizeURIAttribute('poa')

		# Update the hcl attribute in the hosting node (similar to AE)
		nl = self['nl']
		_nl_ = self[Constants.attrNode]

		if nl or _nl_:
			if nl != _nl_:
				if _nl_:
					if nresource := CSE.dispatcher.retrieveResource(_nl_):
						nresource['hcl'] = None # remove old link
						CSE.dispatcher.updateLocalResource(nresource)
				self[Constants.attrNode] = nl

				nresource = CSE.dispatcher.retrieveResource(nl)
				nresource['hcl'] = self['ri']
				nresource.dbUpdate(True)
				#CSE.dispatcher.updateLocalResource(nresource)

			self[Constants.attrNode] = nl


	def willBeRetrieved(self, originator:str, 
							  request:Optional[CSERequest] = None, 
							  subCheck:Optional[bool] = True) -> None:
		super().willBeRetrieved(originator, request, subCheck = subCheck)

		# add the current time to this resource instance
		self.setAttribute('ctm', CSE.time.getCSETimestamp())


	def childWillBeAdded(self, childResource: Resource, originator: str) -> None:
		super().childWillBeAdded(childResource, originator)
		if childResource.ty == ResourceTypes.SCH:
			if CSE.dispatcher.retrieveDirectChildResources(self.ri, ResourceTypes.SCH):
				raise BAD_REQUEST('Only one <schedule> resource is allowed for the CSEBase')


def getCSE() -> CSEBase:	# Actual: CSEBase Resource
	"""	Return the <CSEBase> resource.

		Return:
			<CSEBase> resource.
	"""
	return resourceFromCSI(RC.cseCsi)
