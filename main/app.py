from flask import Flask, request, session, jsonify, render_template, redirect, url_for, send_file, make_response
from flask_cors import CORS
from io import BytesIO
from datetime import date, timedelta
from .config import AppConfig
from .database import DatabaseConnect
from .models import *
from . import utils 
import base64

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SECRET_KEY'] = AppConfig.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = AppConfig.PERMANENT_SESSION_LIFETIME

db = None
publicViews = ["/static", "dropDatabase", "createDatabase", "favicon.ico", "unauthorized", "login", "logout"] 

@app.before_request
def beforeRequest():
    if len([ view for view in publicViews if view in request.path and request.path != view]) == 0:
        global db
        if db == None:
            db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

        if db.engine == None and request.path != "/unauthorized":
            return redirect(url_for('unauthorized'))
            
        if 'userSession' in session:        
            hasViewAccess = utils.validateUserAccess(db, session['userSession']["username"], request.path) 
        else:
            hasViewAccess = utils.validateUserAccess(db, None, request.path) 
        
        if (not hasViewAccess) and request.path != "/unauthorized" and request.path != "/login" and request.path != "/logout" and request.path != "/dropDatabase" and request.path != "/createDatabase":
            return redirect(url_for('unauthorized'))

@app.route("/")
def home():
    if 'userSession' not in session:        
        return redirect(url_for('login'))    
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']

    response["employees"] = users.Person().fetchPersons(db, queryParams=" user_type = 'employee' ORDER BY person.id DESC", queryLimit="5")
    response["accounts"] = accounts.Account().fetchAccountWithProjectCount(db, queryLimit="5")    
    response["projects"] = accounts.Project().fetchProjectWithUserCount(db, queryLimit="10")     
    return render_template("base.html", response=response)

@app.route("/login", methods=['GET','POST'])
def login():
    response = { 'table' : 'login'}
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    if request.method == 'POST':        
        result = users.Person().validatePerson(db, request.form['username'], request.form['password'] )
        returnUrl = request.args.get('returnUrl') if 'returnUrl' in request.args else "/"
        if result != None and "ERROR" not in result:
            activeUser = { 'baseUrl' : '/' if result.user_type != 'candidate' else '/jobs/myapplication' , 'username' : result.username, 'id':result.id, 'email' : result.email, 'first_name':result.first_name, 'last_name':result.last_name}            
            session['userSession'] = activeUser
            return redirect(activeUser['baseUrl'])
        else:
            response["messages"] = result
            if returnUrl == '/jobs/myapplication':
                return redirect('/jobs/myapplication?msg=' + response["messages"])
   
    if db.engine == None:
        response["messages"] = "ERROR : Database Connection Failed"

    return render_template("login.html", response=response)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    try:
        session.pop('userSession', None)
    except Exception as err:
        print(err)
    finally:         
        return redirect(url_for('login'))

@app.route("/search", methods=['GET','POST'])
def globalSearch():
    if 'userSession' not in session:        
        return redirect(url_for('login'))    
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)
    
    response = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']

    if request.method == 'POST':
        response["searchTerm"] = request.form["searchTerm"]
        if "accounts" in response["views"] :
            response["accounts"] = accounts.Account().fetchAccountWithProjectCount(db, queryLimit="5")    
        elif "projects" in response["views"] :
            response["projects"] = accounts.Project().fetchProjectWithUserCount(db, queryLimit="10") 
        elif "employee" in response["views"] :
            response["employee"] = users.Person().fetchPersons(db, queryParams=" user_type = 'employee' ORDER BY person.id DESC", queryLimit="5")
        elif "consultants" in response["views"] or "contractors" in response["views"]  :
            response["consultants"] = users.Person().fetchPersons(db, queryParams=" user_type = 'external' ORDER BY person.id DESC", queryLimit="5")
            
    return render_template("search.html", response=response)

