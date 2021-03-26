#
#	AEStatistics.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	An AE to store statistics about the CSE in a flexContainer.
#


from AEBase import *
from Logging import Logging
from Configuration import Configuration
import Statistics, CSE, Utils
# The following line incorrectly throws an error with mypy
from Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN
import threading, time
from Types import ResourceTypes as T



class AEStatistics(AEBase):



	def __init__(self) -> None:
		super().__init__(	rn=Configuration.get('app.statistics.aeRN'), 
							api=Configuration.get('app.statistics.aeAPI'), 
							originator=Configuration.get('app.statistics.originator'),
							nodeRN=Configuration.get('app.csenode.nodeRN'),					# From CSE-Node
							nodeID=Configuration.get('app.csenode.nodeID'),					# From CSE-Node
							nodeOriginator=Configuration.get('app.csenode.originator')		# From CSE-Node
						)

		self.fcsrn = self.srn + '/' + Configuration.get('app.statistics.fcntRN')
		self.fcntType = Configuration.get('app.statistics.fcntType')

		# Attribute definitions for the statistics specialization
		statisticAttributes =  {
			self.fcntType : {
				'rmRes'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'crRes'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'upRes'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htRet'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htCre'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htUpd'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htDel'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htSRt'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htSCr'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htSUp'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'htSDl'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'cseSU'	: ( BT.timestamp,		CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'lgErr'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'lgWrn'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'cseUT'	: ( BT.string,			CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'ctRes'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'exRes'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
				'notif'	: ( BT.nonNegInteger,	CAR.car01, RO.O, RO.O, RO.O, AN.OA ),
			}
		}

		# Add the definitions to the validator
		CSE.validator.updateAdditionalAttributes(statisticAttributes)


		# Create structure beneath the AE resource
		dct = { self.fcntType : {
				'rn'  : Configuration.get('app.statistics.fcntRN'),
					'cnd' : Configuration.get('app.statistics.fcntCND'),
					'mni' : 2,
					'aa' : ['rmRes', 'crRes', 'upRes', 'crRes', 'cseUT'],
				Statistics.deletedResources : 0,
				Statistics.createdResources : 0,
				Statistics.updatedResources : 0,
				Statistics.httpRetrieves : 0,
				Statistics.httpCreates : 0,
				Statistics.httpUpdates : 0,
				Statistics.httpDeletes : 0,
				Statistics.logErrors : 0,
				Statistics.logWarnings : 0,
				Statistics.cseStartUpTime : '',
				Statistics.cseUpTime : '',
				Statistics.resourceCount: 0
			}
		}
		# add announceTarget if target CSI is given
		if (rcsi:= Configuration.get('cse.registrar.csi')) is not None:
			Utils.setXPath(dct, f'{self.fcntType}/at', [rcsi])
		#Utils.setXPath(dct, f'{self.fcntType}/at', ['/id-in'])

		self.fc = self.retrieveCreate(	srn=self.fcsrn,
										data=dct,
										ty=T.FCNT)

		# Update the statistic resource from time to time
		self.startWorker(Configuration.get('app.statistics.interval'), self.statisticsWorker, 'statsAE')

		Logging.log('AEStatistics AE registered')


	def shutdown(self) -> None:
		super().shutdown()
		Logging.log('AEStatistics AE shut down')

	#########################################################################
	#
	#	Update statistics in a worker thread
	#

	def statisticsWorker(self) -> bool:
		Logging.logDebug('Updating statistics')

		# Update statistics
		if (stats := CSE.statistics.getStats()) is not None:
			self.updateResource(srn=self.fcsrn, data={ self.fcntType : stats })

		return True

