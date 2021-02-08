#
#	DVIAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	DVI : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T, JSON
import Utils


class DVIAnnc(MgmtObjAnnc):

	def __init__(self, dct:JSON=None, pi:str=None, create:bool=False) -> None:
		super().__init__(dct, pi, mgd=T.DVI, create=create)

