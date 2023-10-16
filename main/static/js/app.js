function toggleTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("nav-link");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

$( document ).ready(function() {
    if( document.getElementById("people-data") != null){
        people_data = $('#people-data').data();
        console.log(people_data.table);
        if(people_data.table == "consultants"){
            document.getElementById("manageConsultants").click();
            if(people_data.action == "create"){
                toggleForm('ConsultantForm');
            }
        }else if(people_data.table == "contractors"){
            document.getElementById("manageContractors").click();
            if(people_data.action == "create"){
                toggleForm('ContractorForm');
            }
        }else if(people_data.table == "employees"){
            document.getElementById("manageEmployees").click();
            if(people_data.action == "create" || people_data.action == "edit"){
                toggleForm('EmployeeForm');
                fetchData('profiles','#employee_profile_id');
                fetchData('tiers','#employee_tier_id');
                fetchData('managers','#employee_manager_id');
            }
        }else if(people_data.table == "profiles"){
            if(people_data.action == "create" || people_data.action == "edit"){
                toggleForm('ProfileForm');
            }
        }else if(people_data.table == "joblisting"){
            if(people_data.action == "create" || people_data.action == "edit"){
                toggleForm('JobListingForm');
            }
        }else if(people_data.table == "details"){
            document.getElementById("managePayroll").click();
        }else if(people_data.table == "tiers"){
            document.getElementById("manageTiers").click();
            if(people_data.action == "create" || people_data.action == "edit"){
                toggleForm('TiersForm');
            }
        }else if(people_data.table == "records"){
            document.getElementById("manageAccounts").click();
            if(people_data.action == "create" || people_data.action == "edit"){
                toggleForm('AccountsForm');
            }
        }else if(people_data.table == "projects"){
            document.getElementById("manageProjects").click();
            if(people_data.action == "create" || people_data.action == "edit"){
                toggleForm('ProjectsForm');
                fetchData('accounts','#project_account_id');
                fetchData('managers','#project_manager_id');
            }
        }else if(people_data.table == "projectassignments"){
            document.getElementById("manageProjectAssignments").click();
            if(people_data.action == "create" || people_data.action == "edit"){
                fetchData('persons','#prjasgn_person_id');
                fetchData('projects','#prjasgn_project_id');
            }
        }else if(people_data.table == "itresources"){
            if(people_data.action == "create" || people_data.action == "edit"){
                fetchData('persons','#resource_person_id');
                toggleForm('ITResourcesForm');
            }
        }else if(people_data.table == "bonus"){
            document.getElementById("manageBonuses").click();
            if(people_data.action == "create" || people_data.action == "edit"){
                fetchData('persons','#bonus_person_id');
            }
        }
    }
});

function toggleForm(formId) {
    if(document.getElementById(formId).style.display == "block"){
        document.getElementById(formId).style.display = "none";
    }else{
        document.getElementById(formId).style.display = "block";
    }
}

function autoFillEmail(username) {
    document.getElementById("employee-email").value = username + "@hrs.com";
}

function fetchData(tableName, fieldId) {
    let url = '/fetchData/' + tableName
    fetch(url)
    .then((response) => {
        console.log(response.status);
        return response.json();
    })
    .then(function(data) {
        console.log(data.results);
        let dropdown = $(fieldId);
        dropdown.empty();
        for (var i = 0; i < data.results.length; i++) {
            dropdown.append($('<option></option>').attr('value', data.results[i].id).text( data.results[i].field_name));
        }
    });
}