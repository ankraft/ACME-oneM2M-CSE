#
#	Factory.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Create Resources
#

from typing import Dict, Callable, Tuple, cast
from ..etc.Types import ResourceTypes as T
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


# type definition for Factory lambda
FactoryT = Tuple[object, Callable[ [ Dict[str, object], str, str, bool], object ]]

resourceFactoryMap:Dict[T, FactoryT] = {
	#	Regular resources
	#	type -> (Class, factory)
	
	T.ACP			: (ACP,			lambda dct, tpe, pi, create : ACP(dct, pi = pi, create = create)),
	T.ACTR			: (ACTR,		lambda dct, tpe, pi, create : ACTR(dct, pi = pi, create = create)),		# TODO ACTRAnnc
	T.AE			: (AE,			lambda dct, tpe, pi, create : AE(dct, pi = pi, create = create)),
	T.CIN			: (CIN,			lambda dct, tpe, pi, create : CIN(dct, pi = pi, create = create)),
	T.CNT			: (CNT,			lambda dct, tpe, pi, create : CNT(dct, pi = pi, create = create)),
	T.CNT_LA		: (CNT_LA,		lambda dct, tpe, pi, create : CNT_LA(dct, pi = pi, create = create)),
	T.CNT_OL		: (CNT_OL,		lambda dct, tpe, pi, create : CNT_OL(dct, pi = pi, create = create)),
	T.CSEBase		: (CSEBase,		lambda dct, tpe, pi, create : CSEBase(dct, create = create)),
	T.CSR			: (CSR,			lambda dct, tpe, pi, create : CSR(dct, pi = pi, create = create)),
	T.FCNT			: (FCNT,		lambda dct, tpe, pi, create : FCNT(dct, pi = pi, fcntType = tpe, create = create)),
	T.FCNT_LA		: (FCNT_LA,		lambda dct, tpe, pi, create : FCNT_LA(dct, pi = pi, create = create)),
	T.FCNT_OL		: (FCNT_OL,		lambda dct, tpe, pi, create : FCNT_OL(dct, pi = pi, create = create)),
	T.FCI			: (FCI,			lambda dct, tpe, pi, create : FCI(dct, pi = pi, fcntType = tpe, create = create)),
	T.GRP			: (GRP,			lambda dct, tpe, pi, create : GRP(dct, pi = pi, create = create)),
	T.GRP_FOPT		: (GRP_FOPT,	lambda dct, tpe, pi, create : GRP_FOPT(dct, pi = pi, create = create)),
	T.NOD			: (NOD,			lambda dct, tpe, pi, create : NOD(dct, pi = pi, create = create)),
	T.PCH			: (PCH,			lambda dct, tpe, pi, create : PCH(dct, pi = pi, create = create)),
	T.PCH_PCU		: (PCH_PCU,		lambda dct, tpe, pi, create : PCH_PCU(dct, pi=pi, create = create)),
	T.REQ			: (REQ,			lambda dct, tpe, pi, create : REQ(dct, pi = pi, create = create)),
	T.SUB			: (SUB,			lambda dct, tpe, pi, create : SUB(dct, pi = pi, create = create)),
	T.TS			: (TS,			lambda dct, tpe, pi, create : TS(dct, pi = pi, create = create)),
	T.TS_LA			: (TS_LA,		lambda dct, tpe, pi, create : TS_LA(dct, pi = pi, create = create)),
	T.TS_OL			: (TS_OL,		lambda dct, tpe, pi, create : TS_OL(dct, pi = pi, create = create)),
	T.TSB			: (TSB,			lambda dct, tpe, pi, create : TSB(dct, pi = pi, create = create)),
	T.TSI			: (TSI,			lambda dct, tpe, pi, create : TSI(dct, pi = pi, create = create)),


	# 	Announced Resources
	#	type -> factory

	T.ACPAnnc		: (ACPAnnc,		lambda dct, tpe, pi, create : ACPAnnc(dct, pi = pi, create = create)),
	T.AEAnnc		: (AEAnnc,		lambda dct, tpe, pi, create : AEAnnc(dct, pi = pi, create = create)),
	T.CINAnnc		: (CINAnnc,		lambda dct, tpe, pi, create : CINAnnc(dct, pi = pi, create = create)),
	T.CNTAnnc		: (CNTAnnc,		lambda dct, tpe, pi, create : CNTAnnc(dct, pi = pi, create = create)),
	T.CSEBaseAnnc	: (CSEBaseAnnc,	lambda dct, tpe, pi, create : CSEBaseAnnc(dct, pi = pi, create = create)),
	T.CSRAnnc		: (CSRAnnc,		lambda dct, tpe, pi, create : CSRAnnc(dct, pi = pi, create = create)),
	T.FCNTAnnc		: (FCNTAnnc,	lambda dct, tpe, pi, create : FCNTAnnc(dct, pi = pi, create = create)),
	T.GRPAnnc		: (GRPAnnc,		lambda dct, tpe, pi, create : GRPAnnc(dct, pi = pi, create = create)),
	T.NODAnnc		: (NODAnnc,		lambda dct, tpe, pi, create : NODAnnc(dct, pi = pi, create = create)),
	T.TSAnnc		: (TSAnnc,		lambda dct, tpe, pi, create : TSAnnc(dct, pi = pi, create = create)),
	T.TSIAnnc		: (TSIAnnc,		lambda dct, tpe, pi, create : TSIAnnc(dct, pi = pi, create = create)),


	#	Management specializations
	#	mgd -> factory

	T.ANDI			: (ANDI,		lambda dct, tpe, pi, create : ANDI(dct, pi = pi, create = create)),
	T.ANI			: (ANI,			lambda dct, tpe, pi, create : ANI(dct, pi = pi, create = create)),
	T.BAT			: (BAT,			lambda dct, tpe, pi, create : BAT(dct, pi = pi, create = create)),
	T.DVC			: (DVC,			lambda dct, tpe, pi, create : DVC(dct, pi = pi, create = create)),
	T.DVI			: (DVI,			lambda dct, tpe, pi, create : DVI(dct, pi = pi, create = create)),
	T.EVL			: (EVL,			lambda dct, tpe, pi, create : EVL(dct, pi = pi, create = create)),
	T.FWR			: (FWR,			lambda dct, tpe, pi, create : FWR(dct, pi = pi, create = create)),
	T.MEM			: (MEM,			lambda dct, tpe, pi, create : MEM(dct, pi = pi, create = create)),
	T.NYCFC			: (NYCFC,		lambda dct, tpe, pi, create : NYCFC(dct, pi = pi, create = create)),
	T.RBO			: (RBO,			lambda dct, tpe, pi, create : RBO(dct, pi = pi, create = create)),
	T.SWR			: (SWR,			lambda dct, tpe, pi, create : SWR(dct, pi = pi, create = create)),

	#	Announced Management specializations
	#	mgd -> factory

	T.ANDIAnnc		: (ANDIAnnc,	lambda dct, tpe, pi, create : ANDIAnnc(dct, pi = pi, create = create)),
	T.ANIAnnc		: (ANIAnnc,		lambda dct, tpe, pi, create : ANIAnnc(dct, pi = pi, create = create)),
	T.BATAnnc		: (BATAnnc,		lambda dct, tpe, pi, create : BATAnnc(dct, pi = pi, create = create)),
	T.DVCAnnc		: (DVCAnnc,		lambda dct, tpe, pi, create : DVCAnnc(dct, pi = pi, create = create)),
	T.DVIAnnc		: (DVIAnnc,		lambda dct, tpe, pi, create : DVIAnnc(dct, pi = pi, create = create)),
	T.EVLAnnc		: (EVLAnnc,		lambda dct, tpe, pi, create : EVLAnnc(dct, pi = pi, create = create)),
	T.FWRAnnc		: (FWRAnnc,		lambda dct, tpe, pi, create : FWRAnnc(dct, pi = pi, create = create)),
	T.MEMAnnc		: (MEMAnnc,		lambda dct, tpe, pi, create : MEMAnnc(dct, pi = pi, create = create)),
	T.NYCFCAnnc		: (NYCFCAnnc,	lambda dct, tpe, pi, create : NYCFCAnnc(dct, pi = pi, create = create)),
	T.SWRAnnc		: (SWRAnnc,		lambda dct, tpe, pi, create : SWRAnnc(dct, pi = pi, create = create)),
	T.RBOAnnc		: (RBOAnnc,		lambda dct, tpe, pi, create : RBOAnnc(dct, pi = pi, create = create)),
}



