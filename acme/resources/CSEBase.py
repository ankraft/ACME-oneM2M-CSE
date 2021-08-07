#
#	CSEBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CSEBase
#

from etc.Constants import Constants as C
from etc.Types import ResourceTypes as T, Result, JSON
from resources.Resource import *
from services.Validator import constructPolicy
import services.CSE as CSE, etc.DateUtils as DateUtils


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi',  'ct', 'lt', 'lbl', 'loc', 'hld',
	'acpi', 'poa', 'nl', 'daci', 'esi', 'srv', 'cst', 'csi', 'csz'
])

class CSEBase(Resource):

	# Specify the allowed child-resource types
	allowedChildResourceTypes = [ T.ACP, T.AE, T.CSR, T.CNT, T.FCNT, T.GRP, T.NOD, T.REQ, T.SUB, T.TS ]


	def __init__(self, dct:JSON=None, create:bool=False) -> None:
		super().__init__(T.CSEBase, dct, '', create=create, attributePolicies=attributePolicies)

		self.setAttribute('ri', 'cseid', overwrite=False)
		self.setAttribute('rn', 'cse', overwrite=False)
		self.setAttribute('csi', '/cse', overwrite=False)

		self.setAttribute('rr', False, overwrite=False)
		self.setAttribute('srt', C.supportedResourceTypes, overwrite=False)
		self.setAttribute('csz', C.supportedContentSerializations, overwrite=False)
		self.setAttribute('srv', CSE.supportedReleaseVersions, overwrite=False)	# This must be a list
		self.setAttribute('poa', [ CSE.httpServer.serverAddress ], overwrite=False)		# TODO add more address schemes when available
		self.setAttribute('cst', CSE.cseType, overwrite=False)


	def activate(self, parentResource:Resource, originator:str) -> Result:
		if not (res := super().activate(parentResource, originator)).status:
			return res
		
		if not Utils.isValidCSI(self.csi):
			L.logWarn(dbg := f'Wrong format for CSEBase.csi: {self.csi}')
			return Result(status=False, dbg=dbg)

		return Result(status=True)


	def validate(self, originator:str=None, create:bool=False, dct:JSON=None, parentResource:Resource=None) -> Result:
		if not (res := super().validate(originator, create, dct, parentResource)).status:
			return res
		
		self.normalizeURIAttribute('poa')

		# Update the hcl attribute in the hosting node (similar to AE)
		nl = self['nl']
		_nl_ = self.__node__

		if nl is not None or _nl_ is not None:
			if nl != _nl_:
				if _nl_ is not None:
					if nresource := CSE.dispatcher.retrieveResource(_nl_).resource:
						nresource['hcl'] = None # remove old link
						CSE.dispatcher.updateResource(nresource)
				self[Resource._node] = nl
				if nresource := CSE.dispatcher.retrieveResource(nl).resource:
					nresource['hcl'] = self['ri']
					CSE.dispatcher.updateResource(nresource)
			self[Resource._node] = nl

		return Result(status=True)


	def willBeRetrieved(self, originator:str) -> Result:
		if not (res := super().willBeRetrieved(originator)).status:
			return res

		# add the current time to this resource instance
		self['ctm'] = DateUtils.getResourceDate()
		return Result(status=True)


		