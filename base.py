from flask import Flask, render_template, request, session, redirect, url_for, g
from sqlalchemy import create_engine, text, update
import secrets 

app = Flask(__name__)
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module

conn_str = "mysql://root:cset155@localhost/bankdb" # connects to DataBase
engine = create_engine(conn_str, echo=True)
conn = engine.connect()
# -----------------------------
# ----------------------Before each load------------------------------------
@app.before_request # Before each request it will look for the values below
def load_user():
    if "TestID" in session:
        g.TestID = session["TestID"]
    else:
        g.TestID = None
    if "Admin" in session:
        g.Admin = session["Admin"]
    else:
        g.Admin = None
        
    if "User" in session:
        g.User = session["User"]
    else:
        g.User = None
# ---------------------------
@app.route("/", methods = ["GET"])   #This will be what sends us to login
def Base():
    return render_template("Login.html")

@app.route("/", methods = ["POST"])

def LogIn():
    try:
        ValidUser = (conn.execute(text("select username, password from user Where username = :username"),request.form ).fetchall() + conn.execute(text("select username, password from admin Where username = :username"),request.form ).fetchall())
        # print(ValidUser)
        # print(ValidUser[0][0])
        User={}
        if conn.execute(text("Select username From user Where username in(:username)"),{"username": ValidUser[0][0]}).fetchone(): #Checks if ValidUser is in DB-Student Table 
            User["Name"] = conn.execute(text("Select username From user Where username in(:username)"),{"username": ValidUser[0][0]}).fetchone()[0] #grabs first_name from DB-Student Table
            # User["ID"] = conn.execute(text("Select Sid From student Where Email in(:Email)"),{"Email": ValidUser[0][0]}).fetchone()[0]
            Admin=False 
        else: # if ValidUser is not in DB-Student Table
            User["Name"] = conn.execute(text("Select username From admin Where username in(:username)"),{"username": ValidUser[0][0]}).fetchone()[0]
            Admin=True
            print("Admin")
        session["Admin"] = Admin # Storing Student in SessionStorage to see across mutliple requests
        g.Admin=Admin # Makes Student availabe on current request for template
        session["User"] = User # Storing User in SessionStorage to see across mutliple requests
        g.User = User # Makes UserName availabe on current request for template
        print(f"User Name: {g.User['Name']}")
        
        return render_template("HomePage.html")
    except Exception as e:
        print(f"Error: {e}") 
        return render_template("Login.html", error = "User or password is not correct", success = None)
#--------------Create Account--------------
@app.route("/Register", methods = ['GET'])
def getAccount():
    
    return render_template("Register.html")

#--------SIGN UP----------------
@app.route("/Register", methods = ['POST'])
def createAccount():   
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    SSN = request.form.get("SSN")
    phone_number = request.form.get("PhoneNumber")
    address = request.form.get("Address")
    username = request.form.get("Username")
    password = request.form.get("password")
    
    try:
        conn.execute(text("""INSERT INTO create_info_account (first_name, last_name, SSN, phone_number, address, username, password )
                            VALUES (:first_name, :last_name, :SSN, :phone_number, :address, :username, :password)"""),
                        {"first_name": first_name,
                            "last_name": last_name,
                            "SSN": SSN ,
                            "phone_number": phone_number,
                            "address": address,
                            "username": username,
                            "password": password}) #Insert into DB-User Table
        conn.commit()
        return render_template("Register.html", error = None, success = "Successfull")
    except Exception as e:
        print(f"Error: {e}") 
        return render_template("Register.html", error = "Failed", success = None) 
        
# -----------------ADMIN ADMINPAGE---------
@app.route("/Admin")
def Admin():
    try:
        print("ENTERING ADMIN PAGE")
        PendingUsers =conn.execute(text("""Select * from create_info_account """)).fetchall()
        print(PendingUsers)
        return render_template("AdminPage.html",PendingUsers = PendingUsers)
    except Exception as e:
        print(f"YOU FAIL: {e}")
        return render_template("AdminPage.html")
    
# -----------------USER HOMEPAGE --------------------
@app.route("/Homepage")
def UserPage():
    g.User=session["User"]
    try:
        return render_template("HomePage.html")
    except Exception as e:
        print(f"YOU FAIL: {e}")
        
#---------------end--------- 
if __name__ == '__main__':
        app.run(debug=True)