def resourceFromDict(resDict:JSON = {}, pi:str = None, ty:T = None, create:bool = False, isImported:bool = False) -> Result:
	""" Create a resource from a dictionary structure.
		This will *not* call the activate method, therefore some attributes
		may be set separately.
	"""
	resDict, tpe = Utils.pureResource(resDict)	# remove optional "m2m:xxx" level

	# Determine type
	typ = resDict['ty'] if 'ty' in resDict else ty
	if not typ and (typ := T.fromTPE(tpe)) is  None:
		L.logWarn(dbg := f'cannot determine type for resource: {tpe}')
		return Result.errorResult(dbg = dbg)
	
	# Check for Parent
	if not pi and typ != T.CSEBase and (not (pi := resDict.get('pi')) or len(pi) == 0):
		L.logWarn(dbg := f'pi missing in resource: {tpe}')
		return Result.errorResult(dbg = dbg)

	# Check whether given type during CREATE matches the resource's ty attribute
	if typ != None and ty != None and typ != ty:
		L.logWarn(dbg := f'parameter type ({ty}) and resource type ({typ}) mismatch')
		return Result.errorResult(dbg = dbg)
	
	# Check whether given type during CREATE matches the resource type specifier
	if ty != None and tpe != None and ty not in [ T.FCNT, T.FCNTAnnc, T.FCI, T.MGMTOBJ, T.MGMTOBJAnnc ]  and ty.tpe() != tpe:
		L.logWarn(dbg := f'parameter type ({ty}) and resource type specifier ({tpe}) mismatch')
		return Result.errorResult(dbg = dbg)
	
	# store the import status in the original resDict
	if isImported:
		resDict[Resource._imported] = True	# Indicate that this is an imported resource

	# Determine a factory and call it
	factory:FactoryT = None
	if typ == T.MGMTOBJ:										# for <mgmtObj>
		mgd = resDict['mgd'] if 'mgd' in resDict else None		# Identify mdg in <mgmtObj>
		factory = resourceFactoryMap.get(mgd)
	elif typ == T.MGMTOBJAnnc:									# for <mgmtObjA>
		mgd = resDict['mgd'] if 'mgd' in resDict else None		# Identify mdg in <mgmtObj>
		factory = resourceFactoryMap.get(T(mgd).announced())	# Get the announced version
	else:
		factory = resourceFactoryMap.get(typ)
	if factory:
		return Result(status = True, rsc = RC.OK, resource = factory[1](resDict, tpe, pi, create))

	return Result(status = True, rsc = RC.OK, resource = Unknown(resDict, tpe, pi = pi, create = create))	# Capture-All resource


def resourceClassByType(typ:T) -> Resource:
	"""	Return a resource class by its ResourceType, or None.
	"""
	if not (r := resourceFactoryMap.get(typ)):
		return None
	return cast(Resource, r[0])
