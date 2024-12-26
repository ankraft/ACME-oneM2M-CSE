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
addResourceFactoryCallback(ResourceTypes.ACP, 			ACP,			lambda dct, typeShortname, pi : ACP(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.ACPAnnc,		ACPAnnc,		lambda dct, typeShortname, pi : ACPAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.ACTR, 			ACTR,			lambda dct, typeShortname, pi : ACTR(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.ACTRAnnc, 		ACTRAnnc,		lambda dct, typeShortname, pi : ACTRAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.AE, 			AE,				lambda dct, typeShortname, pi : AE(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.AEAnnc,		AEAnnc,			lambda dct, typeShortname, pi : AEAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CIN, 			CIN,			lambda dct, typeShortname, pi : CIN(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CINAnnc, 		CINAnnc,		lambda dct, typeShortname, pi : CINAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CNT,	 		CNT,			lambda dct, typeShortname, pi : CNT(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CNTAnnc, 		CNTAnnc,		lambda dct, typeShortname, pi : CNTAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CNT_LA,		CNT_LA,			lambda dct, typeShortname, pi : CNT_LA(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CNT_OL,		CNT_OL,			lambda dct, typeShortname, pi : CNT_OL(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CSEBase,		CSEBase,		lambda dct, typeShortname, pi : CSEBase(dct)) 
addResourceFactoryCallback(ResourceTypes.CSEBaseAnnc,	CSEBaseAnnc,	lambda dct, typeShortname, pi : CSEBaseAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CRS,			CRS,			lambda dct, typeShortname, pi : CRS(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CSR,			CSR,			lambda dct, typeShortname, pi : CSR(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.CSRAnnc,		CSRAnnc,		lambda dct, typeShortname, pi : CSRAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DEPR,			DEPR,			lambda dct, typeShortname, pi : DEPR(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DEPRAnnc,		DEPRAnnc,		lambda dct, typeShortname, pi : DEPRAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.FCI,			FCI,			lambda dct, typeShortname, pi : FCI(dct, pi = pi, fcntType = typeShortname)) 
addResourceFactoryCallback(ResourceTypes.FCNT,			FCNT,			lambda dct, typeShortname, pi : FCNT(dct, pi = pi, fcntType = typeShortname)) 
addResourceFactoryCallback(ResourceTypes.FCNTAnnc,		FCNTAnnc,		lambda dct, typeShortname, pi : FCNTAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.FCNT_LA,		FCNT_LA,		lambda dct, typeShortname, pi : FCNT_LA(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.FCNT_OL,		FCNT_OL,		lambda dct, typeShortname, pi : FCNT_OL(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.GRP,			GRP,			lambda dct, typeShortname, pi : GRP(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.GRPAnnc,		GRPAnnc,		lambda dct, typeShortname, pi : GRPAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.GRP_FOPT,		GRP_FOPT,		lambda dct, typeShortname, pi : GRP_FOPT(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.LCP,			LCP,			lambda dct, typeShortname, pi : LCP(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.LCPAnnc,		LCPAnnc,		lambda dct, typeShortname, pi : LCPAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.NOD,			NOD,			lambda dct, typeShortname, pi : NOD(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.NODAnnc,		NODAnnc,		lambda dct, typeShortname, pi : NODAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.PCH,			PCH,			lambda dct, typeShortname, pi : PCH(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.PCH_PCU,		PCH_PCU,		lambda dct, typeShortname, pi : PCH_PCU(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.PRMR,			PRMR,			lambda dct, typeShortname, pi : PRMR(dct, pi = pi))
# TODO addResourceFactoryCallback(ResourceTypes.PRMRAnnc,	PRMRAnnc,		lambda dct, typeShortname, pi : PRMRAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.PRP,			PRP,			lambda dct, typeShortname, pi : PRP(dct, pi = pi))
# TODO addResourceFactoryCallback(ResourceTypes.PRPAnnc,	PRPAnnc,		lambda dct, typeShortname, pi : PRPAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.REQ,			REQ,			lambda dct, typeShortname, pi : REQ(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.SCH,			SCH,			lambda dct, typeShortname, pi : SCH(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.SCHAnnc,		SCHAnnc,		lambda dct, typeShortname, pi : SCHAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.SMD,			SMD,			lambda dct, typeShortname, pi : SMD(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.SMDAnnc,		SMDAnnc,		lambda dct, typeShortname, pi : SMDAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.STTE,			STTE,			lambda dct, typeShortname, pi : STTE(dct, pi = pi))
# TODO addResourceFactoryCallback(ResourceTypes.STTEAnnc,	STTEAnnc,		lambda dct, typeShortname, pi : STTEAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.SUB,			SUB,			lambda dct, typeShortname, pi : SUB(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TS,			TS,				lambda dct, typeShortname, pi : TS(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TSAnnc,		TSAnnc,			lambda dct, typeShortname, pi : TSAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TS_LA,			TS_LA,			lambda dct, typeShortname, pi : TS_LA(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TS_OL,			TS_OL,			lambda dct, typeShortname, pi : TS_OL(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TSB,			TSB,			lambda dct, typeShortname, pi : TSB(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TSBAnnc,		TSBAnnc,		lambda dct, typeShortname, pi : TSBAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TSI,			TSI,			lambda dct, typeShortname, pi : TSI(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.TSIAnnc,		TSIAnnc,		lambda dct, typeShortname, pi : TSIAnnc(dct, pi = pi)) 

# Add for MgmtObj specializations
addResourceFactoryCallback(ResourceTypes.ANDI,			ANDI,			lambda dct, typeShortname, pi : ANDI(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.ANDIAnnc,		ANDIAnnc,		lambda dct, typeShortname, pi : ANDIAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.ANI,			ANI,			lambda dct, typeShortname, pi : ANI(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.ANIAnnc,		ANIAnnc,		lambda dct, typeShortname, pi : ANIAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.BAT,			BAT,			lambda dct, typeShortname, pi : BAT(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.BATAnnc,		BATAnnc,		lambda dct, typeShortname, pi : BATAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DATC,			DATC,			lambda dct, typeShortname, pi : DATC(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DATCAnnc,		DATCAnnc,		lambda dct, typeShortname, pi : DATCAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DVC,			DVC,			lambda dct, typeShortname, pi : DVC(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DVCAnnc,		DVCAnnc,		lambda dct, typeShortname, pi : DVCAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DVI,			DVI,			lambda dct, typeShortname, pi : DVI(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.DVIAnnc,		DVIAnnc,		lambda dct, typeShortname, pi : DVIAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.EVL,			EVL,			lambda dct, typeShortname, pi : EVL(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.EVLAnnc,		EVLAnnc,		lambda dct, typeShortname, pi : EVLAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.FWR,			FWR,			lambda dct, typeShortname, pi : FWR(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.FWRAnnc,		FWRAnnc,		lambda dct, typeShortname, pi : FWRAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.MEM,			MEM,			lambda dct, typeShortname, pi : MEM(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.MEMAnnc,		MEMAnnc,		lambda dct, typeShortname, pi : MEMAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.NYCFC,			NYCFC,			lambda dct, typeShortname, pi : NYCFC(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.NYCFCAnnc,		NYCFCAnnc,		lambda dct, typeShortname, pi : NYCFCAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.RBO,			RBO,			lambda dct, typeShortname, pi : RBO(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.RBOAnnc,		RBOAnnc,		lambda dct, typeShortname, pi : RBOAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.SWR,			SWR,			lambda dct, typeShortname, pi : SWR(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.SWRAnnc,		SWRAnnc,		lambda dct, typeShortname, pi : SWRAnnc(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.WIFIC,			WIFIC,			lambda dct, typeShortname, pi : WIFIC(dct, pi = pi)) 
addResourceFactoryCallback(ResourceTypes.WIFICAnnc,		WIFICAnnc,		lambda dct, typeShortname, pi : WIFICAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.CRDS,			CRDS,			lambda dct, typeShortname, pi : CRDS(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.CRDSAnnc,		CRDSAnnc,		lambda dct, typeShortname, pi : CRDSAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.SIM,			SIM,			lambda dct, typeShortname, pi : SIM(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.SIMAnnc,		SIMAnnc,		lambda dct, typeShortname, pi : SIMAnnc(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.MNWK,			MNWK,			lambda dct, typeShortname, pi : MNWK(dct, pi = pi))
addResourceFactoryCallback(ResourceTypes.MNWKAnnc,		MNWKAnnc,		lambda dct, typeShortname, pi : MNWKAnnc(dct, pi = pi))


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
		newResource = cast(Resource, factory(resDict, typeShortname, pi))
	else:
		newResource = Unknown(resDict, typeShortname, pi = pi)	# Capture-All resource

	if create:
		newResource.willBeActivated(pi, originator)

	return newResource


