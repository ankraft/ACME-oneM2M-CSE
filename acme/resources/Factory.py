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


# Adding factory callbacks to regular resource type details
addResourceFactoryCallback(ResourceTypes.ACP, 			ACP,			lambda dct, typeShortname, create : ACP(dct, create = create))
addResourceFactoryCallback(ResourceTypes.ACPAnnc,		ACPAnnc,		lambda dct, typeShortname, create : ACPAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.ACTR, 			ACTR,			lambda dct, typeShortname, create : ACTR(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.ACTRAnnc, 		ACTRAnnc,		lambda dct, typeShortname, create : ACTRAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.AE, 			AE,				lambda dct, typeShortname, create : AE(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.AEAnnc,		AEAnnc,			lambda dct, typeShortname, create : AEAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CIN, 			CIN,			lambda dct, typeShortname, create : CIN(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CINAnnc, 		CINAnnc,		lambda dct, typeShortname, create : CINAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNT,	 		CNT,			lambda dct, typeShortname, create : CNT(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNTAnnc, 		CNTAnnc,		lambda dct, typeShortname, create : CNTAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNT_LA,		CNT_LA,			lambda dct, typeShortname, create : CNT_LA(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CNT_OL,		CNT_OL,			lambda dct, typeShortname, create : CNT_OL(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSEBase,		CSEBase,		lambda dct, typeShortname, create : CSEBase(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSEBaseAnnc,	CSEBaseAnnc,	lambda dct, typeShortname, create : CSEBaseAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CRS,			CRS,			lambda dct, typeShortname, create : CRS(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSR,			CSR,			lambda dct, typeShortname, create : CSR(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.CSRAnnc,		CSRAnnc,		lambda dct, typeShortname, create : CSRAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.DEPR,			DEPR,			lambda dct, typeShortname, create : DEPR(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.DEPRAnnc,		DEPRAnnc,		lambda dct, typeShortname, create : DEPRAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCI,			FCI,			lambda dct, typeShortname, create : FCI(dct, typeShortname = typeShortname, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCIAnnc,		FCIAnnc,		lambda dct, typeShortname, create : FCIAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.FCNT,			FCNT,			lambda dct, typeShortname, create : FCNT(dct, typeShortname = typeShortname, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCNTAnnc,		FCNTAnnc,		lambda dct, typeShortname, create : FCNTAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCNT_LA,		FCNT_LA,		lambda dct, typeShortname, create : FCNT_LA(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.FCNT_OL,		FCNT_OL,		lambda dct, typeShortname, create : FCNT_OL(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.GRP,			GRP,			lambda dct, typeShortname, create : GRP(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.GRPAnnc,		GRPAnnc,		lambda dct, typeShortname, create : GRPAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.GRP_FOPT,		GRP_FOPT,		lambda dct, typeShortname, create : GRP_FOPT(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.LCP,			LCP,			lambda dct, typeShortname, create : LCP(dct, create = create))
addResourceFactoryCallback(ResourceTypes.LCPAnnc,		LCPAnnc,		lambda dct, typeShortname, create : LCPAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.NOD,			NOD,			lambda dct, typeShortname, create : NOD(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.NODAnnc,		NODAnnc,		lambda dct, typeShortname, create : NODAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.PCH,			PCH,			lambda dct, typeShortname, create : PCH(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.PCH_PCU,		PCH_PCU,		lambda dct, typeShortname, create : PCH_PCU(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.PRMR,			PRMR,			lambda dct, typeShortname, create : PRMR(dct, create = create))
# TODO addResourceFactoryCallback(ResourceTypes.PRMRAnnc,	PRMRAnnc,		lambda dct, typeShortname : PRMRAnnc(dct))
addResourceFactoryCallback(ResourceTypes.PRP,			PRP,			lambda dct, typeShortname, create : PRP(dct, create = create))
# TODO addResourceFactoryCallback(ResourceTypes.PRPAnnc,	PRPAnnc,		lambda dct, typeShortname : PRPAnnc(dct))
addResourceFactoryCallback(ResourceTypes.REQ,			REQ,			lambda dct, typeShortname, create : REQ(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.SCH,			SCH,			lambda dct, typeShortname, create : SCH(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.SCHAnnc,		SCHAnnc,		lambda dct, typeShortname, create : SCHAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.SMD,			SMD,			lambda dct, typeShortname, create : SMD(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.SMDAnnc,		SMDAnnc,		lambda dct, typeShortname, create : SMDAnnc(dct, create = create)) 
addResourceFactoryCallback(ResourceTypes.STTE,			STTE,			lambda dct, typeShortname, create : STTE(dct, create = create))
# TODO addResourceFactoryCallback(ResourceTypes.STTEAnnc,	STTEAnnc,		lambda dct, typeShortname : STTEAnnc(dct)) 
addResourceFactoryCallback(ResourceTypes.SUB,			SUB,			lambda dct, typeShortname, create : SUB(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TS,			TS,				lambda dct, typeShortname, create : TS(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TSAnnc,		TSAnnc,			lambda dct, typeShortname, create : TSAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TS_LA,			TS_LA,			lambda dct, typeShortname, create : TS_LA(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TS_OL,			TS_OL,			lambda dct, typeShortname, create : TS_OL(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TSB,			TSB,			lambda dct, typeShortname, create : TSB(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TSBAnnc,		TSBAnnc,		lambda dct, typeShortname, create : TSBAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TSI,			TSI,			lambda dct, typeShortname, create : TSI(dct, create = create))
addResourceFactoryCallback(ResourceTypes.TSIAnnc,		TSIAnnc,		lambda dct, typeShortname, create : TSIAnnc(dct, create = create))

# Add for MgmtObj specializations
addResourceFactoryCallback(ResourceTypes.ANDI,			ANDI,			lambda dct, typeShortname, create : ANDI(dct, create = create))
addResourceFactoryCallback(ResourceTypes.ANDIAnnc,		ANDIAnnc,		lambda dct, typeShortname, create : ANDIAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.ANI,			ANI,			lambda dct, typeShortname, create : ANI(dct, create = create))
addResourceFactoryCallback(ResourceTypes.ANIAnnc,		ANIAnnc,		lambda dct, typeShortname, create : ANIAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.BAT,			BAT,			lambda dct, typeShortname, create : BAT(dct, create = create))
addResourceFactoryCallback(ResourceTypes.BATAnnc,		BATAnnc,		lambda dct, typeShortname, create : BATAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.DATC,			DATC,			lambda dct, typeShortname, create : DATC(dct, create = create))
addResourceFactoryCallback(ResourceTypes.DATCAnnc,		DATCAnnc,		lambda dct, typeShortname, create : DATCAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.DVC,			DVC,			lambda dct, typeShortname, create : DVC(dct, create = create))
addResourceFactoryCallback(ResourceTypes.DVCAnnc,		DVCAnnc,		lambda dct, typeShortname, create : DVCAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.DVI,			DVI,			lambda dct, typeShortname, create : DVI(dct, create = create))
addResourceFactoryCallback(ResourceTypes.DVIAnnc,		DVIAnnc,		lambda dct, typeShortname, create : DVIAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.EVL,			EVL,			lambda dct, typeShortname, create : EVL(dct, create = create))
addResourceFactoryCallback(ResourceTypes.EVLAnnc,		EVLAnnc,		lambda dct, typeShortname, create : EVLAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.FWR,			FWR,			lambda dct, typeShortname, create : FWR(dct, create = create))
addResourceFactoryCallback(ResourceTypes.FWRAnnc,		FWRAnnc,		lambda dct, typeShortname, create : FWRAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.MEM,			MEM,			lambda dct, typeShortname, create : MEM(dct, create = create))
addResourceFactoryCallback(ResourceTypes.MEMAnnc,		MEMAnnc,		lambda dct, typeShortname, create : MEMAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.NYCFC,			NYCFC,			lambda dct, typeShortname, create : NYCFC(dct, create = create))
addResourceFactoryCallback(ResourceTypes.NYCFCAnnc,		NYCFCAnnc,		lambda dct, typeShortname, create : NYCFCAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.RBO,			RBO,			lambda dct, typeShortname, create : RBO(dct, create = create))
addResourceFactoryCallback(ResourceTypes.RBOAnnc,		RBOAnnc,		lambda dct, typeShortname, create : RBOAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.SWR,			SWR,			lambda dct, typeShortname, create : SWR(dct, create = create))
addResourceFactoryCallback(ResourceTypes.SWRAnnc,		SWRAnnc,		lambda dct, typeShortname, create : SWRAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.WIFIC,			WIFIC,			lambda dct, typeShortname, create : WIFIC(dct, create = create))
addResourceFactoryCallback(ResourceTypes.WIFICAnnc,		WIFICAnnc,		lambda dct, typeShortname, create : WIFICAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.CRDS,			CRDS,			lambda dct, typeShortname, create : CRDS(dct, create = create))
addResourceFactoryCallback(ResourceTypes.CRDSAnnc,		CRDSAnnc,		lambda dct, typeShortname, create : CRDSAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.SIM,			SIM,			lambda dct, typeShortname, create : SIM(dct, create = create))
addResourceFactoryCallback(ResourceTypes.SIMAnnc,		SIMAnnc,		lambda dct, typeShortname, create : SIMAnnc(dct, create = create))
addResourceFactoryCallback(ResourceTypes.MNWK,			MNWK,			lambda dct, typeShortname, create : MNWK(dct, create = create))
addResourceFactoryCallback(ResourceTypes.MNWKAnnc,		MNWKAnnc,		lambda dct, typeShortname, create : MNWKAnnc(dct, create = create))


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
		newResource = cast(Resource, factory(resDict, typeShortname, create))
	else:
		newResource = Unknown(resDict, typeShortname, create)	# Capture-All resource

	if create:
		newResource.initialize(pi, originator)

	return newResource