@app.route("/profile", defaults={'table': 'employee', 'action' : "read", 'key': 'self' }, methods=["GET"])
@app.route("/profile/<table>", defaults={'action' : "read", 'key': 'self' }, methods=['GET'])
@app.route("/profile/<table>/<action>", defaults={ 'key': 'self' }, methods=['GET'])
@app.route("/profile/<table>/<action>/<key>", methods=["GET"])
def profile(table, action, key):
    if 'userSession' not in session:        
        return redirect(url_for('login'))
 
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']
    response["table"] = table
    response["action"] = action
    response["key"] = key

    if key == "self":
        record_id = session['userSession']["id"]
    else:
        record_id = key

    if table == "employee":
        if action == "resign":
            formData = {}
            formData["user_status"] = "INITIATED RESIGNATION"
            result = users.Employee().editEmployeeForm(db,formData)
        queryParams = "employee.person_id = person.id AND person.profile_id = profile.id AND person.id = '" + str(record_id) + "' "
        queryFields = "person.id, num_vacations, employee_id, email, username, salutation, person.first_name, last_name, profile.id AS profile_id, manager_id, tier_id, profile.profile_name, user_dob, addr_line, addr_city, addr_state, addr_country, addr_zip, phone_number"
        employeeDetails = users.Employee().fetchEmployeesWithDetails(db, queryFields=queryFields, queryParams=queryParams, queryLimit="1")     
        if employeeDetails.rowcount > 0:
            response["recDetails"] = list(employeeDetails)[0]  
        else: 
            response["messages"] = "ERROR : USER NOT FOUND"

    elif table == "consultant" or table == "contractor":
        queryParams = "external.person_id = person.id AND person.profile_id = profile.id AND person.id = '" + str(record_id) + "' "
        queryFields = "person.id, email, username, salutation, person.first_name, last_name, profile.id AS profile_id, tier_id, profile.profile_name, user_dob, addr_line, addr_city, addr_state, addr_country, addr_zip, phone_number"
        recDetails = users.External().fetchExternalsWithDetails(db, queryFields=queryFields, queryParams=queryParams, queryLimit="1")     
        if recDetails.rowcount > 0:
            response["recDetails"] = list(recDetails)[0]  
        else: 
            response["messages"] = "ERROR : USER NOT FOUND"

    elif table == "candidate":
        candidateUrl = "/recruitment/candidate/read/" + str(record_id)
        redirect(candidateUrl)
    queryParams = " projectassignment.person_id = person.id AND projectassignment.project_id = project.id AND projectassignment.person_id = '" + str(record_id) + "' "
    queryFields = "role, assigned_on, projectassignment.id, description, project_status, person.last_name, person.first_name "
    response["projectassignments"] = accounts.ProjectAssignment().fetchProjectAssignmentWithDetails(db, queryFields=queryFields, queryParams=queryParams)   
    response["mypayrolls"] = payroll.PayrollDetail().fetchPayrollDetailsByPerson(db, str(record_id))   
    queryParams = " itresource.resource_assignedto = person.id AND itresource.resource_assignedto = '" + str(record_id) + "' "
    response["itresources"] = infrastructure.ITResource().fetchITResourcesWithDetails(db, queryParams=queryParams)   

    return render_template("profile.html", response=response)       
        
@app.route("/accounts",  defaults={'table': None, 'action' : "read", 'key': None }, methods=['GET'])
@app.route("/accounts/<table>", defaults={'action' : None, 'key': None }, methods=['GET'])
@app.route("/accounts/<table>/<action>", defaults={'key': None}, methods=['GET','POST'])
@app.route("/accounts/<table>/<action>/<key>", methods=['GET','POST'])
def manageAccounts(table, action, key):
    if 'userSession' not in session:        
        return redirect(url_for('login'))
    if table == None:
        return redirect("/accounts/records")    

    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = formData = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']
    response["table"] = table
    response["action"] = action
    response["key"] = key
    # formData['proll_period'] = date.today().strftime("%Y-%m")    

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        if action == "create":
            if table == "projects": 
                response["messages"] = accounts.Project().createProjectForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/accounts/projects?msg=" + response["messages"]) 
            elif table == "records":
                response["messages"] = accounts.Account().createAccountForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/accounts/records?msg=" + response["messages"]) 
            elif table == "projectassignments":
                response["messages"] = accounts.ProjectAssignment().createProjectAssignmentForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/accounts/projectassignments?msg=" + response["messages"]) 
        elif action == "edit":
            if table == "projects": 
                response["messages"] = accounts.Project().editProjectForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/accounts/projects?msg=" + response["messages"]) 
            elif table == "details":
                response["messages"] = accounts.Account().editAccountForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/accounts/records?msg=" + response["messages"]) 
            elif table == "projectassignments":
                response["messages"] = accounts.ProjectAssignment().editProjectAssignment(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/accounts/projectassignments?msg=" + response["messages"]) 

    if key != None:        
        if action == "read":            
            pass
        elif action == "edit":
            if table == "projects":                 
                result = accounts.Project().fetchByProjectId(db, list(key))
                if result != None:
                    for row in result:   
                        formData['id'] = row.id       
                        formData['description'] = row.description      
                        formData['account_id'] = row.account_id                      
            elif table == "records": 
                result =  accounts.Account().fetchByAccountId(db, list(key))
                if result != None:
                    for row in result:   
                        formData['acc_name'] = row.acc_name
                        formData['acc_type'] = row.acc_type
                        formData['acc_status'] = row.acc_status
            elif table == "projectassignments": 
                result =  accounts.ProjectAssignment().fetchProjectAssignmentById(db, list(key))
                if result != None:
                    for row in result:   
                        formData['prjasgn_id'] = row.id
                        formData['role'] = row.role
                        formData['person_id'] = row.person_id
                        formData['project_id'] = row.project_id
        elif action == "delete":
            if table == "projects": 
                result =  accounts.Project().deleteProject(db, list(key))
                if result == "SUCCESS":
                    return redirect("/accounts/projects?msg=" + result)
                else:
                    response["messages"] = result    
            elif table == "records":    
                result = accounts.Account().deleteAccount(db, list(key))
                if result == "SUCCESS":
                    return redirect("/accounts/records?msg=" + result)
                else:
                    response["messages"] = result     
    elif key == None and action != None and table != None and request.method == 'GET':
        response["messages"] = "ERROR_ID_NOT_SPECIFIED"     
          
    response["formData"] = formData
    response["accounts"] = accounts.Account().fetchAccountWithProjectCount(db)    
    response["projects"] = accounts.Project().fetchProjectWithUserCount(db)     
    response["projectassignments"] = accounts.ProjectAssignment().fetchProjectAssignmentWithDetails(db)    
    return render_template("accounts.html", response=response)   
             
@app.route("/dailystatus", methods=["GET", "POST"])
def dailystatus():
    if 'userSession' not in session:        
        return redirect(url_for('login'))
        
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        formData["employee_id"] = session['userSession']['id']
        response["messages"] = services.DailyStatus().createDailyStatusForm(db, formData)    
        if "ERROR" not in response["messages"]:
            return redirect("/dailystatus?msg=" + response["messages"])
    else:        
        formData = {}
        formData["status_date"] = date.today()
        response["formData"] = formData
        
    response["formData"] = formData
    response["statuses"] = services.DailyStatus().fetchDailyStatusByUsername(db, session['userSession']['id'])    
    return render_template("dailystatus.html", response=response)       

@app.route("/vacation", methods=["GET", "POST"])
def vacation():
    if 'userSession' not in session:        
        return redirect(url_for('login'))
        
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = formData  = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        response["formData"] = formData
        response["messages"] = utils.validateFormData(formData)
        if "ERROR" in response["messages"]:
            return render_template("vacation.html", response=response)
        formData["employee_id"] =  session['userSession']['id']
        response["messages"] = services.Vacation().createVacationForm(db, formData)    
        if "ERROR" not in response["messages"]:
            return redirect("/vacation?msg=" + response["messages"])
    else:        
        formData = {}
        formData["vac_startdate"] = date.today()
        formData["vac_enddate"] = date.today() + timedelta(days=1)
        response["formData"] = formData

    response["leaveHistory"] = services.Vacation().fetchVacationByUserId(db,  session['userSession']['id'])    
    return render_template("vacation.html", response=response)              

@app.route("/settings", defaults={'table' : 'main', 'action': None}, methods=['GET'])
@app.route("/settings/<table>/<action>", methods=['GET','POST'])
def userSettings(table, action):
    if 'userSession' not in session:        
        return redirect(url_for('login'))    
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)
    
    response = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        response["formData"] = formData
        if table == "password" and action == "change":            
            response["messages"] = utils.validateFormData(formData)
            if "ERROR" in response["messages"]:
                return render_template("settings.html", response=response)
            else:
                result = users.Person().changePassword(db, session['userSession']["username"], request.form['oldpassword'], request.form['newpassword'] )
                if result != None and "ERROR" not in result:
                    return redirect("/settings?msg=" + response["messages"])
                else:
                    response["messages"] = result    
    return render_template("settings.html", response=response)

