import json
import acc_creation
import person_login


while(True):
    print("-----Welcome to Banking Management System------")
    print("1.Login into your Account")
    print("2.Create an account")
    print("3.Administrator Mode")
    print("4.Close the Application")
    choice = int(input("Enter your choice(1,2,3) : "))
    if choice == 2 :
        acc_creation.create_an_account()
    elif choice == 1 :
        person_login.login()
    elif choice == 3:
        pass
    elif choice == 4:
        break

