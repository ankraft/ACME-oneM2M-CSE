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
from .Resource import *
from typing import Union
import Utils, CSE
from Types import ResourceTypes as T, Result, AttributePolicies, JSON, AttributePolicies
from Types import Announced as AN 
from Validator import addPolicy
from Logging import Logging

class AnnounceableResource(Resource):

	def __init__(self, ty:T, dct:JSON=None, pi:str=None, tpe:str=None, create:bool=False, inheritACP:bool=False, readOnly:bool=False, rn:str=None, attributePolicies:AttributePolicies=None, isVirtual:bool=False) -> None:
		super().__init__(ty, dct, pi, tpe=tpe, create=create, inheritACP=inheritACP, readOnly=readOnly, rn=rn, attributePolicies=attributePolicies, isVirtual=isVirtual)
		self._origAA = None	# hold original announceableAttributes when doing an update


	def activate(self, parentResource:Resource, originator:str) -> Result:
		Logging.logDebug(f'Activating AnnounceableResource resource: {self.ri}')
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# Check announcements
		if self.at is not None:
			CSE.announce.announceResource(self)
		return res


	def deactivate(self, originator:str) -> None:
		Logging.logDebug(f'Deactivating AnnounceableResource and removing sub-resources: {self.ri}')

		# perform deannouncements
		if self.at is not None:
			CSE.announce.deAnnounceResource(self)
		super().deactivate(originator)


	def update(self, dct:JSON=None, originator:str=None) -> Result:
		Logging.logDebug(f'Updating AnnounceableResource: {self.ri}')
		self._origAA = self.aa
		self._origAT = self.at
		if not (res := super().update(dct=dct, originator=originator)).status:
			return res

		# Check announcements
		if self.at is not None:
			CSE.announce.announceUpdatedResource(self)
		else:
			if self._origAT is not None:	# at is removed in update, so remove self
				CSE.announce.deAnnounceResource(self)
		return res



	def validate(self, originator:str=None, create:bool=False, dct:JSON=None) -> Result:
		Logging.logDebug(f'Validating AnnounceableResource: {self.ri}')
		if (res := super().validate(originator, create, dct)).status == False:
			return res

		announceableAttributes = []
		if self.aa is not None:
			announceableAttributes = deepcopy(self.aa)
		for attr, v in self.attributePolicies.items():
			# Removing non announceable attributes
			if attr in announceableAttributes:
				if v[5] == AN.NA:  # remove attributes which are not announceable
					announceableAttributes.remove(attr)
					continue
				if not self.hasAttribute(attr):	# remove attributes that are in aa but not in the resource
					announceableAttributes.remove(attr)
					continue


		# If announceableAttributes is now an empty list, set aa to None
		self['aa'] = None if len(announceableAttributes) == 0 else announceableAttributes
		return Result(status=True)


	def createAnnouncedResourceDict(self, remoteCSR:Resource, isCreate:bool=False, csi:str=None) -> JSON:
		"""	Create the dict stub for the announced resource.
		"""
		# special case for FCNT, FCI
		if (additionalAttributes := CSE.validator.getAdditionalAttributesFor(self.tpe)) is not None:
			# policies = addPolicy(deepcopy(self.resourceAttributePolicies), additionalAttributes)
			policies = addPolicy(deepcopy(self.attributePolicies), additionalAttributes)
			return self._createAnnouncedDict(policies, remoteCSR, isCreate=isCreate, remoteCsi=csi)
		# Normal behaviour for other resources
		return self.validateAnnouncedDict( self._createAnnouncedDict(self.attributePolicies, remoteCSR, isCreate=isCreate, remoteCsi=csi) )


	def validateAnnouncedDict(self, dct:JSON) -> JSON:
		""" Possibility to add or modify the announced Dict. This can be implemented
			in the child classes.
		"""
		return dct


	def _createAnnouncedDict(self, policies:AttributePolicies, remoteCSR:Resource, isCreate:bool=False, remoteCsi:str=None) -> JSON:
		"""	Actually create the resource dict.
		"""
		# Stub
		if self.ty != T.MGMTOBJ:
			tpe = T(self.ty).announced().tpe()
		else:
			tpe = T.announcedMgd(self.mgd).tpe()

		# get  all resource specific policies and add the mandatory ones
		announcedAttributes = self._getAnnouncedAttributes(policies)

		if isCreate:
			dct:JSON = { tpe : {  # with the announced variant of the tpe
							'et'	: self.et,
							'lnk'	: f'{CSE.cseCsi}/{self.ri}',
						}
				}
			# Add more  attributes
			body = dct[tpe]
			if (st := self.st) is not None:
				body['st'] = st

			if (lbl := self.lbl) is not None:
				body['lbl'] = deepcopy(lbl)


			# copy mandatoy and optional attributes
			for attr in announcedAttributes:
				body[attr] = self[attr]

			#
			#	overwrite (!) acpi
			#
			# if (acpi := self.acpi) is not None:
			# 	acpi = [ f'{CSE.cseCsi}/{acpi}' for acpi in self.acpi ]	# set to local CSE.csi
			# else:
			# 	acpi = None
			# add remote acpi so that we will have access
			# if remoteCSR is not None and (regAcpi := remoteCSR.acpi) is not None:
			# 	if remoteCsi is not None:
			# 		# acpi.extend([f'{CSE.remote.cseCsi}/{a}' for a in regAcpi])
			# 		acpi.extend([a for a in regAcpi])
			# 	else:
			# 		acpi.extend(regAcpi)
			# Utils.setXPath(	dct, f'{tpe}/acpi', acpi)
			if (acpi := self.acpi) is not None:
				acpi = [ f'{CSE.cseCsi}/{acpi}' for acpi in self.acpi ]	# set to local CSE.csi
				body['acpi'] = acpi
				# Utils.setXPath(	dct, f'{tpe}/acpi', acpi)


		else: # update. Works a bit different

			if (modifiedAttributes := self[self._modified]) is None:
				return None

			dct = { tpe : { } } # with the announced variant of the tpe
			body = dct[tpe]


			# copy only the updated attributes
			for attr in modifiedAttributes:
				if attr in announcedAttributes or (attr in policies and policies[attr][5] == AN.MA):	# either announced or an MA attribute
					body[attr] = self[attr]

			# copy only the updated attributes
			# for attr in announcedAttributes:
			# 	if attr in modifiedAttributes:
			# 		body[attr] = self[attr]

			#Add more attributes
			# TODO: remove?
			# for attr in modifiedAttributes:
			# 	if attr in [ 'lbl' ]:
			# 		body[attr] = self[attr]

			# if aa was modified check also those attributes even when they are not modified
			if 'aa' in modifiedAttributes and modifiedAttributes['aa'] is not None:
				for attr in modifiedAttributes['aa']:
					if attr not in body:
						body[attr] = self[attr]

			# now add the to-be-removed attributes with null in case they are removed from the aa or aa is None
			if self._origAA is not None:
				for attr in self._origAA:
					if attr not in announcedAttributes:
						body[attr] = None

		return dct


	#########################################################################
	#
	#	Policy support
	#

	# def _getAnnouncedAttributes(self, policies:Dict[str, List[Any]]) -> List[str]:
	# 	"""	Return a list of mandatory and optional announced attributes. 
	# 		The function only returns those attributes that are also present in the resource!
	# 	"""
	# 	mandatory = []
	# 	optional = []
	# 	announceableAttributes = []
	# 	if self.aa is not None:
	# 		announceableAttributes = deepcopy(self.aa)
	# 	for attr,v in policies.items():
	# 		# Removing non announceable attributes
	# 		if attr in announceableAttributes and v[5] == AN.NA:  # remove attributes which are not announceable
	# 			announceableAttributes.remove(attr)
	# 		if self.hasAttribute(attr):
	# 			if v[5] == AN.MA:
	# 				mandatory.append(attr)
	# 			elif v[5] == AN.OA and attr in announceableAttributes:	# only add optional attributes that are also in aa
	# 				optional.append(attr)

	# 	# If announceableAttributes is now an empty list, set aa to None
	# 	self['aa'] = None if len(announceableAttributes) == 0 else announceableAttributes

	# 	return mandatory + optional
	def _getAnnouncedAttributes(self, policies:AttributePolicies) -> list[str]:
		"""	Return a list of mandatory and optional announced attributes. 
			The function only returns those attributes that are also present in the resource!
		"""
		mandatory = []
		optional = []
		announceableAttributes = []
		if self.aa is not None:
			announceableAttributes = self.aa
		for attr,v in policies.items():
			if self.hasAttribute(attr):
				if v[5] == AN.MA:
					mandatory.append(attr)
				elif v[5] == AN.OA and attr in announceableAttributes:	# only add optional attributes that are also in aa
					optional.append(attr)
				# else: just ignore AN.NA

		return mandatory + optional
