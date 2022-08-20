#
#	Factory.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Create Resources
#

from typing import Dict, Callable, Tuple, cast
from ..etc.Types import ResourceTypes as T, addResourceFactoryCallback, FactoryCallableT
from ..etc.Types import ResponseStatusCode as RC
from ..etc.Types import Result, JSON
from ..etc import Utils as Utils
from ..services.Logging import Logging as L


from ..resources.ACP import ACP
from ..resources.ACPAnnc import ACPAnnc
from ..resources.ACTR import ACTR				# TODO ANNC
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
from ..resources.FCI import FCI
from ..resources.FCNT import FCNT
from ..resources.FCNTAnnc import FCNTAnnc
from ..resources.FCNT_LA import FCNT_LA
from ..resources.FCNT_OL import FCNT_OL
from ..resources.GRP import GRP
from ..resources.GRPAnnc import GRPAnnc
from ..resources.GRP_FOPT import GRP_FOPT
from ..resources.NOD import NOD
from ..resources.NODAnnc import NODAnnc
from ..resources.PCH import PCH
from ..resources.PCH_PCU import PCH_PCU
from ..resources.REQ import REQ
from ..resources.SUB import SUB
from ..resources.SMD import SMD
from ..resources.SMDAnnc import SMDAnnc
from ..resources.TS import TS
from ..resources.TSAnnc import TSAnnc
from ..resources.TS_LA import TS_LA
from ..resources.TS_OL import TS_OL
from ..resources.TSB import TSB
from ..resources.TSI import TSI
from ..resources.TSIAnnc import TSIAnnc

from ..resources.Unknown import Unknown

from ..resources.ANDI import ANDI
from ..resources.ANDIAnnc import ANDIAnnc
from ..resources.ANI import ANI
from ..resources.ANIAnnc import ANIAnnc
from ..resources.BAT import BAT
from ..resources.BATAnnc import BATAnnc
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
from ..resources.Resource import Resource


