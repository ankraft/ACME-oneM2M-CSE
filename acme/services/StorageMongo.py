from typing import Callable, cast, List, Optional, Tuple

from pymongo import MongoClient
from pymongo import errors as MongoErrors

from ..etc.Types import ResourceTypes, Result, ResponseStatusCode, JSON
from ..etc import DateUtils, Utils
from ..services.Configuration import Configuration
from ..services import CSE
from ..resources.Resource import Resource
from ..resources import Factory
from ..services.Logging import Logging as L

class MongoBinding():
    __COL_RESOURCES = "resources"
    __COL_IDENTIFIERS = "identifiers"
    __COL_CHILDREN = "children"
    __COL_SRN = "srn"
    __COL_SUBSCRIPTIONS = "subscriptions"
    __COL_BATCHNOTIF = "batch_notifications"
    __COL_ACTIONS = "actions"
    __COL_REQUESTS = "requests"
    __COL_STATISTICS = "statistics"
    def __init__(self) -> None:
        L.isInfo and L.log("Initialize mongodb binding and create connection!")

        # Initiate connection to mongodb server
        # TODO: Add parameter to mongo host, port, DB name and auth
        # TODO: Connection pool; Actually it's already enabled on default
        # TODO: Check connection if successfully connected
        self._client = MongoClient("mongodb://username:password@127.0.0.1/acme-cse?authMechanism=PLAIN", 27017)
        self._db = self._client["acme-cse"]
        # TODO: Add locking to each collection access. Lock object are different for each collection
        self._setup_database()
        
    def stop_connection(self):
        L.log("Close MongoDB connection")
        self._client.close()
        
    # def _check_connection(self) -> bool:
    #     try:
    #         # The ping command is cheap and does not require auth.
    #         self._client.admin.command('ping')
    #         return True
    #     except ConnectionFailure:
    #         L.logErr("Server not available")
    #         return False
        
    #
    #   Resources
    #
    
    def insert_resource(self, resource: Resource) -> None:
        self._insert_one(self.__COL_RESOURCES, resource.dict)
        
    def upsert_resource(self, ri: str, resource: Resource) -> None:
        self._update_one(self.__COL_RESOURCES, ri, resource.dict, True)
        
    def update_resource(self, ri: str, resource: Resource) -> Resource:
        """ Update resource from a document
        By first removing field that have None value from the dictionary

        Args:
            ri (str): resource id of a document
            resource (Resource): new data of a resource

        Returns:
            Resource: updated resource
        """
        # remove nullified fields from db and resource
        for k in list(resource.dict):
            if resource.dict[k] is None:	# only remove the real None attributes, not those with 0
                del resource.dict[k]
        self._update_one(self.__COL_RESOURCES, ri, resource.dict, False)
        return resource

    def delete_resource(self, resource: Resource) -> None:
        self._delete_one(self.__COL_RESOURCES, resource.ri)
    
    def search_resource(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[dict]:

        pass

    def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[dict]:
        pass


    def hasResource(self, ri:Optional[str] = None, 
                            csi:Optional[str] = None, 
                            srn:Optional[str] = None,
                            ty:Optional[int] = None) -> bool:
        pass


    def countResources(self) -> int:
        pass


    def searchByFragment(self, dct:dict) -> list[dict]:
        """ Search and return all resources that match the given dictionary/document. """
        pass
    
    
    #
    #   Internal functions
    #
        
    def _setup_database(self):
        """ Setup mongo database by create acme-cse collection if not exist and add unique index of respective collection
        """
        L.isInfo and L.log("Setup acme-cse mongodb database")
        l_col = [self.__COL_RESOURCES, self.__COL_IDENTIFIERS, self.__COL_CHILDREN, self.__COL_SRN, self.__COL_SUBSCRIPTIONS, 
                           self.__COL_BATCHNOTIF, self.__COL_ACTIONS, self.__COL_REQUESTS]
        l_existing_collection = self._db.list_collection_names()
        all_exist = True
        
        # loop through acme-cse collection
        for col in l_col:
            # check if each acme-cse collection not exist then add unique index
            if col not in l_existing_collection:
                all_exist = False
                if col == self.__COL_SRN:
                    tmp = self._db[self.__COL_SRN]
                    tmp.create_index("srn", unique = True)
                elif col == self.__COL_REQUESTS:
                    tmp = self._db[self.__COL_REQUESTS]
                    tmp.create_index("ts", unique = True)
                else:
                    tmp = self._db[col]
                    tmp.create_index("ri", unique = True)

        if not all_exist:
            L.isInfo and L.log("One or more collections not exist and just created")
        
    def _insert_one(self, collection: str, data: dict) -> bool:
        try:
            col = self._db[collection]
            result = col.insert_one(data)
            L.isDebug and L.log(f'Success insert data: {result.inserted_id}')
            return True
        except MongoErrors.DuplicateKeyError as e:
            L.logErr("Failed insert data")
        except Exception:
            L.logErr(str(e))
        return False
            
    def _update_one(self, collection: str, ri: str, data: dict, upsert: bool = False) -> bool:
        # TODO: Add exception
        # TODO: Consider using update_one. But how to know the only specific field to update?
        col = self._db[collection]
        result = col.replace_one({'ri': ri}, data, upsert=upsert)
        return (result.modified_count == 1) or result.upserted_id
    
    def _delete_one(self, collection: str, ri: str) -> bool:
        # TODO: Add exception
        col = self._db[collection]
        result = col.delete_one({'ri': ri})
        return (result.deleted_count == 1)
            

if __name__ == "__main__":
    mongo = MongoBinding()
    print("done")
    mongo.stop_connection()
