from . import base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

class ITResource(base.Model):
    __tablename__ = 'itresource'
    id = Column(Integer, primary_key=True)
    resource_name = Column(String, nullable=False)
    resource_descr = Column(String)
    resource_status = Column(String, default="ACTIVE")
    resource_type = Column(String, default="HARDWARE")
    resource_serialnumber = Column(String)
    resource_externalid = Column(String, unique=True)
    resource_assignedto = Column(Integer, ForeignKey("person.id"))
    
    def __init__(self, formData = None):
        if formData != None:
            self.resource_name = formData["resource_name"]
            self.resource_descr = formData["resource_descr"] if "resource_descr" in formData else ""
            self.resource_status = str(formData["resource_status"] if "resource_status" in formData else "ACTIVE").upper()
            self.resource_type = formData["resource_type"] if "resource_type" in formData else "HARDWARE"    
            self.resource_serialnumber = formData["resource_serialnumber"] if "resource_serialnumber" in formData else ""        
            self.resource_assignedto = formData["resource_person_id"] if "resource_person_id" in formData else None     
            self.resource_externalid = str(self.resource_serialnumber) + "_" + self.resource_status

    def createITResourceForm(self, db, formData):
        self.__init__(formData)
        return self.createITResource(db)

    def createITResource(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_ITRESOURCE"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR_INS_ITRESOURCE" 

    def editITResourceForm(self, db, formData):
        session = db.initiateSession()
        recordToEdit = session.query(ITResource).filter(ITResource.id==formData["resource_id"]).first()
        recordToEdit.resource_name = formData["resource_name"]
        recordToEdit.resource_descr = formData["resource_descr"] if "resource_descr" in formData else recordToEdit.resource_descr
        recordToEdit.resource_status = str(formData["resource_status"] if "resource_status"  in formData else recordToEdit.resource_status).upper()
        recordToEdit.resource_type = formData["resource_type"] if "resource_type"  in formData else recordToEdit.resource_type   
        recordToEdit.resource_serialnumber = formData["resource_serialnumber"] if "resource_serialnumber" in formData else recordToEdit.resource_serialnumber     
        recordToEdit.resource_assignedto = formData["resource_person_id"] if "resource_person_id" in formData else recordToEdit.resource_assignedto
        recordToEdit.resource_externalid = str(recordToEdit.resource_serialnumber) + "_" + str(recordToEdit.resource_status)
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteITResources(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ") "
        return db.deleteData('itresource', queryParams)

    def fetchByITResourceId(self, db, recordIds = []):
        params = ""
        if recordIds != [] and recordIds != None:
            if isinstance(recordIds, str):   
                params = 'id = \'' + recordIds + '\'' 
            elif isinstance(recordIds, list):
                params = 'id IN (' + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ')' 
            return db.fetchData('itresource', None, params, None) 
        return "ERROR_MISSING_ITRESOURCE_IDS"

    def fetchITResourcesWithDetails(self, db, queryFields = None, queryParams = None, queryLimit = None):
        if queryParams == None:
            queryParams = " itresource.resource_assignedto = person.id ORDER BY itresource.id DESC"
        return db.fetchData('itresource, person', "itresource.id, resource_name, resource_descr, resource_status, resource_type, resource_serialnumber, first_name, last_name, person.id AS person_id " , queryParams, queryLimit)

    def fetchITResources(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('itresource', queryFields, queryParams, queryLimit)
