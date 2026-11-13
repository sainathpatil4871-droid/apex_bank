Apex International Banking Limited

A banking management system built in Python. It started as a console application and now also has a web interface and an Android wrapper. Account data is stored in JSON files, and the console and web versions share the same files.

Features

Customer

Open an account (Savings or Current) with a 4-digit PIN
Sign in with account number and PIN
Account details and balance
Deposit, withdraw and transfer money (PIN required each time)
Account statement with filter, CSV download and print
Fixed Deposit at 7% a year, 1 to 10 years, with live maturity preview
Claim a matured FD, or close it early (interest is forfeited)
Change PIN

Administrator

Bank totals: accounts, deposits held, active FDs
Searchable list of all accounts
Per-account transaction history and FD details
PIN reset for customers (PINs are never displayed)
Project structure
apex_bank/
├── server.py            Flask server (web version)
├── static/              Web interface (index.html, PWA icons)
├── main.py              Console version, entry point
├── acc_creation.py      Console: account creation
├── person_login.py      Console: login, deposit, withdraw, transfer, statements
├── fd_sections.py       Console: fixed deposits
├── bank_database.json   Accounts and transactions
├── fd_data.json         Fixed deposits
├── start.bat / start.sh              Start the web version on this computer
└── start_phone.bat / start_phone.sh  Start it so a phone on the same Wi-Fi can connect
apex_bank_android/       Android Studio project (WebView wrapper)
Getting started

Requires Python 3.9 or newer.

bash
pip install -r requirements.txt
python server.py

Then open the address printed in the terminal (usually http://127.0.0.1:5000). On Windows you can double-click start.bat instead.

The console version still works: python main.py.

Administrator password

A random password is printed in the terminal each time the server starts. To set your own:

bash
# Windows (cmd)
set APEX_ADMIN_PASS=YourPassword
# Mac / Linux
export APEX_ADMIN_PASS=YourPassword
Android app
Run start_phone.bat (or start_phone.sh) and note the PHONE ADDRESS it prints.
Open apex_bank_android in Android Studio and choose Build > Build APK(s).
Install the APK, open it and enter the phone address. The phone must be on the same Wi-Fi as the computer.

The connection is plain HTTP, so use this only on a trusted home network.

Security
Every money action is verified on the server, including the PIN
Three wrong PINs lock an account for 5 minutes
Sessions expire after 10 minutes of inactivity
Cookies are HttpOnly and SameSite=Strict, and write requests need a custom header
Input is validated on the server and escaped in the page
JSON files are written atomically with a lock, so a crash cannot corrupt them
Known limitations
PINs are stored as plain numbers in the JSON file. Hashing them is a planned improvement and would need a migration for the console version.
JSON storage suits a single machine and a few users. A database such as SQLite would be the next step.
One Fixed Deposit per account.
No HTTPS in the local setup.
Transfers and statements have no rate limiting beyond the PIN lockout.