import json
import random
acc_no_dataset = []
with open("bank_database.json" , "r") as db:
    acc_info = json.load(db)

def create_an_account():
    name = input("Enter your Name : ")
    age = int(input("Enter your Age : "))
    pin = int(input("Enter the PIN you want to set for your Account : " ))
    acc_type = input("Enter the type of account you want to open(Current/Savings) : ").lower()

    acc_no = str(random.randint(100000, 999999))
    if acc_no in acc_no_dataset :
        acc_no = str(random.randint(100000, 999999))

    acc_info[acc_no] = {
        "name" : name,
        "age" : age,
        "pin" : pin,
        "acc_type" : acc_type,
        "balance" : 0,
        "transaction" : []
    }

    with open("bank_database.json" , "w") as db:
        json.dump(acc_info , db , indent = 4)