@app.route("/itresources", defaults={'action': None, 'key': None }, methods=["GET", "POST"])
@app.route("/itresources/<action>", defaults={'key': None },  methods=["GET", "POST"])
@app.route("/itresources/<action>/<key>", methods=["GET"])
def itResources(action, key):
    if 'userSession' not in session:        
        return redirect(url_for('login'))

    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)
    
    response = formData = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']  
    response["table"] = "itresources"
    response["action"] = action
    response["key"] = key

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        if action == 'edit':
            response["messages"] = infrastructure.ITResource().editITResourceForm(db,formData)
        elif action == 'create':
            response["messages"] = infrastructure.ITResource().createITResourceForm(db,formData)
        return redirect("/itresources?msg=" + response["messages"])
        
    elif key != None:
        if action == 'edit':
            result = list(infrastructure.ITResource().fetchITResources(db, queryParams=" id = '" + key + "'", queryLimit="1"))[0]
            formData["resource_id"] = key
            formData["resource_name"] = result.resource_name
            formData["resource_descr"] = result.resource_descr
            formData["resource_serialnumber"] = result.resource_serialnumber
            formData["resource_status"] = result.resource_status
            formData["resource_type"] = result.resource_type
        elif action == 'delete':
            response["messages"] = infrastructure.ITResource().deleteITResources(db,list(key))
    response["formData"] = formData
    response["resources"] = infrastructure.ITResource().fetchITResourcesWithDetails(db)
    return render_template("itresource.html", response=response)

