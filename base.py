from flask import Flask, render_template, request, session, redirect, url_for, g
from sqlalchemy import create_engine, text, update
import secrets 

app = Flask(__name__)
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module

# conn_str = "DatabaseConnection link" # connects to DataBase
# engine = create_engine(conn_str, echo=True)
# conn = engine.connect()
# -----------------------------
# @app.route("/")
# def base():
#     try:
#         return render_template("Base.html")
#     except Exception as e:
#         print(e)
        
@app.route("/", methods = ["GET"])   #This will be what sends us to login
def Base():
    return render_template("Login.html")

@app.route("/", methods = ["POST"])

def LogIn():
    try:
        # ValidUser = (conn.execute(text("select Email, password from student Where Email = :Email"),request.form ).fetchall() + conn.execute(text("select Email, password from teacher Where Email = :Email"),request.form ).fetchall())
        # User={}
        # if conn.execute(text("Select Email From student Where Email in(:Email)"),{"Email": ValidUser[0][0]}).fetchone(): #Checks if ValidUser is in DB-Student Table 
        #     User["Name"] = conn.execute(text("Select first_name From student Where Email in(:Email)"),{"Email": ValidUser[0][0]}).fetchone()[0] #grabs first_name from DB-Student Table
        #     User["ID"] = conn.execute(text("Select Sid From student Where Email in(:Email)"),{"Email": ValidUser[0][0]}).fetchone()[0]
        #     Student=True 
        #     print(User["Name"])
        # else: # if ValidUser is not in DB-Student Table
        #     Student=False
        #     User["Name"] = conn.execute(text("Select first_name From teacher Where Email in(:Email)"),{"Email": ValidUser[0][0]}).fetchone()[0] #grabs first_name from DB-Teacher Table
        #     User["ID"] = conn.execute(text("Select tid From teacher Where Email in(:Email)"),{"Email": ValidUser[0][0]}).fetchone()[0]
        #     print(User["Name"])
        # session["Student"] = Student # Storing Student in SessionStorage to see across mutliple requests
        # g.Student=Student # Makes Student availabe on current request for template
        # session["User"] = User # Storing User in SessionStorage to see across mutliple requests
        # g.User = User # Makes UserName availabe on current request for template
        # print(g.User["Name"])
        
        return render_template("Accounts.html")
    except Exception as e:
        print(f"Error: {e}") 
        return render_template("Login.html", error = "User or password is not correct", success = None)
#-------------------Create Account---------
@app.route("/Register", methods = ['GET'])
def getAccount():
    
    return render_template("Register.html")

#--------SIGN UP----------------
@app.route("/Register", methods = ['POST'])
def createAccount():   
    # # debugging checking if we are getting data
    # data = request.form
    # print(data)
    
    try:
    #     RadioValue= request.form["Teach-Stud"]
    #     if RadioValue == "1": #Checks whether Student or Teacher was clicked
    #         # prevID = conn.execute(text("select Sid from student order by Sid desc Limit 1;")).fetchone() #Grabs last ID from Student table
    #         if not prevID: # If There is no prevID, newID is 1
    #             newID = 1
    #         else:
    #             newID = int(prevID[0])+1 # Increments 1 from prevID
            
    #         # conn.execute(text("insert into student(Sid, first_name, last_name, password, Email) values (:Sid, :first_name, :last_name, :password, :Email)"), {"Sid": newID, "first_name":request.form["first_name"], "last_name":request.form["last_name"],"password":request.form["password"],"Email":request.form["Email"]}
    #                      )
    #         # conn.commit() 
            
    #         # result = conn.execute(text('select * from student')).fetchall() #For Debugging
            
    #         for row in result:
    #             print(row)
    #     else:
    #         # prevID = conn.execute(text("select Tid from teacher order by Tid desc Limit 1;")).fetchone() #Grabs last ID from Teacher table
    #         if not prevID: # If There is no prevID, newID is 1
    #             newID = 1
    #         else:
    #             newID = int(prevID[0])+1 # Increments 1 from prevID
                
    #         # conn.execute(text("insert into teacher(Tid, first_name, last_name, password, Email) values(:Tid, :first_name, :last_name, :password, :Email)"), {"Tid": newID, "first_name":request.form["first_name"], "last_name":request.form["last_name"],"password":request.form["password"], "Email":request.form["Email"]})
            
    #         # conn.commit()
            
    #         # result = conn.execute(text('select * from teacher')).fetchall()
            
    #         for row in result:
    #             print(row)
            
        return render_template("Register.html", error = None, success = "Successfull")
    except Exception as e:
        print(f"Error: {e}") 
        return render_template("Register.html", error = "Failed", success = None) 
        
        
#---------------end--------- 
if __name__ == '__main__':
        app.run(debug=True)