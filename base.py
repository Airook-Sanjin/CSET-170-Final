from flask import Flask, render_template, request, session, redirect, url_for, g
from sqlalchemy import create_engine, text, update, Row
import secrets 
from jinja2 import Environment
from random import randint
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.secret_key = secrets.token_hex(15) # Generates and sets A secret Key for session with the secrets module
app.jinja_env.filters['number_format']= lambda value:'{:,.2f}'.format(float(value)) # Shows two devcimals

conn_str = "mysql://root:cset155@localhost/bankdb" # connects to DataBase
engine = create_engine(conn_str, echo=True, future=True) # Future =True ensures that SQLAlchemy returns the results objects, dictionary-like access
conn = engine.connect()

def GenerateBankNum():
    SSN = request.form.get("SSN")
    BankAccNUm = randint(100000000000000,99999999999999999)
    print(BankAccNUm)
    if conn.execute(text("""
        SELECT bank_acc_num 
        FROM user 
        WHERE bank_acc_num LIKE (:BankAccNum);"""),{"BankAccNum":BankAccNUm}).fetchone() is not None:
        print("Bank Acc NUm Already assigned to another user")
        GenerateBankNum()
    else:
        return BankAccNUm
def GenerateCardNum():
    SSN = request.form.get("SSN")
    CardNum= randint(1000000000000000,9999999999999999)
    print(CardNum)
    if conn.execute(text("""
        Select card_number
        FROM credit_debit_card
        WHERE card_number like(:CardNum)"""),{"CardNum": CardNum}).fetchone() is not None: # Checks if the bank number is already in DB
        print("Card Number is already assigned to another user")
        GenerateCardNum()
    else:
        return CardNum
def GenerateCVV():
    CVV = randint(100,999) # Generates a random 3-Digit Number
    print(f"CVV : {CVV}")
    return CVV
def GenerateDate():
    Date = datetime.now() # gets current date
    ExpiryDate = Date.replace(year=Date.year+4) # Adds 4 to the year
    return ExpiryDate.strftime('%Y-%m-%d') # Puts it in a format that is acceptable for DataType: Date
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

@app.route("/", methods=["POST"])
def LogIn():
    try:
        # Fetch the user credentials from the database
        credentials = conn.execute(text("""
            SELECT username, password FROM user 
            WHERE username = :username
            UNION
            SELECT username, password FROM admin 
            WHERE username = :username
        """), {"username": request.form.get("username")}).mappings().fetchone()

        if credentials:
            # Verify the password
            input_password = request.form.get("Password")
            stored_password = credentials["password"]

            if bcrypt.checkpw(bytes(input_password, encoding="utf-8"), bytes(stored_password, encoding="utf-8")):
                # Fetch user role
                result = conn.execute(text("""
                    SELECT username, 'user' AS role FROM user 
                    WHERE username = :username
                    UNION
                    SELECT username, 'admin' AS role FROM admin 
                    WHERE username = :username
                """), {"username": credentials["username"]}).mappings().fetchone()

                role = result["role"]
                session["User"] = {"Name": result["username"], "Role": role}
                g.user = session["User"]

                if role == "admin":
                    session["Admin"] = True
                    g.Admin = True
                    return redirect(url_for("Admin"))
                else:
                    session["Admin"] = False
                    g.Admin = False
                    return redirect(url_for("UserPage"))
            else:
                return render_template("Login.html", error="Invalid username or password.", success=None)
        else:
            return render_template("Login.html", error="Invalid username or password.", success=None)
    except Exception as e:
        print(f"Error: {e}")
        return render_template("Login.html", error="An error occurred. Please try again.", success=None)
    
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
        # Hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(bytes(password, encoding="utf-8"), salt)
       
        conn.execute(text("""INSERT INTO create_info_account (first_name, last_name, SSN, phone_number, address, username, password )
                            VALUES (:first_name, :last_name, :SSN, :phone_number, :address, :username, :password)"""),
                        {"first_name": first_name,
                            "last_name": last_name,
                            "SSN": SSN ,
                            "phone_number": phone_number,
                            "address": address,
                            "username": username,
                            "password": hashed_password.decode("utf-8")}) #Insert into DB-User Table
        
        conn.execute(text("""INSERT INTO admin (SSN)
                            VALUES (:SSN)"""),
                        {"SSN": SSN}) #Insert into DB-admin Table
        
        conn.commit()
        return render_template("Register.html", error = None, success = "Successfull")
    except Exception as e:
        print(f"Error: {e}") 
        return render_template("Register.html", error = "ERROR!", success = None) 
        
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
        g.User = session["User"]
        
        # Fetch card details for the logged-in user
        cards = conn.execute(text("""
            SELECT ccc.card_id, ccc.name AS card_name, ccc.card_number, ccc.balance
            FROM credit_debit_card AS ccc
            JOIN user AS u
            ON ccc.bank_acc_num = u.bank_acc_num
            WHERE u.username = :username;
        """), {"username": g.User["Name"]}).mappings().fetchall()
        
        # Debugging: Print card details
        for card in cards:
            print(f"Card ID: {card['card_id']}, Card Name: {card['card_name']}, Balance: {card['balance']}")
        
        # Pass the cards list to the template
        return render_template("HomePage.html", cards=cards)
    
    except Exception as e:
        print(f"YOU FAIL: {e}")
        return render_template("HomePage.html", cards=[])    
