#
#	CSEBase.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	ResourceType: CSEBase
#

from Constants import Constants as C
from Types import ResourceTypes as T
from Configuration import Configuration
from Validator import constructPolicy
from .Resource import *


# Attribute policies for this resource are constructed during startup of the CSE
attributePolicies = constructPolicy([ 
	'rn', 'ty', 'ri', 'pi',  'ct', 'lt', 'lbl', 'loc',
	'acpi', 'poa', 'nl', 'daci', 'esi', 'srv', 'cst', 'csi', 'csz'
])

class CSEBase(Resource):

	def __init__(self, jsn:dict=None, create:bool=False) -> None:
		super().__init__(T.CSEBase, jsn, '', create=create, attributePolicies=attributePolicies)

		if self.json is not None:
			self.setAttribute('ri', 'cseid', overwrite=False)
			self.setAttribute('rn', 'cse', overwrite=False)
			self.setAttribute('csi', 'cse', overwrite=False)

			self.setAttribute('rr', False, overwrite=False)
			self.setAttribute('srt', C.supportedResourceTypes, overwrite=False)
			self.setAttribute('csz', C.supportedContentSerializations, overwrite=False)
			self.setAttribute('srv', C.supportedReleaseVersions, overwrite=False)
			self.setAttribute('poa', [ Configuration.get('http.address') ], overwrite=False)
			self.setAttribute('cst', Configuration.get('cse.type'), overwrite=False)


	# Enable check for allowed sub-resources
	def canHaveChild(self, resource:Resource) -> bool:
		return super()._canHaveChild(resource,	
									 [ T.ACP,
									   T.AE,
									   T.CSR, 
									   T.CNT,
									   T.FCNT,
									   T.GRP,
									   T.NOD,
									   T.REQ,
									   T.SUB
									 ])


	def validate(self, originator:str=None, create:bool=False) -> Result:
		if not (res := super().validate(originator, create)).status:
			return res
		
		self.normalizeURIAttribute('poa')

		# Update the hcl attribute in the hosting node (similar to AE)
		nl = self['nl']
		_nl_ = self.__node__

		if nl is not None or _nl_ is not None:
			if nl != _nl_:
				if _nl_ is not None:
					nresource = CSE.dispatcher.retrieveResource(_nl_).resource
					if nresource is not None:
						nresource['hcl'] = None # remove old link
						CSE.dispatcher.updateResource(nresource)
				self[Resource._node] = nl
				nresource = CSE.dispatcher.retrieveResource(nl)
				if nresource is not None:
					nresource['hcl'] = self['ri']
					CSE.dispatcher.updateResource(nresource)
			self[Resource._node] = nl

		return Result(status=True)
