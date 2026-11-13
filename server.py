"""Apex International Banking Limited - web server.
Uses the SAME bank_database.json and fd_data.json as the console version.
Run:  pip install flask python-dateutil   then   python server.py
Open: http://127.0.0.1:5000
"""
import hmac, json, os, random, re, secrets, tempfile, threading, time
from datetime import date, datetime, timedelta
from functools import wraps

from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify, request, send_from_directory, session

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "bank_database.json")
FD = os.path.join(BASE, "fd_data.json")
LOCK = threading.RLock()
MAX_AMOUNT = 10_000_000
FD_RATE = 7
CREDITS = {"Deposit", "Money Received", "FD Matured", "FD Closed Early"}
ADMIN_PASS = os.environ.get("APEX_ADMIN_PASS") or secrets.token_urlsafe(6)

app = Flask(__name__, static_folder=os.path.join(BASE, "static"))
app.secret_key = os.urandom(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict",
                  PERMANENT_SESSION_LIFETIME=timedelta(minutes=10))
FAILS = {}  # acc_no -> [count, locked_until]


# ---------- storage (atomic writes, same JSON format as the console app) ----------
def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save(path, data):
    fd, tmp = tempfile.mkstemp(dir=BASE, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp, path)

def txn(kind, amount, message):
    now = datetime.now()
    return {"type": kind, "amount": amount, "message": message or "None",
            "date": now.strftime("%d-%m-%Y"), "time": now.strftime("%H:%M:%S")}


# ---------- helpers ----------
def err(msg, code=400):
    return jsonify(error=msg), code

def amount_of(data):
    try:
        a = int(data.get("amount"))
    except (TypeError, ValueError):
        raise ValueError("Enter a valid whole-number amount.")
    if a <= 0:
        raise ValueError("Amount must be greater than zero.")
    if a > MAX_AMOUNT:
        raise ValueError("Amount exceeds the per-transaction limit of ₹1,00,00,000.")
    return a

def pin_ok(acc, data):
    return hmac.compare_digest(str(acc["pin"]), str(data.get("pin", "")).strip())

def clean_msg(data):
    return str(data.get("message", "")).strip()[:80]

def api(fn):
    @wraps(fn)
    def w(*a, **k):
        if request.method == "POST" and request.headers.get("X-Requested-With") != "fetch":
            return err("Invalid request.", 403)
        if "acc" not in session:
            return err("Session expired. Please sign in again.", 401)
        with LOCK:
            db = load(DB)
            if session["acc"] not in db:
                session.clear()
                return err("Account not found.", 401)
            return fn(db, session["acc"], *a, **k)
    return w

def guard_post(fn):
    @wraps(fn)
    def w(*a, **k):
        if request.headers.get("X-Requested-With") != "fetch":
            return err("Invalid request.", 403)
        return fn(*a, **k)
    return w


# ---------- auth ----------
@app.get("/")
def index():
    for folder in (app.static_folder, BASE):
        if os.path.exists(os.path.join(folder, "index.html")):
            return send_from_directory(folder, "index.html")
    return "index.html not found. Keep the 'static' folder next to server.py.", 404

@app.post("/api/signup")
@guard_post
def signup():
    d = request.get_json(silent=True) or {}
    name = re.sub(r"\s+", " ", str(d.get("name", "")).strip())
    acc_type = str(d.get("acc_type", "")).lower()
    pin = str(d.get("pin", "")).strip()
    try:
        age = int(d.get("age"))
    except (TypeError, ValueError):
        return err("Enter a valid age.")
    if not re.fullmatch(r"[A-Za-z .'-]{2,60}", name):
        return err("Enter your full name using letters only.")
    if age < 18 or age > 120:
        return err("You must be 18 or older to open an account.")
    if acc_type not in ("savings", "current"):
        return err("Choose an account type.")
    if not re.fullmatch(r"\d{4}", pin):
        return err("PIN must be exactly 4 digits.")
    with LOCK:
        db = load(DB)
        acc_no = str(random.randint(100000, 999999))
        while acc_no in db:
            acc_no = str(random.randint(100000, 999999))
        db[acc_no] = {"name": name, "age": age, "pin": int(pin), "acc_type": acc_type,
                      "balance": 0, "transaction": []}
        save(DB, db)
    return jsonify(acc_no=acc_no, name=name)

@app.post("/api/login")
@guard_post
def login():
    d = request.get_json(silent=True) or {}
    acc_no = str(d.get("acc_no", "")).strip()
    with LOCK:
        f = FAILS.get(acc_no, [0, 0])
        if f[1] > time.time():
            return err("Too many incorrect attempts. Try again in a few minutes.", 429)
        db = load(DB)
        acc = db.get(acc_no)
        if not acc or not pin_ok(acc, d):
            if acc:
                f[0] += 1
                if f[0] >= 3:
                    f = [0, time.time() + 300]
                FAILS[acc_no] = f
            return err("Account number or PIN is incorrect.", 401)
        FAILS.pop(acc_no, None)
    session.clear()
    session.permanent = True
    session["acc"] = acc_no
    return jsonify(ok=True)

