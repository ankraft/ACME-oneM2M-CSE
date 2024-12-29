#
#	AnnounceableResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all announceable resources
#

from __future__ import annotations
from typing import Optional, Tuple, Any

from copy import deepcopy
from ..etc.Types import ResourceTypes, JSON, AttributePolicyDict, AttributePolicy, BasicType
from ..etc.Types import Announced
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.Constants import Constants, RuntimeConstants as RC
from ..runtime import CSE
from ..runtime.Logging import Logging as L
from ..etc.ACMEUtils import toSPRelative
from .Resource import Resource, addToInternalAttributes

# Add to internal attributes
addToInternalAttributes(Constants.attrAnnouncedTo) # add announcedTo to internal attributes


class AnnounceableResource(Resource):

	def __init__(self, dct:Optional[JSON] = None, create:Optional[bool] = False) -> None:
		super().__init__(dct, create = create)
		
		self._origAA = None	# hold original announceableAttributes when doing an update
		self.setAttribute(Constants.attrAnnouncedTo, [], overwrite = False)


	def activate(self, parentResource:Resource, originator:str) -> None:
		# L.isDebug and L.logDebug(f'Activating AnnounceableResource resource: {self.ri}')
		super().activate(parentResource, originator)

		# Check announcements
		if self.at:
			CSE.announce.announceResource(self)


	def deactivate(self, originator:str, parentResource:Resource) -> None:
		# L.isDebug and L.logDebug(f'Deactivating AnnounceableResource and removing sub-resources: {self.ri}')
		# perform deannouncements
		if self.at:
			CSE.announce.deAnnounceResource(self)
		super().deactivate(originator, parentResource)


	def update(self, dct:JSON = None, 
					 originator:Optional[str] = None, 
					 doValidateAttributes:Optional[bool] = True) -> None:
		# L.isDebug and L.logDebug(f'Updating AnnounceableResource: {self.ri}')
		self._origAA = self.aa
		self._origAT = self.at
		super().update(dct, originator, doValidateAttributes)

		# TODO handle update from announced resource. Check originator???

		# Check announcements
		if self.at:
			CSE.announce.announceUpdatedResource(self, originator)
		else:
			if self._origAT:	# at is removed in update, so remove self
				CSE.announce.deAnnounceResource(self)


	def validate(self, originator:Optional[str] = None, 
					   dct:Optional[JSON] = None, 
					   parentResource:Optional[Resource] = None) -> None:
		# L.isDebug and L.logDebug(f'Validating AnnounceableResource: {self.ri}')
		super().validate(originator, dct, parentResource)

		announceableAttributes = []
		if self.aa:
			# Check whether all the attributes in announcedAttributes are actually resource attributes
			for aa in self.aa:
				if not aa in self._attributes:
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


	def createAnnouncedResourceDict(self, isCreate:Optional[bool] = False) -> JSON:
		"""	Create the dict stub for the announced resource.
		"""
		# special case for FCNT, FCI
		if (additionalAttributes := CSE.validator.getFlexContainerAttributesFor(self.typeShortname)):
			attributes:AttributePolicyDict = deepcopy(self._attributes)
			attributes.update(additionalAttributes)
			return self._createAnnouncedDict(attributes, isCreate = isCreate)
		# Normal behaviour for other resources
		return self.validateAnnouncedDict( self._createAnnouncedDict(self._attributes, isCreate = isCreate) )


	def validateAnnouncedDict(self, dct:JSON) -> JSON:
		""" Possibility to add or modify the announced Dict. This can be implemented
			in the child classes.
		"""
		return dct


	def _createAnnouncedDict(self, attributes:AttributePolicyDict, isCreate:Optional[bool] = False) -> JSON:
		"""	Actually create the resource dict.
		"""

		def _convertIdentifierAttributeToSPRelative(value:Any, typ:BasicType, policy:AttributePolicy) -> Any:
			"""	Convert an attribute to the SP-relative form if it is an identifier.
				This is a recursive function that is called for each attribute of a complex attribute
				(e.g. a list or a complex attribute).

				Args:
					value: The value to convert.
					typ: The type of the value.
					policy: The attribute policy of the value.

				Return:
					The converted value.
				
				TODO:
					This function could be moved to the utils module.
			"""

			# Return None if the value is None (e.g. in updates)
			if value is None:
				return None
			
			# L.logWarn(f'Converting attribute {value} - {typ} - {policy} to SP-relative form.')
			match typ:
				case BasicType.ID:
					return toSPRelative(value)
				case BasicType.list | BasicType.listNE:
					return [ _convertIdentifierAttributeToSPRelative(v, policy.ltype, policy) for v in value]
				case BasicType.complex:
					_r = {}
					typeName = policy.lTypeName if policy.type == BasicType.list else policy.typeName;
					for k, v in value.items():
						if not (_policy := CSE.validator.getAttributePolicy(typeName, k)):
							raise BAD_REQUEST(f'unknown or undefined attribute:{k} in complex type: {typeName}')
						_r[k] = _convertIdentifierAttributeToSPRelative(v, _policy.type, _policy)
					return _r
				case _:
					return value


		# Stub
		typeShortname = ResourceTypes(self.ty).announced(self.mgd).typeShortname()	# Hack, bc management objects do it a bit differently

		# get  all resource specific policies and add the mandatory ones
		announcedAttributes = self._getAnnouncedAttributes(attributes)

		if isCreate:
			dct:JSON = { typeShortname : {  # with the announced variant of the typeShortname
							'et'	: self.et,
							'lnk'	: f'{RC.cseCsi}/{self.ri}',
						}
				}
			# Add more  attributes
			body = dct[typeShortname]

			# Conditional announced
			if lbl := self.lbl:
				body['lbl'] = deepcopy(lbl)

			# copy mandatoy and optional attributes
			for attr in announcedAttributes:
				policy = CSE.validator.getAttributePolicy(self.ty, attr)
				body[attr] = _convertIdentifierAttributeToSPRelative(self[attr], policy.type, policy)
				# body[attr] = self[attr]

			if (acpi := body.get('acpi')) is not None:	# acpi might be an empty list
				acpi = [ f'{RC.cseCsi}/{acpi}' if not acpi.startswith(RC.cseCsi) else acpi for acpi in self.acpi]	# set to local CSE.csi
				body['acpi'] = acpi


		else: # update. Works a bit different

			if not (modifiedAttributes := self[Constants.attrModified]):
				return None
			dct = { typeShortname : { } } # with the announced variant of the typeShortname
			body = dct[typeShortname]


			# copy only the updated attributes
			for attr in modifiedAttributes:
				attributePolicy = attributes.get(attr)
				if attr in announcedAttributes or (attributePolicy is not None and attributePolicy.announcement == Announced.MA):	# either announced or an MA attribute
				# if attr in announcedAttributes or (attr in policies and policies[attr][5] == Announced.MA):	# either announced or an MA attribute
					body[attr] = self[attr]

			# if aa was modified check also those attributes even when they are not modified
			if 'aa' in modifiedAttributes and modifiedAttributes['aa']:
				for attr in modifiedAttributes['aa']:
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
		announceableAttributes = []
		if self.aa is not None:
			announceableAttributes = self.aa
		for attr in attributes.keys():
			if self.hasAttribute(attr):
				if not (policy := attributes.get(attr)):
					continue
				
				match policy.announcement:
					case Announced.MA:
						mandatory.append(attr)
					case Announced.OA if attr in announceableAttributes: # only add optional attributes that are also in aa
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