# Adding factory callbacks to regular resource type details
addResourceFactoryCallback(T.ACP, 			ACP,			lambda dct, tpe, pi, create : ACP(dct, pi = pi, create = create))
addResourceFactoryCallback(T.ACPAnnc,		ACPAnnc,		lambda dct, tpe, pi, create : ACPAnnc(dct, pi = pi, create = create))
addResourceFactoryCallback(T.ACTR, 			ACTR,			lambda dct, tpe, pi, create : ACTR(dct, pi = pi, create = create)) 
# TODO ACTRAnnc
addResourceFactoryCallback(T.AE, 			AE,				lambda dct, tpe, pi, create : AE(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.AEAnnc,		AEAnnc,			lambda dct, tpe, pi, create : AEAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CIN, 			CIN,			lambda dct, tpe, pi, create : CIN(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CINAnnc, 		CINAnnc,		lambda dct, tpe, pi, create : CINAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CNT,	 		CNT,			lambda dct, tpe, pi, create : CNT(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CNTAnnc, 		CNTAnnc,		lambda dct, tpe, pi, create : CNTAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CNT_LA,		CNT_LA,			lambda dct, tpe, pi, create : CNT_LA(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CNT_OL,		CNT_OL,			lambda dct, tpe, pi, create : CNT_OL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CSEBase,		CSEBase,		lambda dct, tpe, pi, create : CSEBase(dct, create = create)) 
addResourceFactoryCallback(T.CSEBaseAnnc,	CSEBaseAnnc,	lambda dct, tpe, pi, create : CSEBaseAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CRS,			CRS,			lambda dct, tpe, pi, create : CRS(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CSR,			CSR,			lambda dct, tpe, pi, create : CSR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.CSRAnnc,		CSRAnnc,		lambda dct, tpe, pi, create : CSRAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.FCI,			FCI,			lambda dct, tpe, pi, create : FCI(dct, pi = pi, fcntType = tpe, create = create)) 
addResourceFactoryCallback(T.FCNT,			FCNT,			lambda dct, tpe, pi, create : FCNT(dct, pi = pi, fcntType = tpe, create = create)) 
addResourceFactoryCallback(T.FCNTAnnc,		FCNTAnnc,		lambda dct, tpe, pi, create : FCNTAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.FCNT_LA,		FCNT_LA,		lambda dct, tpe, pi, create : FCNT_LA(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.FCNT_OL,		FCNT_OL,		lambda dct, tpe, pi, create : FCNT_OL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.GRP,			GRP,			lambda dct, tpe, pi, create : GRP(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.GRPAnnc,		GRPAnnc,		lambda dct, tpe, pi, create : GRPAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.GRP_FOPT,		GRP_FOPT,		lambda dct, tpe, pi, create : GRP_FOPT(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.NOD,			NOD,			lambda dct, tpe, pi, create : NOD(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.NODAnnc,		NODAnnc,		lambda dct, tpe, pi, create : NODAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.PCH,			PCH,			lambda dct, tpe, pi, create : PCH(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.PCH_PCU,		PCH_PCU,		lambda dct, tpe, pi, create : PCH_PCU(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.REQ,			REQ,			lambda dct, tpe, pi, create : REQ(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.SMD,			SMD,			lambda dct, tpe, pi, create : SMD(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.SMDAnnc,		SMDAnnc,		lambda dct, tpe, pi, create : SMDAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.SUB,			SUB,			lambda dct, tpe, pi, create : SUB(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.TS,			TS,				lambda dct, tpe, pi, create : TS(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.TSAnnc,		TSAnnc,			lambda dct, tpe, pi, create : TSAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.TS_LA,			TS_LA,			lambda dct, tpe, pi, create : TS_LA(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.TS_OL,			TS_OL,			lambda dct, tpe, pi, create : TS_OL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.TSB,			TSB,			lambda dct, tpe, pi, create : TSB(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.TSI,			TSI,			lambda dct, tpe, pi, create : TSI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.TSIAnnc,		TSIAnnc,		lambda dct, tpe, pi, create : TSIAnnc(dct, pi = pi, create = create)) 

# Add for MgmtObj specializations
addResourceFactoryCallback(T.ANDI,			ANDI,			lambda dct, tpe, pi, create : ANDI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.ANDIAnnc,		ANDIAnnc,		lambda dct, tpe, pi, create : ANDIAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.ANI,			ANI,			lambda dct, tpe, pi, create : ANI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.ANIAnnc,		ANIAnnc,		lambda dct, tpe, pi, create : ANIAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.BAT,			BAT,			lambda dct, tpe, pi, create : BAT(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.BATAnnc,		BATAnnc,		lambda dct, tpe, pi, create : BATAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.DVC,			DVC,			lambda dct, tpe, pi, create : DVC(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.DVCAnnc,		DVCAnnc,		lambda dct, tpe, pi, create : DVCAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.DVI,			DVI,			lambda dct, tpe, pi, create : DVI(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.DVIAnnc,		DVIAnnc,		lambda dct, tpe, pi, create : DVIAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.EVL,			EVL,			lambda dct, tpe, pi, create : EVL(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.EVLAnnc,		EVLAnnc,		lambda dct, tpe, pi, create : EVLAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.FWR,			FWR,			lambda dct, tpe, pi, create : FWR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.FWRAnnc,		FWRAnnc,		lambda dct, tpe, pi, create : FWRAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.MEM,			MEM,			lambda dct, tpe, pi, create : MEM(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.MEMAnnc,		MEMAnnc,		lambda dct, tpe, pi, create : MEMAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.NYCFC,			NYCFC,			lambda dct, tpe, pi, create : NYCFC(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.NYCFCAnnc,		NYCFCAnnc,		lambda dct, tpe, pi, create : NYCFCAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.RBO,			RBO,			lambda dct, tpe, pi, create : RBO(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.RBOAnnc,		RBOAnnc,		lambda dct, tpe, pi, create : RBOAnnc(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.SWR,			SWR,			lambda dct, tpe, pi, create : SWR(dct, pi = pi, create = create)) 
addResourceFactoryCallback(T.SWRAnnc,		SWRAnnc,		lambda dct, tpe, pi, create : SWRAnnc(dct, pi = pi, create = create)) 


_specResources = [ T.FCNT, T.FCNTAnnc, T.FCI, T.MGMTOBJ, T.MGMTOBJAnnc ]


def resourceFromDict(resDict:JSON = {}, pi:str = None, ty:T = None, create:bool = False, isImported:bool = False) -> Result:
	""" Create a resource from a dictionary structure.

		This function will **not** call the resource's *activate()* method, therefore some attributes
		may need to be set separately.

		Args:
			resDict: Dictionary with the resource definition.
			pi: Resource ID of the parent ID.
			ty: Resource type.
			create: Resource will be newly created.
			isImported: True when the resource is imported, or created by the `ScriptManager`. In this case some checks may not be performed.
		Return:
			`Result` object with the *resource* attribute set to the created resource object.

	"""
	resDict, tpe = Utils.pureResource(resDict)	# remove optional "m2m:xxx" level

	# Determine type
	typ = T(resDict['ty']) if 'ty' in resDict else ty
	if typ is None and (typ := T.fromTPE(tpe)) is None:
		return Result.errorResult(dbg = L.logWarn(f'cannot determine type for creating the resource: {tpe}'))

	if ty is not None:
		if typ is not None and typ != ty:
			return Result.errorResult(dbg = L.logWarn(f'parameter type ({ty}) and resource type ({typ}) mismatch'))
		if tpe is not None and ty.tpe() != tpe and ty not in _specResources:
			return Result.errorResult(dbg = L.logWarn(f'parameter type ({ty}) and resource type specifier ({tpe}) mismatch'))
	
	# Check for Parent
	if pi is None and typ != T.CSEBase and (not (pi := resDict.get('pi')) or len(pi) == 0):
		return Result.errorResult(dbg = L.logWarn(f'pi missing in resource: {tpe}'))

	# store the import status in the original resDict
	if isImported:
		resDict[Resource._imported] = True	# Indicate that this is an imported resource

	# Determine a factory and call it
	factory:FactoryCallableT = None

	if typ == T.MGMTOBJ:										# for <mgmtObj>
		# mgd = resDict['mgd'] if 'mgd' in resDict else None		# Identify mdg in <mgmtObj>
		factory = T(resDict['mgd']).resourceFactory()
	elif typ == T.MGMTOBJAnnc:									# for <mgmtObjA>
		# mgd = resDict['mgd'] if 'mgd' in resDict else None		# Identify mdg in <mgmtObj>
		factory = T(resDict['mgd']).announced().resourceFactory()
	else:
		factory = typ.resourceFactory()
	if factory:
		return Result(status = True, rsc = RC.OK, resource = factory(resDict, tpe, pi, create))

	return Result(status = True, rsc = RC.OK, resource = Unknown(resDict, tpe, pi = pi, create = create))	# Capture-All resource