@app.route("/jobs",  defaults={'table': None, 'action' : "read", 'key': None }, methods=['GET'])
@app.route("/jobs/<table>", defaults={'action' : None, 'key': None }, methods=['GET'])
@app.route("/jobs/<table>/<action>", defaults={'key': None}, methods=['GET','POST'])
@app.route("/jobs/<table>/<action>/<key>", methods=['GET','POST'])
def jobportal(table, action, key):
    if table == None:
        return redirect("/jobs/listing")    

    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)
    
    response = formData = {}
    response["views"] = utils.fetchSidebarLinks(db, None)    
    response["hasSidebar"] = True
    response["formData"] = formData
    response["action"] = action
    response["key"] = key
    response["formData"]["date_of_birth"] = "2004-01-01"

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        response["messages"] = utils.validateFormData(formData)
        if "ERROR" in response["messages"]:
            return redirect("/jobs/myapplication?msg=" + response["messages"])
        response["formData"] = formData
        if table == "resume":
            if action == "create":
                candidate_resume = request.files["candidate_resume"]
                formData["candidate_id"] = session["userSession"]["id"]
                formData["candidate_resume"] = candidate_resume
                response["messages"] = users.Candidate().uploadResume(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/jobs/myapplication")
        elif table == "candidate":
            if action == "register":
                response["messages"] = utils.validateFormData(formData)
                if "ERROR" in response["messages"]:
                    return render_template("myapplications.html", response=response)
                candidate_profile = list(access.Profile().fetchProfiles(db, queryParams=" profile_name = 'CANDIDATE'", queryLimit="1"))
                formData["profile_id"] = candidate_profile[0].id
                response["messages"] = users.Candidate().createCandidateForm(db, formData)
                del formData["password"]
                if "ERROR" not in response["messages"]:
                    result = list(users.Person().fetchPersons(db, queryParams=" user_type = 'candidate' and username = '" + formData["username"] + "'", queryLimit="1"))[0]
                    activeUser = { 'baseUrl' : '/' if result.user_type != 'candidate' else '/jobs/myapplication' , 'username' : result.username, 'id':result.id, 'email' : result.email, 'first_name':result.first_name, 'last_name':result.last_name}            
                    session['userSession'] = activeUser
                    returnUrl = request.args.get('returnUrl') if 'returnUrl' in request.args else activeUser['baseUrl']
                    return redirect(returnUrl)
            elif action == "edit":
                response["messages"] = users.Candidate().editCandidateForm(db, formData)
                if "ERROR" not in response["messages"]:
                    result = list(users.Person().fetchPersons(db, queryParams=" user_type = 'candidate' and username = '" + formData["email"] + "'", queryLimit="1"))[0]
                    activeUser = { 'baseUrl' : '/' if result.user_type != 'candidate' else '/jobs/myapplication' , 'username' : result.username, 'id' : result.id, 'email' : result.email, 'first_name':result.first_name, 'last_name':result.last_name}         
                    session.pop('userSession', None)
                    session['userSession'] = activeUser
                    response['userSession'] = session
                    return redirect("/jobs/myapplication?msg=" + response["messages"])
            return render_template("myapplications.html", response=response)
    else:
        if 'userSession' not in session:  
            if table != "listing" or ( table == "listing" and action == "apply"):
                return render_template("myapplications.html", response=response)
        else:
            response["userSession"] = session['userSession'] 

        if table == "resume" and action == "download" and key != None:
            candidate = users.Candidate().fetchCandidateById(db, key) 
            return send_file(BytesIO(candidate.resume_filedata), download_name= candidate.resume_filename, as_attachment=True)
        elif table == "resume" :
            return render_template("myapplications.html", response=response)
        elif table == "listing" and action == "apply" and key != None :
            formData["job_id"] = key
            formData["candidate_id"] = session["userSession"]["id"]
            response["messages"] = users.Candidate().validateCandidateOnApply(db, session["userSession"]["id"])
            if "ERROR" not in response["messages"]:
                response["messages"] = jobs.JobApplication().createJobApplicationForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/jobs/myapplication?msg=" + response["messages"])
            return redirect("/jobs/myapplication?msg=" + response["messages"])
            
        if table == "myapplication":
            if action == "delete":
                response["messages"] = jobs.JobApplication().deleteJobApplication(db, list(key))
                if "ERROR" not in response["messages"]:
                    return redirect("/jobs/myapplication?msg=" + response["messages"])
            
            queryParams = " person.user_type = 'candidate' AND person.id = candidate.id and username = '" + session["userSession"]["username"] + "' "
            candidate = list(users.Candidate().fetchCandidatesWithDetails(db, None, queryParams, queryLimit="1"))[0] 
            formData["last_name"] = candidate.last_name
            formData["first_name"] = candidate.first_name
            formData["email"] = candidate.email
            formData["resume_filename"] = candidate.resume_filename
            formData["linkedin_username"] = candidate.linkedin_username
            formData["edu_hightest"] = candidate.edu_hightest
            formData["edu_hightest_institution"] = candidate.edu_hightest_institution
            formData["edu_hightest_grade"] = candidate.edu_hightest_grade
            formData["edu_hightest_year"] = candidate.edu_hightest_year
            formData["work_exp_years"] = candidate.work_exp_years
            formData["work_exp_comment"] = candidate.work_exp_comment
            response["formData"] = formData

            queryParams = " jobapplication.candidate_id = '" + str(session["userSession"]["id"]) + "' AND jobapplication.job_id = joblisting.id AND jobapplication.candidate_id = candidate.id AND candidate.id = person.id "
            response["jobapplications"] = jobs.JobApplication().fetchJobApplicationWithDetails(db, queryParams=queryParams)
            return render_template("myapplications.html", response=response)
        response["joblistings"] = jobs.JobListing().fetchJobListings(db, queryParams=" job_status = 'OPEN' ORDER BY job_title ASC")
        return render_template("jobs.html", response=response)
         
@app.route("/recruitment",  defaults={'table': None, 'action' : None, 'key': None }, methods=['GET'])
@app.route("/recruitment/<table>", defaults={'action' : None, 'key': None }, methods=['GET'])
@app.route("/recruitment/<table>/<action>", defaults={'key': None}, methods=['GET','POST'])
@app.route("/recruitment/<table>/<action>/<key>", methods=['GET','POST'])
def recruitment(table, action, key):
    if 'userSession' not in session:        
        return redirect('/login?returnUrl=/recruitment/joblisting')
    if table == None:
        return redirect("/recruitment/joblisting")        
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = formData  = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']
    response["table"] = table
    response["action"] = action
    response["key"] = key

    response['returnUrl'] = "/recruitment/joblisting"
    if request.args.get('returnUrl') != None:
        response["returnUrl"] = request.args.get('returnUrl')
    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        if action == "create":
            if table == "joblisting": 
                response["messages"] = jobs.JobListing().createJobListingForm(db, formData)
        elif action == "edit":
            if table == "joblisting": 
                response["messages"] = jobs.JobListing().editJobListingForm(db, formData)
        if "ERROR" not in response["messages"]:
                return redirect(response["returnUrl"] + '?msg=' + response["messages"])
    
    if key != None:        
        if action == "read":
            if table == "joblisting":    
                queryParams = " id = '" + key + "' ORDER BY job_role, id DESC"             
                response["joblisting"] = jobs.JobListing().fetchJobListingWithApplicantCount(db, queryParams=queryParams)
                queryParams = " jobapplication.job_id = joblisting.id AND jobapplication.candidate_id = candidate.id AND candidate.id = person.id AND jobapplication.job_id = '" + key + "' "
                response["candidateApplications"] = jobs.JobApplication().fetchJobApplicationWithDetails(db, queryParams=queryParams)
            elif table == "candidate":
                response["candidateDetails"] = users.Candidate().fetchCandidateById(db, key)
                queryParams = " jobapplication.job_id = joblisting.id AND jobapplication.candidate_id = candidate.id AND candidate.id = person.id AND candidate.id = '" + key + "' "
                response["candidateApplications"] = jobs.JobApplication().fetchJobApplicationWithDetails(db, queryParams=queryParams)                
            return render_template("recruitment.html", response=response)       
        elif action == "resume":
            candidateToRead = users.Candidate().fetchCandidateById(db, key)
            response = make_response(candidateToRead.resume_filedata)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = "inline; filename = %s.pdf" % candidateToRead.resume_filename    
            return response     
        elif action == "downloadresume":            
            candidate = users.Candidate().fetchCandidateById(db, key) 
            return send_file(BytesIO(candidate.resume_filedata), download_name= candidate.resume_filename, as_attachment=True)
        elif (action == "hired" or action == "rejected" or action == "shortlisted") and table == "candidate":
            response["messages"] = jobs.JobApplication().updateApplicationStatus(db, key, action.upper())
            if "ERROR" not in response["messages"]:
                return redirect(response["returnUrl"])
        elif action == "edit":
            if table == "joblisting": 
                result = jobs.JobListing().fetchByJobListingId(db, key)
                if result != None:
                    for row in result:                
                        formData["job_title"] = row.job_title
                        formData["job_descr"] = row.job_descr
                        formData["job_exp"] = row.job_exp
                        formData["job_location"] = row.job_location
                        formData["job_role"] = row.job_role
                        formData["job_status"] = row.job_status
                        formData["joblisting_id"] = row.id
        elif action == "delete":
            formData = dict(request.form)
            result = jobs.JobListing().deleteJobListing(db, list(key))
            if result == "SUCCESS":
                return redirect("/recruitment?msg=" + result)
            else:
                response["messages"] = result         
    elif key == None and action != None and table != None and request.method == 'GET':
        response["messages"] = "ERROR_ID_NOT_SPECIFIED"

    response["formData"] = formData
    response["joblistings"] = jobs.JobListing().fetchJobListingWithApplicantCount(db)
    response["candidateApplications"] = jobs.JobApplication().fetchJobApplicationWithDetails(db)
    return render_template("recruitment.html", response=response)       

@app.route("/payroll",  defaults={'table': None, 'action' : "read", 'key': None }, methods=['GET'])
@app.route("/payroll/<table>", defaults={'action' : None, 'key': None }, methods=['GET'])
@app.route("/payroll/<table>/<action>", defaults={'key': None}, methods=['GET','POST'])
@app.route("/payroll/<table>/<action>/<key>", methods=['GET','POST'])
def managePayroll(table, action, key):
    if 'userSession' not in session:        
        return redirect(url_for('login'))
    if table == None:
        return redirect("/payroll/details")    

    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = formData = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']
    response["table"] = table
    response["action"] = action
    response["key"] = key
    formData['proll_period'] = date.today().strftime("%Y-%m")    

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        if action == "create":
            formData = dict(request.form)
            if table == "tiers": 
                response["messages"] = payroll.Tier().createTierForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/payroll/tiers?msg=" + response["messages"]) 
            elif table == "details":
                response["messages"] = payroll.Payroll().createPayrollForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/payroll/details?msg=" + response["messages"]) 
            elif table == "bonus":
                formData["prdetail_type"] = "BONUS"
                response["messages"] = payroll.PayrollDetail().createPayrollDetailForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/payroll/bonus?msg=" + response["messages"]) 
        elif action == "edit":
            formData = dict(request.form)
            if table == "tiers": 
                response["messages"] = payroll.Tier().editTierForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/payroll/tiers?msg=" + response["messages"]) 
            elif table == "details":
                response["messages"] = payroll.Payroll().editPayrollForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/payroll/details?msg=" + response["messages"]) 
            elif table == "bonus":
                response["messages"] = payroll.PayrollDetail().editPayrollDetailForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/payroll/bonus?msg=" + response["messages"]) 

    if key != None:        
        if action == "read":            
            if table == "details":
                response["formData"] = formData
                queryParams = " payroll.id = '" + str(key) + "' "
                response["payrolls"] = payroll.Payroll().fetchPayrollsWithDetailCount(db, queryParams=queryParams)    
                response["payrollDetails"] = payroll.PayrollDetail().fetchPayrollDetailsByPayroll(db, key)   
                response["tiers"] = payroll.Tier().fetchTiers(db)      
                response["bonuses"] = payroll.PayrollDetail().fetchBonusPayrollDetails(db)    
                return render_template("payroll.html", response=response)                      
        elif action == "generate" and table == "details":
            response["messages"] = payroll.Payroll().generatePayrollDetails(db, key)
            if "ERROR" not in response["messages"]:
                return redirect("/payroll/details?msg=" + response["messages"]) 
        elif action == "edit":
            if table == "tiers": 
                result = payroll.Tier().fetchByTierId(db, list(key))
                if result != None:
                    for row in result:   
                        formData['tier_name'] = row.tier_name        
                        formData['tier_descr'] = row.tier_descr        
                        formData['tier_payscale'] = row.tier_payscale        
                        formData['tier_active'] = row.tier_active                
            elif table == "details": 
                result = payroll.Payroll().fetchByPayrollId(db, list(key))
                if result != None:
                    for row in result:   
                        formData['proll_period'] = row.proll_year + "-" + row.proll_month
                        formData['proll_status'] = row.proll_status
            elif table == "bonus": 
                result = payroll.PayrollDetail().fetchPayrollDetailsById(db, key)
                if result != None:
                    for row in result:   
                        formData['prdetail_amount'] = row.prdetail_amount
                        formData['prdetail_status'] = row.prdetail_status
        elif action == "delete":
            formData = dict(request.form)
            if table == "tiers": 
                result = payroll.Tier().deleteTier(db, list(key))
                if result == "SUCCESS":
                    return redirect("/payroll/tiers?msg=" + result)
                else:
                    response["messages"] = result    
            elif table == "details":    
                result = payroll.Payroll().deletePayroll(db, list(key))
                if result == "SUCCESS":
                    return redirect("/payroll/details?msg=" + result)
                else:
                    response["messages"] = result     
    elif key == None and action != None and table != None and request.method == 'GET':
        response["messages"] = "ERROR_ID_NOT_SPECIFIED"     
          
    response["formData"] = formData
    response["payrolls"] = payroll.Payroll().fetchPayrollsWithDetailCount(db)    
    response["tiers"] = payroll.Tier().fetchTiers(db)  
    response["bonuses"] = payroll.PayrollDetail().fetchBonusPayrollDetails(db)      
    return render_template("payroll.html", response=response)       

@app.route("/people",  defaults={'table': None, 'action' : None, 'key': None }, methods=['GET'])
@app.route("/people/<table>", defaults={'action' : None, 'key': None }, methods=['GET'])
@app.route("/people/<table>/<action>", defaults={'key': None}, methods=['GET','POST'])
@app.route("/people/<table>/<action>/<key>", methods=['GET','POST'])
def managePeople(table, action, key):
    if 'userSession' not in session:        
        return redirect(url_for('login'))
    if table == None:
        return redirect("/people/employees")    
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = formData = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']
    response["table"] = table
    response["action"] = action
    response["key"] = key
    response["formData"] = formData
    response["formData"]["date_of_birth"] = "2004-01-01"

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        response["formData"] = formData
        if action == "create":
            response["messages"] = utils.validateFormData(formData)
            if "ERROR" in response["messages"]:
                return render_template("people.html", response=response)
            if table == "employees": 
                response["messages"] = users.Employee().createEmployeeForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/people/employees?msg=" + response["messages"])      
            elif table == "contractors":
                formData["ext_type"] = "CONTRACTOR"
                consultant_profile = list(access.Profile().fetchProfiles(db, queryParams=" profile_name = 'CONTRACTOR'", queryLimit="1"))
                formData["profile_id"] = consultant_profile[0].id
                response["messages"]  = users.External().createExternalForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/people/employees?msg=" + response["messages"])      
            elif table == "consultants":
                formData["ext_type"] = "CONSULTANT"
                consultant_profile = list(access.Profile().fetchProfiles(db, queryParams=" profile_name = 'CONSULTANT'", queryLimit="1"))
                formData["profile_id"] = consultant_profile[0].id
                response["messages"] = users.External().createExternalForm(db, formData)
                if "ERROR" not in response["messages"]:
                    return redirect("/people/employees?msg=" + response["messages"])      
            del formData["password"]
        elif action == "edit": 
            if table == "employees":
                response["messages"]  = users.Employee().editEmployeeForm(db, formData)          
                if "ERROR" not in response["messages"]:
                    return redirect("/people/employees?msg=" + response["messages"])      
            elif table == "contractors":
                pass
    
    if key != None:        
        if action == "read":
            pass
        elif action == "edit":
            if table == "employees": 
                result = users.Employee().fetchEmployeeById(db, key)
                if result != None:
                    for row in result:                
                        formData["first_name"] = row.first_name
                        formData["last_name"] = row.last_name
                        formData["email"] = row.email       
                        formData["username"] = row.username       
                        formData["date_of_birth"] = row.user_dob       
                        formData["phone_number"] = row.phone_number    
                        formData["profile_id"] = row["profile_id"]    
                        formData["manager_id"] = row.manager_id    
                        formData["tier_id"] = row.tier_id    
                        formData["addr_line"] = row.addr_line     
                        formData["addr_city"] = row.addr_city     
                        formData["addr_state"] = row.addr_state     
                        formData["addr_country"] = row.addr_country     
                        formData["addr_zip"] = row.addr_zip     
        elif action == "delete":
            formData = dict(request.form)
            result = access.Profile().deleteProfiles(db, list(key))
            if result == "SUCCESS":
                return redirect("/access?msg=" + result)
            else:
                response["messages"] = result         
    elif key == None and action != None and table != None and request.method == 'GET':
        response["messages"] = "ERROR_ID_NOT_SPECIFIED"

    response["formData"] = formData
    response["employees"] = users.Employee().fetchEmployeesWithDetails(db, queryParams=" person.profile_id = profile.id AND person.user_type = 'employee' AND person.id = employee.person_id ORDER BY person.id DESC")
    response["contractors"] = users.External().fetchExternalsWithDetails(db, queryParams=" person.profile_id = profile.id AND external.ext_type = 'CONTRACTOR' AND person.user_type = 'external' AND person.id = external.person_id ORDER BY person.id DESC")
    response["consultants"] = users.External().fetchExternalsWithDetails(db, queryParams=" person.profile_id = profile.id AND external.ext_type = 'CONSULTANT' AND person.user_type = 'external' AND person.id = external.person_id ORDER BY person.id DESC")
    return render_template("people.html", response=response)   
    

@app.route("/access",  defaults={'table': None, 'action' : None, 'key': None }, methods=['GET'])
@app.route("/access/<table>", defaults={'action' : None, 'key': None }, methods=['GET'])
@app.route("/access/<table>/<action>", defaults={'key': None}, methods=['GET','POST'])
@app.route("/access/<table>/<action>/<key>", methods=['GET','POST'])
def manageAccess(table, action, key):
    if 'userSession' not in session:        
        return redirect(url_for('login'))
        
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = formData = profileAccessLines = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']
    response["table"] = table
    response["action"] = action
    response["key"] = key
    response["formData"] = formData
    response["profileAccessLines"] = profileAccessLines

    if request.args.get('msg') != None:
        response["messages"] = request.args.get('msg')

    if request.method == 'POST':
        formData = dict(request.form)
        if action == "create":            
            if table == "profiles":                
                response["messages"]  = access.Profile().createProfileWithAccess(db, None, formData)
            if "ERROR" not in response["messages"]:
                return redirect("/access?msg=" + response["messages"])
        elif action == "edit": 
            if table == "profiles":
                response["messages"]  = access.Profile().editProfileForm(db, formData)          
                if "ERROR" not in response["messages"]:
                    return redirect("/access?msg=" + response["messages"])      
            elif table == "profileaccess":
                pfaList = dict(request.form)
                del pfaList["profile_id"]
                response["messages"] = access.ProfileAccess().bulkEditProfileAccessForm(db, pfaList)
                return redirect("/access/profiles/read/" + request.form["profile_id"] + "?msg=" + response["messages"])

    if key != None:
        if action == "read":
            queryParams = " profile.id = '" + key + "' " 
            response["profileDetails"] = access.Profile().fetchProfiles(db, queryParams=queryParams, queryLimit="1")
            queryParams += " AND person.profile_id = profile.id" 
            response["profileAssignments"] = access.Profile().fetchProfileAssignment(db, queryParams=queryParams)
            response["profileAccess"] = access.ProfileAccess().fetchProfileAccessByProfile(db, key)
            return render_template("access.html", response=response)    
        elif action == "edit" and table == "profiles":
            queryParams = " profile.id = '" + key + "' " 
            result = access.Profile().fetchProfiles(db, queryFields="profile_name, profile_descr, profile_active",queryParams=queryParams, queryLimit="1")
            for row in result:                
                formData["profile_name"] = row.profile_name
                formData["profile_descr"] = row.profile_descr
                formData["profile_active"] = row.profile_active           
        elif action == "delete":
            formData = dict(request.form)
            response["messages"] = access.Profile().deleteProfiles(db, list(key))
            if "ERROR" not in response["messages"]:
                return redirect("/access?msg=" + response["messages"])
    elif key == None and action != None and table != None and request.method == 'GET':
        response["messages"] = "ERROR_ID_NOT_SPECIFIED"
    response["formData"] = formData
    response["profiles"] = access.Profile().fetchProfilesWithPersonCount(db)
    response["defaultviews"] = access.View().fetchViews(db)
    return render_template("access.html", response=response)   

@app.route("/fetchData/<table>", defaults={'limit': 30})
@app.route("/fetchData/<table>/<limit>")   
def fetchData(table, limit):
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    if table == "profiles":
        results = access.Profile().fetchProfiles(db)
        response = [{
            "id": row.id , 
            "field_name" : row.profile_name    
        } for row in results]
    elif table == "tiers":
        results = payroll.Tier().fetchTiers(db)
        response = [{
            "id": row.id , 
            "field_name" : row.tier_name    
        } for row in results]
    elif table == "persons":
        results = users.Person().fetchPersons(db, queryParams=" user_type != 'candidate' ")
        response = [{
            "id": row.id , 
            "field_name" : row.last_name + ( ", " + row.first_name  if row.first_name != "" else "" )
        } for row in results]
    elif table == "accounts":
        results = accounts.Account().fetchAccounts(db)
        response = [{
            "id": row.id , 
            "field_name" : row.acc_name    
        } for row in results]
    elif table == "projects":
        results = accounts.Project().fetchProjects(db,queryParams="project_status = 'ACTIVE'")
        response = [{
            "id": row.id , 
            "field_name" : row.description    
        } for row in results]
    elif table == "myprojects":
        queryParams=" projectassignment.person_id = person.id AND projectassignment.project_id = project.id AND project.project_status = 'ACTIVE' AND projectassignment.person_id = '" + str(session['userSession']['id']) + "' "
        results = accounts.ProjectAssignment().fetchProjectAssignmentWithDetails(db, queryParams=queryParams)
        response = [{
            "id": row.id , 
            "field_name" : row.description    
        } for row in results]
    elif table == "managers":
        results = users.Employee().fetchManagers(db)
        response = [{
            "id": row.id , 
            "field_name" : row.last_name + ( ", " + row.first_name  if row.first_name != "" else "" )
        } for row in results]
    elif table == "views":
        results = utils.fetchSidebarLinks(db, session['userSession']["username"])    
        response = [{
            "id": row.view_name , 
            "profile_name" : row.view_group    
        } for row in results]

    if results != None:
        return jsonify({
            "results" : response})    
    else:
        return jsonify({
             table : []
        }), 201

@app.route("/createDatabase")
def createDB():
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)
    
    try:
        results = db.createDatabase()
    except Exception as err:
        print(err)
        return jsonify({ "error": "error" })
    return jsonify({ "result": [ item for item in results] })

