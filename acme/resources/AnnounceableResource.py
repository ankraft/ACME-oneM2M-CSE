#
#	AnnounceableResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all announceable resources
#

from __future__ import annotations
from copy import deepcopy
from ..etc.Types import ResourceTypes as T, Result, JSON, AttributePolicyDict
from ..etc.Types import Announced as AN, ResponseStatusCode as RC
from ..services import CSE as CSE
from ..services.Logging import Logging as L
from .Resource import *

class AnnounceableResource(Resource):

	def __init__(self, ty:T, dct:JSON = None, pi:str = None, tpe:str = None, create:bool = False, inheritACP:bool = False, readOnly:bool = False, rn:str = None) -> None:
		super().__init__(ty, dct, pi, tpe = tpe, create = create, inheritACP = inheritACP, readOnly = readOnly, rn = rn,)
		self._origAA = None	# hold original announceableAttributes when doing an update


	def activate(self, parentResource:Resource, originator:str) -> Result:
		# L.isDebug and L.logDebug(f'Activating AnnounceableResource resource: {self.ri}')
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# Check announcements
		if self.at:
			return CSE.announce.announceResource(self)
		return res


	def deactivate(self, originator:str) -> None:
		# L.isDebug and L.logDebug(f'Deactivating AnnounceableResource and removing sub-resources: {self.ri}')
		# perform deannouncements
		if self.at:
			CSE.announce.deAnnounceResource(self)
		super().deactivate(originator)


	def update(self, dct:JSON = None, originator:str = None) -> Result:
		# L.isDebug and L.logDebug(f'Updating AnnounceableResource: {self.ri}')
		self._origAA = self.aa
		self._origAT = self.at
		if not (res := super().update(dct = dct, originator = originator)).status:
			return res

		# TODO handle update from announced resource. Check originator???

		# Check announcements
		if self.at:
			CSE.announce.announceUpdatedResource(self, originator)
		else:
			if self._origAT:	# at is removed in update, so remove self
				CSE.announce.deAnnounceResource(self)
		return res


	def validate(self, originator:str = None, create:bool = False, dct:JSON = None, parentResource:Resource = None) -> Result:
		# L.isDebug and L.logDebug(f'Validating AnnounceableResource: {self.ri}')
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res

		announceableAttributes = []
		if self.aa:
			# Check whether all the attributes in announcedAttributes are actually resource attributes
			for aa in self.aa:
				if not aa in self._attributes:
					L.logDebug(dbg := f'Non-resource attribute in aa: {aa}')
					return Result.errorResult(dbg = dbg)

			# deep-copy the announcedAttributes
			announceableAttributes = deepcopy(self.aa)

		for attr, policy in self._attributes.items():
			# Removing non announceable attributes
			if attr in announceableAttributes:
				if policy.announcement == AN.NA:  # remove attributes which are not announceable
					announceableAttributes.remove(attr)
					continue
				if not self.hasAttribute(attr):	# remove attributes that are in aa but not in the resource
					announceableAttributes.remove(attr)
					continue	

		# If announceableAttributes is now an empty list, set aa to None
		self['aa'] = None if len(announceableAttributes) == 0 else announceableAttributes
		return Result.successResult()


	def createAnnouncedResourceDict(self, isCreate:bool = False) -> JSON:
		"""	Create the dict stub for the announced resource.
		"""
		# special case for FCNT, FCI
		if (additionalAttributes := CSE.validator.getFlexContainerAttributesFor(self.tpe)):
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


	def _createAnnouncedDict(self, attributes:AttributePolicyDict, isCreate:bool = False) -> JSON:
		"""	Actually create the resource dict.
		"""
		# Stub
		#tpe = T.announcedMgd(self.mgd).tpe() if self.ty == T.MGMTOBJ else T(self.ty).announced().tpe()
		tpe = T(self.ty).announced().tpe()
		# if self.ty != T.MGMTOBJ:
		# 	tpe = T(self.ty).announced().tpe()
		# else:
		# 	tpe = T.announcedMgd(self.mgd).tpe()

		# get  all resource specific policies and add the mandatory ones
		announcedAttributes = self._getAnnouncedAttributes(attributes)

		if isCreate:
			dct:JSON = { tpe : {  # with the announced variant of the tpe
							'et'	: self.et,
							'lnk'	: f'{CSE.cseCsi}/{self.ri}',
						}
				}
			# Add more  attributes
			body = dct[tpe]

			# Conditional announced
			if lbl := self.lbl:
				body['lbl'] = deepcopy(lbl)

			# copy mandatoy and optional attributes
			for attr in announcedAttributes:
				body[attr] = self[attr]

			if (acpi := body.get('acpi')) is not None:	# acpi might be an empty list
				acpi = [ f'{CSE.cseCsi}/{acpi}' if not acpi.startswith(CSE.cseCsi) else acpi for acpi in self.acpi]	# set to local CSE.csi
				body['acpi'] = acpi


		else: # update. Works a bit different

			if not (modifiedAttributes := self[self._modified]):
				return None

			dct = { tpe : { } } # with the announced variant of the tpe
			body = dct[tpe]


			# copy only the updated attributes
			for attr in modifiedAttributes:
				attributePolicy = attributes.get(attr)
				if attr in announcedAttributes or (attributePolicy is not None and attributePolicy.announcement == AN.MA):	# either announced or an MA attribute
				# if attr in announcedAttributes or (attr in policies and policies[attr][5] == AN.MA):	# either announced or an MA attribute
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


	def addAnnouncementToResource(self, csi:str, remoteRI:str, ) -> None:
		"""	Add anouncement information to the resource. These are a list of tuples of 
			the csi to which the resource is registered and the CSE-relative ri of the 
			resource on the remote CSE. Also, add the reference in the at attribute.

			Args:
				csi: csi of the remote CSE
				remoteRI: ri of the announced resource on the remote CSE
		"""

		# Set the internal __announcedTo__ attribute
		ats = self.getAnnouncedTo()
		ats.append((csi, remoteRI))
		self.setAttribute(Resource._announcedTo, ats)	# TODO replacement as below?

		# Modify the at attribute, if applicable
		if 'at' in self._attributes:
			if (at := self.at) is None:
				at = []
			if len(at) > 0 and csi in at:
				at[at.index(csi)] = f'{csi}/{remoteRI}' # replace the element in at
			else:
				at.append(f'{csi}/{remoteRI}')
			self.setAttribute('at', at)


	# TODO add _removeAnnouncementFromResource() here

	
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
				
				if policy.announcement == AN.MA:
					mandatory.append(attr)
				elif policy.announcement == AN.OA and attr in announceableAttributes:	# only add optional attributes that are also in aa
					optional.append(attr)
				# else: just ignore AN.NA

		return mandatory + optional