# ------------------------SELECTINGCARDTYPE------------
@app.route("/SelectingCardType")
def SelectingCardType():
    AccountType = request.args.get("AccountType")
    try:
        print("ENTERING CARD CREATION")
        return render_template("SelectCardType.html",AccountType = AccountType)
    except Exception as  e:
        print(f"ERROR: {e} ")
        return render_template("SelectCardType.html")

# ----------------------CARDCREATION--------------------
@app.route("/CreateCard",methods=["GET"])

def CardCreate():
    g.user = session["User"] # Makes UserName availabe on current request for template
    CardType = request.args.get("CardType")
    try:
        UserInfo = conn.execute(text("""
            SELECT CONCAT(repeat('*',length(cia.SSN)-4),RIGHT(cia.SSN,4)) AS SSN,
            Concat(cia.first_name,' ', cia.last_name) as 'FullName', cia.address AS Address, cia.phone_number AS 'PhoneNumber'
            FROM user AS u JOIN create_info_account as cia WHERE u.SSN = cia.SSN AND cia.username = :username"""),
            {"username":g.user["Name"]}).mappings().fetchone() # Gets User Info
        print(UserInfo["SSN"]) # FOR DEBUGGING
        print("ENTERING CARD CREATION") # FOR DEBUGGING
        return render_template("CreateCard.html",UserInfo=UserInfo,CardType=CardType)
    except Exception as  e:
        print(f"ERROR: {e} ")
        return render_template("CreateCard.html")
    
@app.route("/CreateCard",methods=["POST"])
def CardSend():
    print('Creating CARD')
    g.user = session["User"] # Makes UserName availabe on current request for template
    
    try:
        UserInfo = conn.execute(text("""
            SELECT u.bank_acc_num as BankAccNum,cia.SSN AS SSN,
            Concat(cia.first_name,' ', cia.last_name) as 'FullName', 
            cia.address AS Address, cia.phone_number AS 'PhoneNumber'
            FROM user AS u JOIN create_info_account as cia WHERE u.SSN = cia.SSN AND cia.username = :username"""),
            {"username":g.user["Name"]}).mappings().fetchone() # GEts User Info
        
        conn.execute(text("""
            INSERT INTO credit_debit_card
            (name,card_number,ccv,expiry,bank_acc_num,status,type)
            Values
            (:name,:cardNumber,:CVV,:expiry,:BankAccNum,:status,:type)"""),
            {"name":request.form.get('Cardtype'),"cardNumber": GenerateCardNum(),
            "CVV":GenerateCVV(),"expiry":GenerateDate(),"BankAccNum":UserInfo["BankAccNum"],
            "status":1,"type":request.form.get('Cardtype')}) #Inserts the new card info into the db
        print(UserInfo["SSN"]) #FOR DEBUGGING PURPOSES
        print("CardCreated") #FOR DEBUGGING PURPOSES
        conn.commit() # Commits DB
        return render_template("CreateCard.html",Error= None,Success = 'Card Created',UserInfo=UserInfo,CardType=request.form.get('Cardtype'))
    except Exception as  e:
        print(f"ERROR: {e} ")
        return render_template("CreateCard.html",Error="Card Not Created",Success=None,UserInfo=UserInfo,CardType=request.form.get('Cardtype'))