@app.post("/api/logout")
@guard_post
def logout():
    session.clear()
    return jsonify(ok=True)


# ---------- account ----------
@app.get("/api/me")
@api
def me(db, acc_no):
    a = db[acc_no]
    m = date.today().strftime("-%m-%Y")
    mi = sum(t["amount"] for t in a["transaction"] if t["date"].endswith(m) and t["type"] in CREDITS)
    mo = sum(t["amount"] for t in a["transaction"] if t["date"].endswith(m) and t["type"] not in CREDITS)
    return jsonify(acc_no=acc_no, name=a["name"], age=a["age"], acc_type=a["acc_type"],
                   balance=a["balance"], recent=a["transaction"][-5:][::-1], month_in=mi, month_out=mo)

@app.get("/api/statements")
@api
def statements(db, acc_no):
    return jsonify(transactions=db[acc_no]["transaction"][::-1], balance=db[acc_no]["balance"])

@app.post("/api/deposit")
@api
def deposit(db, acc_no):
    d = request.get_json(silent=True) or {}
    try:
        amt = amount_of(d)
    except ValueError as e:
        return err(str(e))
    a = db[acc_no]
    if not pin_ok(a, d):
        return err("Incorrect PIN.")
    a["balance"] += amt
    a["transaction"].append(txn("Deposit", amt, clean_msg(d)))
    save(DB, db)
    return jsonify(balance=a["balance"])

@app.post("/api/withdraw")
@api
def withdraw(db, acc_no):
    d = request.get_json(silent=True) or {}
    try:
        amt = amount_of(d)
    except ValueError as e:
        return err(str(e))
    a = db[acc_no]
    if not pin_ok(a, d):
        return err("Incorrect PIN.")
    if amt > a["balance"]:
        return err("Insufficient funds.")
    a["balance"] -= amt
    a["transaction"].append(txn("Withdrawl", amt, clean_msg(d)))
    save(DB, db)
    return jsonify(balance=a["balance"])

@app.post("/api/lookup")
@api
def lookup(db, acc_no):
    r = str((request.get_json(silent=True) or {}).get("acc_no", "")).strip()
    if r == acc_no:
        return err("You cannot transfer to your own account.")
    if r not in db:
        return err("No account found with this number.", 404)
    return jsonify(name=db[r]["name"])

@app.post("/api/transfer")
@api
def transfer(db, acc_no):
    d = request.get_json(silent=True) or {}
    r = str(d.get("to", "")).strip()
    if r not in db:
        return err("No account found with this number.")
    if r == acc_no:
        return err("You cannot transfer to your own account.")
    try:
        amt = amount_of(d)
    except ValueError as e:
        return err(str(e))
    a = db[acc_no]
    if not pin_ok(a, d):
        return err("Incorrect PIN.")
    if amt > a["balance"]:
        return err("Insufficient funds.")
    msg = clean_msg(d)
    a["balance"] -= amt
    db[r]["balance"] += amt
    a["transaction"].append(txn("Money Sent", amt, msg))
    db[r]["transaction"].append(txn("Money Received", amt, msg))
    save(DB, db)
    return jsonify(balance=a["balance"], to=db[r]["name"])

@app.post("/api/pin")
@api
def change_pin(db, acc_no):
    d = request.get_json(silent=True) or {}
    a = db[acc_no]
    if not hmac.compare_digest(str(a["pin"]), str(d.get("old", "")).strip()):
        return err("Current PIN is incorrect.")
    new = str(d.get("new", "")).strip()
    if not re.fullmatch(r"\d{4}", new):
        return err("New PIN must be exactly 4 digits.")
    a["pin"] = int(new)
    save(DB, db)
    return jsonify(ok=True)


# ---------- fixed deposit ----------
@app.get("/api/fd")
@api
def fd_view(db, acc_no):
    fd = load(FD).get(acc_no)
    if not fd:
        return jsonify(fd=None)
    left = (date.fromisoformat(fd["maturity_date"]) - date.today()).days
    fd["days_left"] = left
    fd["status"] = "Active" if left > 0 else ("Matures today" if left == 0 else "Matured")
    return jsonify(fd=fd, rate=FD_RATE)

@app.post("/api/fd")
@api
def fd_start(db, acc_no):
    d = request.get_json(silent=True) or {}
    try:
        amt = amount_of(d)
        tenure = int(d.get("tenure"))
    except (TypeError, ValueError) as e:
        return err(str(e) if str(e) else "Enter valid values.")
    if amt < 1000:
        return err("Minimum amount to start an FD is ₹1,000.")
    if not 1 <= tenure <= 10:
        return err("Tenure must be between 1 and 10 years.")
    a = db[acc_no]
    if not pin_ok(a, d):
        return err("Incorrect PIN.")
    if amt > a["balance"]:
        return err("Insufficient funds for this FD.")
    fds = load(FD)
    ex = fds.get(acc_no)
    if ex:
        return err("You already have a Fixed Deposit. Claim or close it before starting a new one.")
    maturity = amt * (1 + FD_RATE / 100) ** tenure
    issue = date.today()
    fds[acc_no] = {"amount": amt, "tenure": tenure, "rate": FD_RATE,
                   "maturity_amount": round(maturity, 2), "interest": round(maturity - amt, 2),
                   "issue_date": str(issue), "maturity_date": str(issue + relativedelta(years=tenure))}
    a["balance"] -= amt
    a["transaction"].append(txn("FD Created", amt, f"Fixed Deposit for {tenure} years"))
    save(DB, db)
    save(FD, fds)
    return jsonify(balance=a["balance"], fd=fds[acc_no])

