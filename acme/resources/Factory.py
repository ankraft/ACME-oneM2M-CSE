#
#	Factory.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Create Resources
#

from typing import Dict, Callable, Any, Tuple
from Types import ResourceTypes as T
from Types import ResponseCode as RC
from Types import Result
from Logging import Logging
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
from resources.MgmtObj import MgmtObj
from resources.MgmtObjAnnc import MgmtObjAnnc
from resources.NOD import NOD
from resources.NODAnnc import NODAnnc
from resources.PCH import PCH
from resources.PCH_PCU import PCH_PCU
from resources.REQ import REQ
from resources.SUB import SUB

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
FactoryT = Callable[[Dict[str, object], str, str, bool], object]

resourceFactoryMap:Dict[T, FactoryT] = {
	#	Regular resources
	#	type -> factory
	
	T.ACP		: lambda dct, tpe, pi, create : ACP(dct, pi=pi, create=create),
	T.AE		: lambda dct, tpe, pi, create : AE(dct, pi=pi, create=create),
	T.CIN		: lambda dct, tpe, pi, create : CIN(dct, pi=pi, create=create),
	T.CNT		: lambda dct, tpe, pi, create : CNT(dct, pi=pi, create=create),
	T.CNT_LA	: lambda dct, tpe, pi, create : CNT_LA(dct, pi=pi, create=create),
	T.CNT_OL	: lambda dct, tpe, pi, create : CNT_OL(dct, pi=pi, create=create),
	T.CNT		: lambda dct, tpe, pi, create : CNT(dct, pi=pi, create=create),
	T.CSEBase	: lambda dct, tpe, pi, create : CSEBase(dct, create=create),
	T.CSR		: lambda dct, tpe, pi, create : CSR(dct, pi=pi, create=create),
	T.FCNT		: lambda dct, tpe, pi, create : FCNT(dct, pi=pi, fcntType=tpe, create=create),
	T.FCNT_LA	: lambda dct, tpe, pi, create : FCNT_LA(dct, pi=pi, create=create),
	T.FCNT_OL	: lambda dct, tpe, pi, create : FCNT_OL(dct, pi=pi, create=create),
	T.FCI		: lambda dct, tpe, pi, create : FCI(dct, pi=pi, fcntType=tpe, create=create),
	T.GRP		: lambda dct, tpe, pi, create : GRP(dct, pi=pi, create=create),
	T.GRP_FOPT	: lambda dct, tpe, pi, create : GRP_FOPT(dct, pi=pi, create=create),
	T.NOD		: lambda dct, tpe, pi, create : NOD(dct, pi=pi, create=create),
	T.PCH		: lambda dct, tpe, pi, create : PCH(dct, pi=pi, create=create),
	T.PCH_PCU	: lambda dct, tpe, pi, create : PCH_PCU(dct, pi=pi, create=create),
	T.REQ		: lambda dct, tpe, pi, create : REQ(dct, pi=pi, create=create),
	T.SUB		: lambda dct, tpe, pi, create : SUB(dct, pi=pi, create=create),


	# 	Announced Resources
	#	type -> factory

	T.ACPAnnc	: lambda dct, tpe, pi, create : ACPAnnc(dct, pi=pi, create=create),
	T.AEAnnc	: lambda dct, tpe, pi, create : AEAnnc(dct, pi=pi, create=create),
	T.CINAnnc	: lambda dct, tpe, pi, create : CINAnnc(dct, pi=pi, create=create),
	T.CNTAnnc	: lambda dct, tpe, pi, create : CNTAnnc(dct, pi=pi, create=create),
	T.CSRAnnc	: lambda dct, tpe, pi, create : CSRAnnc(dct, pi=pi, create=create),
	T.FCNTAnnc	: lambda dct, tpe, pi, create : FCNTAnnc(dct, pi=pi, create=create),
	T.FCIAnnc	: lambda dct, tpe, pi, create : FCIAnnc(dct, pi=pi, create=create),
	T.GRPAnnc	: lambda dct, tpe, pi, create : GRPAnnc(dct, pi=pi, create=create),
	T.NODAnnc	: lambda dct, tpe, pi, create : NODAnnc(dct, pi=pi, create=create),


	#	Management specializations
	#	mgd -> factory

	T.ANDI		: lambda dct, tpe, pi, create : ANDI(dct, pi=pi, create=create),
	T.ANI		: lambda dct, tpe, pi, create : ANI(dct, pi=pi, create=create),
	T.BAT		: lambda dct, tpe, pi, create : BAT(dct, pi=pi, create=create),
	T.DVC		: lambda dct, tpe, pi, create : DVC(dct, pi=pi, create=create),
	T.DVI		: lambda dct, tpe, pi, create : DVI(dct, pi=pi, create=create),
	T.EVL		: lambda dct, tpe, pi, create : EVL(dct, pi=pi, create=create),
	T.FWR		: lambda dct, tpe, pi, create : FWR(dct, pi=pi, create=create),
	T.MEM		: lambda dct, tpe, pi, create : MEM(dct, pi=pi, create=create),
	T.NYCFC		: lambda dct, tpe, pi, create : NYCFC(dct, pi=pi, create=create),
	T.RBO		: lambda dct, tpe, pi, create : RBO(dct, pi=pi, create=create),
	T.SWR		: lambda dct, tpe, pi, create : SWR(dct, pi=pi, create=create),

	#	Announced Management specializations
	#	mgd -> factory

	T.ANDIAnnc	: lambda dct, tpe, pi, create : ANDIAnnc(dct, pi=pi, create=create),
	T.ANIAnnc	: lambda dct, tpe, pi, create : ANIAnnc(dct, pi=pi, create=create),
	T.BATAnnc	: lambda dct, tpe, pi, create : BATAnnc(dct, pi=pi, create=create),
	T.DVCAnnc	: lambda dct, tpe, pi, create : DVCAnnc(dct, pi=pi, create=create),
	T.DVIAnnc	: lambda dct, tpe, pi, create : DVIAnnc(dct, pi=pi, create=create),
	T.EVLAnnc	: lambda dct, tpe, pi, create : EVLAnnc(dct, pi=pi, create=create),
	T.FWRAnnc	: lambda dct, tpe, pi, create : FWRAnnc(dct, pi=pi, create=create),
	T.MEMAnnc	: lambda dct, tpe, pi, create : MEMAnnc(dct, pi=pi, create=create),
	T.NYCFCAnnc	: lambda dct, tpe, pi, create : NYCFCAnnc(dct, pi=pi, create=create),
	T.SWRAnnc	: lambda dct, tpe, pi, create : SWRAnnc(dct, pi=pi, create=create),
	T.RBOAnnc	: lambda dct, tpe, pi, create : RBOAnnc(dct, pi=pi, create=create),
}