# -----------------VIEW ACCOUNT --------------------
@app.route("/ViewAccount", methods=["GET"])
def getViewAcc():
    try: 
        g.User = session["User"]
        card_id = request.args.get("card_id")
        
        AllAccounts = conn.execute(text("""
            SELECT ccc.card_id as CardID,u.username as username, ccc.name AS card_name, ccc.card_number as CardNum, u.bank_acc_num as BankAccNum
            FROM credit_debit_card AS ccc
            JOIN user AS u
            ON ccc.bank_acc_num = u.bank_acc_num
            WHERE u.username <> :username;
        """), {"username": g.User["Name"]}).mappings().fetchall()
        if AllAccounts:
            AllAccounts = [
                {**account,
                "last_4_digits": str(account["CardNum"])[-4:]}
                for account in AllAccounts# Extract last 4 digits  
            ]
            print(f"AA: {AllAccounts}")
        #Fetch all Card ACCOUNTS of Specific User
        ListofCards = conn.execute(text("""
            SELECT ccc.card_id, ccc.name AS card_name, ccc.card_number as card_number, ccc.balance
            FROM credit_debit_card AS ccc
            JOIN user AS u
            ON ccc.bank_acc_num = u.bank_acc_num
            WHERE u.username = :username;
        """), {"username": g.User["Name"]}).mappings().fetchall()
        
        if ListofCards:
            ListofCards = [
                {**Loc,
                "last_4_digits": str(Loc["card_number"])[-4:]}
                for Loc in ListofCards# Extract last 4 digits  
            ]
            print(f'LLOC: {ListofCards}')
        # Fetch card details for the logged-in user
        card = conn.execute(text("""
           SELECT ccc.card_id, ccc.name AS card_name, ccc.card_number as card_number, ccc.balance,u.bank_acc_num as BAN
            FROM credit_debit_card AS ccc
            JOIN user AS u
            ON ccc.bank_acc_num = u.bank_acc_num
            WHERE u.username = :username AND ccc.card_id = :card_id;
        """), {"username": g.User["Name"], "card_id": card_id}).mappings().fetchone()
        
         # Add the last 4 digits of the card number to each card
        if card:
            card = {
                **card,
                "last_4_digits": str(card["card_number"])[-4:]  # Extract last 4 digits  
            }
        AllTransaction =conn.execute(text("""
            SELECT date_of_transaction as DATE, transaction_type as Type, bank_acc_num as Sender, transaction_status as Status, Amount,rec_bank_acc_num AS RBAN FROM transactions
            WHERE card_to=:CardNum and rec_bank_acc_num= :BAN"""),
            {"CardNum":card['card_number'],"BAN":card['BAN']}).mappings().fetchall()
        if AllTransaction:
            AllTransaction = [
                {**Transaction,
                "last_4_digits": str(Transaction["RBAN"])[-4:]}
                for Transaction in AllTransaction# Extract last 4 digits  
            ]
        print(AllTransaction)
        print(f"Card ID: {card['card_id']}, Card Name: {card['card_name']}, Balance: {card['balance']}")
        
            
        return render_template("ViewAccount.html", card=card,Accounts = ListofCards,AllAccounts=AllAccounts,AllTransaction=AllTransaction)
    except Exception as e:
        print(f"Error: {e}")
        return render_template("ViewAccount.html", card=None, Accounts = None,AllAccounts=None)

@app.route("/ViewAccount", methods=["POST"])
def TransferMoney():
    try:
        g.User = session["User"]
        card_id = request.args.get("card_id")
        
        
        # Fetch card details for the logged-in user
        card = conn.execute(text("""
           SELECT ccc.card_id as CardID, ccc.name AS card_name, ccc.card_number as card_number, ccc.balance,u.bank_acc_num as BAN
            FROM credit_debit_card AS ccc
            JOIN user AS u
            ON ccc.bank_acc_num = u.bank_acc_num
            WHERE u.username = :username AND ccc.card_id = :card_id;
            
        """), {"username": g.User["Name"], "card_id": card_id}).mappings().fetchone()
        # print(f"ALLACC {AllAccounts}\nLOC {ListofCards}\n Card{card}")
       # Inserts Transaction detail
        conn.execute(text("""
            INSERT INTO transactions 
            (amount,card_to,card_from,transaction_type, bank_acc_num,rec_bank_acc_num,transaction_status)
            VALUES 
            (:Amount,:CardTo,:CardFrom,:TransactionType,:BankAccNum,:RecBankAccNum,"completed")"""),
            {"Amount":request.form.get("Amount"),"CardTo":request.form.get("TransferTo"),"CardFrom":card["card_number"],
            "TransactionType":"Deposit","BankAccNum":card['BAN'],"RecBankAccNum": request.form.get("BankAccNum")})
       
       # updates Sender's Balance
        conn.execute(text("""
            Update credit_debit_card
            SET balance = balance - :NewBalance
            where bank_acc_num = :BankAccNum and card_id= :CardID"""),
            {"BankAccNum":card['BAN'],"CardID":card['CardID'],"NewBalance": request.form.get("Amount")})
       
       
        # updates reciever's Balance
        conn.execute(text("""
            Update credit_debit_card
            SET balance = balance + :NewBalance
            where bank_acc_num = :BankAccNum and card_number= :CardNum"""),
            {"BankAccNum":request.form.get("BankAccNum"),"CardNum":request.form.get("TransferTo"),"NewBalance": request.form.get("Amount")})
        
        conn.commit() # Commits DB
        return redirect(url_for("getViewAcc", card_id=card_id))
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for("getViewAcc", card_id=card_id))
  #---------------end--------------  
if __name__ == '__main__':
        app.run(debug=True)
        
