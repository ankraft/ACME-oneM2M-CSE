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
from Types import ResourceTypes as T
from Validator import addPolicy

# TODO Update
# TODO Activate

class AnnounceableResource(Resource):

	def __init__(self, ty:Union[T, int], jsn:dict = None, pi:str = None, tpe:str = None, create:bool = False, inheritACP:bool = False, readOnly:bool = False, rn:str = None, attributePolicies:dict = None, isVirtual:bool = False) -> None:
		super().__init__(ty, jsn, pi, tpe=tpe, create=create, inheritACP=inheritACP, readOnly=readOnly, rn=rn, attributePolicies=attributePolicies, isVirtual=isVirtual)


	def activate(self, parentResource:Resource, originator:str) -> Tuple[bool, int, str]:
		Logging.logDebug('Activating AnnounceableResource resource: %s' % self.ri)
		if not (result := super().activate(parentResource, originator))[0]:
			return result
		# Check announcement
		if self['at'] is not None:
			CSE.announce.announceResource(self)
		return result


	def deactivate(self, originator:str) -> None:
		Logging.logDebug('Deactivating AnnounceableResource and removing sub-resources: %s' % self.ri)
		# Check deannouncement
		if self['at'] is not None:
			CSE.announce.deAnnounceResource(self)
		super().deactivate(originator)


	def update(self, jsn:dict = None, originator:str = None) -> Tuple[bool, int, str]:
		Logging.logDebug('Updating AnnounceableResource: %s' % self.ri)
		if not (result := super().update(jsn=jsn, originator=originator))[0]:
			return result
		# Check announcement
		if self['at'] is not None:
			CSE.announce.announceUpdatedResource(self)
		return result


	# create the json stub for the announced resource
	def createAnnouncedResourceJSON(self) ->  dict:
		# special case for FCNT, FCI
		if (additionalAttributes := CSE.validator.getAdditionalAttributesFor(self.tpe)) is not None:
			policies = addPolicy(self.resourceAttributePolicies.copy(), additionalAttributes)
			return self._createAnnouncedJSON(policies)
		# Normal behaviour for other resources
		return self._createAnnouncedJSON(self.resourceAttributePolicies)



	# Actually create the json
	def _createAnnouncedJSON(self, policies:Dict[str, List[Any]]) -> dict:
		rn = Utils.announcedRN(self)
		jsn = { self.tpe : {
					'rn'	: rn,	# Random? Or let the remote CSE decide? RI?
					'lnk'	: '/~%s/%s' % (Configuration.get('cse.csi'), self.ri),
					# set by parent: ri, pi, ct, lt, et
			}
		}
		if (st := self.st) is not None:
			Utils.setXPath(jsn, '%s/st' % self.tpe, st)

		# TODO ACPI
		# if (acpi := self.acpi) is not None:
		# 	Utils.setXPath(jsn, '%s/acpi' % self.tpe, acpi.copy())	
		if (lbl := self.lbl) is not None:
			Utils.setXPath(jsn, '%s/lbl' % self.tpe, lbl.copy())

		# get  all resource specific policies and add the mandatory ones
		mandatoryAttributes, optionalAttributes = CSE.validator.getAnnouncedAttributes(self, policies)
		for attr in mandatoryAttributes:
			Utils.setXPath(jsn, '%s/%s' % (self.tpe, attr), self[attr])
		for attr in optionalAttributes:
			Utils.setXPath(jsn, '%s/%s' % (self.tpe, attr), self[attr])
		return jsn

