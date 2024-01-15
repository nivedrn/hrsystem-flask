from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models.manageDB import createDB, dropDB

class DatabaseConnect():
    dbURI = ""
    session = None
    engine = None
    conn = None
    
    def __init__(self, dbURI):
        self.dbURI = dbURI

    def initiateEngine(self):        
        try:
            self.engine = create_engine(self.dbURI, echo=True)
            return self.engine
        except Exception as e:
            print(e)
            return None

    def initiateConnection(self):        
        if self.engine == None:
            self.conn = self.initiateEngine().connect()
        else:
            self.conn = self.engine.connect()
        return self.conn

    def initiateSession(self):   
        if self.session == None:     
            if self.engine == None:
                Session = sessionmaker(bind=self.initiateEngine())
            else:
                Session = sessionmaker(bind=self.engine)
            
            self.session = Session()
        return self.session
    
    def closeSession(self, session):
        if session != None:
            session.close()

    def commitSession(self, session, autoClose = True):
        commitStatus = "INITIATED"
        if session == None:
            session = self.initiateSession()        
        try: 
            session.commit() 
            commitStatus = "SUCCESS"
        except Exception as err:
            session.rollback()
            print("ERROR_ROLLBACK :", str(err))
            if "duplicate key" in str(err):
                commitStatus = "DUPLICATE_KEY"
            else:
                commitStatus = "ERROR_ROLLBACK : ON DBCOMMIT" 
        finally: 
            if autoClose:
                self.closeSession(session)  
        return commitStatus          

    def fetchData(self, queryTable, queryFields, queryParams, queryLimit):        
        if queryTable != None:
            sql = "SELECT " 
            sql += (queryFields if queryFields != None else "*" ) 
            sql += " FROM " + queryTable
            if queryParams != None:
                sql += " WHERE " + queryParams
            if queryLimit != None:
                sql += " LIMIT " + queryLimit
                
            results = self.executeQuery(sql)
            return results        
        else:
            return "TABLE_NOT_SPECIFIED" 

    def deleteData(self, queryTable, queryParams):        
        if queryTable != None:
            sql = "DELETE FROM " + queryTable
            if queryParams != None:
                sql += " WHERE " + queryParams
            rs = self.executeQuery(sql, autoCommit = True)
            return "DELETE_SUCCESS"        
        else:
            return "TABLE_NOT_SPECIFIED" 

    def executeQuery(self, sql, autoClose = True, autoCommit = False):        
        if self.session == None:
            self.session = self.initiateSession()

        try:
            results = self.session.execute(sql)
        except Exception as err:
            print("ERROR_SQL_EXECUTE :", str(err))
            results = "ERROR : SQL_EXECUTE"
        finally: 
            if autoCommit:
                self.commitSession(self.session)     
            elif autoClose:
                self.closeSession(self.session)     
            return results     
            
    def createDatabase(self):
        print("Create DB")
        return createDB(self)

    def dropDatabase(self):
        print("Drop DB")
        return dropDB(self)
        
        
