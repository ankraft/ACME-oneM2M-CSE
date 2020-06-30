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
import Statistics, CSE
# The following line incorrectly throws an error with mypy
from Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN 	# type: ignore
import threading, time


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
				'rmRes'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'crRes'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'upRes'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'htRet'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'htCre'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'htUpd'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'htDel'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'cseSU'	: [ BT.timestamp,		CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'lgErr'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'lgWrn'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'cseUT'	: [ BT.string,			CAR.car01, 	RO.O,	RO.O,  AN.OA ],
				'ctRes'	: [ BT.nonNegInteger,	CAR.car01, 	RO.O,	RO.O,  AN.OA ]
			}
		}

		# Add the definitions to the validator
		CSE.validator.addAdditionalAttributes(statisticAttributes)


		# Create structure beneath the AE resource
		self.fc = self.retrieveCreate(	srn=self.fcsrn,
										jsn={ self.fcntType : {
												'rn'  : Configuration.get('app.statistics.fcntRN'),
       											'cnd' : Configuration.get('app.statistics.fcntCND'),
       											'acpi': [ self.acpi ],	# assignde by CSE,
       											'mni' : 10,
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
										},
										ty=C.tFCNT)

		# Update the statistic resource from time to time
		self.startWorker(Configuration.get('app.statistics.intervall'), self.statisticsWorker, 'statisticsWorker')

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
		stats = CSE.statistics.getStats()
		self.updateResource(srn=self.fcsrn, jsn={ self.fcntType : stats })

		return True