@app.route("/dropDatabase")
def dropDB():
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)
    
    try:
        db.dropDatabase()
    except Exception as err:
        print(err)
        return jsonify({ "error": "error" })
    return jsonify({ "result": "SUCCESS" })

@app.route("/<table>/<action>/<key>", methods=['GET','POST'])
def viewPerson(table, action, key):
    if 'userSession' not in session:        
        return redirect(url_for('login'))
          
    global db
    if db == None:
        db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

    response = formData = {}
    response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
    response["hasSidebar"] = True
    response["userSession"] = session['userSession']
    response["table"] = table
    response["action"] = action
    response["key"] = key

    if request.method == 'POST':
        pass
    else:
        if table == "employee":
            pass
        elif table == "contractor":
            pass
        elif table == "consultant":
            pass
        elif table == "candidate":        
            response["candidateDetails"] = users.Candidate().fetchCandidateById(db, key)
            response["candidateApplications"] = jobs.JobApplication().fetchJobApplicationWithDetails(db)      
    return render_template("person.html", response=response)   

@app.errorhandler(404)
@app.route("/unauthorized")
def unauthorized(e=None):
    if 'userSession' not in session:        
        return redirect(url_for('login'))
    else:
        global db
        if db == None:
            db = DatabaseConnect(AppConfig.SQLALCHEMY_DATABASE_URI)

        response = {}
        response["views"] = utils.fetchSidebarLinks(db, session['userSession']["username"])    
        response["hasSidebar"] = True 
        response["userSession"] = session['userSession'] 
        return render_template('404.html', response=response)

if __name__ == "__main__":
    app.run(debug=True)

