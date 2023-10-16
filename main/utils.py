from .models import *
from .config import AppConfig
from datetime import date, timedelta, datetime
import re

def fetchSidebarLinks(db, username):    
    viewData = {}
    if username != None:
        results = access.ProfileAccess().fetchProfileAccessByUsername(db, username=username, viewType="PAGE")
    else:
        results = access.View().fetchViews(db, queryParams="view_group = \'PUBLIC\'")
        
    for row in results:
        if row.view_group not in viewData:
            viewData[row.view_group] = []
        viewData[row.view_group].append(row)
    
    return viewData 

def fetchSearchableViews(db, username):    
    return access.ProfileAccess().fetchProfileAccessByUsername(db, username)
    
def validateUserAccess(db, username, viewUrl, action=None):    
    if username != None:
        results = access.ProfileAccess().fetchProfileAccessByUsername(db, username, True)
    else:
        results = access.View().fetchViews(db, queryParams="view_group = \'PUBLIC\'")
        
    for row in results:
        if row.view_url == "/" and row.view_url == viewUrl:
            return True
        elif row.view_url in viewUrl and row.view_url != "/":
            return True
    return False     

def changePassword(db, formData):    
    pass

def validateFormData(formData):
    errors = []
    if "email" in formData:
        if not regexCheck(formData["email"], AppConfig.REGEX["EMAIL"]):
            errors.append("- Invalid email address.")
    
    if "password" in formData:
        if not regexCheck(formData["password"], AppConfig.REGEX["PASSWORD"]):
            errors.append("- Password should be a minimum of 8 characters long and contain atleast one each of number, uppercase and special character.")

    if "newpassword" in formData and "newpasswordrepeat" in formData :
        if formData["newpassword"] != formData["newpasswordrepeat"]:
            errors.append("- New passowrds entered do not match.")

        if not regexCheck(formData["newpassword"], AppConfig.REGEX["PASSWORD"]):
            errors.append("- Password should be a minimum of 8 characters long and contain atleast one each of number, uppercase and special character.")

    if "date_of_birth" in formData:
        result = dateDiff(date.today(), datetime.strptime(formData["date_of_birth"], '%Y-%m-%d').date(), "years")
        if result < 18:
            errors.append("- You need to be at least 18 years old to apply for the job.")

    if "status_date" in formData:
        result = dateDiff(date.today(), datetime.strptime(formData["status_date"], '%Y-%m-%d').date(), "days")
        if result > 7:
            errors.append("- Status date cannot be older than 1 week.")

    if "vac_startdate" in formData and "vac_enddate" in formData:
        result = dateDiff(datetime.strptime(formData["vac_enddate"], '%Y-%m-%d').date(), datetime.strptime(formData["vac_startdate"], '%Y-%m-%d').date(), "years")
        if result < 0:
            errors.append("- Start date cannot be later than End date.")

    if "edu_hightest_year" in formData:
        if int(formData["edu_hightest_year"]) < 1900 or int(formData["edu_hightest_year"]) > 2050:
            errors.append("- Please enter a valid year.")

    print("ERROR", errors)
    return "SUCCESS" if errors == [] else "ERROR: Please correct the below errors before submitting the form.<br/>" + '<br/>'.join([ item for item in errors])

def dateDiff( date1, date2, resultType):
    diff = date1 - date2
    if resultType == "years":
        return diff.days//365
    elif resultType == "days":
        return diff.days

def regexCheck( value, pattern):    
    regexString = r''+ pattern
    if re.fullmatch(regexString, value):
        return True
    return False 