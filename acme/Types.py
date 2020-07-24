#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M types
#

from __future__ import annotations
from enum import IntEnum, Enum, auto
from collections import namedtuple


# ResourceType = namedtuple('ResourceType', ['type', 'name'])

# class ResourceTypes(Enum):
# 	ACP 		=  ResourceType(1, 'm2m:acp')

# 	@property
# 	def name(self):
# 		return self.value.name

class ResourceTypes(IntEnum):

	UNKNOWN		= -1

	# Resource Types

	MIXED		=  0
	ACP 		=  1
	AE			=  2
	CNT			=  3
	CIN 		=  4
	CSEBase 	=  5
	GRP 		=  9
	MGMTOBJ		= 13
	NOD			= 14
	CSR			= 16
	SUB			= 23
	FCNT	 	= 28
	FCI 		= 58


	# Virtual resources (proprietary resource types)

	CNT_OL		=  -20001
	CNT_LA		=  -20002
	GRP_FOPT	=  -20003
	FCNT_OL		=  -20004
	FCNT_LA		=  -20005
	PCH_PCU		=  -20006

	# <mgmtObj> Specializations

	FWR			= 1001
	SWR			= 1002
	MEM			= 1003
	ANI			= 1004
	ANDI		= 1005
	BAT			= 1006
	DVI 		= 1007
	DVC 		= 1008
	RBO 		= 1009
	EVL 		= 1010

	# Announced Resources

	ACPAnnc 	= 10001
	AEAnnc 		= 10002	
	CNTAnnc 	= 10003
	CINAnnc 	= 10004
	GRPAnnc 	= 10009
	MGMTOBJAnnc = 10013
	NODAnnc 	= 10014
	CSRAnnc 	= 10016
	FCNTAnnc 	= 10028
	FCIAnnc 	= 10058

	def tpe(self) -> str:
		return ResourceTypes._names[self.value] 				#  type: ignore

	def announced(self) -> ResourceTypes:
		if self.value in ResourceTypes._announcedMapping:		#  type: ignore
			return ResourceTypes._announcedMapping[self.value] 	#  type: ignore
		return ResourceTypes.UNKNOWN

	def isAnnounced(self) -> bool:
		return self.value in ResourceTypes._announcedSet 		# type: ignore



ResourceTypes._announcedMapping = {								#  type: ignore
	ResourceTypes.ACP 		: ResourceTypes.ACPAnnc,
	ResourceTypes.AE 		: ResourceTypes.AEAnnc,
	ResourceTypes.CNT		: ResourceTypes.CNTAnnc,
	ResourceTypes.CIN 		: ResourceTypes.CINAnnc,
	ResourceTypes.GRP		: ResourceTypes.GRPAnnc,
	ResourceTypes.MGMTOBJ	: ResourceTypes.MGMTOBJAnnc,
	ResourceTypes.NOD		: ResourceTypes.NODAnnc,
	ResourceTypes.CSR		: ResourceTypes.CSRAnnc,
	ResourceTypes.FCNT		: ResourceTypes.FCNTAnnc,
	ResourceTypes.FCI		: ResourceTypes.FCIAnnc,
}

ResourceTypes._announcedSet = [									#  type: ignore
	ResourceTypes.ACPAnnc, ResourceTypes.AEAnnc, ResourceTypes.CNTAnnc, ResourceTypes.CINAnnc,
	ResourceTypes.GRPAnnc, ResourceTypes.MGMTOBJAnnc, ResourceTypes.NODAnnc, 
	ResourceTypes.CSRAnnc, ResourceTypes.FCNTAnnc, ResourceTypes.FCIAnnc
]


ResourceTypes._names 	= {										# type: ignore
		ResourceTypes.UNKNOWN		: 'unknown',

		ResourceTypes.MIXED			: 'mixed',
		ResourceTypes.ACP 			: 'm2m:acp',
		ResourceTypes.AE 			: 'm2m:ae',
		ResourceTypes.CNT			: 'm2m:cnt',
		ResourceTypes.CIN 			: 'm2m:cin',
		ResourceTypes.CSEBase		: 'm2m:cb',
		ResourceTypes.GRP			: 'm2m:grp',
		ResourceTypes.MGMTOBJ		: 'm2m:mgo',				# not an official shortname
		ResourceTypes.NOD			: 'm2m:nod',
		ResourceTypes.CSR 			: 'm2m:csr',
		ResourceTypes.SUB			: 'm2m:sub',
		ResourceTypes.FCNT			: 'm2m:fcnt',				# not an official shortname
		ResourceTypes.FCI			: 'm2m:fci',				# not an official shortname

		ResourceTypes.ACPAnnc 		: 'm2m:acpA',
		ResourceTypes.AEAnnc 		: 'm2m:aeA',
		ResourceTypes.CNTAnnc 		: 'm2m:cntA',
		ResourceTypes.CINAnnc 		: 'm2m:cinA',
		ResourceTypes.GRPAnnc 		: 'm2m:grpA',
		ResourceTypes.MGMTOBJAnnc 	: 'm2m:mgoA',
		ResourceTypes.NODAnnc 		: 'm2m:nodA',
		ResourceTypes.CSRAnnc 		: 'm2m:csrA',
		ResourceTypes.FCNTAnnc 		: 'm2m:fcntA',
		ResourceTypes.FCIAnnc 		: 'm2m:fciA',

		ResourceTypes.CNT_OL		: 'm2m:ol',
		ResourceTypes.CNT_LA		: 'm2m:la',
		ResourceTypes.GRP_FOPT		: 'm2m:fopt',
		ResourceTypes.FCNT_OL		: 'm2m:ol',
		ResourceTypes.FCNT_LA		: 'm2m:la',
		ResourceTypes.PCH_PCU		: 'm2m:pcu',

		ResourceTypes.FWR			: 'm2m:fwr',
		ResourceTypes.SWR			: 'm2m:swr',
		ResourceTypes.MEM			: 'm2m:mem',
		ResourceTypes.ANI			: 'm2m:ani',
		ResourceTypes.ANDI			: 'm2m:andi',
		ResourceTypes.BAT			: 'm2m:bat',
		ResourceTypes.DVI			: 'm2m:dvi',
		ResourceTypes.DVC			: 'm2m:dvc',
		ResourceTypes.RBO			: 'm2m:rbo',
		ResourceTypes.EVL			: 'm2m:evl',
	}




class BasicType(IntEnum):
	""" Basic resource types """
	positiveInteger	= auto()
	nonNegInteger	= auto()
	unsignedInt		= auto()
	unsignedLong	= auto()
	string 			= auto()
	timestamp		= auto()
	list 			= auto()
	dict 			= auto()
	anyURI			= auto()
	boolean			= auto()
	float 			= auto()
	geoCoordinates	= auto()


class Cardinality(IntEnum):
	""" Resource attribute cardinalities """
	car1			= auto()
	car1L			= auto()
	car01			= auto()
	car01L			= auto()


class RequestOptionality(IntEnum):
	""" request optionalities """
	NP				= auto()
	O 				= auto()
	M 				= auto()


class Announced(IntEnum):
	""" anouncent attribute indications """
	NA				= auto()
	OA				= auto()
	MA				= auto()
