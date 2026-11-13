import datetime
import json
import fd_sections


# Login Interface
def login():

    with open("bank_database.json", "r") as db:
        credentials = json.load(db)
    acc_no = input("Enter your Account Number: ")

    if acc_no in credentials:
        pin = int(input("Enter your 4 Digit PIN: "))
        name = credentials[acc_no]["name"]
        if pin == credentials[acc_no]["pin"]:

            print("Account Login Successfully!")
            print("-" * 10)

            user_interface(name,acc_no=acc_no)

        else:
            print("Incorrect PIN!")

    else:
        print("No such Account Found. Create an account First!")


def user_interface(name,acc_no):

    print(f"Welcome {name} !!")
    print("----------------------------\n")
    while(True):
        print("What would you like to do?")
        print("1. Account Details")
        print("2. Deposit Money")
        print("3. Withdraw Money")
        print("4. Transfer Money")
        print("5. View Statements")
        print("6.FD Section")
        print("7.Logout")
        try:
            choice = int(input("Select an option : "))
            if choice == 1:
                get_details(acc_no)
            elif choice == 2:
                deposit_money(acc_no)
            elif choice == 3:
                withdraw_money(acc_no)
            elif choice == 4:
                transfer_money(acc_no)
            elif choice == 5:
                view_statements(acc_no)
            elif choice == 6:
                fd_sections.open_fd(acc_no)
            elif choice == 7:
                print("Logged Out Succesfully")
                break
                
        except:
            print("Please type an integer value")

def get_details(acc_no):
    with open("bank_database.json", "r") as db:
        credentials = json.load(db)
    print("Here are your Details :- \n\n")
    print(f"NAME : {credentials[acc_no]["name"]}")
    print(f"ACC_NUMBER : {acc_no}")
    print(f"AGE : {credentials[acc_no]["age"]}")
    print(f"BALANCE : {credentials[acc_no]["balance"]}")

def deposit_money(acc_no):
    with open("bank_database.json" , "r") as db:
        credentials = json.load(db)
    amt_to_deposit = int(input("Enter your Amount to Deposit : ₹ "))
    message = input("Write a message for deposit : ")
    if amt_to_deposit <= 0:
        print("Enter an valid Amount to deposit")
        return
    else:
        pin = int(input("Enter your PIN : "))
        if pin == credentials[acc_no]["pin"]:
            credentials[acc_no]["balance"] += amt_to_deposit
            transaction = {
                            "type" : "Deposit",
                            "amount" : amt_to_deposit,
                            "message" : message,
                            "date": datetime.datetime.now().strftime("%d-%m-%Y"),
                            "time": datetime.datetime.now().strftime("%H:%M:%S")
                        }
            
            credentials[acc_no]["transaction"].append(transaction)
            with open("bank_database.json" , "w") as db:
                json.dump(credentials , db , indent=4)
            print("Money Deposited Succesfully")
        else:
            print("Incorrect PIN . Please Try again")

def withdraw_money(acc_no):
    with open("bank_database.json" , "r") as db:
        credentials = json.load(db)
    amt_to_withdraw = int(input("Enter an amount to withdraw : ₹ "))
    if amt_to_withdraw <= 0:
        print("You cannot withdraw a negative or 0 amount !")
        return
    message = input("Write a message for withdrawl : ")
    if amt_to_withdraw > credentials[acc_no]["balance"]:
        print("Unsufficent Funds to withdraw.")
        return
    else:
        pin = int(input("Enter your PIN : "))
        if pin == credentials[acc_no]["pin"]:
            credentials[acc_no]["balance"] -= amt_to_withdraw

            transaction = {
                "type" : "Withdrawl",
                "amount" : amt_to_withdraw,
                "message" : message,
                "date": datetime.datetime.now().strftime("%d-%m-%Y"),
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            }

            credentials[acc_no]["transaction"].append(transaction)
            with open("bank_database.json" , "w") as db:
                json.dump(credentials , db , indent=4)
            print("Amount Withdrawn Succesfully")
        else:
            print("Incorrect PIN . Please Try again")


def transfer_money(acc_no):
    with open("bank_database.json", "r") as db:
        credentials = json.load(db)
    reciever_acc_no = input("Enter the ACC_NO of the receiver: ")
    if reciever_acc_no not in credentials:
        print("No such account found!")
        return
    if reciever_acc_no == acc_no:
        print("You cannot transfer money to your own account!")
        return
    print("Account Found :- ")
    print(f"Name : {credentials[reciever_acc_no]['name']}")

    try:
        amt_to_send = int(input("Enter the amount to Transfer : ₹ "))
    except ValueError:
        print("Please enter a valid amount!")
        return

    if amt_to_send <= 0:
        print("Invalid Amount. Please try again!")
        return

    try:
        pin = int(input("Enter your PIN : "))
    except ValueError:
        print("Invalid PIN!")
        return

    if pin != credentials[acc_no]["pin"]:
        print("Incorrect PIN. Try Again!")
        return
    message = input("Enter the message to transfer : ")

    while amt_to_send > credentials[acc_no]["balance"]:
        print("You have insufficient funds to transfer.")
        choice = input("Do you want to try again (Y/N) : ").lower()
        if choice == "y":
            try:
                amt_to_send = int(input("Enter a lower amount : ₹ "))
            except ValueError:
                print("Invalid amount!")
                return

            if amt_to_send <= 0:
                print("Invalid amount!")
                return

        else:
            print("Transaction cancelled!")
            return

    credentials[reciever_acc_no]["balance"] += amt_to_send
    credentials[acc_no]["balance"] -= amt_to_send

    transaction_statement_sender = {
        "type": "Money Sent",
        "amount": amt_to_send,
        "message": message,
        "date": datetime.datetime.now().strftime("%d-%m-%Y"),
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }

    transaction_statement_reciever = {
        "type": "Money Received",
        "amount": amt_to_send,
        "message": message,
        "date": datetime.datetime.now().strftime("%d-%m-%Y"),
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    }

    credentials[acc_no]["transaction"].append(transaction_statement_sender)

    credentials[reciever_acc_no]["transaction"].append(transaction_statement_reciever)

    with open("bank_database.json", "w") as db:
        json.dump(credentials, db, indent=4)

    print("Money transferred successfully!")
    print(f"₹{amt_to_send} sent to {credentials[reciever_acc_no]['name']}")


def view_statements(acc_no):
    print("Here are your statements for your account : ")
    with open("bank_database.json" , "r") as db:
        credentials = json.load(db)
    account = credentials[acc_no]
    print("\n" + "="*60)
    print("<-----ACCOUNT STATEMENT----->")
    print(f"Account Holder : {account['name']}")
    print(f"Account Number: {acc_no}")
    print(f"Account Type  : {account['acc_type']}")
    print(f"Available Balance: ₹{account['balance']}")
    print("\n\n")
    print("-" * 60)
    print(f"{'DATE':<15}{'TYPE':<15}{'AMOUNT':<15}")
    print("-"*60)
    for transaction in account["transaction"]:

        print(
            f"{transaction['date']:<15}"
            f"{transaction['type']:<15}"
            f"₹{transaction['amount']:<14}"
        )

    print("-"*60)
    print("These are the records of transactions you made")
    print("-"*60)

    

        
    
