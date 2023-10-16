from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker    
from .base import Model
from .access import Profile, ProfileAccess, View
from .jobs import JobListing, JobApplication
from .accounts import Account, Project, ProjectAssignment
from .services import DailyStatus, Vacation
from .payroll import Tier, Payroll, PayrollDetail
from .users import Person, Employee, External, Candidate

def createDB(db):
    engine = create_engine(db.dbURI, echo=True)
    Model.metadata.create_all(bind=engine)
    result = initializeDB(db)
    return result

def dropDB(db):
    engine = create_engine(db.dbURI, echo=True)
    Model.metadata.drop_all(bind=engine)

def initializeDB(db):
    results = []
    formData = {}

    #CREATE_VIEWS
    viewList = []
    viewList.append(View(view_name = "dashboard", view_group = "default", view_url = "/", view_label = "Dashboard", view_icon = "fa-solid fa-border-none fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "profile", view_group = "default", view_url = "/profile", view_label = "Profile", view_icon = "fa-regular fa-user fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "dailystatus", view_group = "default", view_url = "/dailystatus", view_label = "Daily Status", view_icon = "fa-solid fa-calendar-day fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "vacation", view_group = "default", view_url = "/vacation", view_label = "Vacation", view_icon = "fa-solid fa-plane-departure fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "account", view_group = "default", view_url = "/account", view_label = "Account", view_icon = "fa-solid fa-briefcase fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "project", view_group = "default", view_url = "/project", view_label = "Project", view_icon = "fa-regular fa-folder-open fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "search", view_group = "default", view_url = "/search", view_label = "Search", view_icon = "fa-solid fa-magnifying-glass fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "employee", view_group = "default", view_url = "/employee", view_label = "Employee", view_icon = "fa-regular fa-address-card fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "consultant", view_group = "default", view_url = "/contractor", view_label = "Contractor", view_icon = "fa-regular fa-address-card fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "contractor", view_group = "default", view_url = "/consultant", view_label = "Consultant", view_icon = "fa-regular fa-address-card fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "candidate", view_group = "default", view_url = "/candidate", view_label = "Candidate", view_icon = "fa-regular fa-address-card fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "people", view_group = "manage", view_url = "/people", view_label = "People", view_icon = "fa-solid fa-user-group fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "accounts", view_group = "manage", view_url = "/accounts", view_label = "Accounts", view_icon = "fa-solid fa-address-card fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "payroll", view_group = "manage", view_url = "/payroll", view_label = "Payroll", view_icon = "fa-solid fa-file-invoice-dollar fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "recruitment", view_group = "manage", view_url = "/recruitment", view_label = "Recruitment", view_icon = "fa-solid fa-tower-observation fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "jobs", view_group = "public", view_url = "/jobs", view_label = "Jobs", view_icon = "fa-solid fa-tower-observation fa-fw", view_type = "PAGE", view_tab = True, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "myapplication", view_group = "public", view_url = "/jobs/myapplication", view_label = "My Applications", view_icon = "fa-regular fa-user fa-fw", view_type = "PAGE", view_tab = True, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "access", view_group = "admin", view_url = "/access", view_label = "Access", view_icon = "fa-solid fa-fingerprint fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "profiles", view_group = "admin", view_url = "/profile", view_label = "Profile", view_icon = "fa-solid fa-fingerprint fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "views", view_group = "admin", view_url = "/view", view_label = "View", view_icon = "fa-solid fa-fingerprint fa-fw", view_type = "TABLE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "itresources", view_group = "admin", view_url = "/itresources", view_label = "IT Resources", view_icon = "fa-solid fa-computer", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "settings", view_group = "admin", view_url = "/settings", view_label = "Settings", view_icon = "fa-solid fa-gear fa-fw", view_type = "PAGE", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    viewList.append(View(view_name = "fetchData", view_group = "admin", view_url = "/fetchData", view_label = "FetchData", view_icon = "fa-solid fa-link", view_type = "API", view_tab = False, allow_read_default = False, allow_create_default = False, allow_edit_default = False, allow_delete_default = False))
    session = db.initiateSession()
    session.add_all(viewList)
    db.commitSession(session, True)
    
    formData["profile_name"] = "ADMIN"
    formData["profile_descr"] = "Default Admin Profile"
    formData["profile_active"] = True
    formData["profile_fullaccess"] = True
    prf = Profile(formData)
    results.append(prf.createProfileWithAccess(db, viewList, formData))
    del formData['profile_fullaccess']

    formData["profile_name"] = "CONSULTANT"
    formData["profile_descr"] = "Default Consultant Profile"
    formData["profile_active"] = True
    prf2 = Profile(formData)
    results.append(prf2.createProfileWithAccess(db, viewList, formData))

    formData["profile_name"] = "CONTRACTOR"
    formData["profile_descr"] = "Default Contractor Profile"
    formData["profile_active"] = True
    prf3 = Profile(formData)
    results.append(prf3.createProfileWithAccess(db, viewList, formData))
    
    formData["profile_name"] = "CANDIDATE"
    formData["profile_descr"] = "Default Candidate Profile"
    formData["profile_active"] = True
    prf4 = Profile(formData)
    results.append(prf4.createProfileWithAccess(db, viewList, formData))

    formData= {}
    formData["username"] = "admin"
    formData["email"] = "admin@hrs.com"
    formData["password"] = "admin"
    formData["last_name"] = "Admin"
    formData["first_name"] = "IT"
    formData["date_of_birth"] = "2004-01-01"
    formData["profile_id"] = 1
    
    emp = Employee()
    results.append(emp.createEmployeeForm(db, formData))

    return results
    