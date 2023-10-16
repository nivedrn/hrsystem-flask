from . import base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from datetime import date

class Account(base.Model):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    acc_name = Column(String, nullable=False, index=True)
    acc_type = Column(String, nullable=False, index=True)
    acc_status = Column(String, nullable=False, index=True, default="ACTIVE")
    addr_line = Column(String)
    addr_city = Column(String)
    addr_state = Column(String)
    addr_country = Column(String)
    addr_zip = Column(String)
    projects = relationship("Project", back_populates="account")
    external_persons = relationship("External", back_populates="account")

    def __init__(self, formData = None):
        if formData != None:
            self.acc_name = formData["acc_name"]
            self.acc_type = str(formData["acc_type"] if "acc_type" in formData else "").upper()
            self.acc_status = str(formData["acc_status"] if "acc_status" in formData else "").upper()
            self.addr_line = formData["addr_line"] if "addr_line" in formData else ""
            self.addr_city = formData["addr_city"] if "addr_city" in formData else ""
            self.addr_state = formData["addr_state"] if "addr_state" in formData else ""
            self.addr_country = formData["addr_country"] if "addr_country" in formData else ""
            self.addr_zip = formData["addr_zip"] if "addr_zip" in formData else ""

    def createAccountForm(self, db, formData):
        self.__init__(formData)
        return self.createAccount(db)

    def createAccount(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_ACCOUNT"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR : INS_ACCOUNT"

    def editAccountForm(self, db, formData):
        session = db.initiateSession()
        recordToEdit = session.query(Account).filter(Account.id==formData["account_id"]).first()
        recordToEdit.account_name = formData["account_name"] if "account_name" in formData else recordToEdit.account_name
        recordToEdit.account_type = formData["account_type"] if "account_type" in formData else recordToEdit.account_type
        recordToEdit.account_status = formData["account_status"] if "account_status" in formData else recordToEdit.account_status
        recordToEdit.addr_line = formData["addr_line"] if "addr_line" in formData else recordToEdit.addr_line
        recordToEdit.addr_city = formData["addr_city"] if "addr_city" in formData else recordToEdit.addr_city
        recordToEdit.addr_state = formData["addr_state"] if "addr_state" in formData else recordToEdit.addr_state
        recordToEdit.addr_country = formData["addr_country"] if "addr_country" in formData else recordToEdit.addr_zip
        recordToEdit.addr_zip = formData["addr_zip"] if "addr_zip" in formData else recordToEdit.addr_zip
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteAccount(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ") "
        return db.deleteData('account', queryParams)

    def fetchByAccountId(self, db, recordIds = []):
        params = ""
        if recordIds != [] and recordIds != None:
            if isinstance(recordIds, str):   
                params = 'id = \'' + recordIds + '\'' 
            elif isinstance(recordIds, list):
                params = 'id IN (' + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ')' 
            return db.fetchData('Account', None, params, None) 
        return "ERROR : MISSING_AccountIDS"

    def fetchAccountWithProjectCount(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('account', "id, acc_name, acc_type, acc_status, addr_line, addr_city, addr_state, addr_country, addr_zip, (SELECT COUNT(id) FROM project) AS count" , queryParams, queryLimit)

    def fetchAccounts(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('account', queryFields, queryParams, queryLimit)

class Project(base.Model):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True)
    description = Column(String)
    account_id = Column(Integer, ForeignKey("account.id"))
    manager_id = Column(Integer, ForeignKey('person.id'))
    project_status = Column(String)
    account = relationship("Account", back_populates="projects")
    manager = relationship("Person", back_populates="managedprojects")
    children = relationship("ProjectAssignment", back_populates="project")
    def __init__(self, formData = None):
        if formData != None:
            self.description = formData["description"] if "description" in formData else ""
            self.account_id = formData["project_account_id"] if "project_account_id" in formData else None
            self.manager_id = formData["project_manager_id"] if "project_manager_id" in formData else None
            self.project_status = formData["project_status"] if "project_status" in formData else "ACTIVE"

    def createProjectForm(self, db, formData):
        self.__init__(formData)
        return self.createProject(db)

    def createProject(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_PROJECT"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR : INS_PROJECT"

    def editProjectForm(self, db, formData):
        session = db.initiateSession()
        recordToEdit = session.query(Project).filter(Project.id==formData["project_id"]).first()
        recordToEdit.project_id = formData["project_id"] if "project_id" in formData else recordToEdit.project_id
        recordToEdit.project_description = formData["description"] if "description" in formData else recordToEdit.project_description
        recordToEdit.account_id = formData["project_account_id"] if "project_account_id" in formData else recordToEdit.account_id
        recordToEdit.manager_id = formData["project_manager_id"] if "project_manager_id" in formData else recordToEdit.manager_id
        recordToEdit.project_status = formData["project_status"] if "project_status" in formData else recordToEdit.project_status
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteProject(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ") "
        return db.deleteData('project', queryParams)

    def fetchByProjectId(self, db, recordIds = []):
        params = ""
        if recordIds != [] and recordIds != None:
            if isinstance(recordIds, str):   
                params = 'id = \'' + recordIds + '\'' 
            elif isinstance(recordIds, list):
                params = 'id IN (' + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ')' 
            return db.fetchData('project', None, params, None) 
        return "ERROR : MISSING_PROJECTIDS"

    def fetchProjectWithUserCount(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('project LEFT JOIN person ON person.id = project.manager_id INNER JOIN account ON account.id = project.account_id ', "project.id, acc_name, description, person.last_name, project_status, person.first_name, (SELECT COUNT(id) FROM projectassignment)" , queryParams, queryLimit)

    def fetchProjects(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('project', queryFields, queryParams, queryLimit)
    
class ProjectAssignment(base.Model):
    __tablename__ = 'projectassignment'
    id = Column(Integer, primary_key=True)
    role = Column(String, index=True)
    assigned_on = Column(Date)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.id"), nullable=False)
    project = relationship("Project", back_populates="children")

    def __init__(self, formData = None):
        if formData != None:
            self.role = formData["role"] if "role" in formData else "MEMBER"
            self.person_id = formData["prjasgn_person_id"] if "prjasgn_person_id" in formData else None
            self.project_id = formData["prjasgn_project_id"] if "prjasgn_project_id" in formData else None
            self.assigned_on = date.today()

    def createProjectAssignmentForm(self, db, formData):
        if "prjasgn_person_id" in formData and "prjasgn_project_id" in formData:
            self.__init__(formData)
            return self.createProjectAssignment(db)
        return "ERROR : PROJECT AND PERSON ARE REQUIRED FIELDS"

    def createProjectAssignment(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_PROJECTASSIGNMENT"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR : INS_PROJECTASSIGNMENT"

    def editProjectAssignment(self, db, formData):
        session = db.initiateSession()
        recordToEdit = session.query(ProjectAssignment).filter(ProjectAssignment.id==formData["prjasgn_id"]).first()
        recordToEdit.role = formData["role"] if "role" in formData else recordToEdit.role
        recordToEdit.project_id = formData["prjasgn_project_id"] if "prjasgn_project_id" in formData else recordToEdit.project_id
        recordToEdit.person_id = formData["prjasgn_person_id"] if "prjasgn_person_id" in formData else recordToEdit.person_id
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteProjectAssignment(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ") "
        return db.deleteData('projectassignment', queryParams)

    def fetchProjectAssignmentById(self, db, recordIds = []):
        params = ""
        if recordIds != [] and recordIds != None:
            if isinstance(recordIds, str):   
                params = 'id = \'' + recordIds + '\'' 
            elif isinstance(recordIds, list):
                params = 'id IN (' + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ')' 
            return db.fetchData('projectassignment', None, params, None) 
        return "ERROR : MISSING_PROJECTASSIGNMENT_IDS"

    def fetchProjectAssignmentWithDetails(self, db, queryFields = None, queryParams = None, queryLimit = None):
        if queryParams == None:
            queryParams = " projectassignment.person_id = person.id AND projectassignment.project_id = project.id"
        return db.fetchData('projectassignment, person, project ', "role, assigned_on, projectassignment.id, description, project_status, person.last_name, person.first_name " , queryParams, queryLimit)

    def fetchProjectAssignments(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('project', queryFields, queryParams, queryLimit)
    