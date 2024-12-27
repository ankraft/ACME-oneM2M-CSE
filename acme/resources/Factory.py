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

from __future__ import annotations
from typing import Optional, cast

from ..etc.Types import ResourceTypes, addResourceFactoryCallback, FactoryCallableT
from ..etc.ResponseStatusCodes import BAD_REQUEST
from ..etc.Types import JSON
from ..etc.ACMEUtils import pureResource
from ..etc.Constants import Constants
from ..runtime.Logging import Logging as L


from ..resources.Resource import Resource
from ..resources.ACP import ACP
from ..resources.ACPAnnc import ACPAnnc
from ..resources.ACTR import ACTR
from ..resources.ACTRAnnc import ACTRAnnc
from ..resources.AE import AE
from ..resources.AEAnnc import AEAnnc
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
from ..resources.DEPR import DEPR
from ..resources.DEPRAnnc import DEPRAnnc
from ..resources.FCI import FCI
# TODO from ..resources.FCIAnnc import FCIAnnc
from ..resources.FCNT import FCNT
from ..resources.FCNTAnnc import FCNTAnnc
from ..resources.FCNT_LA import FCNT_LA
from ..resources.FCNT_OL import FCNT_OL
from ..resources.GRP import GRP
from ..resources.GRPAnnc import GRPAnnc
from ..resources.GRP_FOPT import GRP_FOPT
from ..resources.LCP import LCP
from ..resources.LCPAnnc import LCPAnnc
from ..resources.NOD import NOD
from ..resources.NODAnnc import NODAnnc
from ..resources.PCH import PCH
from ..resources.PCH_PCU import PCH_PCU
from ..resources.PRMR import PRMR
# TODO from ..resources.PRMRAnnc import PRMRAnnc
from ..resources.PRP import PRP
#from ..resources.PRPAnnc import PRPAnnc
from ..resources.REQ import REQ
from ..resources.SUB import SUB
from ..resources.SCH import SCH
from ..resources.SCHAnnc import SCHAnnc
from ..resources.SMD import SMD
from ..resources.SMDAnnc import SMDAnnc
from ..resources.STTE import STTE
# TODO from ..resources.STTEAnnc import STTEAnnc
from ..resources.TS import TS
from ..resources.TSAnnc import TSAnnc
from ..resources.TS_LA import TS_LA
from ..resources.TS_OL import TS_OL
from ..resources.TSB import TSB
from ..resources.TSBAnnc import TSBAnnc
from ..resources.TSI import TSI
from ..resources.TSIAnnc import TSIAnnc

from ..resources.Unknown import Unknown

from ..resources.ANDI import ANDI
from ..resources.ANDIAnnc import ANDIAnnc
from ..resources.ANI import ANI
from ..resources.ANIAnnc import ANIAnnc
from ..resources.BAT import BAT
from ..resources.BATAnnc import BATAnnc
from ..resources.DATC import DATC
from ..resources.DATCAnnc import DATCAnnc
from ..resources.DVC import DVC
from ..resources.DVCAnnc import DVCAnnc
from ..resources.DVI import DVI
from ..resources.DVIAnnc import DVIAnnc
from ..resources.EVL import EVL
from ..resources.EVLAnnc import EVLAnnc
from ..resources.FWR import FWR
from ..resources.FWRAnnc import FWRAnnc
from ..resources.MEM import MEM
from ..resources.MEMAnnc import MEMAnnc
from ..resources.NYCFC import NYCFC
from ..resources.NYCFCAnnc import NYCFCAnnc
from ..resources.RBO import RBO
from ..resources.RBOAnnc import RBOAnnc
from ..resources.SWR import SWR
from ..resources.SWRAnnc import SWRAnnc
from ..resources.WIFIC import WIFIC
from ..resources.WIFICAnnc import WIFICAnnc
from ..resources.CRDS import CRDS
from ..resources.CRDSAnnc import CRDSAnnc
from ..resources.SIM import SIM
from ..resources.SIMAnnc import SIMAnnc
from ..resources.MNWK import MNWK
from ..resources.MNWKAnnc import MNWKAnnc


