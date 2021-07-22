#
#	Factory.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Create Resources
#

from typing import Dict, Callable, Any
from Types import ResourceTypes as T
from Types import ResponseCode as RC
from Types import Result
from Logging import Logging as L
import Utils


from resources.ACP import ACP
from resources.ACPAnnc import ACPAnnc
from resources.AE import AE
from resources.AEAnnc import AEAnnc
from resources.CIN import CIN
from resources.CINAnnc import CINAnnc
from resources.CNT import CNT
from resources.CNTAnnc import CNTAnnc
from resources.CNT_LA import CNT_LA
from resources.CNT_OL import CNT_OL
from resources.CSEBase import CSEBase
from resources.CSR import CSR
from resources.CSRAnnc import CSRAnnc
from resources.FCI import FCI
from resources.FCIAnnc import FCIAnnc
from resources.FCNT import FCNT
from resources.FCNTAnnc import FCNTAnnc
from resources.FCNT_LA import FCNT_LA
from resources.FCNT_OL import FCNT_OL
from resources.GRP import GRP
from resources.GRPAnnc import GRPAnnc
from resources.GRP_FOPT import GRP_FOPT
from resources.NOD import NOD
from resources.NODAnnc import NODAnnc
from resources.PCH import PCH
from resources.PCH_PCU import PCH_PCU
from resources.REQ import REQ
from resources.SUB import SUB
from resources.TS import TS
from resources.TSAnnc import TSAnnc
from resources.TS_LA import TS_LA
from resources.TS_OL import TS_OL
from resources.TSI import TSI
from resources.TSIAnnc import TSIAnnc

#from resources.TSAnnc import TSAnnc


from resources.Unknown import Unknown

from resources.ANDI import ANDI
from resources.ANDIAnnc import ANDIAnnc
from resources.ANI import ANI
from resources.ANIAnnc import ANIAnnc
from resources.BAT import BAT
from resources.BATAnnc import BATAnnc
from resources.DVC import DVC
from resources.DVCAnnc import DVCAnnc
from resources.DVI import DVI
from resources.DVIAnnc import DVIAnnc
from resources.EVL import EVL
from resources.EVLAnnc import EVLAnnc
from resources.FWR import FWR
from resources.FWRAnnc import FWRAnnc
from resources.MEM import MEM
from resources.MEMAnnc import MEMAnnc
from resources.NYCFC import NYCFC
from resources.NYCFCAnnc import NYCFCAnnc
from resources.RBO import RBO
from resources.RBOAnnc import RBOAnnc
from resources.SWR import SWR
from resources.SWRAnnc import SWRAnnc
from resources.Resource import Resource


# type definition for Factory lambda
FactoryT = Callable[[Dict[str, object], str, str, bool, bool], object]