def resourceFromDict(resDict:Dict[str, Any]={}, pi:str=None, ty:T=None, create:bool=False, isImported:bool=False) -> Result:
	""" Create a resource from a dictionary structure.
		This will *not* call the activate method, therefore some attributes
		may be set separately.
	"""
	resDict, tpe = Utils.pureResource(resDict)	# remove optional "m2m:xxx" level
	typ = resDict['ty'] if 'ty' in resDict else ty

	# Check whether given type during CREATE matches the resource's ty attribute
	if typ != None and ty != None and typ != ty:
		Logging.logWarn(dbg := f'parameter type ({ty}) and resource type ({typ}) mismatch')
		return Result(dbg=dbg, rsc=RC.badRequest)
	
	# Check whether given type during CREATE matches the resource type specifier
	if ty != None and tpe != None and ty not in [ T.FCNT, T.FCNTAnnc, T.FCI, T.FCIAnnc, T.MGMTOBJ, T.MGMTOBJAnnc ]  and ty.tpe() != tpe:
		Logging.logWarn(dbg := f'parameter type ({ty}) and resource type specifier ({tpe}) mismatch')
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
		return Result(resource=factory(resDict, tpe, pi, create))

	return Result(resource=Unknown(resDict, tpe, pi=pi, create=create))	# Capture-All resource


