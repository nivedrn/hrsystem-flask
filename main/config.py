from datetime import timedelta
import os
class AppConfig():

    if os.getenv('INSTANCE') != None:        
        #POSTGRESQL URI
        SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") 
    else:
        #POSTGRESQL URI
        SQLALCHEMY_DATABASE_URI = "postgresql://postgres:v4ri4nt@localhost/srhsdp"
        #SQLALCHEMY_DATABASE_URI = "postgresql://nivedsdp:AGNUSWgGoZ74UpmPu3OF7njqsjVwBj6U@dpg-ce365msgqg43k3jg08jg-a.frankfurt-postgres.render.com/sdp"
        
    #SESSION SECRET KEY
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)
    REGEX = {
        "PASSWORD" : "^(?=.*\d)(?=.*[!@#$&*])(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,}$",
        "EMAIL" : "^[\w\-\.+]+@([\w\-]+\.)+[\w\-]{2,5}$"
    }

    #DEFAULT CREDS
    DFLT_PASSWORD = 'qwerty1234'