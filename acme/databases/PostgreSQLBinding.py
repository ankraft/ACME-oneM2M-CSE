#
#	PostgreSQLBinding.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Database Binding for PostgreSQL
#
"""	This module provides the database binding for PostgreSQL. It implements the
	DBBinding interface and provides the necessary functions to interact with a
	PostgreSQL database. The module uses the psycopg2 library to connect to the
	database and execute SQL queries.
"""

from __future__ import annotations
from typing import Optional, Callable, Sequence, Any, Tuple

from psycopg2 import connect, Error
from psycopg2.extras import Json as PsyJson
from psycopg2.extensions import cursor as PsyCursor, connection as PsyConnection

from .DBBinding import DBBinding
from ..etc.Constants import Constants as C
from ..etc.Types import JSON, ResourceTypes
from ..etc.ResponseStatusCodes import INTERNAL_SERVER_ERROR
from ..runtime.Logging import Logging as L


# TODO Add error handling ansd exceptions to fetch methods?

class PostgreSQLBinding(DBBinding):
	"""	PostgreSQLBinding class.
	"""
	
	tableActions = 'actions'
	"""	The name of the table for actions. """

	tableBatchNotifications = 'batchNotifications'
	"""	The name of the table for batch notifications. """

	tableChildResources = 'childResources'
	"""	The name of the table for child resource mappings. """

	tableIdentidiers = 'identifiers'
	"""	The name of the table for identifier mappings. """

	tableRequests = 'requests'
	"""	The name of the table to store requests and responses. """

	tableResources = 'resources'
	"""	The name of the table for resources. """

	tableSchedules = 'schedules'
	"""	The name of the table for schedules. """

	tableStatistics = 'statistics'
	"""	The name of the table for statistic information. """

	tableSubscriptions = 'subscriptions'
	"""	The name of the table for subscription mappings. """


	def __init__(self,	dbHost:str, 
			  			dbPort:int,
						dbUser:str,
						dbPassword:str,
						dbDatabase:str,
						dbSchema:str) -> None:
		"""	Initialize the PostgreSQLBinding object.

			Args:
				dbHost: The hostname of the database server.
				dbPort: The port of the database server.
				dbUser: The username to connect to the database.
				dbPassword: The password to connect to the database.
				dbDatabase: The name of the database to connect to.
				dbSchema: The schema to use in the database.
		"""
		super().__init__()
	
		# Store the connection parameters
		self.dbHost = dbHost
		"""	The hostname of the database server. """
		
		self.dbPort = dbPort
		"""	The port of the database server. """

		self.dbUser = dbUser
		"""	The username to connect to the database. """

		self.dbPassword = dbPassword
		"""	The password to connect to the database. """

		self.dbDatabase = dbDatabase
		"""	The name of the database to connect to. """

		self.dbSchema = dbSchema
		"""	The schema to use in the database. """

		self.dbConnection:Optional[PsyConnection] = None
		"""	The database connection object. """

		# Connect to the database
		self._checkOpenConnection()

		# Create and upgrade the tables if necessary
		self.createTables()
		self.upgradeTables()
	

	def closeDB(self) -> None:
		if self.dbConnection is not None:
			# L.isDebug and L.logDebug('Closing database connection')
			self.dbConnection.close()
			self.dbConnection = None


	def purgeDB(self) -> None:
		# L.isDebug and L.logDebug('Purging database')
		with self.dbConnection.cursor() as cursor:
			cursor.execute(f'''
				TRUNCATE TABLE {self.tableActions};
				TRUNCATE TABLE {self.tableBatchNotifications};
				TRUNCATE TABLE {self.tableChildResources};
				TRUNCATE TABLE {self.tableIdentidiers};
				TRUNCATE TABLE {self.tableRequests};
				TRUNCATE TABLE {self.tableResources};
				TRUNCATE TABLE {self.tableSchedules};
				TRUNCATE TABLE {self.tableStatistics};
				TRUNCATE TABLE {self.tableSubscriptions};
			''')
	

	def backupDB(self, dir:str) -> bool:
		# L.isDebug and L.logDebug(f'Database backup is not supported for PostgreSQL. Skipping.')
		return True


	###########################################################################


	def createTables(self) -> None:
		"""	Create the necessary schema and tables if they do not exist.
		"""

		# L.isDebug and L.logDebug('Creating database tables')
		
		with self.dbConnection.cursor() as cursor:

			# Create the schema
			cursor.execute(f'''
				CREATE SCHEMA IF NOT EXISTS {self.dbSchema}
			''')

			# Create the resources table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableResources} (
					ri TEXT PRIMARY KEY,
					resource JSONB NOT NULL
				)
			''')

			# Create the identifier table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableIdentidiers} (
					ri TEXT PRIMARY KEY,
					rn TEXT NOT NULL,
					srn TEXT NOT NULL UNIQUE,	-- automatic index
					ty INTEGER NOT NULL
				)
			''')

			# Create the childResources table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableChildResources} (
					id SERIAL PRIMARY KEY,
					pi TEXT NOT NULL,
					childRi TEXT NOT NULL UNIQUE,	-- automatic index
					childTy INTEGER NOT NULL
				);
			''')

   			# Create the statistics table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableStatistics} (
					id SERIAL PRIMARY KEY,
					statistics JSONB NOT NULL
				);
			''')

			# Create the subscriptions table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableSubscriptions} (
					ri TEXT PRIMARY KEY,
					subscription JSONB NOT NULL
				)
			''')

			# Create the actions table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableActions} (
					ri TEXT PRIMARY KEY,
					action JSONB NOT NULL
				)
			''')

			# Create the batchNotifications table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableBatchNotifications} (
					id SERIAL PRIMARY KEY,
					batch JSONB NOT NULL
				)
			''')

			# Create the schedules table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableSchedules} (
					ri TEXT PRIMARY KEY,
					schedule JSONB NOT NULL
				)
			''')

			# Create the requests table
			cursor.execute(f'''
				CREATE TABLE IF NOT EXISTS {self.tableRequests} (
					ts text PRIMARY KEY,
					request JSONB NOT NULL
				)
			''')

	
	def upgradeTables(self) -> None:
		"""	Upgrade the tables if necessary.
		"""
		pass


	def prepareStatements(self) -> None:
		"""	Prepare the PreparedStatements for various SQL operations. 
		
			This method is called after the database connection is established and
			the tables are created. It prepares the SQL statements for the various
			operations that can be performed on the database. This includes inserting,
			updating, and deleting resources, identifiers, child resources, and
			subscriptions.

			Note that prepared statements are only usable within the same connection.
			Therefore, this method should be called after the connection is established.
		"""
		# L.isDebug and L.logDebug('Preparing SQL statements')
		with self.dbConnection.cursor() as cur:

			# Prepare resource operations
   
			cur.execute(f'''
				PREPARE insertResource AS
					INSERT INTO {self.tableResources} (ri, resource) VALUES ($1, $2);
				PREPARE upsertResource AS
					INSERT INTO {self.tableResources} (ri, resource) VALUES ($1, $2)
					ON CONFLICT (ri) DO 
						UPDATE SET resource = jsonb_strip_nulls({self.tableResources}.resource || $3);
				PREPARE updateResource AS
					UPDATE {self.tableResources} 
					SET resource = jsonb_strip_nulls({self.tableResources}.resource || $1)
					WHERE ri = $2;

				PREPARE getResources AS
					SELECT resource FROM {self.tableResources};
				PREPARE getResourceByRI AS
					SELECT resource FROM {self.tableResources} 
					WHERE ri = $1;
				PREPARE getResourceByAEI AS
					SELECT resource FROM {self.tableResources} 
					WHERE resource->>'aei' = $1;
				PREPARE getResourceByCSI AS
					SELECT resource FROM {self.tableResources} 
					WHERE resource->>'csi' = $1;
				PREPARE getResourcesByPI AS
					SELECT resource FROM {self.tableResources} 
					WHERE resource->>'pi' = $1;
				PREPARE getResourcesByTY AS
					SELECT resource FROM {self.tableResources} 
					WHERE resource->>'ty' = $1;
				PREPARE getResourcesByPIandTY AS
					SELECT resource FROM {self.tableResources} 
					WHERE resource->>'pi' = $1 AND resource->>'ty' = $2;

				PREPARE countResources AS
					SELECT COUNT(*) FROM {self.tableResources};
				PREPARE countResourcesByRI AS
					SELECT COUNT(*) FROM {self.tableResources} 
					WHERE ri = $1;
				PREPARE countResourcesByTY AS
					SELECT COUNT(*) FROM {self.tableResources} 
					WHERE resource->>'ty' = $1;

				PREPARE deleteResourceByRI AS
					DELETE FROM {self.tableResources} WHERE ri = $1;
			''')

			# Prepare identifier and childResource operations
   
			cur.execute(f'''
			   	PREPARE insertIdentifier AS
					INSERT INTO {self.tableIdentidiers} (ri, rn, srn, ty) VALUES ($1, $2, $3, $4);
				PREPARE getIdentifierBySRN AS
					SELECT ri, srn FROM {self.tableIdentidiers} 
					WHERE srn = $1;
				PREPARE getIdentifierByRI AS
					SELECT ri, srn FROM {self.tableIdentidiers} 
					WHERE ri = $1;
				PREPARE deleteIdentifier AS
					DELETE FROM {self.tableIdentidiers} 
					WHERE ri = $1;

				PREPARE insertChildResource AS
					INSERT into {self.tableChildResources} (pi, childRi, childTy) VALUES ($1, $2, $3);
				PREPARE getChildResourcesByPI AS
					SELECT childRi, childTy FROM {self.tableChildResources} 
					WHERE pi = $1;
				PREPARE deleteChildResource AS
					DELETE FROM {self.tableChildResources} 
					WHERE pi = $1 AND childRi = $2;
			''')

			# Prepare subscription operations
   
			cur.execute(f'''
			   PREPARE upsertSubscription AS
	   				INSERT INTO {self.tableSubscriptions} (ri, subscription) VALUES ($1, $2)
					ON CONFLICT (ri) DO 
					UPDATE SET subscription = {self.tableSubscriptions}.subscription || $3;
			   PREPARE getSubscriptionByRI AS
					SELECT subscription FROM {self.tableSubscriptions} 
					WHERE ri = $1;
				PREPARE getSubscriptionByPI AS
					SELECT subscription FROM {self.tableSubscriptions} 
					WHERE subscription->>'pi' = $1;
				PREPARE deleteSubscription AS
					DELETE FROM {self.tableSubscriptions} 
					WHERE ri = $1;
			''')

			# Prepare batchNotification operations
   
			cur.execute(f'''
				PREPARE insertBatchNotification AS
					INSERT INTO {self.tableBatchNotifications} (batch) VALUES ($1);
				PREPARE countBatchNotifications AS
					SELECT COUNT(*) FROM {self.tableBatchNotifications} 
					WHERE batch->>'ri' = $1 AND batch->>'nu' = $2;
				PREPARE getBatchNotifications AS
					SELECT batch FROM {self.tableBatchNotifications} 
					WHERE batch->>'ri' = $1 AND batch->>'nu' = $2;
				PREPARE deleteBatchNotification AS
					DELETE FROM {self.tableBatchNotifications} 
					WHERE batch->>'ri' = $1 AND batch->>'nu' = $2;
			''')

			# Prepare statistics operations
   
			cur.execute(f'''
				PREPARE getStatistics AS
					SELECT statistics FROM {self.tableStatistics} 
					WHERE id = 1;
				PREPARE upsertStatistics AS
					INSERT INTO {self.tableStatistics} (id, statistics) VALUES (1, $1)
					ON CONFLICT (id) DO 
					UPDATE SET statistics = jsonb_strip_nulls({self.tableStatistics}.statistics || $2);
				PREPARE deleteStatistics AS
					DELETE FROM {self.tableStatistics};
			''')

			# Prepare action operations
   
			cur.execute(f'''
				PREPARE getActions AS
	   				SELECT action FROM {self.tableActions};
				PREPARE getActionByRI AS
					SELECT action FROM {self.tableActions} 
					WHERE ri = $1;
				PREPARE getActionBySubject AS
					SELECT action FROM {self.tableActions}
					WHERE action->>'subject' = $1;

				PREPARE upsertAction AS
					INSERT INTO {self.tableActions} (ri, action) VALUES ($1, $2)
					ON CONFLICT (ri) DO
					UPDATE SET action = {self.tableActions}.action || $3;
				PREPARE updateAction AS
					UPDATE {self.tableActions} 
					SET action = {self.tableActions}.action || $1
					WHERE ri = $2;

				PREPARE deleteAction AS
					DELETE FROM {self.tableActions}
					WHERE ri = $1;
			''')

			# Prepare request operations
   
			cur.execute(f'''
			   PREPARE getRequestsByRI AS
					SELECT request FROM {self.tableRequests} 
					WHERE request->>'ri' = $1;
				PREPARE getRequests AS
					SELECT request FROM {self.tableRequests};

				PREPARE insertRequest AS
					INSERT INTO {self.tableRequests} (ts, request) VALUES ($1, $2);
				PREPARE selectMaxRequests AS
					SELECT ts FROM {self.tableRequests} 
					ORDER BY ts DESC OFFSET $1;
				
				PREPARE deleteOldRequests AS
					DELETE FROM {self.tableRequests} 
					WHERE ts <= $1;
				PREPARE deleteRequestsByRI AS
					DELETE FROM {self.tableRequests}
					WHERE request->>'ri' = $1;
				PREPARE deleteRequests AS
					DELETE FROM {self.tableRequests};
			''')

			# Prepare schedule operations
   
			cur.execute(f'''
				PREPARE getSchedules AS
					SELECT schedule FROM {self.tableSchedules};
				PREPARE getScheduleByRI AS
					SELECT schedule FROM {self.tableSchedules} 
					WHERE ri = $1;
				PREPARE getSchedulesForParent AS
					SELECT schedule FROM {self.tableSchedules}
					 WHERE schedule->>'pi' = $1;
				
				PREPARE upsertSchedule AS
					INSERT INTO {self.tableSchedules} (ri, schedule) VALUES ($1, $2)
					ON CONFLICT (ri) DO 
					UPDATE SET schedule = {self.tableSchedules}.schedule || $3;

				PREPARE deleteSchedule AS
					DELETE FROM {self.tableSchedules}
					 WHERE ri = $1;
			''')

	
	def _checkOpenConnection(self) -> None:
		"""	Check if the database connection is open.

			Try to reconnect if the connection is closed.

		"""
		if not self.dbConnection or self.dbConnection.closed:
			try:
				# L.isDebug and L.logDebug('Reconnecting to database')
				self.dbConnection = connect(
					database = self.dbDatabase,
					user = self.dbUser,
					password = self.dbPassword,
					host = self.dbHost,
					port = self.dbPort,
					options = f'-c search_path={self.dbSchema}'	# schema path
				)
				self.dbConnection.autocommit = True
				# L.isDebug and L.logDebug(f'Reconnected to database: {self.dbConnection}')
			except Error:
				L.logErr(f'Error reconnecting to postgreSQL database at {self.dbHost}:{self.dbPort} as "{self.dbUser}" with database "{self.dbDatabase}"')
				raise

			# Prepare the statements (again)
			self.prepareStatements()


	def _executePrepared(self, statement:str, args:Tuple, closure:Optional[Callable] = None) -> Any:
		"""	Execute a prepared statement.

			This is the main method to execute a prepared statement. It will execute the statement
			with the given arguments and return the result of the closure, if one is provided.

			Almost all database operations are done through this method.


			Args:
				statement: The name of the prepared statement to execute and its parameters.
				args: The arguments to pass to the prepared statement. This must be a tuple.
				closure: An optional closure callback to process the result of the query. This closure will be
							passed the cursor object and should return the result of the query.

			Return:
				The result of the closure, if one is provided, or True if no closure is provided.
		"""
		try:
			self._checkOpenConnection()

			with self.dbConnection.cursor() as cursor:
				cursor.execute(f'EXECUTE {statement}', args)
				if closure:
					return closure(cursor)
				return True
		except Exception as e:
			raise INTERNAL_SERVER_ERROR(dbg = L.logErr(f'Error executing prepared statement: {e}'))


	def _fetchSingleRow(self, cursor:PsyCursor, asList:bool = True) -> Any|list[Any]:
		"""	Fetch the first element from the first row from the database cursor.

			Args:
				cursor: The database cursor to fetch the row from.
				asList: Whether to return the row as a list or not.

			Return:
				The fetched row as a single object or in a list, or None or an empty list if no row was fetched.
		"""
		if cursor.rowcount > 0:
			row = cursor.fetchone()[0]
			return [ row ] if asList else row
		return [] if asList else None
	
	
	def _fetchAllRows(self, cursor:PsyCursor) -> list[JSON]:
		"""	Fetch the first elements from all rows from the database cursor.

			Args:
				cursor: The database cursor to fetch the rows from.
			
			Return:
				The fetched rows, or an empty list if no rows were fetched.
		"""
		return [ r[0] for r in cursor ]
	

	def _fetchNumber(self, cursor:PsyCursor) -> int:
		"""	Fetch one number from the database cursor.

			Args:
				cursor: The database cursor to fetch the number from.

			Return:
				The fetched number, or None if no number was fetched.
		"""
		if cursor.rowcount > 0:
			return int(cursor.fetchone()[0])
		return None

	#
	#	Resource operations
	#

	def insertResource(self, resource:JSON, ri:str) -> None:
		# L.isDebug and L.logDebug(f'Inserting resource {ri} into database: {resource}')
		self._executePrepared('insertResource (%s, %s)', (ri, PsyJson(resource)))


	def upsertResource(self, resource:JSON, ri:str) -> None:
		# L.isDebug and L.logDebug(f'Upserting resource {ri} into database: {resource}')
		_resource = PsyJson(resource)
		self._executePrepared('upsertResource (%s, %s, %s)', (ri, _resource, _resource))


	def updateResource(self, resource:JSON, ri:str) -> JSON:
		# L.isDebug and L.logDebug(f'Updating resource {ri} in database: {resource}')

		# First save complex attributes that may contain attributes with NULL values themselves 
		# that must be preserved.
		# The prepared statement calls jsonb_strip_nulls to remove NULL values from the resource
		# and this removes NULL values in complex attributes as well, which is not what we want.
		_savedAttributes = { a: resource[a] for a in (C.attrModified,) if a in resource }
		L.isDebug and L.logDebug(f'Saving attributes: {_savedAttributes}')

		# Update first
		self._executePrepared('updateResource (%s, %s)', (PsyJson(resource), ri))
	
		# Get the updated resource
		result = self._executePrepared('getResourceByRI (%s)', (ri,), 
									   lambda c: self._fetchSingleRow(c, False))
		
		# Restore the saved attributes
		for k, v in _savedAttributes.items():
			result[k] = v

		# Finally return the updated resource
		return result
	

	def deleteResource(self, ri:str) -> None:
		# L.isDebug and L.logDebug(f'Deleting resource {ri} from database')
		self._executePrepared('deleteResourceByRI (%s)',(ri,))
	

	def searchResources(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[JSON]:
		# L.isDebug and L.logDebug(f'Searching for resources: ri={ri}, csi={csi}, srn={srn}, pi={pi}, ty={ty}, aei={aei}')
		if not srn:
			if ri:
				return self._executePrepared('getResourceByRI (%s)', (ri,), 
											 lambda c: self._fetchSingleRow(c))
			elif csi:
				return self._executePrepared('getResourceByCSI (%s)', (csi,), 
											 lambda c: self._fetchSingleRow(c))
			elif pi:
				if ty is not None:	# ty is an int
					return self._executePrepared('getResourcesByPIandTY (%s, %s)', (pi, str(ty)), 
												 lambda c: self._fetchAllRows(c))
				else:
					return self._executePrepared('getResourcesByPI (%s)', (pi,), 
												 lambda c: self._fetchAllRows(c))
			elif ty is not None:	# ty is an int
				return self._executePrepared('getResourcesByTY (%s)', (str(ty),), 
											 lambda c: self._fetchAllRows(c))
			elif aei:
				return self._executePrepared('getResourceByAEI (%s)', (aei,), 
											 lambda c: self._fetchAllRows(c))
		else:
			# for SRN find the ri first and then try again recursively (outside the lock!!)
			if len((identifiers := self.searchIdentifiers(srn = srn))) == 1:
				return self.searchResources(ri = identifiers[0]['ri'])

		return []
	

	def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[JSON]:
		# L.isDebug and L.logDebug(f'Discovering resources by filter')
		return self._executePrepared('getResources', (), 
									 lambda c: [ r[0] for r in c if func(r[0]) ])
			

	def hasResource(self, ri:Optional[str] = None, 
						  srn:Optional[str] = None,
						  ty:Optional[int] = None) -> bool:
		# L.isDebug and L.logDebug(f'hasResource: ri={ri}, srn={srn}, ty={ty}')
		if srn:
			# find the ri first and then try again recursively
			if len((identifiers := self.searchIdentifiers(srn = srn))) == 1:
				return self.hasResource(ri = identifiers[0]['ri'])
		else:
			if ri:
				# This returns the number (int) of rows found
				return self._executePrepared('countResourcesByRI (%s)', (ri,), 
											  lambda c: self._fetchNumber(c)) > 0
			elif ty is not None:	# ty is an int
				# This returns the number (int) of rows found
				return self._executePrepared('countResourcesByTY (%s)', (str(ty),), 
											 lambda c: self._fetchNumber(c)) > 0
		return False


	def countResources(self) -> int:
		# L.isDebug and L.logDebug('Counting resources')
		# This returns the number (int) of rows found
		return self._executePrepared('countResources', (), 
									 lambda c: self._fetchNumber(c))


	def searchByFragment(self, dct:dict) -> list[JSON]:
		# L.isDebug and L.logDebug(f'Searching by fragment: {dct}')
		where:list[str] = []
		args:Tuple[str, ...] = ()
		for k, v in dct.items():
			where.append(f"resource->>'{k}' = %s")
			args += (str(v),)

		try:
			with self.dbConnection.cursor() as cursor:
				cursor.execute(f'SELECT resource FROM {self.tableResources} WHERE {" AND ".join(where)}',
							   args)	# Cannot be a prepared statement. It is constructued dynamically
				return self._fetchAllRows(cursor)
		except Exception as e:
			raise INTERNAL_SERVER_ERROR(dbg = L.logErr(f'Error searching by fragment: {e}'))

	#
	#	Identifiers, Structured RI, Child Resources operations
	#

	def upsertIdentifier(self, identifierMapping:JSON, structuredPathMapping:JSON, ri:str, srn:str) -> None:
		# L.isDebug and L.logDebug(f'Upserting identifier {identifierMapping} and structured path {structuredPathMapping} for resource {ri}')
		self._executePrepared('insertIdentifier (%s, %s, %s, %s)', (ri, identifierMapping['rn'], srn, identifierMapping['ty']))


	def deleteIdentifier(self, ri:str, srn:str) -> None:
		# L.isDebug and L.logDebug(f'Deleting identifier for resource {ri} and structured path {srn}')
		self._executePrepared('deleteIdentifier (%s)', (ri,))


	def searchIdentifiers(self, ri:Optional[str] = None, 
								srn:Optional[str] = None) -> list[JSON]:
		# L.isDebug and L.logDebug(f'searchIdentifiers: ri={ri}, srn={srn}')
  
		def _cl(cursor:PsyCursor) -> list[JSON]:
			if cursor.rowcount > 0:
				_row = cursor.fetchone()
				return [ { 'ri': _row[0], 'srn': _row[1] } ]
			return []
		
		if srn:
			return self._executePrepared('getIdentifierBySRN (%s)', (srn,),
								 		 _cl)
		elif ri:
			return self._executePrepared('getIdentifierByRI (%s)', (ri,),
										 _cl)
		else:
			raise ValueError('Either ri or srn must be given')
		

	def upsertChildResource(self, childResource:JSON, ri:str) -> None:
		# L.isDebug and L.logDebug(f'Upserting child resource {childResource} for resource {ri}')
  		# Add a record to the childResources table for this resource
		self._executePrepared('insertChildResource (%s, %s, %s)', (childResource['pi'], childResource['ri'], childResource['ty']))

			
	def removeChildResource(self, ri:str, pi:str) -> None:
		# L.isDebug and L.logDebug(f'Removing child resource {ri} from parent resource {pi}')
		# Remove the record from the childResources table
		self._executePrepared('deleteChildResource (%s, %s)', (pi, ri))


	def searchChildResourceIDsByParentRIAndType(self, pi:str, ty:Optional[ResourceTypes|list[ResourceTypes]] = None) -> list[str]:
		# L.isDebug and L.logDebug(f'Searching child resources for parent resource {pi} and type {ty}')

		if isinstance(ty, int):
			ty = [ty]

		def _cl(cursor:PsyCursor) -> list[str]:
			if cursor.rowcount > 0:
				return [ c[0] 
						 for c in cursor 
						 if ty is None or c[1] in ty ]
			return []

		return self._executePrepared('getChildResourcesByPI (%s)', (pi,), 
									 _cl)

	#
	#	Subscription operations
	#

	def searchSubscriptionReprs(self, ri:Optional[str] = None, 
								  pi:Optional[str] = None) -> Optional[list[JSON]]:
		# L.isDebug and L.logDebug(f'Searching for subscription representations: ri={ri}, pi={pi}')
		if ri:
			return self._executePrepared('getSubscriptionByRI (%s)', (ri,),
										 lambda c: self._fetchAllRows(c))
		elif pi:
			return self._executePrepared('getSubscriptionByPI (%s)', (pi,),
										 lambda c: self._fetchAllRows(c))
		return None


	def upsertSubscriptionRepr(self, subscription:JSON, ri:str) -> bool:
		# L.isDebug and L.logDebug(f'Upserting subscription representation {subscription} for resource {ri}')
		_subscription = PsyJson(subscription)
		return self._executePrepared('upsertSubscription (%s, %s, %s)', (ri, _subscription, _subscription))
		

	def removeSubscriptionRepr(self, ri:str) -> bool:
		# L.isDebug and L.logDebug(f'Removing subscription representation for resource {ri}')
		return self._executePrepared('deleteSubscription (%s)', (ri,))

	#
	#	BatchNotification operations
	#

	def addBatchNotification(self, batchRecord:JSON) -> bool:
		# L.isDebug and L.logDebug(f'Adding batch notification: {batchRecord}')
		return self._executePrepared('insertBatchNotification (%s)', (PsyJson(batchRecord),))


	def countBatchNotifications(self, ri:str, nu:str) -> int:
		# L.isDebug and L.logDebug(f'Counting batch notifications for resource {ri} and notification URI {nu}')
		return self._executePrepared('countBatchNotifications (%s, %s)', (ri, nu), 
									 lambda c: self._fetchNumber(c))


	def getBatchNotifications(self, ri:str, nu:str) -> list[JSON]:
		# L.isDebug and L.logDebug(f'Getting batch notifications for resource {ri} and notification URI {nu}')
		return self._executePrepared('getBatchNotifications (%s, %s)', (ri, nu), 
									 lambda c: self._fetchAllRows(c))


	def removeBatchNotifications(self, ri:str, nu:str) -> bool:
		# L.isDebug and L.logDebug(f'Removing batch notifications for resource {ri} and notification URI {nu}')
		return self._executePrepared('deleteBatchNotification (%s, %s)', (ri, nu))

	#
	#	Statistic operations
	#

	def searchStatistics(self) -> JSON:
		# L.isDebug and L.logDebug('Searching for statistics')

		def _cl(cursor:PsyCursor) -> JSON:
			if not (_s := self._fetchSingleRow(cursor, False)):
				return {}
			return _s	# type: ignore[return-value]
		
		return self._executePrepared('getStatistics', (), 
									 _cl)


	def upsertStatistics(self, stats:JSON) -> bool:
		# L.isDebug and L.logDebug(f'Upserting statistics into database: {stats}')
		_stats = PsyJson(stats)
		return self._executePrepared('upsertStatistics (%s, %s)', (_stats, _stats))


	def purgeStatistics(self) -> None:
		L.isDebug and L.logDebug('Purging statistics')
		self._executePrepared('deleteStatistics', ())

	#
	#	Action operations
	#

	def getAllActionReprs(self) -> list[JSON]:
		# L.isDebug and L.logDebug('Getting all action representations from database')
		return self._executePrepared('getActions', (), 
									 lambda c: self._fetchAllRows(c))
		

	def getActionRep(self, ri:str) -> Optional[JSON]:
		# L.isDebug and L.logDebug(f'Getting action representation {ri} from database')
		return self._executePrepared('getActionByRI (%s)', (ri,),
									 lambda c: self._fetchSingleRow(c, False))
							   	

	def searchActionsReprsForSubject(self, subjectRi:str) -> Sequence[JSON]:
		# L.isDebug and L.logDebug(f'Searching for action representations for subject {subjectRi}')
		return self._executePrepared('getActionBySubject (%s)', (subjectRi,),
									 lambda c: self._fetchAllRows(c))


	def upsertActionRepr(self, actionRepr:JSON, ri:str) -> bool:
		# L.isDebug and L.logDebug(f'Upserting action representation {ri} into database: {actionRepr}')
		_actionRepr = PsyJson(actionRepr)
		return self._executePrepared('upsertAction (%s, %s, %s)', (ri, _actionRepr, _actionRepr))


	def updateActionRepr(self, actionRepr:JSON) -> bool:
		# L.isDebug and L.logDebug(f'Updating action representation in database: {actionRepr}')
		return self._executePrepared('updateAction (%s, %s)', (PsyJson(actionRepr), actionRepr['ri']))


	def removeActionRepr(self, ri:str) -> bool:
		# L.isDebug and L.logDebug(f'Removing action representation {ri} from database')
		return self._executePrepared('deleteAction (%s)', (ri,))

	#
	#	Request operations
	#

	def insertRequest(self, req:JSON, ts:float) -> bool:
		# L.isDebug and L.logDebug(f'Inserting request/response for ts: {ts}')
		return self._executePrepared('insertRequest (%s, %s)', (ts, PsyJson(req)))

	
	def removeOldRequests(self, maxRequests:int) -> None:
		# L.isDebug and L.logDebug(f'Removing old requests from the database')
		def _cl(cursor:PsyCursor) -> None:
			if cursor.rowcount > 0:
				_ts = cursor.fetchone()[0]
				cursor.execute(f'EXECUTE deleteOldRequests (%s)', (_ts,))

		self._executePrepared('selectMaxRequests (%s)', (maxRequests,), 
							  _cl)


	def getRequests(self, ri:Optional[str] = None) -> list[JSON]:
		# L.isDebug and L.logDebug(f'Getting requests for resource {ri}')
		if ri:
			return self._executePrepared('getRequestsByRI (%s)', (ri,),
										 lambda c: self._fetchAllRows(c))
		else:
			return self._executePrepared('getRequests', (),
										 lambda c: self._fetchAllRows(c))


	def deleteRequests(self, ri:Optional[str] = None) -> None:
		# L.isDebug and L.logDebug(f'Deleting requests for resource {ri}')
		if ri:
			self._executePrepared('deleteRequestsByRI (%s)', (ri,))
		else:
			self._executePrepared('deleteRequests', ())

	#
	#	Schedule operations
	#

	def getSchedules(self) -> list[JSON]:
		# L.isDebug and L.logDebug('Getting all schedules from database')
		return self._executePrepared('getSchedules', (),
									 lambda c: self._fetchAllRows(c))


	def getSchedule(self, ri:str) -> Optional[JSON]:
		# L.isDebug and L.logDebug(f'Getting schedule {ri} from database')
		return self._executePrepared('getScheduleByRI (%s)', (ri,),
									 lambda c: self._fetchSingleRow(c, False))
	

	def searchSchedulesForParent(self, pi:str) -> list[JSON]:
		# L.isDebug and L.logDebug(f'Searching for schedules for parent resource {pi}')
		return self._executePrepared('getSchedulesForParent (%s)', (pi,),
									 lambda c: self._fetchAllRows(c))
	

	def upsertSchedule(self, schedule:JSON, ri:str) -> bool:
		# L.isDebug and L.logDebug(f'Upserting schedule {ri} into database: {schedule}')
		_schedule = PsyJson(schedule)
		return self._executePrepared('upsertSchedule (%s, %s, %s)', (ri, _schedule, _schedule))


	def removeSchedule(self, ri:str) -> bool:
		# L.isDebug and L.logDebug(f'Removing schedule {ri} from database')
		return self._executePrepared('deleteSchedule (%s)', (ri,))
