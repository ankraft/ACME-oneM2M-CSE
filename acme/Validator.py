#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Validation service and functions
#

from typing import Any
from Logging import Logging
from Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN
from Constants import Constants as C
import Utils


# TODO add wildcard, e.g. for custom attributes

# predefined policies
# type, cardinality, optional.create, optional.update, optional.discovery, announcement
attributePolicies = {
	'ty'	: [ BT.positiveInteger,	CAR.car1,   RO.NP, 	RO.NP, RO.O, AN.NA ],
	'ri'	: [ BT.string, 			CAR.car1,   RO.NP, 	RO.NP, RO.O, AN.NA ],
	'rn' 	: [ BT.string, 			CAR.car1,   RO.O,  	RO.NP, RO.O, AN.NA ],
	'pi' 	: [ BT.string, 			CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ],
	'acpi'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.MA ],
	'ct'	: [ BT.timestamp, 		CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ],
	'et'	: [ BT.timestamp, 		CAR.car1,   RO.O,	RO.O,  RO.O, AN.MA ],
	'lt'	: [ BT.timestamp, 		CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ],
	'st'	: [ BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ],
	'lbl'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.MA ],
	'at'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.NA ],
	'aa'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.NA ],
	'daci'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  RO.O, AN.OA ],		# AE, CSE, CNT
	'loc'	: [ BT.list, 			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# CSE, AE, CNT, FCNT



	'acrs'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# m2m:listOfURIs - SUB
	'act'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ],		# SWR
	'acts'	: [ BT.dict,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.NA ],		# SWR
	'adri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  RO.O, AN.MA ],		# m2m:listOfURIs - ACP
	'aei'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, RO.O, AN.OA ],		# AE
	'airi'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  RO.O, AN.MA ],		# m2m:listOfURIs - ACP
	'ant'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# ANI
	'ape'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# m2m:activityPatternElements - AE
	'api'	: [ BT.string,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.OA ],		# AE
	'apn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# AE
	'apri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  RO.O, AN.MA ],		# m2m:listOfURIs - ACP
	'att'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# BAT
	'awi'	: [ BT.anyURI,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# ANDI
	'bn'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'btl'	: [ BT.unsignedInt,		CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# BAT
	'bts'	: [ BT.positiveInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# BAT
	'can'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# BAT
	'cas'	: [ BT.dict,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# BAT
	'cbs'	: [ BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, RO.O, AN.NA ],		# CNT
	'cmlk'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# MGO
	'cnd'	: [ BT.string,			CAR.car1,   RO.M,	RO.NP, RO.O, AN.MA ],		# CND
	'cnf'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# m2m_contentInfo - CIN
	'cni'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, RO.O, AN.NA ],		# CNT, FCNT (CAR01)
	'cnm'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, RO.O, AN.NA ],		# GRP
	'cnty'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# DVI
	'con'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# CIN
	'conr'	: [ BT.dict,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# m2m:contentRef - CIN
	'cr'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ],		# CNT
	'cs'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, RO.O, AN.NA ],		# CIN, FCNT
	'csi'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, RO.O, AN.OA ],		# CSE
	'cst'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ],		# CSE
	'csy'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# m2m:consistencyStrategy - GRP
	'csz'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# m2m:serializations - AE, CSE (RO!)
	'cus'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# BAT
	'dc'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# MGO
	'dea'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ],		# SWR
	'dis'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# BAT
	'disr'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# CNT
	'dlb'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# DVI
	'dty'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# DVI
	'dvd'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# ANDI
	'dvnm'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'dvt'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# ANDI
	'ena'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# BAT
	'enc'	: [ BT.dict,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'esi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.MA ],		# m2m:e2eSecInfo - AE, CSE
	'exc'	: [	BT.positiveInteger, CAR.car01, 	RO.O, 	RO.O,  RO.O, AN.NA ],  	# SUB
	'far'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# RBO
	'fwn'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# FWR
	'fwv'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'gn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# GRP
	'gpi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'hael'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# NOD
	'hcl'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# NOD
	'hsl'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# NOD
	'hwv'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# DVI
	'in'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ],		# SWR
	'ins'	: [ BT.dict,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.NA ],		# SWR
	'ldv'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# ANI
	'lga'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# ELV
	'lgd'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# ELV
	'lgo'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# ELV
	'lgst'	: [ BT.nonNegInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# ELV
	'lgt'	: [ BT.nonNegInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# ELV
	'li'	: [ BT.anyURI,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ],		# CNT
	'ln'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'lnh'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# ANDI
	'loc'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'macp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# CNT
	'man'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# DVI
	'mbs'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# CNT, FCNT
	'mei'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# m2m:externalID - AE
	'mfd'	: [ BT.timestamp,		CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'mfdl'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'mgca'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# NOD
	'mgd'	: [ BT.nonNegInteger,	CAR.car1,   RO.M,	RO.NP, RO.O, AN.MA ],		# MGO
	'mgs'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.MA ],		# MGO
	'mia'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# CNT, FCNT
	'mid'	: [ BT.list,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# list of m2m:anyURI - GRP
	'mma'	: [ BT.unsignedLong,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# MEM
	'mmt'	: [ BT.unsignedLong,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# MEM
	'mni'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# CNT, FCNT
	'mnm'	: [ BT.positiveInteger,	CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# GRP
	'mod'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# DVI
	'mt'	: [ BT.nonNegInteger,	CAR.car1,   RO.O,	RO.NP, RO.O, AN.OA ],		# m2m:memberType - GRP
	'mtv'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ],		# GRP
	'nar'	: [ BT.dict,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# GRP
	'nec'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'nct'	: [ BT.nonNegInteger,	CAR.car1,  	RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'nfu'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'ni'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.MA ],		# NOD
	'nid'	: [ BT.string,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ],		# NOD
	'nl'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# AE, CSE, FCNT
	'nsp'	: [ BT.positiveInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'nty'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# NOD
	'nu'	: [	BT.list, 			CAR.car1, 	RO.M, 	RO.O,  RO.O, AN.NA ],  	# SUB
	'obis'	: [ BT.list,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# MGO
	'obps'	: [ BT.list,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# MGO
	'or'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# CNT, FCNT
	'osv'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'pn'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'poa'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# m2m:poaList - AE, CSE
	'psn'	: [ BT.positiveInteger,	CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ],		# SUB
	'ptl'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'purl'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'pv'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  RO.O, AN.MA ],		# m2m:setOfArcs - ACP
	'pvs'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  RO.O, AN.MA ],		# m2m:setOfArcs - ACP
	'rbo'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# RBO
	'regs'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# m2m:AERegistrationStatus - AE
	'rl'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.NA ],		# SUB
	'rms'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ],		# NOD
	'rr'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# AE
	'scp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# m2m:sessionCapabilities - AE
	'sld'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# ANDI
	'sli'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# ANDI
	'smod'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'spty'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, RO.O, AN.OA ],		# m2m:specializationType - GRP
	'spur'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'srt'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ],		# CSE
	'srv'	: [ BT.list,			CAR.car01,  RO.M,	RO.O,  RO.O, AN.MA ],		# m2m:supportedReleaseVersions - AE, CSE
	'ss'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# ANDI
	'ssi'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, RO.O, AN.OA ],		# GRP
	'su'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, RO.O, AN.NA ],		# SUB
	'swn'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# SWR
	'swv'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'syst'	: [ BT.timestamp,		CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# DVI
	'tren'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# AE
	'trps'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  RO.O, AN.OA ],		# AE
	'ud'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# FWR
	'uds'	: [ BT.dict,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ],		# FWR
	'Un'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  RO.O, AN.OA ],		# SWR
	'url'	: [ BT.anyURI,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# FWR, SWR
	'vr'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  RO.O, AN.OA ],		# FWR, SWR

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

	'cra'	: [ BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'crb'	: [ BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'cty'	: [ BT.string,			CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'drt'	: [ BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'exa'	: [ BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'exb'	: [ BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'fo'	: [ BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'fu'	: [ BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'lbq'	: [ BT.string,			CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'lim'	: [ BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'lvl'	: [ BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'ms'	: [ BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'ofst'	: [ BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'rcn'	: [ BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'stb'	: [ BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'sts'	: [ BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'sza'	: [ BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'szb'	: [ BT.positiveInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery	
	#'ty'	: [ BT.nonNegInteger,	CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery
	'us'	: [ BT.timestamp,		CAR.car01,   RO.O,	RO.O,  RO.O, AN.NA ],		# discovery

	# TODO lbl, catr, patr



}



def constructPolicy(attributes : list) -> dict:
	""" Help to construct a dict of policies for the given list of shortnames. """
	return { k:attributePolicies.get(k) for k in attributes }


class Validator(object):

	def __init__(self):
		Logging.log('Validator initialized')


	def shutdown(self):
		Logging.log('Validator shut down')

	#########################################################################


	def	validateAttributes(self, jsn : dict, tpe: str, attributePolicies : dict, create : bool = True , isImported : bool = False) -> (bool, int):
		""" Validate a resources attributes for types etc."""
		Logging.logDebug('Validating attributes')

		# Just return in case the resource instance is imported
		if isImported is not None and isImported:
			return (True, C.rcOK)

		# No policies?
		if attributePolicies is None:
			Logging.logWarn("No attribute policies: %s" % jsn)
			return (True, C.rcOK)

		# determine the request column, depending on create or updates
		reqp = 2 if create else 3
		(pureJson, _tpe) = Utils.pureResource(jsn)
		tpe = _tpe if _tpe is not None and _tpe != tpe else tpe 				# determine the real tpe

		# if tpe is not None and not tpe.startswith("m2m:"):
		# 	pureJson = jsn
		attributePolicies = self._checkAdditionalAttributes(tpe, attributePolicies)

		#Logging.logDebug(attributePolicies.items())
		for r in pureJson.keys():
			if r not in attributePolicies.keys():
				Logging.logWarn('Unknown attribute: %s in resource: %s' % (r, tpe))
				return (False, C.rcBadRequest)
		for r, p in attributePolicies.items():
			if p is None:
				Logging.logWarn('No validation policy found for attribute: %s' % r)
				continue
			# Check whether the attribute is allowed or mandatory in the request
			if (v := pureJson.get(r)) is None:
				if p[reqp] == RO.M:		# Not okay, this attribute is mandatory
					Logging.logWarn('Cannot find mandatory attribute: %s' % r)
					return (False, C.rcBadRequest)
				if r in pureJson and p[1] == CAR.car1:
					Logging.logWarn('Cannot delete a mandatory attribute: %s' % r)
					return (False, C.rcBadRequest)
				if p[reqp] in [ RO.NP, RO.O]:	# Okay that the attribute is not in the json, since it is provided or optional
					continue
			else:
				if p[reqp] == RO.NP:
					Logging.logWarn('Found non-provision attribute: %s' % r)
					return (False, C.rcBadRequest)
				if r == 'pvs' and not self.validatePvs(pureJson):
					return (False, C.rcBadRequest)

			# Check whether the value is of the correct type
			if self._validateType(p[0], v):
				continue
			
			# fall-through means: not validated
			Logging.logWarn('Attribute/value validation error: %s=%s' % (r, str(v)))
			return (False, C.rcBadRequest)

		return (True, C.rcOK)


	def validatePvs(self, jsn : dict) -> bool:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		if (l :=len(jsn['pvs'])) == 0:
			Logging.logWarn('Attribute pvs must not be an empty list')
			return False
		elif l > 1:
			Logging.logWarn('Attribute pvs must contain only one item')
			return False
		if (acr := Utils.findXPath(jsn, 'pvs/acr')) is None:
			Logging.logWarn('Attribute pvs/acr not found')
			return False
		if not isinstance(acr, list):
			Logging.logWarn('Attribute pvs/acr must be a list')
			return False
		if len(acr) == 0:
			Logging.logWarn('Attribute pvs/acr must not be an empty list')
			return False
		return True


	def validateRequestArgument(self, argument : str, value : Any) -> bool:
		""" Validate a request argument. """
		if (policy := attributePolicies.get(argument)) is not None:
			return self._validateType(policy[0], value, True)
		return False



	#
	#	Additional attribute definitions, e.g. for <flexContainer> specialisations.
	#

	# Will be filled by further specialization definitions.
	additionalAttributes = { }


	def addAdditionalAttributes(self, attributes : dict):
		""" Add new specialization attribute definitions to the validator. """
		self.additionalAttributes.update(attributes)


	def _checkAdditionalAttributes(self, tpe : str, attributePolicies : dict) -> dict:
		if tpe is not None and not tpe.startswith('m2m:') and tpe in self.additionalAttributes:
			attributePolicies.update(self.additionalAttributes.get(tpe))
		return attributePolicies


	def _validateType(self, tpe : BT, value : Any, convert : bool = False) -> bool:
		""" Check a value for its type. If the convert parameter is True then it
			is assumed that the value could be a stringified value and the method
			will attempt to convert the value to its target type; otherwise this
			is an error. """

		if tpe == BT.positiveInteger:
			if isinstance(value, int) and value > 0:
				return True
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					if int(value) > 0:
						return True
				except:
					return False
			return False

		if tpe == BT.nonNegInteger:
			if isinstance(value, int) and value >= 0:
				return True
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					if int(value) >= 0:
						return True
				except:
					return False
			return False

		if tpe in [ BT.unsignedInt, BT.unsignedLong ]:
			if isinstance(value, int):
				return True
			# try to convert string to number 
			if convert and isinstance(value, str):
				try:
					int(value)
					return True
				except:
					return False
			return False

		if tpe in [ BT.string, BT.timestamp, BT.anyURI ] and isinstance(value, str):
			return True

		if tpe == BT.list and isinstance(value, list):
			return True
		
		if tpe == BT.dict and isinstance(value, dict):
			return True
		
		if tpe == BT.boolean:
			if isinstance(value, bool):
				return True
			# try to convert string to bool
			if convert and isinstance(value, str):	# "true"/"false"
				try:
					bool(value)
					return True
				except:
					return False
			return False

		if tpe == BT.geoCoordinates and isinstance(value, dict):
			return True

		return False


