from . import base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship
from datetime import date

class JobListing(base.Model):
    __tablename__ = 'joblisting'
    id = Column(Integer, primary_key=True)
    job_title = Column(String, nullable=False, index=True)
    job_descr = Column(String)
    job_exp = Column(String)
    job_role = Column(String)
    job_location = Column(String)
    job_status = Column(String(10))
    created_at = Column(Date)
    children = relationship("JobApplication", back_populates="jobListing")

    def __init__(self, formData = None):
        if formData != None:
            self.job_title = formData["job_title"]
            self.job_descr = formData["job_descr"] if "job_descr" in formData else ""
            self.job_exp = formData["job_exp"] if "job_exp" in formData else ""
            self.job_role = formData["job_role"] if "job_role" in formData else ""
            self.job_status = formData["job_status"] if "job_status" in formData else "OPEN"
            self.job_location = formData["job_location"] if "job_location" in formData else "TBD"

    def createJobListingForm(self, db, formData):
        self.__init__(formData)
        self.created_at = date.today()
        return self.createJobListing(db)

    def createJobListing(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_JOBLISTING"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR : INS_JOBLISTING" 

    def editJobListingForm(self, db, formData):
        session = db.initiateSession()
        joblistingToEdit = session.query(JobListing).filter(JobListing.id==formData["joblisting_id"]).first()
        joblistingToEdit.job_title = formData["job_title"] if "job_title" in formData else ""
        joblistingToEdit.job_descr = formData["job_descr"] if "job_descr" in formData else ""
        joblistingToEdit.job_exp = formData["job_exp"] if "job_exp" in formData else ""
        joblistingToEdit.job_role = formData["job_role"] if "job_role" in formData else ""
        joblistingToEdit.job_status = formData["job_status"] if "job_status" in formData else "OPEN"
        joblistingToEdit.job_location = formData["job_location"] if "job_location" in formData else "TBD"
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteJobListing(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcid + '\'' for rcid in recordIds]) + ") "
        return db.deleteData('joblisting', queryParams)

    def fetchByJobListingId(self, db, jobListingIds = []):
        if jobListingIds != [] and jobListingIds != None:
            if isinstance(jobListingIds, str):   
                params = 'id = \'' + jobListingIds + '\'' 
            elif isinstance(jobListingIds, list):
                params = 'id IN (' + ','.join([ '\'' + jl + '\'' for jl in jobListingIds]) + ')' 
            return db.fetchData('joblisting', None, params, None) 
        return "ERROR : MISSING_JOBLISTINGIDS"

    def fetchJobListingWithApplicantCount(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('joblisting', "id, created_at, job_title, job_descr, job_exp, job_location, job_status, job_role, (SELECT COUNT(id) FROM jobapplication WHERE jobapplication.job_id = joblisting.id)" , queryParams, queryLimit)

    def fetchJobListings(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('joblisting', queryFields, queryParams, queryLimit)

class JobApplication(base.Model):
    __tablename__ = 'jobapplication'
    id = Column(Integer, primary_key=True)
    application_status = Column(String, default="APPLIED")
    application_date = Column(Date)
    job_id = Column(Integer, ForeignKey("joblisting.id"))
    candidate_id = Column(Integer, ForeignKey("candidate.id"))
    jobListing = relationship("JobListing", back_populates="children")

    def __init__(self, formData = None):
        if formData != None:
            self.job_id = formData["job_id"]
            self.candidate_id = formData["candidate_id"]
            self.application_status = formData["application_status"] if "application_status" in formData else "APPLIED"

    def createJobApplicationForm(self, db, formData):
        if "job_id" in formData and "candidate_id" in formData:
            
            queryParams = " id = '"  +  str(formData["job_id"]) + "' AND job_status = 'OPEN'"
            activeJobs = JobListing().fetchJobListings(db, queryParams=queryParams)
            if activeJobs == "ERROR : SQL_EXECUTE":
                return "ERROR : SQL_EXECUTE"
            if activeJobs == None or activeJobs.rowcount == 0:
                return "ERROR : JOB_LISTINNG_INACTIVE"
            queryParams = " job_id = '"  +  str(formData["job_id"]) + "' AND candidate_id = '" + str(formData["candidate_id"]) + "' "
            existingRecords = self.fetchJobApplication(db, queryParams=queryParams)
            if existingRecords == "ERROR : SQL_EXECUTE":
                return "ERROR : SQL_EXECUTE"
            if existingRecords == None or existingRecords.rowcount == 0:
                self.__init__(formData)
                self.application_date = date.today()
                return self.createJobApplication(db)
            else:
                return "ERROR : DUPLICATE_APPPLICATION"
        return "ERROR : MISSING_REQUIRED_IDS"

    def createJobApplication(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_JOBAPPLICATION"
            else:
                return "ERROR : DBCOMMIT"
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR : INS_JOBAPPLCATION" 

    def updateApplicationStatus(self, db, recordId, status):
        session = db.initiateSession()
        itemToEdit = session.query(JobApplication).filter(JobApplication.id==str(recordId)).first()
        itemToEdit.application_status = status.upper()        
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteJobApplication(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcid + '\'' for rcid in recordIds]) + ") "
        return db.deleteData('jobapplication', queryParams)

    def fetchJobApplication(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('jobapplication', queryFields, queryParams, queryLimit)
        
    def fetchJobApplicationWithDetails(self, db, queryFields = None, queryParams = None, queryLimit = None):
        if queryParams == None:
            queryParams = " jobapplication.job_id = joblisting.id AND jobapplication.candidate_id = candidate.id AND candidate.id = person.id ORDER BY joblisting.job_title"
        return db.fetchData('jobapplication, joblisting, candidate, person', "jobapplication.id, application_date, application_status, application_date, resume_filename, job_title, job_descr, email, first_name, last_name, candidate_id", queryParams, queryLimit)
