#
#	AnnounceableResource.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Base class for all announceable resources
#


from .Resource import *
import Utils
from Types import ResourceTypes as T, Result
from Types import Announced as AN 		# type: ignore
from Validator import addPolicy

# TODO Update
# TODO Activate

class AnnounceableResource(Resource):

	def __init__(self, ty:Union[T, int], jsn:dict=None, pi:str=None, tpe:str=None, create:bool=False, inheritACP:bool=False, readOnly:bool=False, rn:str
		=None, attributePolicies:dict=None, isVirtual:bool=False) -> None:
		super().__init__(ty, jsn, pi, tpe=tpe, create=create, inheritACP=inheritACP, readOnly=readOnly, rn=rn, attributePolicies=attributePolicies, isVirtual=isVirtual)
		self._origAA = None	# hold original announceableAttributes when doing an update


	def activate(self, parentResource:Resource, originator:str) -> Result:
		Logging.logDebug('Activating AnnounceableResource resource: %s' % self.ri)
		if not (res := super().activate(parentResource, originator)).status:
			return res

		# Check announcements
		if self.at is not None:
			CSE.announce.announceResource(self)
		return res


	def deactivate(self, originator:str) -> None:
		Logging.logDebug('Deactivating AnnounceableResource and removing sub-resources: %s' % self.ri)

		# perform deannouncements
		if self.at is not None:
			CSE.announce.deAnnounceResource(self)
		super().deactivate(originator)


	def update(self, jsn:dict=None, originator:str=None) -> Result:
		Logging.logDebug('Updating AnnounceableResource: %s' % self.ri)
		self._origAA = self.aa
		self._origAT = self.at
		if not (res := super().update(jsn=jsn, originator=originator)).status:
			return res

		# Check announcements
		if self.at is not None:
			CSE.announce.announceUpdatedResource(self)
		else:
			if self._origAT is not None:	# at is removed in update, so remove self
				CSE.announce.deAnnounceResource(self)
		return res


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self, remoteCSR:Resource, isCreate:bool=False, csi:str=None) ->  dict:
		# special case for FCNT, FCI
		if (additionalAttributes := CSE.validator.getAdditionalAttributesFor(self.tpe)) is not None:
			policies = addPolicy(self.resourceAttributePolicies.copy(), additionalAttributes)
			return self._createAnnouncedJSON(policies, remoteCSR, isCreate=isCreate, remoteCsi=csi)
		# Normal behaviour for other resources
		return self._createAnnouncedJSON(self.resourceAttributePolicies, remoteCSR, isCreate=isCreate, remoteCsi=csi)


	# Actually create the json
	def _createAnnouncedJSON(self, policies:Dict[str, List[Any]], remoteCSR:Resource, isCreate:bool=False, remoteCsi:str=None) -> dict:
		# Stub
		if self.ty != T.MGMTOBJ:
			tpe = T(self.ty).announced().tpe()
		else:
			tpe = T(self.ty).announcedMgd(self.mgd).tpe()

		# get  all resource specific policies and add the mandatory ones
		announcedAttributes = self._getAnnouncedAttributes(policies)


		if isCreate:

			localCsi = Configuration.get('cse.csi')

			jsn = { tpe : {  # with the announced variant of the tpe
						'et'	: self.et,
						'lnk'	: '%s/%s' % (localCsi, self.ri),
						# set by parent: ri, pi, ct, lt, et
				}
			}
			# Add more  attributes
			body = jsn[tpe]
			if (st := self.st) is not None:
				body['st'] = st

			if (lbl := self.lbl) is not None:
				body['lbl'] = lbl.copy()


			# copy mandatoy and optional attributes
			for attr in announcedAttributes:
				body[attr] = self[attr]

			#
			#	overwrite (!) acpi
			#
			if (acpi := self.acpi) is not None:
				acpi = [ '%s/%s' % (localCsi, acpi) for acpi in self.acpi ]
			else:
				acpi = []
			# add remote acpi so that we will have access
			if remoteCSR is not None and (regAcpi := remoteCSR.acpi) is not None:
				if remoteCsi is not None:
					# acpi.extend(['%s/%s' % (CSE.remote.cseCsi, a) for a in regAcpi])
					acpi.extend([a for a in regAcpi])
				else:
					acpi.extend(regAcpi)
			Utils.setXPath(	jsn, '%s/acpi' % tpe, acpi)

		else: # update. Works a bit different

			if (modifiedAttributes := self[self._modified]) is None:
				return None

			jsn = { tpe : { } } # with the announced variant of the tpe
			body = jsn[tpe]

			# copy only the updated attributes
			for attr in announcedAttributes:
				if attr in modifiedAttributes:
					body[attr] = self[attr]

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

		return jsn


	#########################################################################
	#
	#	Policy support
	#

	def _getAnnouncedAttributes(self, policiespolicies:Dict[str, List[Any]]) -> List[str]:
		"""	Return a list of mandatory and optional announced attributes. 
			The function only returns those attributes that are also present in the resource!
		"""
		announceableAttributes = self.aa
		mandatory = []
		optional = []
		for attr,v in policiespolicies.items():
			if self.hasAttribute(attr):
				if v[5] == AN.MA:
					mandatory.append(attr)
				elif announceableAttributes is not None and v[5] == AN.OA and attr in announceableAttributes:	# only add optional attributes that are also in aa
					optional.append(attr)
		return mandatory + optional
