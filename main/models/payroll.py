from . import base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

class Tier(base.Model):
    __tablename__ = 'tier'
    id = Column(Integer, primary_key=True)
    tier_name = Column(String, nullable=False)
    tier_descr = Column(String)
    tier_payscale = Column(Integer, default=0)
    tier_active = Column(Boolean, default=True)
    tier_default = Column(Boolean, default=False)
    persons = relationship("Employee", back_populates="tier")
    
    def __init__(self, formData = None):
        if formData != None:
            self.tier_name = formData["tier_name"]
            self.tier_descr = formData["tier_descr"] if "tier_descr" in formData else ""
            self.tier_payscale = formData["tier_payscale"] if "tier_payscale" in formData else 0
            self.tier_active = True if "tier_active" in formData else False
            self.tier_default = True if "tier_default" in formData else False

    def createTierForm(self, db, formData):
        self.__init__(formData)
        return self.createTier(db)

    def createTier(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_TIER"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR_INS_TIER" 

    def editTierForm(self, db, formData):
        session = db.initiateSession()
        recordToEdit = session.query(Tier).filter(Tier.id==formData["tier_id"]).first()
        recordToEdit.tier_name = formData["tier_name"] 
        recordToEdit.tier_descr = formData["tier_descr"] 
        recordToEdit.tier_payscale = formData["tier_payscale"] 
        recordToEdit.tier_active = True if "tier_active" in formData else False
        recordToEdit.tier_default = True if "tier_default" in formData else False
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteTier(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ") AND tier_default != true"
        return db.deleteData('tier', queryParams)

    def fetchByTierId(self, db, recordIds = []):
        params = ""
        if recordIds != [] and recordIds != None:
            if isinstance(recordIds, str):   
                params = 'id = \'' + recordIds + '\'' 
            elif isinstance(recordIds, list):
                params = 'id IN (' + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ')' 
            return db.fetchData('tier', None, params, None) 
        return "ERROR_MISSING_TIERIDS"

    def fetchTierWithUserCount(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('tier, person', "id, tier_name, tier_descr, tier_active, tier_default, tier_payscale, (SELECT COUNT(id) FROM person WHERE person.tier_id = tier.id)" , queryParams, queryLimit)

    def fetchTiers(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('tier', queryFields, queryParams, queryLimit)

class Payroll(base.Model):
    __tablename__ = 'payroll'
    id = Column(Integer, primary_key=True)
    proll_month = Column(String, nullable=False)
    proll_year = Column(String, nullable=False)
    proll_status = Column(String, nullable=False, default="DRAFT")
    proll_externalid = Column(String, unique=True, nullable=False)
    proll_details = relationship("PayrollDetail", back_populates="payroll")
    
    def __init__(self, formData = None):
        if formData != None:
            if formData["proll_period"] != None:
                period = formData["proll_period"].split("-")
                self.proll_month = period[1]
                self.proll_year = period[0]
                self.proll_status = str(formData["proll_status"] if "proll_status" in formData else "DRAFT").upper()
                self.proll_externalid = self.proll_month.lower() + '_' + self.proll_year.lower()  + '_' +  self.proll_status

    def createPayrollForm(self, db, formData):
        self.__init__(formData)
        return self.createPayroll(db)

    def createPayroll(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_PAYROLL"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR : INS_PAYROLL" 

    def editPayrollForm(self, db, formData):
        session = db.initiateSession()
        recordToEdit = session.query(Payroll).filter(Payroll.id==formData["payroll_id"]).first()
        period = formData["proll_period"].split("-")
        self.proll_month = period[1]
        self.proll_year = period[0]
        recordToEdit.proll_status = formData["proll_status"] 
        commitStatus = db.commitSession(session)
        return commitStatus

    def deletePayroll(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ") AND proll_status = 'DRAFT'"
        return db.deleteData('payroll', queryParams)

    def fetchByPayrollId(self, db, recordIds = []):
        params = ""
        if recordIds != [] and recordIds != None:
            if isinstance(recordIds, str):   
                params = 'id = \'' + recordIds + '\'' 
            elif isinstance(recordIds, list):
                params = 'id IN (' + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ')' 
            return db.fetchData('payroll', None, params, None) 
        return "ERROR : MISSING_PAYROLLIDS"

    def fetchPayrolls(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('payroll', queryFields, queryParams, queryLimit)

    def fetchPayrollsWithDetailCount(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('payroll', "id, proll_externalid, proll_status, proll_year, proll_month, (SELECT COUNT(id) FROM payrolldetail WHERE payrolldetail.payroll_id = payroll.id) AS detailcount, (SELECT SUM(prdetail_amount) FROM payrolldetail WHERE payrolldetail.payroll_id = payroll.id AND prdetail_status != 'DISCARDED' ) AS detailTotal ", queryParams, queryLimit)

    def generatePayrollDetails(self, db, payroll_id):
        queryFields = " person.id AS person_id, person.tier_id, tier.id, tier.tier_payscale, tier.tier_active "
        queryParams = " person.tier_id = tier.id AND person.user_status = 'ACTIVE'"
        queryLimit = None
        records = db.fetchData('person, tier', queryFields, queryParams, queryLimit)
        session = db.initiateSession()
        for row in records:
            formData = {}
            formData["person_id"] = row["person_id"]
            formData["payroll_id"] = payroll_id
            formData["prdetail_amount"] = row["tier_payscale"]
            prollDetail = PayrollDetail(formData)
            session.add(prollDetail)
        
        #bonusRecords = db.fetchedData('payrolldetail', " prdetail_amount, prdetail_type, prdetail_status, person_id ", " payroll_id = null AND prdetail_type = 'BONUS' AND prdetail_status != 'DISCARDED' ", None)
        all_filters = [PayrollDetail.payroll_id == None]
        all_filters.append(PayrollDetail.prdetail_type == 'BONUS')
        all_filters.append(PayrollDetail.prdetail_status != 'DISCARDED')
        bonusRecords = session.query(PayrollDetail).filter(*all_filters).all()
        for row in bonusRecords:
            row.payroll_id = payroll_id
        
        commitStatus = db.commitSession(session)
        if commitStatus == "SUCCESS":
            recordToEdit = session.query(Payroll).filter(Payroll.id==payroll_id).first()
            recordToEdit.proll_status = "DETAILS GENERATED"
            commitStatus = db.commitSession(session)
            return "GENERATED_PAYROLLDETAILS"
        else:
            return "ERROR : " + commitStatus

class PayrollDetail(base.Model):
    __tablename__ = 'payrolldetail'
    id = Column(Integer, primary_key=True)
    prdetail_amount = Column(Integer, nullable=False)
    prdetail_type = Column(String, nullable=False, default="SALARY")
    prdetail_status = Column(String, nullable=False)
    payroll_id = Column(Integer, ForeignKey("payroll.id"))
    person_id = Column(Integer, ForeignKey("person.id"))
    payroll = relationship("Payroll", back_populates="proll_details")
    person = relationship("Person", back_populates="person_payrolls")

    def __init__(self, formData = None):
        if formData != None:            
            self.prdetail_amount = formData["prdetail_amount"]
            self.prdetail_type = formData["prdetail_type"] if "prdetail_type" in formData else "SALARY"
            self.prdetail_status = formData["prdetail_status"] if "prdetail_status" in formData else "CREATED" 
            self.payroll_id = formData["payroll_id"] if "payroll_id" in formData else None
            self.person_id = formData["person_id"] if "person_id" in formData else None 
            
    def createPayrollDetailForm(self, db, formData):
        if "person_id" in formData:
            self.__init__(formData)
            return self.createPayrollDetail(db)
        return "ERROR  : PERSON ID IS REQUIRED"

    def createPayrollDetail(self, db):
        try:
            session = db.initiateSession()
            session.add(self)
            commitStatus = db.commitSession(session)
            if commitStatus == "SUCCESS":
                return "INSERTED_PAYROLLDETAIL"
            else:
                return "ERROR : " + commitStatus
        except Exception as err:
            if "duplicate key" in str(err):
                return "ERROR : DUPLICATE KEY" 
            return "ERROR : INS_PAYROLLDETAIL" 

    def editPayrollDetail(self, db, formData):
        session = db.initiateSession()
        recordToEdit = session.query(PayrollDetail).filter(PayrollDetail.id==formData["prollDetail_id"]).first()
        recordToEdit.payroll_id = formData["payroll_id"] if "payroll_id" in formData else recordToEdit.payroll_id 
        recordToEdit.person_id = formData["person_id"] if "person_id" in formData else recordToEdit.person_id 
        recordToEdit.prdetail_amount = formData["prdetail_amount"] if "prdetail_type" in formData else recordToEdit.prdetail_amount 
        recordToEdit.prdetail_type = formData["prdetail_type"] if "prdetail_type" in formData else recordToEdit.prdetail_type 
        recordToEdit.prdetail_status = formData["prdetail_status"] if "prdetail_status" in formData else recordToEdit.prdetail_status
        commitStatus = db.commitSession(session)
        return commitStatus

    def deletePayroll(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + rcdId + '\'' for rcdId in recordIds]) + ") AND prdetail_status != 'INVOICED'"
        return db.deleteData('payrolldetail', queryParams)

    def fetchPayrollDetailsById(self, db, prdetail_id):
        queryParams = " payrolldetail.payroll_id = payroll.id AND payrolldetail.person_id = person.id AND payrolldetail.id = '" + str(prdetail_id) + "' ORDER BY person_id,  prdetail_status ASC  "
        return db.fetchData('payrolldetail, person, payroll', None, queryParams, None)

    def fetchPayrollDetailsByPayroll(self, db, payroll_id):
        queryParams = " payrolldetail.payroll_id = payroll.id AND payrolldetail.person_id = person.id AND payrolldetail.payroll_id = '" + str(payroll_id) + "' ORDER BY person_id,  prdetail_status ASC  "
        return db.fetchData('payrolldetail, person, payroll', None, queryParams, None)

    def fetchPayrollDetailsByPerson(self, db, person_id):
        queryParams = " payrolldetail.payroll_id = payroll.id AND payrolldetail.person_id = person.id AND payrolldetail.person_id = '" + str(person_id) + "' ORDER BY person_id,  prdetail_status ASC  "
        return db.fetchData('payrolldetail, person, payroll', None, queryParams, None)

    def fetchBonusPayrollDetails(self, db):
        queryParams = " payrolldetail.person_id = person.id AND payrolldetail.prdetail_type = 'BONUS' ORDER BY person_id, prdetail_status ASC  "
        return db.fetchData('payrolldetail, person', "last_name, first_name, prdetail_amount, prdetail_type, prdetail_status, payrolldetail.id, payrolldetail.person_id", queryParams, None)