# Adding factory callbacks to regular resource type details
addResourceFactoryCallback(ResourceTypes.ACP, 			ACP,			lambda dct, typeShortname : ACP(dct))
addResourceFactoryCallback(ResourceTypes.ACPAnnc,		ACPAnnc,		lambda dct, typeShortname : ACPAnnc(dct))
addResourceFactoryCallback(ResourceTypes.ACTR, 			ACTR,			lambda dct, typeShortname : ACTR(dct)) 
addResourceFactoryCallback(ResourceTypes.ACTRAnnc, 		ACTRAnnc,		lambda dct, typeShortname : ACTRAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.AE, 			AE,				lambda dct, typeShortname : AE(dct)) 
addResourceFactoryCallback(ResourceTypes.AEAnnc,		AEAnnc,			lambda dct, typeShortname : AEAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.CIN, 			CIN,			lambda dct, typeShortname : CIN(dct)) 
addResourceFactoryCallback(ResourceTypes.CINAnnc, 		CINAnnc,		lambda dct, typeShortname : CINAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.CNT,	 		CNT,			lambda dct, typeShortname : CNT(dct)) 
addResourceFactoryCallback(ResourceTypes.CNTAnnc, 		CNTAnnc,		lambda dct, typeShortname : CNTAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.CNT_LA,		CNT_LA,			lambda dct, typeShortname : CNT_LA(dct)) 
addResourceFactoryCallback(ResourceTypes.CNT_OL,		CNT_OL,			lambda dct, typeShortname : CNT_OL(dct)) 
addResourceFactoryCallback(ResourceTypes.CSEBase,		CSEBase,		lambda dct, typeShortname : CSEBase(dct)) 
addResourceFactoryCallback(ResourceTypes.CSEBaseAnnc,	CSEBaseAnnc,	lambda dct, typeShortname : CSEBaseAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.CRS,			CRS,			lambda dct, typeShortname : CRS(dct)) 
addResourceFactoryCallback(ResourceTypes.CSR,			CSR,			lambda dct, typeShortname : CSR(dct)) 
addResourceFactoryCallback(ResourceTypes.CSRAnnc,		CSRAnnc,		lambda dct, typeShortname : CSRAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.DEPR,			DEPR,			lambda dct, typeShortname : DEPR(dct)) 
addResourceFactoryCallback(ResourceTypes.DEPRAnnc,		DEPRAnnc,		lambda dct, typeShortname : DEPRAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.FCI,			FCI,			lambda dct, typeShortname : FCI(dct, fcntType = typeShortname)) 
addResourceFactoryCallback(ResourceTypes.FCNT,			FCNT,			lambda dct, typeShortname : FCNT(dct, fcntType = typeShortname)) 
addResourceFactoryCallback(ResourceTypes.FCNTAnnc,		FCNTAnnc,		lambda dct, typeShortname : FCNTAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.FCNT_LA,		FCNT_LA,		lambda dct, typeShortname : FCNT_LA(dct)) 
addResourceFactoryCallback(ResourceTypes.FCNT_OL,		FCNT_OL,		lambda dct, typeShortname : FCNT_OL(dct)) 
addResourceFactoryCallback(ResourceTypes.GRP,			GRP,			lambda dct, typeShortname : GRP(dct)) 
addResourceFactoryCallback(ResourceTypes.GRPAnnc,		GRPAnnc,		lambda dct, typeShortname : GRPAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.GRP_FOPT,		GRP_FOPT,		lambda dct, typeShortname : GRP_FOPT(dct)) 
addResourceFactoryCallback(ResourceTypes.LCP,			LCP,			lambda dct, typeShortname : LCP(dct))
addResourceFactoryCallback(ResourceTypes.LCPAnnc,		LCPAnnc,		lambda dct, typeShortname : LCPAnnc(dct))
addResourceFactoryCallback(ResourceTypes.NOD,			NOD,			lambda dct, typeShortname : NOD(dct)) 
addResourceFactoryCallback(ResourceTypes.NODAnnc,		NODAnnc,		lambda dct, typeShortname : NODAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.PCH,			PCH,			lambda dct, typeShortname : PCH(dct)) 
addResourceFactoryCallback(ResourceTypes.PCH_PCU,		PCH_PCU,		lambda dct, typeShortname : PCH_PCU(dct)) 
addResourceFactoryCallback(ResourceTypes.PRMR,			PRMR,			lambda dct, typeShortname : PRMR(dct))
# TODO addResourceFactoryCallback(ResourceTypes.PRMRAnnc,	PRMRAnnc,		lambda dct, typeShortname : PRMRAnnc(dct))
addResourceFactoryCallback(ResourceTypes.PRP,			PRP,			lambda dct, typeShortname : PRP(dct))
# TODO addResourceFactoryCallback(ResourceTypes.PRPAnnc,	PRPAnnc,		lambda dct, typeShortname : PRPAnnc(dct))
addResourceFactoryCallback(ResourceTypes.REQ,			REQ,			lambda dct, typeShortname : REQ(dct)) 
addResourceFactoryCallback(ResourceTypes.SCH,			SCH,			lambda dct, typeShortname : SCH(dct)) 
addResourceFactoryCallback(ResourceTypes.SCHAnnc,		SCHAnnc,		lambda dct, typeShortname : SCHAnnc(dct))
addResourceFactoryCallback(ResourceTypes.SMD,			SMD,			lambda dct, typeShortname : SMD(dct)) 
addResourceFactoryCallback(ResourceTypes.SMDAnnc,		SMDAnnc,		lambda dct, typeShortname : SMDAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.STTE,			STTE,			lambda dct, typeShortname : STTE(dct))
# TODO addResourceFactoryCallback(ResourceTypes.STTEAnnc,	STTEAnnc,		lambda dct, typeShortname : STTEAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.SUB,			SUB,			lambda dct, typeShortname : SUB(dct)) 
addResourceFactoryCallback(ResourceTypes.TS,			TS,				lambda dct, typeShortname : TS(dct)) 
addResourceFactoryCallback(ResourceTypes.TSAnnc,		TSAnnc,			lambda dct, typeShortname : TSAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.TS_LA,			TS_LA,			lambda dct, typeShortname : TS_LA(dct)) 
addResourceFactoryCallback(ResourceTypes.TS_OL,			TS_OL,			lambda dct, typeShortname : TS_OL(dct)) 
addResourceFactoryCallback(ResourceTypes.TSB,			TSB,			lambda dct, typeShortname : TSB(dct)) 
addResourceFactoryCallback(ResourceTypes.TSBAnnc,		TSBAnnc,		lambda dct, typeShortname : TSBAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.TSI,			TSI,			lambda dct, typeShortname : TSI(dct)) 
addResourceFactoryCallback(ResourceTypes.TSIAnnc,		TSIAnnc,		lambda dct, typeShortname : TSIAnnc(dct)) 

