
from abc import ABC, abstractmethod
from typing import Any, Callable
from Types import ResourceTypes as T, Result
from resources.Resource import Resource

class IBindingLayer(ABC):

	@abstractmethod
	def run(self): # This does NOT return
		pass

	@abstractmethod
	def sendRetrieveRequest(self, url:str, originator:str) -> Result:
		pass

	@abstractmethod
	def sendCreateRequest(self, url:str, originator:str, ty:T=None, data:Any=None, headers:dict=None) -> Result:
		pass

	@abstractmethod
	def sendUpdateRequest(self, url:str, originator:str, data:Any) -> Result:
		pass

	@abstractmethod
	def sendDeleteRequest(self, url:str, originator:str) -> Result:
		pass

	@abstractmethod
	def sendRequest(self, method:Callable , url:str, originator:str, ty:T=None, data:Any=None, ct:str='application/json', headers:dict=None) -> Result:
		pass

	@abstractmethod
	def shutdown(self) -> bool:
		pass

        # End of interface IBindingLayer

# End of file