resourceFactoryMap:Dict[T, FactoryT] = {
	#	Regular resources
	#	type -> factory
	
	T.ACP		: lambda dct, tpe, pi, create, isRemote : ACP(dct, pi=pi, create=create, isRemote=isRemote),
	T.AE		: lambda dct, tpe, pi, create, isRemote : AE(dct, pi=pi, create=create, isRemote=isRemote),
	T.CIN		: lambda dct, tpe, pi, create, isRemote : CIN(dct, pi=pi, create=create, isRemote=isRemote),
	T.CNT		: lambda dct, tpe, pi, create, isRemote : CNT(dct, pi=pi, create=create, isRemote=isRemote),
	T.CNT_LA	: lambda dct, tpe, pi, create, isRemote : CNT_LA(dct, pi=pi, create=create, isRemote=isRemote),
	T.CNT_OL	: lambda dct, tpe, pi, create, isRemote : CNT_OL(dct, pi=pi, create=create, isRemote=isRemote),
	T.CNT		: lambda dct, tpe, pi, create, isRemote : CNT(dct, pi=pi, create=create, isRemote=isRemote),
	T.CSEBase	: lambda dct, tpe, pi, create, isRemote : CSEBase(dct, create=create, isRemote=isRemote),
	T.CSR		: lambda dct, tpe, pi, create, isRemote : CSR(dct, pi=pi, create=create, isRemote=isRemote),
	T.FCNT		: lambda dct, tpe, pi, create, isRemote : FCNT(dct, pi=pi, fcntType=tpe, create=create, isRemote=isRemote),
	T.FCNT_LA	: lambda dct, tpe, pi, create, isRemote : FCNT_LA(dct, pi=pi, create=create, isRemote=isRemote),
	T.FCNT_OL	: lambda dct, tpe, pi, create, isRemote : FCNT_OL(dct, pi=pi, create=create, isRemote=isRemote),
	T.FCI		: lambda dct, tpe, pi, create, isRemote : FCI(dct, pi=pi, fcntType=tpe, create=create),
	T.GRP		: lambda dct, tpe, pi, create, isRemote : GRP(dct, pi=pi, create=create, isRemote=isRemote),
	T.GRP_FOPT	: lambda dct, tpe, pi, create, isRemote : GRP_FOPT(dct, pi=pi, create=create, isRemote=isRemote),
	T.NOD		: lambda dct, tpe, pi, create, isRemote : NOD(dct, pi=pi, create=create, isRemote=isRemote),
	T.PCH		: lambda dct, tpe, pi, create, isRemote : PCH(dct, pi=pi, create=create, isRemote=isRemote),
	T.PCH_PCU	: lambda dct, tpe, pi, create, isRemote : PCH_PCU(dct, pi=pi, create=create, isRemote=isRemote),
	T.REQ		: lambda dct, tpe, pi, create, isRemote : REQ(dct, pi=pi, create=create, isRemote=isRemote),
	T.SUB		: lambda dct, tpe, pi, create, isRemote : SUB(dct, pi=pi, create=create, isRemote=isRemote),
	T.TS		: lambda dct, tpe, pi, create, isRemote : TS(dct, pi=pi, create=create, isRemote=isRemote),
	T.TS_LA		: lambda dct, tpe, pi, create, isRemote : TS_LA(dct, pi=pi, create=create, isRemote=isRemote),
	T.TS_OL		: lambda dct, tpe, pi, create, isRemote : TS_OL(dct, pi=pi, create=create, isRemote=isRemote),
	T.TSI		: lambda dct, tpe, pi, create, isRemote : TSI(dct, pi=pi, create=create, isRemote=isRemote),


	# 	Announced Resources
	#	type -> factory

	T.ACPAnnc	: lambda dct, tpe, pi, create, isRemote : ACPAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.AEAnnc	: lambda dct, tpe, pi, create, isRemote : AEAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.CINAnnc	: lambda dct, tpe, pi, create, isRemote : CINAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.CNTAnnc	: lambda dct, tpe, pi, create, isRemote : CNTAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.CSRAnnc	: lambda dct, tpe, pi, create, isRemote : CSRAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.FCNTAnnc	: lambda dct, tpe, pi, create, isRemote : FCNTAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.FCIAnnc	: lambda dct, tpe, pi, create, isRemote : FCIAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.GRPAnnc	: lambda dct, tpe, pi, create, isRemote : GRPAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.NODAnnc	: lambda dct, tpe, pi, create, isRemote : NODAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.TSAnnc	: lambda dct, tpe, pi, create, isRemote : TSAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.TSIAnnc	: lambda dct, tpe, pi, create, isRemote : TSIAnnc(dct, pi=pi, create=create, isRemote=isRemote),


	#	Management specializations
	#	mgd -> factory

	T.ANDI		: lambda dct, tpe, pi, create, isRemote : ANDI(dct, pi=pi, create=create, isRemote=isRemote),
	T.ANI		: lambda dct, tpe, pi, create, isRemote : ANI(dct, pi=pi, create=create, isRemote=isRemote),
	T.BAT		: lambda dct, tpe, pi, create, isRemote : BAT(dct, pi=pi, create=create, isRemote=isRemote),
	T.DVC		: lambda dct, tpe, pi, create, isRemote : DVC(dct, pi=pi, create=create, isRemote=isRemote),
	T.DVI		: lambda dct, tpe, pi, create, isRemote : DVI(dct, pi=pi, create=create, isRemote=isRemote),
	T.EVL		: lambda dct, tpe, pi, create, isRemote : EVL(dct, pi=pi, create=create, isRemote=isRemote),
	T.FWR		: lambda dct, tpe, pi, create, isRemote : FWR(dct, pi=pi, create=create, isRemote=isRemote),
	T.MEM		: lambda dct, tpe, pi, create, isRemote : MEM(dct, pi=pi, create=create, isRemote=isRemote),
	T.NYCFC		: lambda dct, tpe, pi, create, isRemote : NYCFC(dct, pi=pi, create=create, isRemote=isRemote),
	T.RBO		: lambda dct, tpe, pi, create, isRemote : RBO(dct, pi=pi, create=create, isRemote=isRemote),
	T.SWR		: lambda dct, tpe, pi, create, isRemote : SWR(dct, pi=pi, create=create, isRemote=isRemote),

	#	Announced Management specializations
	#	mgd -> factory

	T.ANDIAnnc	: lambda dct, tpe, pi, create, isRemote : ANDIAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.ANIAnnc	: lambda dct, tpe, pi, create, isRemote : ANIAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.BATAnnc	: lambda dct, tpe, pi, create, isRemote : BATAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.DVCAnnc	: lambda dct, tpe, pi, create, isRemote : DVCAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.DVIAnnc	: lambda dct, tpe, pi, create, isRemote : DVIAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.EVLAnnc	: lambda dct, tpe, pi, create, isRemote : EVLAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.FWRAnnc	: lambda dct, tpe, pi, create, isRemote : FWRAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.MEMAnnc	: lambda dct, tpe, pi, create, isRemote : MEMAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.NYCFCAnnc	: lambda dct, tpe, pi, create, isRemote : NYCFCAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.SWRAnnc	: lambda dct, tpe, pi, create, isRemote : SWRAnnc(dct, pi=pi, create=create, isRemote=isRemote),
	T.RBOAnnc	: lambda dct, tpe, pi, create, isRemote : RBOAnnc(dct, pi=pi, create=create, isRemote=isRemote),
}