# Add for MgmtObj specializations
addResourceFactoryCallback(ResourceTypes.ANDI,			ANDI,			lambda dct, typeShortname : ANDI(dct)) 
addResourceFactoryCallback(ResourceTypes.ANDIAnnc,		ANDIAnnc,		lambda dct, typeShortname : ANDIAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.ANI,			ANI,			lambda dct, typeShortname : ANI(dct)) 
addResourceFactoryCallback(ResourceTypes.ANIAnnc,		ANIAnnc,		lambda dct, typeShortname : ANIAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.BAT,			BAT,			lambda dct, typeShortname : BAT(dct)) 
addResourceFactoryCallback(ResourceTypes.BATAnnc,		BATAnnc,		lambda dct, typeShortname : BATAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.DATC,			DATC,			lambda dct, typeShortname : DATC(dct)) 
addResourceFactoryCallback(ResourceTypes.DATCAnnc,		DATCAnnc,		lambda dct, typeShortname : DATCAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.DVC,			DVC,			lambda dct, typeShortname : DVC(dct)) 
addResourceFactoryCallback(ResourceTypes.DVCAnnc,		DVCAnnc,		lambda dct, typeShortname : DVCAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.DVI,			DVI,			lambda dct, typeShortname : DVI(dct)) 
addResourceFactoryCallback(ResourceTypes.DVIAnnc,		DVIAnnc,		lambda dct, typeShortname : DVIAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.EVL,			EVL,			lambda dct, typeShortname : EVL(dct)) 
addResourceFactoryCallback(ResourceTypes.EVLAnnc,		EVLAnnc,		lambda dct, typeShortname : EVLAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.FWR,			FWR,			lambda dct, typeShortname : FWR(dct)) 
addResourceFactoryCallback(ResourceTypes.FWRAnnc,		FWRAnnc,		lambda dct, typeShortname : FWRAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.MEM,			MEM,			lambda dct, typeShortname : MEM(dct)) 
addResourceFactoryCallback(ResourceTypes.MEMAnnc,		MEMAnnc,		lambda dct, typeShortname : MEMAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.NYCFC,			NYCFC,			lambda dct, typeShortname : NYCFC(dct)) 
addResourceFactoryCallback(ResourceTypes.NYCFCAnnc,		NYCFCAnnc,		lambda dct, typeShortname : NYCFCAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.RBO,			RBO,			lambda dct, typeShortname : RBO(dct)) 
addResourceFactoryCallback(ResourceTypes.RBOAnnc,		RBOAnnc,		lambda dct, typeShortname : RBOAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.SWR,			SWR,			lambda dct, typeShortname : SWR(dct)) 
addResourceFactoryCallback(ResourceTypes.SWRAnnc,		SWRAnnc,		lambda dct, typeShortname : SWRAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.WIFIC,			WIFIC,			lambda dct, typeShortname : WIFIC(dct)) 
addResourceFactoryCallback(ResourceTypes.WIFICAnnc,		WIFICAnnc,		lambda dct, typeShortname : WIFICAnnc(dct))
addResourceFactoryCallback(ResourceTypes.CRDS,			CRDS,			lambda dct, typeShortname : CRDS(dct))
addResourceFactoryCallback(ResourceTypes.CRDSAnnc,		CRDSAnnc,		lambda dct, typeShortname : CRDSAnnc(dct))
addResourceFactoryCallback(ResourceTypes.SIM,			SIM,			lambda dct, typeShortname : SIM(dct))
addResourceFactoryCallback(ResourceTypes.SIMAnnc,		SIMAnnc,		lambda dct, typeShortname : SIMAnnc(dct))
addResourceFactoryCallback(ResourceTypes.MNWK,			MNWK,			lambda dct, typeShortname : MNWK(dct))
addResourceFactoryCallback(ResourceTypes.MNWKAnnc,		MNWKAnnc,		lambda dct, typeShortname : MNWKAnnc(dct))


