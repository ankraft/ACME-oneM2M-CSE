#
#	Factory.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Create Resources
#

"""	This Module provides a resource factory. 
"""

# TODO store the factories in this module and not in the ResourceTypeDetails, 

from __future__ import annotations
from typing import Optional, Type, Tuple, Callable, TYPE_CHECKING

if TYPE_CHECKING:
	from ..resources.Resource import Resource

from ..etc.Types import ResourceTypes, FactoryCallableT, resourceTypeDetails
from ..etc import Types
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.Types import JSON
from ..etc.JSONUtils import pureResource
from ..helpers.Singleton import Singleton
from .Logging import Logging as L

class Factory(metaclass=Singleton):
	""" Factory for creating resources. """

	resourceClassMapping:dict[ResourceTypes, Tuple[Type[Resource], Callable]] = {}
	""" Mapping of resource types to their corresponding resource classes and factory callables. 
		The factory callable is used to create an instance of the resource class from a dictionary. 
	"""

	def getResourceClassForType(self, ty:ResourceTypes) -> Optional[Type[Resource]]:
		""" Get the resource class for a given resource type. 

			Args:
				ty: The resource type.
			Returns:
				The resource class for the given resource type, or *None* if not found.
			
		"""
		tup = self.resourceClassMapping.get(ty)
		return tup[0] if tup else None


	def initResources(self) -> bool:
		""" Initialize the resource factory. """

		from ..resources.ACP import ACP
		from ..resources.ACPAnnc import ACPAnnc
		from ..resources.ACTR import ACTR
		from ..resources.ACTRAnnc import ACTRAnnc
		from ..resources.AE import AE
		from ..resources.AEAnnc import AEAnnc
		from ..resources.ALPC import ALPC
		from ..resources.ALST import ALST
		from ..resources.CIN import CIN
		from ..resources.CINAnnc import CINAnnc
		from ..resources.CNT import CNT
		from ..resources.CNTAnnc import CNTAnnc
		from ..resources.CNT_LA import CNT_LA
		from ..resources.CNT_OL import CNT_OL
		from ..resources.CSEBase import CSEBase
		from ..resources.CSEBaseAnnc import CSEBaseAnnc
		from ..resources.CRS import CRS
		from ..resources.CSR import CSR
		from ..resources.CSRAnnc import CSRAnnc
		from ..resources.DAC import DAC
		from ..resources.DEPR import DEPR
		from ..resources.DEPRAnnc import DEPRAnnc
		from ..resources.FCI import FCI
		from ..resources.FCIAnnc import FCIAnnc
		from ..resources.FCNT import FCNT
		from ..resources.FCNTAnnc import FCNTAnnc
		from ..resources.FCNT_LA import FCNT_LA
		from ..resources.FCNT_OL import FCNT_OL
		from ..resources.GRP import GRP
		from ..resources.GRPAnnc import GRPAnnc
		from ..resources.GRP_FOPT import GRP_FOPT
		from ..resources.LCP import LCP
		from ..resources.LCPAnnc import LCPAnnc
		from ..resources.MgmtObj import MgmtObj
		from ..resources.MgmtObjAnnc import MgmtObjAnnc
		from ..resources.NOD import NOD
		from ..resources.NODAnnc import NODAnnc
		from ..resources.NTP import NTP
		from ..resources.NTPR import NTPR
		from ..resources.NTSR import NTSR
		from ..resources.PCH import PCH
		from ..resources.PCH_PCU import PCH_PCU
		from ..resources.PDR import PDR
		from ..resources.PRMR import PRMR
		from ..resources.PRMRAnnc import PRMRAnnc
		from ..resources.PRP import PRP
		from ..resources.PRPAnnc import PRPAnnc
		from ..resources.REQ import REQ
		from ..resources.SUB import SUB
		from ..resources.SCH import SCH
		from ..resources.SCHAnnc import SCHAnnc
		from ..resources.SMD import SMD
		from ..resources.SMDAnnc import SMDAnnc
		from ..resources.STTE import STTE
		from ..resources.STTEAnnc import STTEAnnc
		from ..resources.TGR import TGR
		from ..resources.TS import TS
		from ..resources.TSAnnc import TSAnnc
		from ..resources.TS_LA import TS_LA
		from ..resources.TS_OL import TS_OL
		from ..resources.TSB import TSB
		from ..resources.TSBAnnc import TSBAnnc
		from ..resources.TSI import TSI
		from ..resources.TSIAnnc import TSIAnnc

		from ..resources.mgmtobjs.ANDI import ANDI
		from ..resources.mgmtobjs.ANDIAnnc import ANDIAnnc
		from ..resources.mgmtobjs.ANI import ANI
		from ..resources.mgmtobjs.ANIAnnc import ANIAnnc
		from ..resources.mgmtobjs.BAT import BAT
		from ..resources.mgmtobjs.BATAnnc import BATAnnc
		from ..resources.mgmtobjs.DATC import DATC
		from ..resources.mgmtobjs.DATCAnnc import DATCAnnc
		from ..resources.mgmtobjs.DVC import DVC
		from ..resources.mgmtobjs.DVCAnnc import DVCAnnc
		from ..resources.mgmtobjs.DVI import DVI
		from ..resources.mgmtobjs.DVIAnnc import DVIAnnc
		from ..resources.mgmtobjs.EVL import EVL
		from ..resources.mgmtobjs.EVLAnnc import EVLAnnc
		from ..resources.mgmtobjs.FWR import FWR
		from ..resources.mgmtobjs.FWRAnnc import FWRAnnc
		from ..resources.mgmtobjs.MEM import MEM
		from ..resources.mgmtobjs.MEMAnnc import MEMAnnc
		from ..resources.mgmtobjs.NYCFC import NYCFC
		from ..resources.mgmtobjs.NYCFCAnnc import NYCFCAnnc
		from ..resources.mgmtobjs.RBO import RBO
		from ..resources.mgmtobjs.RBOAnnc import RBOAnnc
		from ..resources.mgmtobjs.SWR import SWR
		from ..resources.mgmtobjs.SWRAnnc import SWRAnnc
		from ..resources.mgmtobjs.WIFIC import WIFIC
		from ..resources.mgmtobjs.WIFICAnnc import WIFICAnnc
		from ..resources.mgmtobjs.CRDS import CRDS
		from ..resources.mgmtobjs.CRDSAnnc import CRDSAnnc
		from ..resources.mgmtobjs.SIM import SIM
		from ..resources.mgmtobjs.SIMAnnc import SIMAnnc
		from ..resources.mgmtobjs.MNWK import MNWK
		from ..resources.mgmtobjs.MNWKAnnc import MNWKAnnc

		L.isDebug and L.logDebug('Initializing resource factory, resources and type mappings')

		self.resourceClassMapping = {
			# Normal resource types
			ResourceTypes.ACP 			: (ACP, 		lambda dct, tySN, create : ACP(dct, create=create)),
			ResourceTypes.ACPAnnc 		: (ACPAnnc, 	lambda dct, tySN, create : ACPAnnc(dct, create=create)),
			ResourceTypes.ACTR 			: (ACTR,		lambda dct, tySN, create : ACTR(dct, create=create)),
			ResourceTypes.ACTRAnnc		: (ACTRAnnc,	lambda dct, tySN, create : ACTRAnnc(dct, create=create)),
			ResourceTypes.AE 			: (AE,			lambda dct, tySN, create : AE(dct, create=create)),
			ResourceTypes.AEAnnc		: (AEAnnc,		lambda dct, tySN, create : AEAnnc(dct, create=create)),
			ResourceTypes.ALPC			: (ALPC,		lambda dct, tySN, create : ALPC(dct, create=create)),	
			ResourceTypes.ALST			: (ALST,		lambda dct, tySN, create : ALST(dct, create=create)),	
			ResourceTypes.CIN 			: (CIN,			lambda dct, tySN, create : CIN(dct, create=create)),
			ResourceTypes.CINAnnc 		: (CINAnnc,		lambda dct, tySN, create : CINAnnc(dct, create=create)),
			ResourceTypes.CNT 			: (CNT,			lambda dct, tySN, create : CNT(dct, create=create)),
			ResourceTypes.CNTAnnc 		: (CNTAnnc,		lambda dct, tySN, create : CNTAnnc(dct, create=create)),
			ResourceTypes.CNT_LA		: (CNT_LA,		lambda dct, tySN, create : CNT_LA(dct, create=create)),
			ResourceTypes.CNT_OL		: (CNT_OL,		lambda dct, tySN, create : CNT_OL(dct, create=create)),
			ResourceTypes.CSEBase		: (CSEBase,		lambda dct, tySN, create : CSEBase(dct, create=create)),
			ResourceTypes.CSEBaseAnnc	: (CSEBaseAnnc,	lambda dct, tySN, create : CSEBaseAnnc(dct, create=create)),
			ResourceTypes.CRS			: (CRS,			lambda dct, tySN, create : CRS(dct, create=create)),
			ResourceTypes.CSR			: (CSR,			lambda dct, tySN, create : CSR(dct, create=create)),
			ResourceTypes.CSRAnnc		: (CSRAnnc,		lambda dct, tySN, create : CSRAnnc(dct, create=create)),
			ResourceTypes.DAC			: (DAC,			lambda dct, tySN, create : DAC(dct, create=create)),
			ResourceTypes.DEPR			: (DEPR,		lambda dct, tySN, create : DEPR(dct, create=create)),
			ResourceTypes.DEPRAnnc		: (DEPRAnnc,	lambda dct, tySN, create : DEPRAnnc(dct, create=create)),
			ResourceTypes.FCI			: (FCI,			lambda dct, tySN, create : FCI(dct, typeShortname=tySN, create=create)),
			ResourceTypes.FCIAnnc		: (FCIAnnc,		lambda dct, tySN, create : FCIAnnc(dct, create=create)),
			ResourceTypes.FCNT			: (FCNT,		lambda dct, tySN, create : FCNT(dct, typeShortname=tySN, create=create)),
			ResourceTypes.FCNTAnnc		: (FCNTAnnc,	lambda dct, tySN, create : FCNTAnnc(dct, typeShortname=tySN, create=create)),
			ResourceTypes.FCNT_LA		: (FCNT_LA,		lambda dct, tySN, create : FCNT_LA(dct, create=create)),
			ResourceTypes.FCNT_OL		: (FCNT_OL,		lambda dct, tySN, create : FCNT_OL(dct, create=create)),
			ResourceTypes.GRP			: (GRP,			lambda dct, tySN, create : GRP(dct, create=create)),
			ResourceTypes.GRPAnnc		: (GRPAnnc,		lambda dct, tySN, create : GRPAnnc(dct, create=create)),
			ResourceTypes.GRP_FOPT		: (GRP_FOPT,	lambda dct, tySN, create : GRP_FOPT(dct, create=create)),
			ResourceTypes.LCP			: (LCP,			lambda dct, tySN, create : LCP(dct, create=create)),
			ResourceTypes.LCPAnnc		: (LCPAnnc,		lambda dct, tySN, create : LCPAnnc(dct, create=create)),
			ResourceTypes.MGMTOBJ		: (MgmtObj,		None),
			ResourceTypes.MGMTOBJAnnc	: (MgmtObjAnnc,	None),
			ResourceTypes.NOD			: (NOD,			lambda dct, tySN, create : NOD(dct, create=create)),
			ResourceTypes.NODAnnc		: (NODAnnc,		lambda dct, tySN, create : NODAnnc(dct, create=create)),
			ResourceTypes.NTP			: (NTP,			lambda dct, tySN, create : NTP(dct, create=create)),
			ResourceTypes.NTPR			: (NTPR,		lambda dct, tySN, create : NTPR(dct, create=create)),
			ResourceTypes.NTSR			: (NTSR,		lambda dct, tySN, create : NTSR(dct, create=create)),
			ResourceTypes.PCH			: (PCH,			lambda dct, tySN, create : PCH(dct, create=create)),
			ResourceTypes.PCH_PCU		: (PCH_PCU,		lambda dct, tySN, create : PCH_PCU(dct, create=create)),
			ResourceTypes.PDR			: (PDR,			lambda dct, tySN, create : PDR(dct, create=create)),
			ResourceTypes.PRMR			: (PRMR,		lambda dct, tySN, create : PRMR(dct, create=create)),
			ResourceTypes.PRMRAnnc		: (PRMRAnnc,	lambda dct, tySN, create : PRMRAnnc(dct, create=create)),
			ResourceTypes.PRP			: (PRP,			lambda dct, tySN, create : PRP(dct, create=create)),
			ResourceTypes.PRPAnnc		: (PRPAnnc,		lambda dct, tySN, create : PRPAnnc(dct, create=create)),
			ResourceTypes.REQ			: (REQ,			lambda dct, tySN, create : REQ(dct, create=create)),
			ResourceTypes.SCH			: (SCH,			lambda dct, tySN, create : SCH(dct, create=create)),
			ResourceTypes.SCHAnnc		: (SCHAnnc,		lambda dct, tySN, create : SCHAnnc(dct, create=create)),
			ResourceTypes.SMD			: (SMD,			lambda dct, tySN, create : SMD(dct, create=create)),
			ResourceTypes.SMDAnnc		: (SMDAnnc,		lambda dct, tySN, create : SMDAnnc(dct, create=create)),
			ResourceTypes.STTE			: (STTE,		lambda dct, tySN, create : STTE(dct, create=create)),
			ResourceTypes.STTEAnnc		: (STTEAnnc,	lambda dct, tySN, create : STTEAnnc(dct, create=create)),
			ResourceTypes.SUB			: (SUB,			lambda dct, tySN, create : SUB(dct, create=create)),
			ResourceTypes.TGR			: (TGR,			lambda dct, tySN, create : TGR(dct, create=create)),
			ResourceTypes.TS			: (TS,			lambda dct, tySN, create : TS(dct, create=create)),
			ResourceTypes.TSAnnc		: (TSAnnc,		lambda dct, tySN, create : TSAnnc(dct, create=create)),
			ResourceTypes.TS_LA			: (TS_LA,		lambda dct, tySN, create : TS_LA(dct, create=create)),
			ResourceTypes.TS_OL			: (TS_OL,		lambda dct, tySN, create : TS_OL(dct, create=create)),
			ResourceTypes.TSB			: (TSB,			lambda dct, tySN, create : TSB(dct, create=create)),
			ResourceTypes.TSBAnnc		: (TSBAnnc,		lambda dct, tySN, create : TSBAnnc(dct, create=create)),
			ResourceTypes.TSI			: (TSI,			lambda dct, tySN, create : TSI(dct, create=create)),
			ResourceTypes.TSIAnnc		: (TSIAnnc,		lambda dct, tySN, create : TSIAnnc(dct, create=create)),

			# Add for MgmtObj specializations
			ResourceTypes.ANDI			: (ANDI,		lambda dct, tySN, create : ANDI(dct, create=create)),
			ResourceTypes.ANDIAnnc		: (ANDIAnnc,	lambda dct, tySN, create : ANDIAnnc(dct, create=create)),
			ResourceTypes.ANI			: (ANI,			lambda dct, tySN, create : ANI(dct, create=create)),
			ResourceTypes.ANIAnnc		: (ANIAnnc,		lambda dct, tySN, create : ANIAnnc(dct, create=create)),
			ResourceTypes.BAT			: (BAT,			lambda dct, tySN, create : BAT(dct, create=create)),
			ResourceTypes.BATAnnc		: (BATAnnc,		lambda dct, tySN, create : BATAnnc(dct, create=create)),
			ResourceTypes.DATC			: (DATC,		lambda dct, tySN, create : DATC(dct, create=create)),
			ResourceTypes.DATCAnnc		: (DATCAnnc,	lambda dct, tySN, create : DATCAnnc(dct, create=create)),
			ResourceTypes.DVC			: (DVC,			lambda dct, tySN, create : DVC(dct, create=create)),
			ResourceTypes.DVCAnnc		: (DVCAnnc,		lambda dct, tySN, create : DVCAnnc(dct, create=create)),
			ResourceTypes.DVI			: (DVI,			lambda dct, tySN, create : DVI(dct, create=create)),
			ResourceTypes.DVIAnnc		: (DVIAnnc,		lambda dct, tySN, create : DVIAnnc(dct, create=create)),
			ResourceTypes.EVL			: (EVL,			lambda dct, tySN, create : EVL(dct, create=create)),
			ResourceTypes.EVLAnnc		: (EVLAnnc,		lambda dct, tySN, create : EVLAnnc(dct, create=create)),
			ResourceTypes.FWR			: (FWR,			lambda dct, tySN, create : FWR(dct, create=create)),
			ResourceTypes.FWRAnnc		: (FWRAnnc,		lambda dct, tySN, create : FWRAnnc(dct, create=create)),
			ResourceTypes.MEM			: (MEM,			lambda dct, tySN, create : MEM(dct, create=create)),
			ResourceTypes.MEMAnnc		: (MEMAnnc,		lambda dct, tySN, create : MEMAnnc(dct, create=create)),
			ResourceTypes.NYCFC			: (NYCFC,		lambda dct, tySN, create : NYCFC(dct, create=create)),
			ResourceTypes.NYCFCAnnc		: (NYCFCAnnc,	lambda dct, tySN, create : NYCFCAnnc(dct, create=create)),
			ResourceTypes.RBO			: (RBO,			lambda dct, tySN, create : RBO(dct, create=create)),
			ResourceTypes.RBOAnnc		: (RBOAnnc,		lambda dct, tySN, create : RBOAnnc(dct, create=create)),
			ResourceTypes.SWR			: (SWR,			lambda dct, tySN, create : SWR(dct, create=create)),
			ResourceTypes.SWRAnnc		: (SWRAnnc,		lambda dct, tySN, create : SWRAnnc(dct, create=create)),
			ResourceTypes.WIFIC			: (WIFIC,		lambda dct, tySN, create : WIFIC(dct, create=create)),
			ResourceTypes.WIFICAnnc		: (WIFICAnnc,	lambda dct, tySN, create : WIFICAnnc(dct, create=create)),
			ResourceTypes.CRDS			: (CRDS,		lambda dct, tySN, create : CRDS(dct, create=create)),
			ResourceTypes.CRDSAnnc		: (CRDSAnnc,	lambda dct, tySN, create : CRDSAnnc(dct, create=create)),
			ResourceTypes.SIM			: (SIM,			lambda dct, tySN, create : SIM(dct, create=create)),
			ResourceTypes.SIMAnnc		: (SIMAnnc,		lambda dct, tySN, create : SIMAnnc(dct, create=create)),
			ResourceTypes.MNWK			: (MNWK,		lambda dct, tySN, create : MNWK(dct, create=create)),
			ResourceTypes.MNWKAnnc		: (MNWKAnnc,	lambda dct, tySN, create : MNWKAnnc(dct, create=create)),
		}

		# Assign attributes and allowed child resource types to the resource classes based on the resource type
		#  definitions in Types.resourceTypeDetails
		for ty, desc in resourceTypeDetails.items():

			# Get the resource class for the resource type.
			if ty in (ResourceTypes.MIXED,
					ResourceTypes.ALL, 
					ResourceTypes.REQRESP, 
					ResourceTypes.COMPLEX,
					ResourceTypes.REQUEST, 
					ResourceTypes.RESPONSE,
					ResourceTypes.NOTIFICATION,
					ResourceTypes.UNKNOWN):
				continue	# skip special types
			resourceClass = self.getResourceClassForType(ty)
			if resourceClass is None:
				L.logWarn(f'No resource class found for resource type: {ty}. Skipping resource type initialization.')
				continue


			# Set some attributes dependencies in the resource class based on the resource type definition. 
			# Only set them if they are not already set (ie. None) to allow for overrides in the resource class itself.

			setattr(resourceClass, 'resourceType', desc.type)	# type:ignore[attr-defined]
			setattr(resourceClass, 'typeShortname', desc.typeName)	# type:ignore[attr-defined]
			setattr(resourceClass, 'inheritACP', desc.inheritACP)	# type:ignore[attr-defined]
			if desc.virtualResourceName:
				setattr(resourceClass, 'resourceName', desc.virtualResourceName)	# type:ignore[attr-defined]
			
			if desc.isMgmtSpecialization:
				setattr(resourceClass, 'mgmtType', desc.mgmtType)	# type:ignore[attr-defined]


			# Assign attributes to the resource class
			if desc.attributes is not None:
				attributes = desc.attributes
				if not isinstance(attributes, list):
					L.logErr(f'Wrong attributes definition for resource type: {ty}. Must be a list.')
					return False 
				#  Create a dict with the attribute names as keys and None (ie. policies will be added later) as values, and assign it to the resource class
				setattr(resourceClass, '_attributes', { attr: None for attr in attributes })	# type:ignore[attr-defined]
			
			# Assign allowed child resource types to the resource class
			# if hasattr(resourceClass, '_allowedChildResourceTypes') and resourceClass._allowedChildResourceTypes is None:
			# if not hasattr(resourceClass, '_allowedChildResourceTypes'):
			if desc.childResourceTypes is not None: 
				childResourceTypes = desc.childResourceTypes if desc.childResourceTypes is not None else []
				if not isinstance(childResourceTypes, list):
					L.logErr(f'Wrong child resource types definition for resource type: {ty}. Must be a list.')
					return False
				setattr(resourceClass, '_allowedChildResourceTypes', childResourceTypes)	# type:ignore[attr-defined]

		#
		#	Initialize the various resource type mappings 
		#

		# Map resource types to their announced types
		Types._resourceTypesAnnouncedMappings = { 
			t : d.announcedType
			for t, d in resourceTypeDetails.items()
			if d.announcedType 
		}

		# Map announced types to their resource types
		Types._resourceTypesAnnouncedReverseMappings = {
			d.announcedType : t
			for t, d in resourceTypeDetails.items()
			if d.announcedType 
		}

		# A list of ALL resource types that are announced resources 
		Types._resourceTypesAnnouncedSetFull = [
			t
			for t, d in resourceTypeDetails.items()
			if d.isAnnouncedResource 
		]

		# A sorted list of resource types that are announced resources, 
		# but exclude management specialization resources and CSEBase
		Types._resourceTypesAnnouncedResourceTypes = [
			d.announcedType
			for t, d in resourceTypeDetails.items()
			if d.announcedType and not d.isMgmtSpecialization and t != ResourceTypes.CSEBase
		]
		Types._resourceTypesAnnouncedResourceTypes.sort()

		# A sorted list of resource types that are supported resources,
		# but exclude management specialization resources, virtual resources, internal types and CSEBaseAnnc 
		Types._resourceTypesSupportedResourceTypes = [
			t
			for t, d in resourceTypeDetails.items()
			if not d.isMgmtSpecialization and not d.virtualResourceName and not d.isInternalType and t != ResourceTypes.CSEBaseAnnc
		]
		Types._resourceTypesSupportedResourceTypes.sort()	

		# A list of ALL resource types that are virtual resources
		Types._resourceTypesVirtualResourcesSet = [
			t
			for t, d in resourceTypeDetails.items()
			if d.virtualResourceName 
		]

		# A list of instance resource types
		Types._resourceTypesInstanceResourcesSet = [ 
			t
			for t, d in resourceTypeDetails.items()
			if d.isInstanceResource 
		]

		# A list of container resource types	
		Types._resourceTypesContainerResourcesSet = [ 
			t
			for t, d in resourceTypeDetails.items()
			if d.isContainer 
		]
		
		# A unique list of virtual resource names
		Types._resourceTypesVirtualResourcesNames = [
			d.virtualResourceName
			for d in resourceTypeDetails.values()
			if d.virtualResourceName 
		]
		Types._resourceTypesVirtualResourcesNames = list(set(Types._resourceTypesVirtualResourcesNames))	# unique names

		# A mapping of resource types to their type shortnames
		Types._resourceTypesNames = {
			t : d.typeName
			for t, d in resourceTypeDetails.items()
			if not d.isInternalType
		}

		# A mapping of resource type shortnames to their resource types
		Types._resourceNamesTypes = { d.typeName : t
			for t, d in resourceTypeDetails.items()
			if not d.isInternalType
		}

		# A list of resource types that can be created by a request
		Types._resourceTypesIsRequestCreatable = [
			t
			for t, d in resourceTypeDetails.items()
			if d.isRequestCreatable
		]

		# A list of resource types that can be updated by a request
		Types._resourceTypesIsRequestUpdatable = [
			t
			for t, d in resourceTypeDetails.items()
			if d.isRequestUpdatable
		]

		# A list of resource types that can be deleted by a request
		Types._resourceTypesIsRequestDeletable = [
			t
			for t, d in resourceTypeDetails.items()
			if d.isRequestDeletable
		]

		# A list of resource types that are notification entities
		Types._resourceTypesIsNotificationEntity = [ 
			t
			for t, d in resourceTypeDetails.items()
			if d.isNotificationEntity
		]

		# A list of resource types that either latest or oldest resources
		Types._resourceTypesLatestOldest = [
			t
			for t, d in resourceTypeDetails.items()
			if d.typeName in [ 'm2m:la', 'm2m:ol' ]
		]

		# A list of resource types that are base for specialization resources
		Types._resourceTypesSpecializationBase = [
			t
			for t, d in resourceTypeDetails.items()
			if d.isSpecializationBaseResource
		]

		#
		#	Add specific resource factory callbacks to each resource type.
		#

		for ty, tup in self.resourceClassMapping.items():
			if ty not in resourceTypeDetails:
				raise RuntimeError(f'Unknown resource type: {ty}')
			if not (clazz := self.getResourceClassForType(ty)):
				raise RuntimeError('undefined class')
			typeDetails = resourceTypeDetails[ty]
			typeDetails.clazz = clazz
			typeDetails.factory = tup[1] # 1 = factory callback in the tuple

		return True


	def resourceFromDict(self,
					  	resDict: Optional[JSON]={}, 
						pi: Optional[str]=None, 
						ty: Optional[ResourceTypes]=None, 
						create: Optional[bool]=False, 
						template: Optional[bool]=False,
						trusted: bool=True) -> Resource:
		""" Create a resource from a dictionary structure.

			This function will **not** call the resource's *activate()* method, therefore some attributes
			may need to be set separately.

			Args:
				resDict: Dictionary with the resource definition.
				pi: The parent's resource ID.
				ty: The resource type of the resource that shall be created.
				create: The resource will be newly created.
				template: True when the resource is used as a template. In this case some checks may not be performed.
				trusted: True when the resource is created from a trusted source, such as an internal process, or was already validated.

			Return:
				`Result` object with the *resource* attribute set to the created resource object.

		"""
		resDict, typeShortname, _attr = pureResource(resDict)	# remove optional "m2m:xxx" level
		
		if not trusted:
			# Check resouce type name (typeShortname), especially in FCT resources
			if not template and typeShortname is None and ty in [ None, ResourceTypes.FCNT, ResourceTypes.FCI ]:
				raise BAD_REQUEST(L.logWarn(f'Resource type name has the wrong format (must be "<domain>:<name>", not "{_attr}" for resource type {ty})'))

		# Determine type
		typ = ResourceTypes(resDict['ty']) if 'ty' in resDict else ty
		if typ is None and (typ := ResourceTypes.fromTypeShortname(typeShortname)) is None:
			raise BAD_REQUEST(L.logWarn(f'Cannot determine type for creating the resource: {typeShortname}'))

		if ty is not None:
			if typ is not None and typ != ty:
				raise BAD_REQUEST(L.logWarn(f'Parameter type ({ty}) and resource type ({typ}) mismatch'))
			if typeShortname is not None and ty.typeShortname() != typeShortname and ty not in Types._resourceTypesSpecializationBase:
				raise BAD_REQUEST(L.logWarn(f'Parameter type ({ty}) and resource type specifier ({typeShortname}) mismatch'))
		
		# Check for Parent
		if not trusted:
			if not template and pi is None and typ != ResourceTypes.CSEBase and (not (pi := resDict.get('pi')) or len(pi) == 0):
				raise BAD_REQUEST(L.logWarn(f'pi missing in resource: {typeShortname}'))

		# Determine a factory and call it
		factory:FactoryCallableT = None

		match typ:
			case ResourceTypes.MGMTOBJ:
				# mgd = resDict['mgd'] if 'mgd' in resDict else None		# Identify mdg in <mgmtObj>
				factory = ResourceTypes(resDict['mgd']).resourceFactory()
			case ResourceTypes.MGMTOBJAnnc:
				# mgd = resDict['mgd'] if 'mgd' in resDict else None		# Identify mdg in <mgmtObj>
				factory = ResourceTypes(resDict['mgd']).announced().resourceFactory()
			case ResourceTypes.FCNT | ResourceTypes.FCNTAnnc:
				if template:
					typeShortname = 'NS:TYPE'	# Set a default type for FCNT resources
				factory = typ.resourceFactory()
			case _:
				factory = typ.resourceFactory()
		
		# !!!
		# In the following we don't want to use "Resource" as type cast, because to avoid
		# circular imports. Therefore we ignore the type checks here.
		# The result of the factory call will always be a Resource.

		newResource = factory(resDict, typeShortname, create)

		if create:
			#This is not the activation of the resource. That must done separately
			newResource.initialize(pi)	# type: ignore[attr-defined] 
			# L.inspect(newResource)

		return newResource	# type: ignore[return-value]

