from . import base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

class Profile(base.Model):
    __tablename__ = 'profile'
    id = Column(Integer, primary_key=True)
    profile_name = Column(String, nullable=False, index=True)
    profile_descr = Column(String)
    profile_active = Column(Boolean, default=True)
    profile_custom = Column(Boolean, default=False)
    children = relationship("ProfileAccess", back_populates="profile")
    persons = relationship("Person", back_populates="profile")
    
    def __init__(self, formData = None):
        if formData != None:
            self.profile_name = str(formData["profile_name"]).upper()
            self.profile_descr = formData["profile_descr"]
            self.profile_active = True if "profile_active" in formData else False
            self.profile_custom = True if "profile_custom" in formData else False

    def createProfileForm(self, db, formData):
        self.__init__(formData)
        return self.createProfile(db)

    def createProfileWithAccess(self, db, viewList, formData):        
        self.__init__(formData)
        response = self.createProfile(db)
        if response == "INSERTED_PROFILE":
            session = db.initiateSession()
            if viewList != None:
                try:
                    for item in viewList:
                        pfa = ProfileAccess(self, item, formData)
                        session.add(pfa)
                    commitStatus = db.commitSession(session)
                    if commitStatus == "SUCCESS":
                        return "INSERTED_PROFILE_WITH_ACCESS"
                    else:
                        return "ERROR : " + commitStatus
                except Exception as err:
                    return "ERROR_INS_PROFILE_WITH_ACCESS"
            else:
                viewList = View().fetchViews(db)
                try:
                    for item in viewList:
                        formData["inherit_view_id"] = item.id
                        formData["inherit_view_tab"] = item.view_tab_default
                        formData["inherit_view_allow_read"] = item.allow_read_default
                        formData["inherit_view_allow_create"] = item.allow_create_default
                        formData["inherit_view_allow_edit"] = item.allow_edit_default
                        formData["inherit_view_allow_delete"] = item.allow_delete_default
                        pfa = ProfileAccess(self, view=None, formData=formData)
                        session.add(pfa)
                    commitStatus = db.commitSession(session)
                    if commitStatus == "SUCCESS":
                        return "INSERTED_PROFILE_WITH_ACCESS"
                    else:
                        return "ERROR_" + commitStatus
                except Exception as err:
                    if "duplicate key" in str(err):
                        return "ERROR : DUPLICATE KEY" 
                    return "ERROR_INS_PROFILE_WITH_ACCESS"
        else:
            return response

    def createProfile(self, db):
        queryParams = "profile_name = '" + str(self.profile_name) + "'"
        existingProfile = self.fetchProfiles(db, queryParams = queryParams)
        if (existingProfile == None or list(existingProfile) == []) and self.profile_name != "":
            try:
                session = db.initiateSession()
                session.add(self)
                commitStatus = db.commitSession(session)
                if commitStatus == "SUCCESS":
                    return "INSERTED_PROFILE"
                else:
                    return "ERROR_" + commitStatus
            except Exception as err:
                return "ERROR"
        elif self.profile_name == "" or self.profile_name == None:
            return "ERROR_MISSING_PROFILE_NAME"
        else:
            return "ERROR_DUPLICATE_PROFILE"
    
    def fetchProfiles(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('profile', queryFields, queryParams, queryLimit)

    def fetchProfilesWithPersonCount(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('profile', 'id, profile_name, profile_descr, profile_active, profile_custom, (SELECT COUNT(id) FROM person WHERE person.profile_id = profile.id)', queryParams, queryLimit)    
        
    def fetchProfileAssignment(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('profile, person', 'person.id, person.email, person.first_name, person.last_name', queryParams, queryLimit)

    def editProfileForm(self, db, formData):
        session = db.initiateSession()
        profileToEdit = session.query(Profile).filter(Profile.id==formData["profile_id"]).first()
        profileToEdit.profile_name = formData["profile_name"] 
        profileToEdit.profile_descr = formData["profile_descr"] 
        profileToEdit.profile_active = True if "profile_active" in formData else False
        commitStatus = db.commitSession(session)
        return commitStatus

    def deleteProfiles(self, db, recordIds):
        queryParams = "id IN (" + ','.join([ '\'' + prfid + '\'' for prfid in recordIds]) + ") AND profile_custom = true"
        return db.deleteData('profile', queryParams)

class ProfileAccess(base.Model):
    __tablename__ = 'profileaccess'
    id = Column(Integer, primary_key=True)
    allow_read = Column(Boolean, default=False)
    allow_create = Column(Boolean, default=False)
    allow_edit = Column(Boolean, default=False)
    allow_delete = Column(Boolean, default=False)
    view_tab = Column(Boolean, default=False)
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"))
    view_id = Column(Integer, ForeignKey("view.id", ondelete="CASCADE"))
    profile = relationship("Profile", back_populates="children")
    view = relationship("View", back_populates="children")

    def __init__(self, profile = None, view = None, formData = None):
        if view != None:
            self.view = view if view is not None else None        
        if profile != None:             
            self.profile = profile if profile is not None else None
        if formData != None:
            print(formData)
            self.view_id = formData["inherit_view_id"] if "inherit_view_id" in formData else None
            if "profile_fullaccess" in formData:
                self.view_tab = True
                self.allow_read = True
                self.allow_create = True
                self.allow_edit = True
                self.allow_delete = True
            elif "profile_readonlyaccess" in formData:
                self.view_tab = True
                self.allow_read = True
                self.allow_create = False
                self.allow_edit = False
                self.allow_delete = False
            elif "inherit_view_id" in formData:
                self.view_tab = formData["inherit_view_tab"]
                self.allow_read = formData["inherit_view_allow_read"]
                self.allow_create =  formData["inherit_view_allow_create"]
                self.allow_edit =  formData["inherit_view_allow_edit"]
                self.allow_delete =  formData["inherit_view_allow_delete"]
            else:
                self.view_tab = False
                self.allow_read = False
                self.allow_create = False
                self.allow_edit = False
                self.allow_delete = False

    def createProfileAccessForm(self, db, formData):
        self.__init__(formData)
        return self.createProfileAccess(db)

    def createProfileAccess(self, db):
        existingProfileAccess = None #self.fetchUsers(db, username)
        if existingProfileAccess == None or existingProfileAccess == []:
            try:
                session = db.initiateSession()
                session.add(self)
                commitStatus = db.commitSession(session)
                if commitStatus == "SUCCESS":
                    return "INSERTED_PROFILEACCESS"
                else:
                    return "ERROR : " + commitStatus
            except Exception as err:
                if "duplicate key" in str(err):
                    return "ERROR : DUPLICATE KEY" 
                return "ERROR_INS_PROFILE_WITH_ACCESS"
        else:
            return "ERROR_DUPLICATE_PROFILEACCESS"
    
    def fetchProfileAccess(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('profileaccess', queryFields, queryParams, queryLimit)

    def fetchProfileAccessByProfile(self, db, profileId):
        queryParams = 'profileaccess.view_id = view.id AND profileaccess.profile_id =  \'' + profileId + '\' ORDER BY id ASC'
        queryFields = 'profileaccess.id, view_id, view_name, view_group, view_url, view_label, view_tab, view_icon, allow_read, allow_create, allow_edit, allow_delete'         
        return db.fetchData('profileaccess, view', queryFields, queryParams, None)

    def fetchProfileAccessByUsername(self, db, username, accessCheck = False, viewType = "ALL"):
        if username != None and username != '':
            queryParams = 'profileaccess.view_id = view.id AND profileaccess.profile_id = person.profile_id AND username = \'' + username + '\''
            if accessCheck:
                queryParams += ' AND profileaccess.allow_read = true '
            else:
                queryParams += ' AND profileaccess.view_tab = true '
            queryFields = 'view_name, view_group, view_url, view_label, view_tab, view_icon, allow_read, allow_create, allow_edit, allow_delete' if accessCheck else 'view_name, view_group, view_url, view_label, view_tab, view_icon, allow_read'
        else:
            queryParams = 'profileaccess.view_id = view.id AND profileaccess.profile_id = person.profile_id AND view.view_group = \'PUBLIC\''
            queryFields = 'view_name, view_group, view_url, view_label, view_tab, view_icon, allow_read'
        
        if viewType != "ALL":
            queryParams += ' AND view.view_type = \'' + viewType + '\' '
        queryParams += ' ORDER BY profileaccess.id ASC '
        return db.fetchData('profileaccess, view, person', queryFields, queryParams, None)

    def bulkEditProfileAccessForm(self, db, pfaList):
        pfaMap = {}
        for key, value in pfaList.items():
            pfa = key.split('_')
            if pfa[0] not in pfaMap:
                pfaMap[pfa[0]] = {}

            if pfa[1] == "read":
                pfaMap[pfa[0]]["allow_read"] = True
            elif pfa[1] == "create":
                pfaMap[pfa[0]]["allow_create"] = True
            elif pfa[1] == "edit":
                pfaMap[pfa[0]]["allow_edit"] = True
            elif pfa[1] == "delete":
                pfaMap[pfa[0]]["allow_delete"] = True
            elif pfa[1] == "viewtab":
                pfaMap[pfa[0]]["view_tab"] = True
            #elif pfa[1] == "viewid":
                #pfaMap[pfa[0]]["view_id"] = value

        session = db.initiateSession()
        pfaToUpdate = {}
        viewToUpdate = {}
        for key, value in pfaMap.items():
            pfaToUpdate[key] = session.query(ProfileAccess).filter(ProfileAccess.id==key).first()
            
            
            pfaToUpdate[key].view_tab = value["view_tab"] if "view_tab" in value else False
            if pfaToUpdate[key].view_tab:
                pfaToUpdate[key].allow_read = True
            pfaToUpdate[key].allow_read = value["allow_read"] if "allow_read" in value else False
            pfaToUpdate[key].allow_create = value["allow_create"] if "allow_create" in value else False
            if pfaToUpdate[key].allow_create:
                pfaToUpdate[key].allow_read = True
            pfaToUpdate[key].allow_edit = value["allow_edit"] if "allow_edit" in value else False
            if pfaToUpdate[key].allow_edit:
                pfaToUpdate[key].allow_read = True           
            pfaToUpdate[key].allow_delete = value["allow_delete"] if "allow_delete" in value else False
            if pfaToUpdate[key].allow_delete:
                pfaToUpdate[key].allow_read = pfaToUpdate[key].allow_create = pfaToUpdate[key].allow_edit = True

            #viewToUpdate[key] = session.query(View).filter(View.id== value["view_id"]).first()
            #viewToUpdate[key].view_tab = value["view_tab"] if "view_tab" in value else False
        commitStatus = db.commitSession(session)
        return commitStatus
        
class View(base.Model):
    __tablename__ = 'view'
    id = Column(Integer, primary_key=True)
    view_name = Column(String, default="default", unique=True, index=True) 
    view_group = Column(String, default="default", index=True) 
    view_type = Column(String, default="default", index=True) 
    view_url = Column(String, default="/", index=True) 
    view_label = Column(String) 
    view_icon = Column(String) 
    view_tab_default = Column(Boolean, default=False)
    allow_read_default = Column(Boolean, default=False)
    allow_create_default = Column(Boolean, default=False)
    allow_edit_default = Column(Boolean, default=False)
    allow_delete_default = Column(Boolean, default=False)
    children = relationship("ProfileAccess", back_populates="view")

    def __init__(self, **kwargs):
        if len(list(kwargs.keys())) > 0:
            self.view_name = kwargs["view_name"]
            self.view_group = str(kwargs["view_group"]).upper()
            self.view_type = str(kwargs["view_type"]).upper()
            self.view_url = kwargs["view_url"]
            self.view_label = kwargs["view_label"]
            self.view_icon = kwargs["view_icon"]
            self.view_tab_default = kwargs["view_tab"] if "view_tab" in kwargs else False
            self.allow_read_default = kwargs["allow_read_default"] if "allow_read_default" in kwargs else False
            self.allow_create_default = kwargs["allow_create_default"] if "allow_create_default" in kwargs else False
            self.allow_edit_default = kwargs["allow_edit_default"] if "allow_edit_default" in kwargs else False
            self.allow_delete_default = kwargs["allow_delete_default"] if "allow_delete_default" in kwargs else False

    def createView(self, db):
        existingView = None #self.fetchUsers(db, username)
        if existingView == None or existingView == []:
            try:
                session = db.initiateSession()
                session.add(self)
                commitStatus = db.commitSession(session)
                if commitStatus == "SUCCESS":
                    return "INSERTED_VIEW"
                else:
                    return "ERROR : " + commitStatus
            except Exception as err:
                if "duplicate key" in str(err):
                    return "ERROR : DUPLICATE KEY" 
                return "ERROR_INS_VIEW"
        else:
            return "ERROR_DUPLICATE_VIEW"
    
    def fetchViews(self, db, queryFields = None, queryParams = None, queryLimit = None):
        return db.fetchData('view', queryFields, queryParams, queryLimit)