_specResources = [ ResourceTypes.FCNT, 
				   ResourceTypes.FCNTAnnc, 
				   ResourceTypes.FCI, 
				   ResourceTypes.MGMTOBJ, 
				   ResourceTypes.MGMTOBJAnnc ]
"""	Resources with type specifiers."""


def resourceFromDict(resDict:Optional[JSON] = {}, 
					 pi:Optional[str] = None, 
					 ty:Optional[ResourceTypes] = None, 
					 create:Optional[bool] = False, 
					 isImported:Optional[bool] = False,
					 template:Optional[bool] = False,
					 originator:Optional[str] = None) -> Resource:
	""" Create a resource from a dictionary structure.

		This function will **not** call the resource's *activate()* method, therefore some attributes
		may need to be set separately.

		Args:
			resDict: Dictionary with the resource definition.
			pi: The parent's resource ID.
			ty: The resource type of the resource that shall be created.
			create: The resource will be newly created.
			isImported: True when the resource is imported, or created by the `ScriptManager`. In this case some checks may not be performed.
			template: True when the resource is used as a template. In this case some checks may not be performed.

		Return:
			`Result` object with the *resource* attribute set to the created resource object.

	"""
	resDict, typeShortname, _attr = pureResource(resDict)	# remove optional "m2m:xxx" level
	
	# Check resouce type name (typeShortname), especially in FCT resources
	if not template and typeShortname is None and ty in [ None, ResourceTypes.FCNT, ResourceTypes.FCI ]:
		raise BAD_REQUEST(L.logWarn(f'Resource type name  has the wrong format (must be "<domain>:<name>", not "{_attr})"'))

	# Determine type
	typ = ResourceTypes(resDict['ty']) if 'ty' in resDict else ty
	if typ is None and (typ := ResourceTypes.fromTypeShortname(typeShortname)) is None:
		raise BAD_REQUEST(L.logWarn(f'Cannot determine type for creating the resource: {typeShortname}'))

	if ty is not None:
		if typ is not None and typ != ty:
			raise BAD_REQUEST(L.logWarn(f'Parameter type ({ty}) and resource type ({typ}) mismatch'))
		if typeShortname is not None and ty.typeShortname() != typeShortname and ty not in _specResources:
			raise BAD_REQUEST(L.logWarn(f'Parameter type ({ty}) and resource type specifier ({typeShortname}) mismatch'))
	
	# Check for Parent
	if not template and pi is None and typ != ResourceTypes.CSEBase and (not (pi := resDict.get('pi')) or len(pi) == 0):
		raise BAD_REQUEST(L.logWarn(f'pi missing in resource: {typeShortname}'))

	# store the import status in the original resDict
	if isImported:
		resDict[Constants.attrImported] = True	# Indicate that this is an imported resource

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
	
	if factory:
		newResource = cast(Resource, factory(resDict, typeShortname))
	else:
		newResource = Unknown(resDict, typeShortname)	# Capture-All resource

	if create:
		newResource.initialize(pi, originator)

	return newResource


