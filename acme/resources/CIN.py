#
#	CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: ContentInstance
#

from __future__ import annotations
from etc.Constants import Constants as C
from etc.Types import ResourceTypes as T, Result, ResponseCode as RC, JSON
from services.Validator import constructPolicy, addPolicy
from resources.Resource import *
from resources.AnnounceableResource import AnnounceableResource

# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi', 'et', 'ct', 'lt', 'st', 'lbl', 'at', 'aa', 'cr',
])
cinPolicies = constructPolicy([
	'cnf', 'cs', 'conr', 'con', 'or', 'conr', 'dcnt'
])
attributePolicies = addPolicy(attributePolicies, cinPolicies)


class CIN(AnnounceableResource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes:list[T] = [ ]


	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(T.CIN, dct, pi, create=create, inheritACP=True, readOnly = True, attributePolicies=attributePolicies)

		self.resourceAttributePolicies = cinPolicies	# only the resource type's own policies

		if self.dict is not None:
			self.setAttribute('con', '', overwrite=False)
			self.setAttribute('cs', Utils.getAttributeSize(self.con))


	# Forbid updating
	def update(self, dct:JSON=None, originator:str=None) -> Result:
		return Result(status=False, rsc=RC.operationNotAllowed, dbg='updating CIN is forbidden')


	def willBeRetrieved(self, originator:str) -> Result:
		if not (res := super().willBeRetrieved(originator)).status:
			return res

		# Check whether the parent container's *disableRetrieval* attribute is set to True.
		if (cnt := self.retrieveParentResource()) is not None and (disr := cnt.disr) is not None and disr:	# False means "not disabled retrieval"
			L.isDebug and L.logDebug(dbg := f'Retrieval is disabled for the parent <container>')
			return Result(status=False, rsc=RC.operationNotAllowed, dbg=dbg)
		
		# Check deletion Count
		if (dcnt := self.dcnt) is not None:
			L.isDebug and L.logDebug(f'Decreasing dcnt for <cin>, ri: {self.ri}, ({dcnt} -> {dcnt-1})')
			dcnt -= 1
			if dcnt > 0:	# still > 0 -> CIN is not deleted
				self.setAttribute('dcnt', dcnt)
				self.dbUpdate()
				# Since this is handled as a post decrement we need to set-back the value of dcnt.
				# Attn: After this this value in the hold instance and in the DB are different !
				self.setAttribute('dcnt', dcnt+1)
			else:
				L.isDebug and L.logDebug(f'Deleting <cin>, ri: {self.ri} because dcnt reached 0')
				CSE.dispatcher.deleteResource(self, originator=originator)

		return Result(status=True)


	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if (res := super().validate(originator, create, dct, parentResource)).status == False:
			return res

		# Check the format of the CNF attribute
		if (cnf := self.cnf) is not None:
			if not (res := CSE.validator.validateCNF(cnf)).status:
				return Result(status=False, rsc=RC.badRequest, dbg=res.dbg)

		# Add ST attribute
		if (parentResource := parentResource.dbReload().resource) is not None:		# Read the resource again in case it was updated in the DB
			self.setAttribute('st', parentResource.st)
		
		return Result(status=True)

