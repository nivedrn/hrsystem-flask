from . import base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date

class DailyStatus(base.Model):
    __tablename__ = 'dailystatus'
    id = Column(Integer, primary_key=True)
    status_descr = Column(String, nullable=False, index=True)
    status_date = Column(Date, nullable=False, index=True)
    work_hours = Column(Integer, nullable=False, index=True)
    status_project = Column(String)
    project_id = Column(Integer, ForeignKey("project.id"))
    employee_id = Column(Integer, ForeignKey("person.id"))

    def __init__(self, formData = None):
        if formData != None:
            self.status_descr = formData["status_descr"]
            self.status_date = formData["status_date"]
            self.work_hours = formData["work_hours"] if "work_hours" in formData else 0
            self.status_project = formData["status_project"]
            self.employee_id = formData["employee_id"] if "employee_id" in formData else None

    def createDailyStatusForm(self, db, formData):
        self.__init__(formData)
        return self.createDailyStatus(db)

    def createDailyStatus(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_DAILYSTATUS"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR_INS_DAILYSTATUS" 

    def fetchDailyStatusByUsername(self, db, userId):
        queryParams = " employee_id = '" + str(userId) + "' ORDER BY id DESC"
        return db.fetchData('dailystatus', None, queryParams, None)

    def fetchDailyStatus(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('dailystatus', queryFields, queryParams, queryLimit)

class Vacation(base.Model):
    __tablename__ = 'vacation'
    id = Column(Integer, primary_key=True)
    vac_type = Column(String, nullable=False, index=True)
    vac_comment = Column(String)
    vac_status = Column(String)
    vac_startdate = Column(Date)
    vac_enddate = Column(Date)
    vac_numdays = Column(Integer)
    employee_id = Column(Integer, ForeignKey("person.id"))

    def __init__(self, formData = None):
        if formData != None:
            self.vac_type = formData["vac_type"]
            self.vac_comment = formData["vac_comment"]
            self.employee_id = formData["employee_id"]
            self.vac_status = "APPLIED"
            self.vac_startdate = datetime.strptime(formData["vac_startdate"], '%Y-%m-%d').date()
            self.vac_enddate = datetime.strptime(formData["vac_enddate"], '%Y-%m-%d').date()
            self.vac_numdays = int((self.vac_enddate - self.vac_startdate).days)

    def createVacationForm(self, db, formData):
        self.__init__(formData)
        return self.createVacation(db)

    def createVacation(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_VACATION"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR_INS_VACATION" 

    def fetchVacationByUserId(self, db, userId):
        queryParams = " employee_id = '" + str(userId) + "' ORDER BY id DESC"
        return db.fetchData('vacation', None, queryParams, None)

    def fetchVacation(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('vacation', queryFields, queryParams, queryLimit)