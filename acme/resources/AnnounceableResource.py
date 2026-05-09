#
#	AnnounceableResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" This module implements the base class for all announceable resources.
"""

from __future__ import annotations
from typing import Optional, Tuple, Any, TYPE_CHECKING

from copy import deepcopy
from ..etc.Types import ResourceTypes, JSON, AttributePolicyDict
from ..etc.Types import Announced, IdentifierScope
from ..etc.ResponseStatusCodes import BAD_REQUEST, NOT_IMPLEMENTED
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..etc.IDUtils import isAbsolute, toAbsolute, toSPRelative
from ..runtime.Logging import Logging as L
from ..runtime.PluginSupport import requires
from .Resource import Resource, addToInternalAttributes

if TYPE_CHECKING:
	from ..plugins.services.AnnouncementManager import AnnouncementManager
	from ..services.Validator import Validator


# Add to internal attributes
addToInternalAttributes(Constants.attrAnnouncedTo) # add announcedTo to internal attributes


@requires(announcementManager='acme.plugins.services.AnnouncementManager', required=False)
@requires(validator='acme.services.Validator')
class AnnounceableResource(Resource):
	"""	Base class for all announceable resources.
	"""

	announcementManager: Optional[AnnouncementManager] = None
	""" AnnouncementManager instance. """

	validator: Validator = None
	""" Validator instance. """

	def __init__(self, dct:Optional[JSON]=None, create:Optional[bool]=False) -> None:
		super().__init__(dct, create=create)
		
		self._origAA = None	# hold original announceableAttributes when doing an update
		self.setAttribute(Constants.attrAnnouncedTo, [], overwrite=False)


	def activate(self, parentResource:Resource, originator:str) -> None:
		# L.isDebug and L.logDebug(f'Activating AnnounceableResource resource: {self.ri}')
		super().activate(parentResource, originator)

		# Check announcements
		if self.at:
			if not self.announcementManager:
				raise NOT_IMPLEMENTED(L.logWarn('AnnouncementManager is disabled, cannot announce resource'))
			self.announcementManager.announceResource(self)


	def deactivate(self, originator:str, parentResource:Resource) -> None:
		# L.isDebug and L.logDebug(f'Deactivating AnnounceableResource and removing sub-resources: {self.ri}')
		# perform deannouncements
		if self.at:
			if not self.announcementManager:
				raise NOT_IMPLEMENTED(L.logWarn('AnnouncementManager is disabled, cannot de-announce resource'))
			self.announcementManager.deAnnounceResource(self)
		super().deactivate(originator, parentResource)


	def update(self, dct:JSON=None, 
					 originator:Optional[str]=None, 
					 doValidateAttributes:Optional[bool]=True) -> None:
		# L.isDebug and L.logDebug(f'Updating AnnounceableResource: {self.ri}')
		self._origAA = self.aa
		""" Store the original announceableAttributes for later use in the update
			so that we can check whether they are removed.
		"""

		self._origAT = self.at
		""" Store the original at attribute for later use in the update
			so that we can check whether it is removed.
		"""
		
		super().update(dct, originator, doValidateAttributes)

		# TODO handle update from announced resource. Check originator???

		# Check announcements
		if self.at:
			if not self.announcementManager:
				raise NOT_IMPLEMENTED(L.logWarn('AnnouncementManager is disabled, cannot announce updated resource'))
			self.announcementManager.announceUpdatedResource(self, originator)
		else:
			if self._origAT:	# at is removed in update, so remove self
				if not self.announcementManager:
					raise NOT_IMPLEMENTED(L.logWarn('AnnouncementManager is disabled, cannot de-announce updated resource'))
				self.announcementManager.deAnnounceResource(self)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		# L.isDebug and L.logDebug(f'Validating AnnounceableResource: {self.ri}')
		super().validate(originator, dct, parentResource)

		announceableAttributes = []
		if self.aa:
			# Check whether all the attributes in announcedAttributes are actually resource attributes
			# For FCNT and FCI also check the customAttributes
			for aa in self.aa:
				if not (aa in self._attributes or (self.ty in (ResourceTypes.FCNT, ResourceTypes.FCI) and aa in self.customAttributes)):
					raise BAD_REQUEST(L.logDebug(f'Non-resource attribute in aa: {aa}'))

			# deep-copy the announcedAttributes
			announceableAttributes = deepcopy(self.aa)

		for attr, policy in self._attributes.items():
			# Removing non announceable attributes
			if attr in announceableAttributes:
				if policy.announcement == Announced.NA:  # remove attributes which are not announceable
					announceableAttributes.remove(attr)
					continue
				if not self.hasAttribute(attr):	# remove attributes that are in aa but not in the resource
					announceableAttributes.remove(attr)
					continue	

		# If announceableAttributes is now an empty list, set aa to None
		if self.aa:
			self['aa'] = None if len(announceableAttributes) == 0 else announceableAttributes


	def createAnnouncedResourceDict(self, isCreate:Optional[bool]=False, announceTo:Optional[str]=None) -> JSON:
		"""	Create the dict stub for the announced resource.
		"""
		# special case for FCNT, FCI
		if (additionalAttributes := self.validator.getFlexContainerAttributesFor(self.typeShortname)):
			attributes:AttributePolicyDict = deepcopy(self._attributes)
			attributes.update(additionalAttributes)
			return self._createAnnouncedDict(attributes, isCreate=isCreate, isRemoteSP=isAbsolute(announceTo))
		# Normal behaviour for other resources
		# L.inspect(self._createAnnouncedDict(self._attributes, isCreate=isCreate, isRemoteSP=isAbsolute(announceTo)) )
		return self.validateAnnouncedDict( self._createAnnouncedDict(self._attributes, isCreate=isCreate, isRemoteSP=isAbsolute(announceTo)) )


	def validateAnnouncedDict(self, dct:JSON) -> JSON:
		""" Possibility to add or modify the announced Dict. This can be implemented
			in the child classes.
		"""
		return dct


	def _createAnnouncedDict(self, attributes: AttributePolicyDict, isCreate: bool, isRemoteSP: bool) -> JSON:
		"""	Actually create the resource dict.
		"""

		# Stub
		if self.ty in (ResourceTypes.FCNT, ResourceTypes.FCI):
			typeShortname = f'{self.typeShortname}Annc'
		else:
			typeShortname = ResourceTypes(self.ty).announced(self.mgd).typeShortname()	# Hack, bc management objects do it a bit differently

		# get  all resource specific policies and add the mandatory ones
		announcedAttributes = self._getAnnouncedAttributes(attributes)

		match isCreate:
			case True:
				dct:JSON = { typeShortname : {  # with the announced variant of the typeShortname
								'et'	: self.et,
								'lnk'	: f'{RC.cseSPCsi}/{self.ri}' if isRemoteSP else f'{RC.cseCsi}/{self.ri}',
							}
					}
				# Add more  attributes
				body = dct[typeShortname]

				# Conditional announced
				if lbl := self.lbl:
					body['lbl'] = deepcopy(lbl)

				# copy mandatoy and optional attributes
				ty = self.ty if self.ty != ResourceTypes.MGMTOBJ else self.mgd
				for attr in announcedAttributes:
					policy = attributes.get(attr) # The policy must in the "attributes" dict. So use it instead of asking the validator again
					body[attr] = self.validator.convertIdentifierAttributeToScope(self[attr], 
																				  policy.type, 
																				  policy, 
																				  scope=IdentifierScope.Absolute if isRemoteSP else IdentifierScope.SPRelative)	# convert to Absolute for remote SP, SP-relative for local CSE
					# body[attr] = self[attr]

				if (acpi := body.get('acpi')) is not None:	# acpi might be an empty list
					# acpi = [ f'{RC.cseCsi}/{acpi}' if not acpi.startswith(RC.cseCsi) else acpi 
					# 		 for acpi in self.acpi]	# set to local CSE.csi
					acpi = [ toAbsolute(acpi, spId=RC.cseSPid) if isRemoteSP else toSPRelative(acpi) for acpi in acpi ]
					body['acpi'] = acpi
				
				# Set the resourceName explicitly for the CSEBase
				if self.ty == int(ResourceTypes.CSEBase):
					body['rn'] = f'{RC.cseSPIDSlashLess}_{self.rn}'

			case False: # update. Works a bit different
				if not (modifiedAttributes := self[Constants.attrModified]):
					return None
				dct = { typeShortname : { } } # with the announced variant of the typeShortname
				body = dct[typeShortname]


				# copy only the modified  attributes
				for attr in modifiedAttributes:
					attributePolicy = attributes.get(attr)
					if attr in announcedAttributes or (attributePolicy is not None and attributePolicy.announcement == Announced.MA):	# either announced or an MA attribute
					# if attr in announcedAttributes or (attr in policies and policies[attr][5] == Announced.MA):	# either announced or an MA attribute
						body[attr] = self[attr]

				# if aa was modified check also those attributes even when they are not modified
				if 'aa' in modifiedAttributes and modifiedAttributes['aa']:
					for attr in modifiedAttributes['aa']:
						L.logWarn(attr)
						if attr not in body:
							body[attr] = self[attr]

				# now add the to-be-removed attributes with null in case they are removed from the aa or aa is None
				if self._origAA:
					for attr in self._origAA:
						if attr not in announcedAttributes:
							body[attr] = None

		return dct


	def addAnnouncementToResource(self, csi:str, remoteRI:str) -> None:
		"""	Add anouncement information to the resource. These are a list of tuples of 
			the csi to which the resource is registered and the CSE-relative ri of the 
			resource on the remote CSE. Also, add the reference in the at attribute.

			Args:
				csi: csi of the remote CSE
				remoteRI: ri of the announced resource on the remote CSE
		"""

		if not csi or not remoteRI:
			raise ValueError('csi and remoteRI must be provided')
		
		# Set the internal __announcedTo__ attribute
		ats = self.getAnnouncedTo()
		ats.append((csi, remoteRI))
		self.setAnnouncedTo(ats)

		# Modify the at attribute, if applicable
		if 'at' in self._attributes:
			if (at := self.at) is None:
				at = []
			if len(at) > 0 and csi in at:
				at[at.index(csi)] = f'{csi}/{remoteRI}' # replace the element in at
			else:
				at.append(f'{csi}/{remoteRI}')
			self.setAttribute('at', at)


	def removeAnnouncementFromResource(self, csi:str) -> Optional[str]:
		"""	Remove anouncement information from the resource. These are a list of tuples of 
			the csi to which the resource is registered and the CSE-relative ri of the 
			resource on the remote CSE. Also, remove the reference from the at attribute.

			Args:
				csi: csi of the remote CSE
		"""
		ats = self.getAnnouncedTo()
		remoteRI = None
		for x in ats:
			if x[0] == csi:
				remoteRI = x[1]
				ats.remove(x)
				self.setAnnouncedTo(ats)
				break
		return remoteRI

	
	#########################################################################
	#
	#	Policy support
	#
	def _getAnnouncedAttributes(self, attributes:AttributePolicyDict) -> list[str]:
		"""	Return a list of mandatory and optional announced attributes. 
			The function only returns those attributes that are also present in the resource!
		"""
		mandatory = []
		optional = []
		# announceableAttributes:Optional[list[str]] = None
		# if self.aa is not None:
		# 	announceableAttributes = self.aa
		_aa = self.aa
		for attr in attributes.keys():
			if self.hasAttribute(attr):
				if not (policy := attributes.get(attr)):
					continue
				
				match policy.announcement:
					case Announced.MA:
						mandatory.append(attr)
					case Announced.OA if _aa is not None and attr in _aa: # only add optional attributes that are also in aa
						optional.append(attr)			
					case Announced.NA:
						# just ignore Announced.NA
						pass

		return mandatory + optional


	def getAnnouncedTo(self) -> list[Tuple[str, str]]:
		"""	Return the internal *announcedTo* list attribute of a resource.

			Return:
				The internal list of *announcedTo* tupples (csi, remote resource ID) for this resource.
		"""
		return self[Constants.attrAnnouncedTo]
	

	def setAnnouncedTo(self, announcedTo:list[Tuple[str, str]]) -> None:
		"""	Set the internal *announcedTo* list attribute of a resource.

			Args:
				announcedTo: The list of *announcedTo* tupples (csi, remote resource ID) to assign to a resource.
		"""
		self.setAttribute(Constants.attrAnnouncedTo, announcedTo)
