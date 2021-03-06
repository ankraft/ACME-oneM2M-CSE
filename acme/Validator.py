#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Validation service and functions
#

from copy import deepcopy
from typing import Any, List, Dict
from Logging import Logging
from Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN, ResponseCode as RC
from Types import JSON, AttributePolicies
from Constants import Constants as C
from Types import Result, AttributePolicies
from Configuration import Configuration
from resources.Resource import Resource
import Utils


# TODO owner attribute, annnouncedSyncType

# predefined policiespolicies
# type, cardinality, optional.create, optional.update, optional.discovery, announcement
attributePolicies:AttributePolicies = {
	'ty'	: ( BT.positiveInteger,	CAR.car1,   RO.NP, 	RO.NP, RO.O, AN.NA ),
	'ri'	: ( BT.string, 			CAR.car1,   RO.NP, 	RO.NP, RO.O, AN.NA ),
	'rn' 	: ( BT.string, 			CAR.car1,   RO.O,  	RO.NP, RO.O, AN.NA ),
	'pi' 	: ( BT.string, 			CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ),
	'acpi'	: ( BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.MA ),
	'ct'	: ( BT.timestamp, 		CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ),
	'et'	: ( BT.timestamp, 		CAR.car1N,  RO.O,	RO.O,  RO.O, AN.MA ),
	'lt'	: ( BT.timestamp, 		CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ),
	'st'	: ( BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ),
	'lbl'	: ( BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.MA ),
	'at'	: ( BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.NA ),
	'aa'	: ( BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.NA ),
	'daci'	: ( BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.OA ),		# AE, CSE, CNT
	'loc'	: ( BT.list, 			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CSE, AE, CNT, FCNT
	'hld' 	: ( BT.string, 			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),




	'acrs'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# m2m:listOfURIs - SUB
	'act'	: ( BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ),		# SWR
	'acts'	: ( BT.dict,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.NA ),		# SWR
	'adri'	: ( BT.list,			CAR.car1,	RO.O,	RO.O,  RO.O, AN.MA ),		# m2m:listOfURIs - ACP
	'aei'	: ( BT.string,			CAR.car1,   RO.NP,	RO.NP, RO.O, AN.OA ),		# AE
	'airi'	: ( BT.list,			CAR.car1,	RO.O,	RO.O,  RO.O, AN.MA ),		# m2m:listOfURIs - ACP
	'ant'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# ANI
	'ape'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# m2m:activityPatternElements - AE, CSR
	'api'	: ( BT.string,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.OA ),		# AE
	'apn'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# AE
	'apri'	: ( BT.list,			CAR.car1,	RO.O,	RO.O,  RO.O, AN.MA ),		# m2m:listOfURIs - ACP
	'att'	: ( BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# BAT
	'awi'	: ( BT.anyURI,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# ANDI
	'bn'	: ( BT.dict,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'btl'	: ( BT.unsignedInt,		CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# BAT
	'bts'	: ( BT.positiveInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# BAT
	'can'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# BAT
	'cas'	: ( BT.dict,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# BAT
	'cb'	: ( BT.string,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.OA ),		# CSR
	'cbs'	: ( BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ),		# CNT
	'cmlk'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# MGO
	'cnd'	: ( BT.string,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.MA ),		# CND
	'cnf'	: ( BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# m2m_contentInfo - CIN
	'cni'	: ( BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, RO.O, AN.NA ),		# CNT, FCNT (CAR01)
	'cnm'	: ( BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, RO.O, AN.NA ),		# GRP
	'cnty'	: ( BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# DVI
	'con'	: ( BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# CIN
	'conr'	: ( BT.list,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# m2m:contentRef - CIN
	'cr'	: ( BT.list, 			CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ),		# CNT
	'cs'	: ( BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, RO.O, AN.NA ),		# CIN, FCNT
	'csi'	: ( BT.string,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.OA ),		# CSE, CSR
	'cst'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# CSE, CSR
	'csy'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# m2m:consistencyStrategy - GRP
	'csz'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# m2m:serializations - AE, CSE (RO!), CSR
	'cus'	: ( BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# BAT
	'dc'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# MGO
	'dea'	: ( BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ),		# SWR
	'dcse'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CSR
	'dgt'	: ( BT.timestamp,		CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# FCNT
	'dis'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# BAT
	'disr'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CNT
	'dlb'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# DVI
	'dty'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# DVI
	'dvd'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# ANDI
	'dvnm'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'dvt'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# ANDI
	'egid'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CSR
	'ena'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# BAT
	'enc'	: ( BT.dict,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'esi'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.MA ),		# m2m:e2eSecInfo - AE, CSE, CSR
	'exc'	: (	BT.positiveInteger, CAR.car01, 	RO.O, 	RO.O,  RO.O, AN.NA ),  		# SUB
	'far'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# RBO
	'fwn'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# FWR
	'fwv'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'gn'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# GRP
	'gpi'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'hael'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# NOD
	'hcl'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# NOD
	'hsl'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# NOD
	'hwv'	: ( BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# DVI
	'in'	: ( BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ),		# SWR
	'ins'	: ( BT.dict,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.NA ),		# SWR
	'ldv'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# ANI
	'lga'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# ELV
	'lgd'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# ELV
	'lgo'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# ELV
	'lgst'	: ( BT.nonNegInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# ELV
	'lgt'	: ( BT.nonNegInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# ELV
	'li'	: ( BT.anyURI,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ),		# CNT
	'ln'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'lnh'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# ANDI
	'lnk'	: ( BT.anyURI,			CAR.car1, 	RO.NP,	RO.NP, RO.O, AN.MA ),		# announcedResources
	'loc'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'macp'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CNT
	'man'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# DVI
	'mbs'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CNT, FCNT
	'mcfc'	: ( BT.string,			CAR.car1,   RO.M,	RO.NP,  RO.O, AN.OA),		# NYCFC
	'mcff'	: ( BT.anyURI,			CAR.car1,   RO.M,	RO.NP,  RO.O, AN.OA),		# NYCFC
	'mei'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# m2m:externalID - AE, CSR
	'mfd'	: ( BT.timestamp,		CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'mfdl'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'mgca'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# NOD
	'mgd'	: ( BT.nonNegInteger,	CAR.car1,   RO.M,	RO.NP, RO.O, AN.MA ),		# MGO
	'mgs'	: ( BT.anyURI,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.MA ),		# MGO
	'mi'	: ( BT.dict,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.OA ),		# REQ
	'mia'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CNT, FCNT
	'mid'	: ( BT.list,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# list of m2m:anyURI - GRP
	'mma'	: ( BT.unsignedLong,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# MEM
	'mmt'	: ( BT.unsignedLong,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# MEM
	'mni'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CNT, FCNT
	'mnm'	: ( BT.positiveInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# GRP
	'mod'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# DVI
	'mt'	: ( BT.nonNegInteger,	CAR.car1,   RO.O,	RO.NP, RO.O, AN.OA ),		# m2m:memberType - GRP
	'mtcc'	: ( BT.positiveInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CSR
	'mtv'	: ( BT.boolean,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ),		# GRP
	'nar'	: ( BT.dict,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# GRP
	'nec'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'nct'	: ( BT.nonNegInteger,	CAR.car1,  	RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'nfu'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'ni'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.MA ),		# NOD
	'nid'	: ( BT.string,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ),		# NOD
	'nl'	: ( BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# AE, CSE, FCNT
	'nsp'	: ( BT.positiveInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'nty'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# NOD
	'nu'	: (	BT.list, 			CAR.car1, 	RO.M, 	RO.O,  RO.O, AN.NA ),  		# SUB
	'obis'	: ( BT.list,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# MGO
	'obps'	: ( BT.list,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# MGO
	'op'	: ( BT.nonNegInteger,	CAR.car1,   RO.M,	RO.NP, RO.O, AN.NA ),		# REQ
	'or'	: ( BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CNT, FCNT
	'org'	: ( BT.string,			CAR.car1,   RO.NP,	RO.NP, RO.NP,AN.NA ),		# REQ
	'ors'	: ( BT.dict,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CNT, FCNT, REQ
	'osv'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'pc'	: ( BT.dict,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# REQ
	'pn'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'poa'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# m2m:poaList - AE, CSE
	'psn'	: ( BT.positiveInteger,	CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ),		# SUB
	'ptl'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'purl'	: ( BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'pv'	: ( BT.dict,			CAR.car1,	RO.M,	RO.O,  RO.O, AN.MA ),		# m2m:setOfArcs - ACP
	'pvs'	: ( BT.dict,			CAR.car1,	RO.M,	RO.O,  RO.O, AN.MA ),		# m2m:setOfArcs - ACP
	'rbo'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# RBO
	'regs'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# m2m:AERegistrationStatus - AE
	'rid'	: ( BT.string,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.OA ),		# REQ
	'rl'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ),		# SUB
	'rms'	: ( BT.boolean,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ),		# NOD
	'rr'	: ( BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# AE
	'rs'	: ( BT.nonNegInteger,	CAR.car1,   RO.M,	RO.NP, RO.O, AN.OA ),		# REQ
	'scp'	: ( BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# m2m:sessionCapabilities - AE
	'sld'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# ANDI
	'sli'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# ANDI
	'smod'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'spty'	: ( BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ),		# m2m:specializationType - GRP
	'spur'	: ( BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'srt'	: ( BT.list, 			CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ),		# CSE
	'srv'	: ( BT.list,			CAR.car01,  RO.M,	RO.O,  RO.O, AN.MA ),		# m2m:supportedReleaseVersions - AE, CSE, CSR
	'ss'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# ANDI
	'ssi'	: ( BT.boolean,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ),		# GRP
	'su'	: ( BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ),		# SUB
	'suids'	: ( BT.list,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# NYCFC
	'swn'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# SWR
	'swv'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'syst'	: ( BT.timestamp,		CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# DVI
	'tg'	: ( BT.anyURI,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.NA ),		# REQ
	'tren'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# AE, CSR
	'tri'	: ( BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CSR
	'trn'	: ( BT.unsignedInt,		CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# CSR
	'trps'	: ( BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ),		# AE
	'ud'	: ( BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# FWR
	'uds'	: ( BT.dict,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ),		# FWR
	'un'	: ( BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ),		# SWR
	'url'	: ( BT.anyURI,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# FWR, SWR
	'vr'	: ( BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ),		# FWR, SWR
	

	

	# TODO Lookup in TS-0004, 0001

	# CSE notificationCongestionPolicy 'ncp'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP,  AN.OA ],		# CSE

	# AE Not defined yet: ExternalGroupID?
	# AE CSE Not defined yet: enableTimeCompensation
	# CSE currentTime
	# CIN deletionCnt
	# GRP: somecastEnable, somecastAlgorithm not defined yet (shortname)

	#
	#	Request arguments
	#

	'cra'	: ( BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'crb'	: ( BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'cty'	: ( BT.string,			CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'drt'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'exa'	: ( BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'exb'	: ( BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'fo'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'fu'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'lbq'	: ( BT.string,			CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'lim'	: ( BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'lvl'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'ms'	: ( BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'ofst'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'rcn'	: ( BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'stb'	: ( BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'sts'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'sza'	: ( BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'szb'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery	
	#'ty'	: ( BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'us'	: ( BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'arp'	: ( BT.string,			CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# discovery
	'rt'	: ( BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# request
	'rp'	: ( BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ),		# request 

	# TODO lbl, catr, patr



}



def constructPolicy(attributes: List[str]) -> AttributePolicies:
	""" Help to construct a dict of policies for the given list of shortnames. """
	return { k:attributePolicies.get(k) for k in attributes }


def addPolicy(policies:AttributePolicies, newPolicies:AttributePolicies) -> AttributePolicies:
	"""	Add further policies to a policy dictionary. """
	policies = deepcopy(policies)
	policies.update( newPolicies )
	return policies


AdditionalAttributes = Dict[str, AttributePolicies]

class Validator(object):


	# Will be filled by further specialization definitions.
	additionalAttributes:AdditionalAttributes = { }

	def __init__(self) -> None:
		self.validationEnabled = Configuration.get('cse.enableValidation')
		Logging.log('Validator initialized')


	def shutdown(self) -> bool:
		Logging.log('Validator shut down')
		return True

	#########################################################################


	def	validateAttributes(self, dct:JSON, tpe:str, attributePolicies:AttributePolicies, create:bool=True , isImported:bool=False, createdInternally:bool=False, isAnnounced:bool=False) -> Result:
		""" Validate a resources attributes for types etc."""
		if not self.validationEnabled:	# just return if disabled
			return Result(status=True)

		Logging.logDebug('Validating attributes')

		# Just return in case the resource instance is imported
		if isImported is not None and isImported:
			return Result(status=True)

		# No policies?
		if attributePolicies is None:
			Logging.logWarn(f'No attribute policies: {dct}')
			return Result(status=True)

		# determine the request column, depending on create or updates
		if isAnnounced:
			reqp = 5
		else:
			reqp = 2 if create else 3

		(pureResDict, _tpe) = Utils.pureResource(dct)
		if pureResDict is None:
			return Result(status=False, rsc=RC.badRequest, dbg='content is None')

		tpe = _tpe if _tpe is not None and _tpe != tpe else tpe 				# determine the real tpe

		# if tpe is not None and not tpe.startswith("m2m:"):
		# 	pureResDict = dct
		if (attributePolicies := self._addAdditionalAttributes(tpe, attributePolicies)) is None:
			Logging.logWarn(err := f'Unknown resource type: {tpe}')
			return Result(status=False, rsc=RC.badRequest, dbg=err)

		# Logging.logDebug(attributePolicies.items())
		for r in pureResDict.keys():
			if r not in attributePolicies.keys():
				Logging.logWarn(err := f'Unknown attribute: {r} in resource: {tpe}')
				return Result(status=False, rsc=RC.badRequest, dbg=err)
		for r, p in attributePolicies.items():
			if p is None:
				Logging.logWarn(f'No validation policy found for attribute: {r}')
				continue
			# Check whether the attribute is allowed or mandatory in the request
			if (v := pureResDict.get(r)) is None:

				# check the the announced cases first
				if isAnnounced:
					# MA are not checked bc they are only present if they are presennt in the original resource
					continue
					
				if p[reqp] == RO.M:		# Not okay, this attribute is mandatory
					Logging.logWarn(err := f'Cannot find mandatory attribute: {r}')
					return Result(status=False, rsc=RC.badRequest, dbg=err)
				if r in pureResDict and p[1] == CAR.car1: # but ignore CAR.car1N (which may be Null/None)
					Logging.logWarn(err := f'Cannot delete a mandatory attribute: {r}')
					return Result(status=False, rsc=RC.badRequest, dbg=err)
				if p[reqp] in [ RO.NP, RO.O ]:	# Okay that the attribute is not in the dict, since it is provided or optional
					continue
			else:
				if not createdInternally:
					if p[reqp] == RO.NP:
						Logging.logWarn(err := f'Found non-provision attribute: {r}')
						return Result(status=False, rsc=RC.badRequest, dbg=err)

				# check the the announced cases
				if isAnnounced:
					if p[reqp] == AN.NA:	# Not okay, attribute is not announced
						Logging.logWarn(err := f'Found non-announced attribute: {r}')
						return Result(status=False, rsc=RC.badRequest, dbg=err)
					continue

				if r == 'pvs' and not (res := self.validatePvs(pureResDict)).status:
					return Result(status=False, rsc=RC.badRequest, dbg=res.dbg)

			# Check whether the value is of the correct type
			if (res := self._validateType(p[0], v)).status:
				continue

			# fall-through means: not validated
			Logging.logWarn(err := f'Attribute/value validation error: {r}={str(v)} ({res.dbg})')
			return Result(status=False, rsc=RC.badRequest, dbg=err)

		return Result(status=True)


	def validatePvs(self, dct:JSON) -> Result:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		if (l :=len(dct['pvs'])) == 0:
			err = 'Attribute pvs must not be an empty list'
			Logging.logWarn(err)
			return Result(status=False, dbg=err)
		elif l > 1:
			err = 'Attribute pvs must contain only one item'
			Logging.logWarn(err)
			return Result(status=False, dbg=err)
		if (acr := Utils.findXPath(dct, 'pvs/acr')) is None:
			err = 'Attribute pvs/acr not found'
			Logging.logWarn(err)
			return Result(status=False, dbg=err)
		if not isinstance(acr, list):
			err = 'Attribute pvs/acr must be a list'
			Logging.logWarn(err)
			return Result(status=False, dbg=err)
		if len(acr) == 0:
			err = 'Attribute pvs/acr must not be an empty list'
			Logging.logWarn(err)
			return Result(status=False, dbg=err)
		return Result(status=True)


	def validateRequestArgument(self, argument:str, value:Any) -> Result:
		""" Validate a request argument. """
		if (policy := attributePolicies.get(argument)) is not None:
			return self._validateType(policy[0], value, True)
		return Result(status=False, dbg='attribute not defined')



	#
	#	Additional attribute definitions, e.g. for <flexContainer> specialisations.
	#


	def updateAdditionalAttributes(self, additionalAttributes:AdditionalAttributes) -> bool:
		""" Add or update new specialization attribute definitions to the validator.
			The dict has a single entry (the type) that contains another dict 
			of attribute definitions for that type. 
		"""
		if len(additionalAttributes.keys()) != 1:
			Logging.logErr('Additional attributes must only contain 1 type')
			return False
		entries = additionalAttributes[next(iter(additionalAttributes))]	# get first and only entry
		for k,v in entries.items():
			if len(v) != 6:
				Logging.logErr(f'Attribute description for {k} must contain 6 entries')
				return False
		try:
			self.additionalAttributes.update(additionalAttributes)
		except Exception as e:
			Logging.logErr(str(e))
			return False
		return True


	def addAdditionalAttributePolicy(self, tpe:str, attributePolicies:AttributePolicies) -> bool:
		""" Add a new policy dictionary for a type's attributes. """
		if (attrs := self.additionalAttributes.get(tpe)) is None:
			defs = { tpe : attributePolicies }
		else:
			attrs.update(attributePolicies)
			defs = { tpe : attrs }
		return self.updateAdditionalAttributes(defs)


	def getAdditionalAttributesFor(self, tpe:str) -> AttributePolicies:
		""" Return the dictionary of additional attributes for a type or None. """
		return self.additionalAttributes.get(tpe)


	def _addAdditionalAttributes(self, tpe: str, attributePolicies:AttributePolicies) -> AttributePolicies:
		#if tpe is not None and not tpe.startswith('m2m:'):
		if tpe is not None and tpe in self.additionalAttributes:
			if tpe in self.additionalAttributes:
				newap = deepcopy(attributePolicies)
				newap.update(self.additionalAttributes.get(tpe))
				return newap
			else:
				return None # tpe not defined
		return attributePolicies


	def _validateType(self, tpe:int, value:Any, convert:bool = False) -> Result:
		""" Check a value for its type. If the convert parameter is True then it
			is assumed that the value could be a stringified value and the method
			will attempt to convert the value to its target type; otherwise this
			is an error. """

		if tpe == BT.positiveInteger:
			if isinstance(value, int):
				if value > 0:
					return Result(status=True)
				return Result(status=False, dbg='value must be > 0')
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					if int(value) > 0:
						return Result(status=True)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg='unknown type for value')

		if tpe == BT.nonNegInteger:
			if isinstance(value, int):
				if value >= 0:
					return Result(status=True)
				return Result(status=False, dbg='value must be >= 0')
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					if int(value) >= 0:
						return Result(status=True)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg='unknown type for value')

		if tpe in [ BT.unsignedInt, BT.unsignedLong ]:
			if isinstance(value, int):
				return Result(status=True)
			# try to convert string to number 
			if convert and isinstance(value, str):
				try:
					int(value)
					return Result(status=True)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg='unknown type for value')

		if tpe in [ BT.string, BT.timestamp, BT.anyURI ] and isinstance(value, str):
			return Result(status=True)

		if tpe == BT.list and isinstance(value, list):
			return Result(status=True)
		
		if tpe == BT.dict and isinstance(value, dict):
			return Result(status=True)
		
		if tpe == BT.boolean:
			if isinstance(value, bool):
				return Result(status=True)
			# try to convert string to bool
			if convert and isinstance(value, str):	# "true"/"false"
				try:
					bool(value)
					return Result(status=True)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg='unknown type for value')

		if tpe == BT.float:
			if isinstance(value, float):
				return Result(status=True)
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					float(value)
					return Result(status=True)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg='unknown type for value')

		if tpe == BT.integer:
			if isinstance(value, int):
				return Result(status=True)
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					int(value)
					return Result(status=True)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg='unknown type for value')

		if tpe == BT.geoCoordinates and isinstance(value, dict):
			return Result(status=True)

		return Result(status=False, dbg='unknown type')


