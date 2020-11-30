#
#	MEMAnnc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	MEM : Announceable variant
#

from .MgmtObjAnnc import *
from Types import ResourceTypes as T
import Utils


class MEMAnnc(MgmtObjAnnc):

	def __init__(self, dct: dict = None, pi: str = None, create: bool = False) -> None:
		super().__init__(dct, pi, mgd=T.MEM, create=create)

