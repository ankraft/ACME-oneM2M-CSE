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
addResourceFactoryCallback(ResourceTypes.ACP, 			ACP,			lambda dct, typeShortname, pi, create : ACP(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.ACPAnnc,		ACPAnnc,		lambda dct, typeShortname, pi, create : ACPAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.ACTR, 			ACTR,			lambda dct, typeShortname, pi, create : ACTR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.ACTRAnnc, 		ACTRAnnc,		lambda dct, typeShortname, pi, create : ACTRAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.AE, 			AE,				lambda dct, typeShortname, pi, create : AE(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.AEAnnc,		AEAnnc,			lambda dct, typeShortname, pi, create : AEAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CIN, 			CIN,			lambda dct, typeShortname, pi, create : CIN(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CINAnnc, 		CINAnnc,		lambda dct, typeShortname, pi, create : CINAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNT,	 		CNT,			lambda dct, typeShortname, pi, create : CNT(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNTAnnc, 		CNTAnnc,		lambda dct, typeShortname, pi, create : CNTAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNT_LA,		CNT_LA,			lambda dct, typeShortname, pi, create : CNT_LA(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNT_OL,		CNT_OL,			lambda dct, typeShortname, pi, create : CNT_OL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSEBase,		CSEBase,		lambda dct, typeShortname, pi, create : CSEBase(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSEBaseAnnc,	CSEBaseAnnc,	lambda dct, typeShortname, pi, create : CSEBaseAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CRS,			CRS,			lambda dct, typeShortname, pi, create : CRS(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSR,			CSR,			lambda dct, typeShortname, pi, create : CSR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSRAnnc,		CSRAnnc,		lambda dct, typeShortname, pi, create : CSRAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DEPR,			DEPR,			lambda dct, typeShortname, pi, create : DEPR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DEPRAnnc,		DEPRAnnc,		lambda dct, typeShortname, pi, create : DEPRAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCI,			FCI,			lambda dct, typeShortname, pi, create : FCI(dct, pi = pi, fcntType = typeShortname, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCNT,			FCNT,			lambda dct, typeShortname, pi, create : FCNT(dct, pi = pi, fcntType = typeShortname, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCNTAnnc,		FCNTAnnc,		lambda dct, typeShortname, pi, create : FCNTAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCNT_LA,		FCNT_LA,		lambda dct, typeShortname, pi, create : FCNT_LA(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCNT_OL,		FCNT_OL,		lambda dct, typeShortname, pi, create : FCNT_OL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.GRP,			GRP,			lambda dct, typeShortname, pi, create : GRP(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.GRPAnnc,		GRPAnnc,		lambda dct, typeShortname, pi, create : GRPAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.GRP_FOPT,		GRP_FOPT,		lambda dct, typeShortname, pi, create : GRP_FOPT(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.LCP,			LCP,			lambda dct, typeShortname, pi, create : LCP(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.LCPAnnc,		LCPAnnc,		lambda dct, typeShortname, pi, create : LCPAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.NOD,			NOD,			lambda dct, typeShortname, pi, create : NOD(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.NODAnnc,		NODAnnc,		lambda dct, typeShortname, pi, create : NODAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.PCH,			PCH,			lambda dct, typeShortname, pi, create : PCH(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.PCH_PCU,		PCH_PCU,		lambda dct, typeShortname, pi, create : PCH_PCU(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.PRMR,			PRMR,			lambda dct, typeShortname, pi, create : PRMR(dct, pi = pi, create = create))
# TODO addResourceFactoryCallback(ResourceTypes.PRMRAnnc,	PRMRAnnc,		lambda dct, typeShortname, pi, create : PRMRAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.PRP,			PRP,			lambda dct, typeShortname, pi, create : PRP(dct, pi = pi, create = create))
# TODO addResourceFactoryCallback(ResourceTypes.PRPAnnc,	PRPAnnc,		lambda dct, typeShortname, pi, create : PRPAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.REQ,			REQ,			lambda dct, typeShortname, pi, create : REQ(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.SCH,			SCH,			lambda dct, typeShortname, pi, create : SCH(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.SCHAnnc,		SCHAnnc,		lambda dct, typeShortname, pi, create : SCHAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.SMD,			SMD,			lambda dct, typeShortname, pi, create : SMD(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.SMDAnnc,		SMDAnnc,		lambda dct, typeShortname, pi, create : SMDAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.STTE,			STTE,			lambda dct, typeShortname, pi, create : STTE(dct, pi = pi, create = create))
# TODO addResourceFactoryCallback(ResourceTypes.STTEAnnc,	STTEAnnc,		lambda dct, typeShortname, pi, create : STTEAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.SUB,			SUB,			lambda dct, typeShortname, pi, create : SUB(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TS,			TS,				lambda dct, typeShortname, pi, create : TS(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TSAnnc,		TSAnnc,			lambda dct, typeShortname, pi, create : TSAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TS_LA,			TS_LA,			lambda dct, typeShortname, pi, create : TS_LA(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TS_OL,			TS_OL,			lambda dct, typeShortname, pi, create : TS_OL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TSB,			TSB,			lambda dct, typeShortname, pi, create : TSB(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TSBAnnc,		TSBAnnc,		lambda dct, typeShortname, pi, create : TSBAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TSI,			TSI,			lambda dct, typeShortname, pi, create : TSI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.TSIAnnc,		TSIAnnc,		lambda dct, typeShortname, pi, create : TSIAnnc(dct, pi = pi, create = create)) 

# Add for MgmtObj specializations
addResourceFactoryCallback(ResourceTypes.ANDI,			ANDI,			lambda dct, typeShortname, pi, create : ANDI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.ANDIAnnc,		ANDIAnnc,		lambda dct, typeShortname, pi, create : ANDIAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.ANI,			ANI,			lambda dct, typeShortname, pi, create : ANI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.ANIAnnc,		ANIAnnc,		lambda dct, typeShortname, pi, create : ANIAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.BAT,			BAT,			lambda dct, typeShortname, pi, create : BAT(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.BATAnnc,		BATAnnc,		lambda dct, typeShortname, pi, create : BATAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DATC,			DATC,			lambda dct, typeShortname, pi, create : DATC(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DATCAnnc,		DATCAnnc,		lambda dct, typeShortname, pi, create : DATCAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DVC,			DVC,			lambda dct, typeShortname, pi, create : DVC(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DVCAnnc,		DVCAnnc,		lambda dct, typeShortname, pi, create : DVCAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DVI,			DVI,			lambda dct, typeShortname, pi, create : DVI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.DVIAnnc,		DVIAnnc,		lambda dct, typeShortname, pi, create : DVIAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.EVL,			EVL,			lambda dct, typeShortname, pi, create : EVL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.EVLAnnc,		EVLAnnc,		lambda dct, typeShortname, pi, create : EVLAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.FWR,			FWR,			lambda dct, typeShortname, pi, create : FWR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.FWRAnnc,		FWRAnnc,		lambda dct, typeShortname, pi, create : FWRAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.MEM,			MEM,			lambda dct, typeShortname, pi, create : MEM(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.MEMAnnc,		MEMAnnc,		lambda dct, typeShortname, pi, create : MEMAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.NYCFC,			NYCFC,			lambda dct, typeShortname, pi, create : NYCFC(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.NYCFCAnnc,		NYCFCAnnc,		lambda dct, typeShortname, pi, create : NYCFCAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.RBO,			RBO,			lambda dct, typeShortname, pi, create : RBO(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.RBOAnnc,		RBOAnnc,		lambda dct, typeShortname, pi, create : RBOAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.SWR,			SWR,			lambda dct, typeShortname, pi, create : SWR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.SWRAnnc,		SWRAnnc,		lambda dct, typeShortname, pi, create : SWRAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.WIFIC,			WIFIC,			lambda dct, typeShortname, pi, create : WIFIC(dct, pi = pi, create = create)) 
addResourceFactoryCallback(ResourceTypes.WIFICAnnc,		WIFICAnnc,		lambda dct, typeShortname, pi, create : WIFICAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.CRDS,			CRDS,			lambda dct, typeShortname, pi, create : CRDS(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.CRDSAnnc,		CRDSAnnc,		lambda dct, typeShortname, pi, create : CRDSAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.SIM,			SIM,			lambda dct, typeShortname, pi, create : SIM(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.SIMAnnc,		SIMAnnc,		lambda dct, typeShortname, pi, create : SIMAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.MNWK,			MNWK,			lambda dct, typeShortname, pi, create : MNWK(dct, pi = pi, create = create))
addResourceFactoryCallback(ResourceTypes.MNWKAnnc,		MNWKAnnc,		lambda dct, typeShortname, pi, create : MNWKAnnc(dct, pi = pi, create = create))


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
					 template:Optional[bool] = False) -> Resource:
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
		return cast(Resource, factory(resDict, typeShortname, pi, create))

	return  Unknown(resDict, typeShortname, pi = pi, create = create)	# Capture-All resource