def resourceFromDict(resDict:Dict[str, Any]={}, pi:str=None, ty:T=None, create:bool=False, isImported:bool=False, isRemote:bool=False) -> Result:
	""" Create a resource from a dictionary structure.
		This will *not* call the activate method, therefore some attributes
		may be set separately.
	"""
	resDict, tpe = Utils.pureResource(resDict)	# remove optional "m2m:xxx" level

	# Determine type
	typ = resDict['ty'] if 'ty' in resDict else ty
	if typ is None and (typ := T.fromTPE(tpe)) is  None:
		L.logWarn(dbg := f'cannot determine type for resource: {tpe}')
		return Result(status=False, dbg=dbg, rsc=RC.badRequest)
	
	# Check for Parent
	if pi is None and typ != T.CSEBase and ((pi := resDict.get('pi')) is None or len(pi) == 0):
		L.logWarn(dbg := f'pi missing in resource: {tpe}')
		return Result(status=False, dbg=dbg, rsc=RC.badRequest)


	# Check whether given type during CREATE matches the resource's ty attribute
	if typ != None and ty != None and typ != ty:
		L.logWarn(dbg := f'parameter type ({ty}) and resource type ({typ}) mismatch')
		return Result(dbg=dbg, rsc=RC.badRequest)
	
	# Check whether given type during CREATE matches the resource type specifier
	if ty != None and tpe != None and ty not in [ T.FCNT, T.FCNTAnnc, T.FCI, T.FCIAnnc, T.MGMTOBJ, T.MGMTOBJAnnc ]  and ty.tpe() != tpe:
		L.logWarn(dbg := f'parameter type ({ty}) and resource type specifier ({tpe}) mismatch')
		return Result(dbg=dbg, rsc=RC.badRequest)
	
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
		factory = resourceFactoryMap.get(T.announcedMgd(mgd))	# Get the announced version
	else:
		factory = resourceFactoryMap.get(typ)
	if factory is not None:
		return Result(resource=factory(resDict, tpe, pi, create, isRemote))

	return Result(resource=Unknown(resDict, tpe, pi=pi, create=create, isRemote=isRemote))	# Capture-All resource


