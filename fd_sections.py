import json
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
import person_login
def open_fd(acc_no):
    while(True):
        print("-------Main Menu---------")
        print("1.Start an FD ")
        print("2.View FD status")
        print("3.Close FD section")
        choice = int(input("Enter your choice : "))
        if choice == 1:
            start_fd(acc_no)
        elif choice == 2:
            view_fd_status(acc_no)
        elif choice == 3:
            break


def start_fd(acc_no):
    with open("bank_database.json" , "r") as db:
        credentials = json.load(db)

    print("Welcome to Our Bank's Fixed Deposit (FD) Service!")
    print("Grow your savings with guaranteed '7%' returns.")
    print("Choose your deposit amount and tenure, and let us calculate your maturity amount.")
    print("-" * 60)

    fd_amount = int(input("Enter an amount to start FD(minimum ₹ 1000) : "))
    if fd_amount > credentials[acc_no]["balance"]:
        print("Insufficient Funds for FD. Try Lower amount")
        return
    if fd_amount < 1000:
        print("Minimum amount to start an FD is ₹ 1000")
        return
    else:
        tenure = int(input("Enter the amount of years you would like to do FD for : "))
        if tenure > 0 :
            rate = 7
            maturity_amount = fd_amount*(1+rate/100)**tenure
            interest_earned = maturity_amount - fd_amount
            issue_date = date.today()
            maturity_date = issue_date + relativedelta(years=tenure)
            credentials[acc_no]["balance"] -= fd_amount
            transaction = {
                    "type": "FD Created",
                    "amount": fd_amount,
                    "message": f"Fixed Deposit for {tenure} years",
                    "date": date.today().strftime("%d-%m-%Y"),
                    "time": datetime.now().strftime("%H:%M:%S")
                    }
            credentials[acc_no]["transaction"].append(transaction)


            print("\n------FD SUMMARY------")
            print(f"Principal Amount : ₹ {fd_amount:.2f}")
            print(f"Duration         : {tenure:.2f} years")
            print(f"Rate of Interest : {rate:.2f} %")
            print(f"Maturity Amount  : ₹{maturity_amount:.2f}")
            print(f"Issue Date       : {issue_date}")
            print(f"Maturity Date    : {maturity_date}")

            with open("fd_data.json" , "r") as file : 
                fd_data = json.load(file)

            fd_data[acc_no] = {
                "amount" : fd_amount,
                "tenure" : tenure,
                "rate" : rate,
                "maturity_amount" : round(maturity_amount , 2),
                "interest" : round(interest_earned , 2),
                "issue_date" : str(issue_date),
                "maturity_date" : str(maturity_date)
            }

            with open("bank_database.json" , "w") as db:
                json.dump(credentials , db , indent=4)
            with open("fd_data.json" , "w") as file:
                json.dump(fd_data , file , indent=4)

            print("FD Created Succesfully")


def view_fd_status(acc_no):

    print("\n------- FIXED DEPOSIT STATUS -------")
    with open("fd_data.json", "r") as db:
        credentials = json.load(db)
    if acc_no in credentials:
        account = credentials[acc_no]
        print(f"Account Number   : {acc_no}")
        print(f"Principal Amount : ₹{account['amount']:.2f}")
        print(f"Tenure           : {account['tenure']} Years")
        print(f"Interest Rate    : {account['rate']}%")
        print(f"Interest Earned  : ₹{account['interest']:.2f}")
        print(f"Maturity Amount  : ₹{account['maturity_amount']:.2f}")
        print(f"Issue Date       : {account['issue_date']}")
        print(f"Maturity Date    : {account['maturity_date']}")
        maturity_date = date.fromisoformat(account['maturity_date'])
        today = date.today()
        days_left = (maturity_date - today).days

        if days_left > 0:
            print(f"FD Status        : ACTIVE")
            print(f"Days Left        : {days_left} Days")

        elif days_left == 0:
            print("FD Status        : MATURES TODAY!")

        else:
            print("FD Status        : MATURED")
            print(f"Matured          : {abs(days_left)} Days Ago")

    else:
        print("No Fixed Deposit found for this account!")

    print("-" * 45)