@app.post("/api/fd/close")
@api
def fd_close(db, acc_no):
    d = request.get_json(silent=True) or {}
    a = db[acc_no]
    if not pin_ok(a, d):
        return err("Incorrect PIN.")
    fds = load(FD)
    fd = fds.get(acc_no)
    if not fd:
        return err("No Fixed Deposit found for this account.")
    if date.fromisoformat(fd["maturity_date"]) <= date.today():
        pay, kind, note = fd["maturity_amount"], "FD Matured", "Fixed Deposit matured, principal and interest credited"
    else:
        pay, kind, note = fd["amount"], "FD Closed Early", "Closed before maturity, interest forfeited"
    pay = int(round(pay))
    a["balance"] += pay
    a["transaction"].append(txn(kind, pay, note))
    del fds[acc_no]
    save(DB, db)
    save(FD, fds)
    return jsonify(balance=a["balance"], credited=pay, kind=kind)


# ---------- administrator mode ----------
def admin(fn):
    @wraps(fn)
    def w(*a, **k):
        if request.method == "POST" and request.headers.get("X-Requested-With") != "fetch":
            return err("Invalid request.", 403)
        if not session.get("admin"):
            return err("Admin session expired. Please sign in again.", 401)
        with LOCK:
            return fn(*a, **k)
    return w

@app.post("/api/admin/login")
@guard_post
def admin_login():
    f = FAILS.get("__admin__", [0, 0])
    if f[1] > time.time():
        return err("Too many incorrect attempts. Try again in a few minutes.", 429)
    pw = str((request.get_json(silent=True) or {}).get("password", ""))
    if not hmac.compare_digest(pw, ADMIN_PASS):
        f[0] += 1
        FAILS["__admin__"] = [0, time.time() + 300] if f[0] >= 3 else f
        return err("Incorrect administrator password.", 401)
    FAILS.pop("__admin__", None)
    session.clear()
    session.permanent = True
    session["admin"] = True
    return jsonify(ok=True)

@app.get("/api/admin/overview")
@admin
def admin_overview():
    db, fds = load(DB), load(FD)
    accts = [{"acc_no": k, "name": v["name"], "acc_type": v["acc_type"], "age": v["age"],
              "balance": v["balance"], "txns": len(v["transaction"]), "fd": k in fds}
             for k, v in db.items()]
    return jsonify(accounts=accts, total=sum(a["balance"] for a in accts),
                   fd_count=len(fds), fd_total=sum(f["amount"] for f in fds.values()))

@app.get("/api/admin/account/<acc_no>")
@admin
def admin_account(acc_no):
    db = load(DB)
    if acc_no not in db:
        return err("Account not found.", 404)
    a = db[acc_no]
    return jsonify(acc_no=acc_no, name=a["name"], age=a["age"], acc_type=a["acc_type"],
                   balance=a["balance"], transactions=a["transaction"][::-1], fd=load(FD).get(acc_no))

@app.post("/api/admin/resetpin")
@admin
def admin_reset_pin():
    d = request.get_json(silent=True) or {}
    db = load(DB)
    acc_no, new = str(d.get("acc_no", "")), str(d.get("pin", "")).strip()
    if acc_no not in db:
        return err("Account not found.")
    if not re.fullmatch(r"\d{4}", new):
        return err("PIN must be exactly 4 digits.")
    db[acc_no]["pin"] = int(new)
    save(DB, db)
    FAILS.pop(acc_no, None)
    return jsonify(ok=True)


def free_port(start=5000):
    import socket
    for p in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk:
            if sk.connect_ex(("127.0.0.1", p)) != 0:
                return p
    raise SystemExit("No free port found between 5000 and 5019.")

if __name__ == "__main__":
    if not os.path.exists(DB):
        raise SystemExit("\nERROR: bank_database.json not found in:\n  " + BASE +
                         "\nPut server.py in the same folder as your bank_database.json and fd_data.json.\n")
    if not os.path.exists(FD):
        save(FD, {})
    try:
        n = len(load(DB))
    except json.JSONDecodeError as e:
        raise SystemExit("\nERROR: bank_database.json is not valid JSON: %s\n" % e)
    port = free_port()
    url = "http://127.0.0.1:%d" % port
    print("\n  Apex International Banking Limited")
    print("  Loaded %d accounts from %s" % (n, DB))
    print("  Open this address in your browser:  " + url)
    print("  Administrator password:", ADMIN_PASS, "(set APEX_ADMIN_PASS to choose your own)")
    print("  Keep this window open while using the bank. Press Ctrl+C to stop.\n")
    import webbrowser
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
