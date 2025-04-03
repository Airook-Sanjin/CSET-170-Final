from flask import Flask, render_template, request, session, redirect, url_for, g
from sqlalchemy import create_engine, text, update, Row
import secrets 
from random import randint

app = Flask(__name__)
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module

conn_str = "mysql://root:cset155@localhost/bankdb" # connects to DataBase
engine = create_engine(conn_str, echo=True, future=True) # Future =True ensures that SQLAlchemy returns the results objects, dictionary-like access
conn = engine.connect()

def GenerateBankNum():
    SSN = request.form.get("SSN")
    BankAccNUm = randint(100000000000000,99999999999999999)
    print(BankAccNUm)
    if conn.execute(text("""select bank_acc_num 
                            from user 
                            where bank_acc_num like (:BankAccNum);"""),{"BankAccNum":BankAccNUm}).fetchone() is not None:
        print("Bank Acc NUm Already assigned to another user")
        GenerateBankNum()
    else:
        return BankAccNUm

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
        ValidUser = conn.execute(text("""SELECT username, password from user 
                                          Where username = :username AND password = :Password 
                                          UNION
                                          SELECT username, password from admin 
                                          WHERE username = :username AND password = :Password"""),{"username": request.form.get("username"), "Password":request.form.get("Password")}).mappings().fetchone() #Uses Mappings to convert the result in dictionaries- Uses
        
        result = conn.execute(text("""
                              SELECT username,'user' AS role FROM user 
                              WHERE username= :username AND password=:password
                              UNION
                              SELECT username,'admin' AS role FROM admin 
                              WHERE username = :username AND password = :password"""),{"username": ValidUser["username"], "password":ValidUser["password"]}).mappings().fetchone()
        print(result["username"])
        if result: #checks if user exists
            role = result["role"]
            
            session["User"] = {"Name":result["username"],"Role":role} # Storing User in SessionStorage to see across mutliple requests
            
            g.user = session["User"]# Makes UserName availabe on current request for template
            
            if result["role"] == "admin":
                session["Admin"] = True # Storing Admin in SessionStorage to see across mutliple requests
                
                g.Admin = True # Makes Admin availabe on current request for template
                
                return redirect(url_for("Admin")) # Looks for the function named "Admin" then finds the route associated with that function and generates the URL
            else:
                session["Admin"] =False # Storing Admin in SessionStorage to see across mutliple requests
                
                g.Admin = False # Makes Admin availabe on current request for template
                
                return redirect(url_for("UserPage")) # Looks for the function named "UserPage" then finds the route associated with that function and generates the URL
        else:
            return render_template("Login.html", error = "An error occured please try again",success = None)
        
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
        
        conn.execute(text("""INSERT INTO admin (SSN)
                            VALUES (:SSN)"""),
                        {"SSN": SSN}) #Insert into DB-User Table
        
        conn.commit()
        return render_template("Register.html", error = None, success = "Successfull")
    except Exception as e:
        print(f"Error: {e}") 
        return render_template("Register.html", error = "Failed", success = None) 
        
# -----------------ADMIN ADMINPAGE---------
@app.route("/AdminDashboard")
def Admin():
    try:
        print("ENTERING ADMIN PAGE")
        # Fetch all users with their status
        PendingUsers = conn.execute(text("""
            SELECT c.SSN, c.username, c.first_name, c.last_name, c.address, c.phone_number, a.form_number, a.status, c.password
            FROM admin AS a
            JOIN create_info_account AS c
            ON a.SSN = c.SSN
        """)).fetchall()
        print(PendingUsers)
        return render_template("AdminPage.html", PendingUsers=PendingUsers)
    except Exception as e:
        print(f"YOU FAIL 2: {e}")
        return render_template("AdminPage.html", success=None)
    
@app.route("/AdminDashboard", methods = ['POST'])
def AdminPOST():
    try:
       # Get the SSN of the user being approved
        SSN = request.form.get("SSN")
        username = request.form.get("username")
        password = request.form.get("password")
        
        if SSN:
            # Update the status of the user in the database
            conn.execute(text("UPDATE admin SET status = 1 WHERE SSN = :SSN"),
                {"SSN": SSN})
            print(f"Approved user with SSN: {SSN}")
        
        
        # Fetch the updated list of pending users
        PendingUsers = conn.execute(text("""
                                         SELECT c.SSN, c.username, c.first_name, c.last_name, c.address, phone_number,a.form_number, a.status, c.password
                                            FROM admin AS a
                                            JOIN create_info_account AS c
                                            ON a.SSN = c.SSN; where status = 0""")).fetchall()
        
        
        conn.execute(text("""INSERT INTO user (bank_acc_num,username, password, SSN )
                            VALUES (:bank_acc_num,:username, :password, :SSN)"""),
                        {"username": username,
                            "password": password,
                            "SSN": SSN,
                            "bank_acc_num":GenerateBankNum() })
        conn.commit()
        
        
        
        return render_template("AdminPage.html", PendingUsers=PendingUsers, success = "User Approved")
    except Exception as e:
        print(f"YOU FAIL 1: {e}")
        return render_template("AdminPage.html", success = None)
    

    
# -----------------USER HOMEPAGE --------------------
@app.route("/Homepage")
def UserPage():
    try:
        
        return render_template("HomePage.html")
    
    except Exception as e:
        print(f"YOU FAIL: {e}")

# -----------------VIEW ACCOUNT --------------------
@app.route("/ViewAccount")
def getViewAcc():
    g.User=session["User"]
    try:
        return render_template("ViewAccount.html")
    except:
        return render_template("ViewAccount.html")
#---------------end--------- 
if __name__ == '__main__':
        app.run(debug=True)
        
