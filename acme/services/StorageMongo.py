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
        # TODO: Add transaction if possible when querying (with)
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
        """ Insert resource

        Args:
            resource (Resource): Data of the resource
        """
        self._insert_one(self.__COL_RESOURCES, resource.dict)
        
        
    def upsert_resource(self, ri: str, resource: Resource) -> None:
        """ Update resource if exist and insert if not exist

        Args:
            ri (str): Resource ri to update if exist
            resource (Resource): Data of the resource
        """
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
        """ Delete resource

        Args:
            resource (Resource): Target resource to delete
        """
        self._delete_one(self.__COL_RESOURCES, resource.ri)
    

    def search_resource(self, ri:Optional[str] = None, 
							  csi:Optional[str] = None, 
							  srn:Optional[str] = None, 
							  pi:Optional[str] = None, 
							  ty:Optional[int] = None, 
							  aei:Optional[str] = None) -> list[dict]:
        """ Search resource from hosting cse by using attribute as filter

        Args:
            ri (Optional[str], optional): ri of resource. Defaults to None.
            csi (Optional[str], optional): csi of CSE resource. Defaults to None.
            srn (Optional[str], optional): srn of resource. Defaults to None.
            pi (Optional[str], optional): pi of multiple resource. Defaults to None.
            ty (Optional[int], optional): ty of multiple resource. Defaults to None.
            aei (Optional[str], optional): aei of AE resource. Defaults to None.

        Returns:
            list[dict]: List of resource data
        """
        if not srn:
            if ri:
                # Limit resource to 1 because every resource should have unique ri
                return self._find(self.__COL_RESOURCES, {'ri': ri}, 1)
            elif csi:
                # Limit resource to 1 because every CSE should have unique csi
                return self._find(self.__COL_RESOURCES, {'csi': csi}, 1)
            elif aei:
                # Limit resource to 1 because every AE should have unique aei
                return self._find(self.__COL_RESOURCES, {'aei': aei}, 1)
            elif pi:
                # Format query, by adding ty field if exist
                query = {'pi': pi}
                if ty:
                    query['ty'] = ty
                    
                # Can have multiple value, so set limit to default
                return self._find(self.__COL_RESOURCES, query)
            elif ty:
                # Can have multiple value, so set limit to default
                return self._find(self.__COL_RESOURCES, {'ty': ty})
            
        else:
            # for SRN find the ri first from identifiers collection and then find resource using ri
            # TODO: Consider to find directly to resources collection
            if len(( identifiers := self._find(self.__COL_IDENTIFIERS, {'srn': srn}, 1) )) == 1:
                return self._find(self.__COL_RESOURCES, {'ri': identifiers[0]['ri']}, 1)
        

    def discoverResourcesByFilter(self, func:Callable[[JSON], bool]) -> list[dict]:
        pass


    def hasResource(self, ri:Optional[str] = None, 
                            csi:Optional[str] = None, 
                            srn:Optional[str] = None,
                            ty:Optional[int] = None) -> bool:
        """ Check if resource is exist by using attribute as filter

        Args:
            ri (Optional[str], optional): ri of the resource. Defaults to None.
            csi (Optional[str], optional): csi of the CSE resource. Defaults to None.
            srn (Optional[str], optional): srn of the resource. Defaults to None.
            ty (Optional[int], optional): ty to check if exist in hosting cse. Defaults to None.

        Returns:
            bool: True if resource is exist and vice versa
        """
        if not srn:
            if ri:
                # Limit document count result to 1 because only ri is unique
                return bool( self._count_documents(self.__COL_RESOURCES, {'ri': ri}, 1) )
            elif csi :
                # Limit document count result to 1 because only csi is unique
                return bool( self._count_documents(self.__COL_RESOURCES, {'csi': csi}, 1) )
            elif ty is not None:	# ty is an int
                # Limit is provided because hasResource only expect if resource with ty is exist
                return bool( self._count_documents(self.__COL_RESOURCES, {'ty': ty}, 1) )
        else:
            # TODO: Consider directly count srn from resources collection
            # for SRN find the ri first from identifiers collection and then find resource using ri
            if len(( identifiers := self._find(self.__COL_IDENTIFIERS, {'srn': srn}, 1) )) == 1:
                return bool( self._count_documents(self.__COL_RESOURCES, {'ri': identifiers[0]['ri']}, 1) )
        return False


    def countResources(self) -> int:
        """ Count how many resources in hosting CSE

        Returns:
            int: Total resources exist
        """
        return self._count_documents(self.__COL_RESOURCES, {})


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
        """ Insert resource to a collection

        Args:
            collection (str): Target collection to where it will inserted
            data (dict): data to insert (document)

        Returns:
            bool: Success insert or not
        """
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
        """ Update document from collection; It actually replace the whole document

        Args:
            collection (str): Target collection to update the document
            ri (str): ri of the resource to filter
            data (dict): data to update (changed attribute and not)
            upsert (bool, optional): Set to true if want to insert if ri is not found. Defaults to False.

        Returns:
            bool: Success update or upsert
        """
        # TODO: Add exception
        # TODO: Consider using update_one. But how to know the only specific field to update?
        col = self._db[collection]
        result = col.replace_one({'ri': ri}, data, upsert=upsert)
        return (result.modified_count == 1) or result.upserted_id
    
    def _delete_one(self, collection: str, ri: str) -> bool:
        """ Delete a document from collection

        Args:
            collection (str): Target collection to find the document
            ri (str): ri field of the document to delete

        Returns:
            bool: success or not deleting document; False might be because document is not found
        """
        # TODO: Add exception
        col = self._db[collection]
        result = col.delete_one({'ri': ri})
        return (result.deleted_count == 1)
    
    def _find(self, collection: str, query: dict, limit: int = 0) -> list[dict]:
        """ Find document on a collection

        Args:
            collection (str): Target collection to find
            query (dict): Filter of the search
            limit (int, optional): Limit of how many documents as a result. Defaults to 0 will make it unlimited

        Returns:
            list[dict]: List of documents found
        """
        # TODO: Add exception
        col = self._db[collection]
        result = col.find(filter = query, limit = limit)
        return [x for x in result]
    
    def _count_documents(self, collection: str, query: dict, limit: int = 0) -> int:
        """ Count how many document/s found on a collection

        Args:
            collection (str): Target collection to search
            query (dict): Filter of the search
            limit (int, optional): Limit of how many document to search for. Don't set limit don't want to limit count. Defaults to 0.

        Returns:
            int: Total documents found
        """
        # TODO: Add exception
        col = self._db[collection]
        result = None
        if limit > 0:
            result = col.find(filter = query, limit = limit)
        else:
            result = col.find(filter = query)
        return result
            

if __name__ == "__main__":
    mongo = MongoBinding()
    print("done")
    mongo.stop_connection()
