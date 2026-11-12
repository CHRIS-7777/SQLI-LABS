#!/usr/bin/env python3
"""Create and populate every database used by the lab.   usage: seed.py [wait|sqlite|mysql|mssql|all]"""
import os
import sqlite3
import sys
import time

import config as C
from fakedata import (FLAGS, R, TEST_CARDS, address, date, md5, people, phone, pw)

os.makedirs(C.DATA, exist_ok=True)


# ----------------------------------------------------------------------------- helpers
def many(n, fn):
    return [fn(i + 1) for i in range(n)]


def wait_for_dbs(timeout=240):
    import pymssql
    import pymysql
    t0 = time.time()
    ok_mysql = ok_mssql = False
    while time.time() - t0 < timeout:
        if not ok_mysql:
            try:
                pymysql.connect(host=C.MYSQL_HOST, port=C.MYSQL_PORT, user="root", password=C.MYSQL_ROOT_PW).close()
                ok_mysql = True
            except Exception:
                pass
        if not ok_mssql:
            try:
                pymssql.connect(server=C.MSSQL_HOST, port=C.MSSQL_PORT, user="sa", password=C.MSSQL_SA_PW,
                                login_timeout=5).close()
                ok_mssql = True
            except Exception:
                pass
        if ok_mysql and ok_mssql:
            return True
        time.sleep(3)
    raise SystemExit(f"database containers not ready (mysql={ok_mysql}, mssql={ok_mssql})")


# ----------------------------------------------------------------------------- SQLite : shop
def seed_shop():
    path = os.path.join(C.DATA, "shop.db")
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE categories(id INTEGER PRIMARY KEY, name TEXT);
    CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, price REAL, image TEXT, badge TEXT,
                          description TEXT, category TEXT, stock INTEGER, featured INTEGER);
    CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, email TEXT, password_hash TEXT, role TEXT, created_at TEXT);
    CREATE TABLE orders(id TEXT PRIMARY KEY, user_id INTEGER, total REAL, status TEXT, shipping_address TEXT, created_at TEXT);
    CREATE TABLE order_items(id INTEGER PRIMARY KEY, order_id TEXT, product_id INTEGER, qty INTEGER, unit_price REAL);
    CREATE TABLE payment_methods(id INTEGER PRIMARY KEY, user_id INTEGER, card_holder TEXT, card_number TEXT, expiry TEXT, brand TEXT);
    CREATE TABLE coupons(code TEXT, discount_pct INTEGER, active INTEGER);
    CREATE TABLE internal_config(id INTEGER PRIMARY KEY, config_key TEXT, config_value TEXT);
    """)
    cats = ["Outdoor", "Travel", "Kitchen", "Tech", "Home"]
    db.executemany("INSERT INTO categories VALUES(?,?)", list(enumerate(cats, 1)))
    prods = [
        ("Trail Runner Backpack 30L", 89.0, "🎒", "bestseller", "Lightweight pack with rain cover and hydration sleeve.", "Outdoor", 1),
        ("Summit Insulated Bottle", 27.5, "🍶", "new", "Keeps drinks cold for 24h, hot for 12h.", "Outdoor", 1),
        ("Ridgeline Trekking Poles", 64.0, "🥾", "sale", "Carbon fibre, collapsible, cork grip.", "Outdoor", 1),
        ("Nomad Carry-On Spinner", 159.0, "🧳", "bestseller", "Hard-shell carry-on with USB charging port.", "Travel", 1),
        ("AirLoop Neck Pillow", 24.0, "😴", "new", "Memory foam, washable cover.", "Travel", 1),
        ("Passport Sleeve RFID", 18.0, "🛂", "sale", "Slim RFID-blocking passport wallet.", "Travel", 1),
        ("Cast Iron Skillet 12in", 42.0, "🍳", "bestseller", "Pre-seasoned and oven safe.", "Kitchen", 1),
        ("Pour-Over Coffee Set", 56.0, "☕", "new", "Glass carafe, steel filter, scoop included.", "Kitchen", 1),
        ("Chef's Knife 8in", 79.0, "🔪", "sale", "German steel, full tang.", "Kitchen", 1),
        ("Wireless Earbuds Pro", 129.0, "🎧", "bestseller", "ANC, 30h battery, IPX5.", "Tech", 1),
        ("Smart Desk Lamp", 49.0, "💡", "new", "Adjustable colour temperature with touch dimmer.", "Tech", 1),
        ("Portable Power Bank 20k", 39.0, "🔋", "sale", "USB-C PD 65W fast charging.", "Tech", 1),
        ("Linen Throw Blanket", 58.0, "🛋️", "", "Stonewashed linen, 130x170cm.", "Home", 0),
        ("Ceramic Planter Set", 34.0, "🪴", "", "Set of three matte planters.", "Home", 0),
        ("Bamboo Cutting Board", 29.0, "🪵", "", "Juice groove, 40x28cm.", "Kitchen", 0),
        ("Camping Hammock", 45.0, "⛺", "", "Parachute nylon, straps included.", "Outdoor", 0),
        ("Packing Cubes (6)", 31.0, "📦", "", "Compression cubes in assorted sizes.", "Travel", 0),
        ("Mechanical Keyboard 75%", 99.0, "⌨️", "", "Hot-swappable switches, aluminium case.", "Tech", 0),
        ("Scented Soy Candle", 19.0, "🕯️", "", "Cedar and amber, 45h burn time.", "Home", 0),
        ("Enamel Camp Mug", 14.0, "🥤", "", "Classic speckled enamel mug.", "Outdoor", 0),
        ("Toiletry Roll Bag", 33.0, "👜", "", "Water-resistant hanging organiser.", "Travel", 0),
        ("French Press 1L", 38.0, "🫖", "", "Double-wall stainless steel.", "Kitchen", 0),
        ("Webcam 4K", 119.0, "📷", "", "Autofocus, dual mics, privacy shutter.", "Tech", 0),
        ("Weighted Door Stop", 12.0, "🚪", "", "Cast iron with felt base.", "Home", 0),
    ]
    db.executemany("INSERT INTO products(name,price,image,badge,description,category,stock,featured) VALUES(?,?,?,?,?,?,?,?)",
                   [(n, p, i, b, d, c, R.randint(0, 120), f) for n, p, i, b, d, c, f in prods])
    ppl = people(29, "mail.example")
    users = [(1, "admin", "admin@parcelo.example", md5("Pcl#Adm1n!2024"), "admin", "2022-01-03"),
             (2, "support", "support@parcelo.example", md5("Sup0rt@Parcelo"), "staff", "2022-01-03")]
    for i, (f, l, e) in enumerate(ppl, 3):
        users.append((i, f"{f}{l}".lower()[:14], e, md5(pw()), "customer", date()))
    db.executemany("INSERT INTO users VALUES(?,?,?,?,?,?)", users)
    orders, items, oid = [], [], 0
    for n in range(1, 61):
        o = f"ORD-{1000 + n}"
        uid = R.randint(3, len(users))
        total = 0
        for _ in range(R.randint(1, 3)):
            pid = R.randint(1, len(prods))
            q = R.randint(1, 2)
            price = prods[pid - 1][1]
            total += q * price
            oid += 1
            items.append((oid, o, pid, q, price))
        orders.append((o, uid, round(total, 2), R.choice(["processing", "shipped", "delivered", "delivered"]), address(), date(2024, 2024)))
    db.executemany("INSERT INTO orders VALUES(?,?,?,?,?,?)", orders)
    db.executemany("INSERT INTO order_items VALUES(?,?,?,?,?)", items)
    pms = []
    for i in range(1, 21):
        u = users[i + 2]
        pms.append((i, u[0], u[1].title(), R.choice(TEST_CARDS), f"{R.randint(1, 12):02d}/{R.randint(25, 29)}", R.choice(["VISA", "MASTERCARD", "AMEX"])))
    db.executemany("INSERT INTO payment_methods VALUES(?,?,?,?,?,?)", pms)
    db.executemany("INSERT INTO coupons VALUES(?,?,?)", [("WELCOME10", 10, 1), ("SUMMER25", 25, 0), ("STAFF50", 50, 1), ("FREESHIP", 0, 1)])
    db.executemany("INSERT INTO internal_config(config_key,config_value) VALUES(?,?)", [
        ("smtp_host", "smtp.parcelo.example"), ("smtp_password", "Sm7p#Relay2024"),
        ("payment_gateway_key", "pk_live_51Lab0nlyD0n0tUs3ThisKey"), ("backup_bucket", "s3://parcelo-backups-2024"),
        ("flag", FLAGS["shop"])])
    db.commit()
    db.close()


# ----------------------------------------------------------------------------- SQLite : help centre
def seed_help():
    path = os.path.join(C.DATA, "help.db")
    if os.path.exists(path):
        os.remove(path)
    db = sqlite3.connect(path)
    db.executescript("""
    CREATE TABLE kb_articles(id INTEGER PRIMARY KEY, title TEXT, category TEXT, summary TEXT, body TEXT, published INTEGER, updated TEXT);
    CREATE TABLE users(id INTEGER PRIMARY KEY, email TEXT, full_name TEXT, plan TEXT, password_hash TEXT, created_at TEXT);
    CREATE TABLE tickets(id TEXT PRIMARY KEY, user_id INTEGER, subject TEXT, status TEXT, priority TEXT, opened TEXT);
    CREATE TABLE agents(id INTEGER PRIMARY KEY, username TEXT, email TEXT, password_hash TEXT, role TEXT);
    CREATE TABLE canned_responses(id INTEGER PRIMARY KEY, title TEXT, body TEXT);
    CREATE TABLE api_tokens(id INTEGER PRIMARY KEY, owner TEXT, token TEXT, scope TEXT);
    CREATE TABLE support_config(id INTEGER PRIMARY KEY, name TEXT, value TEXT);
    """)
    arts = [
        ("How to reset your password", "Account", "Steps to recover access to your Nimbus account.", 1),
        ("Changing your email address", "Account", "Update the email linked to your workspace.", 1),
        ("Enabling two-factor authentication", "Security", "Protect your account with an authenticator app.", 1),
        ("Understanding your invoice", "Billing", "A breakdown of every line on your monthly invoice.", 1),
        ("Updating payment method", "Billing", "Add, remove or replace a credit card.", 1),
        ("Cancelling your subscription", "Billing", "How to cancel and what happens to your data.", 1),
        ("Getting started with workspaces", "Getting Started", "Create your first workspace and invite teammates.", 1),
        ("Inviting team members", "Getting Started", "Send invitations and manage roles.", 1),
        ("Importing data from CSV", "Data", "Supported formats and column mapping.", 1),
        ("Exporting your data", "Data", "Download a full export of your workspace.", 1),
        ("API rate limits explained", "Developers", "Understand request quotas and 429 responses.", 1),
        ("Creating API tokens", "Developers", "Generate and rotate personal access tokens.", 1),
        ("Webhook delivery and retries", "Developers", "How webhook retries and signatures work.", 1),
        ("Single sign-on (SAML) setup", "Security", "Configure SAML with your identity provider.", 1),
        ("Audit log overview", "Security", "Review who changed what and when.", 1),
        ("Service status and incidents", "General", "Where to check uptime and past incidents.", 1),
        ("Supported browsers", "General", "Browsers and versions we officially support.", 1),
        ("Data retention policy", "General", "How long we keep deleted workspace data.", 1),
        ("Mobile app troubleshooting", "General", "Fix sync and login issues on iOS and Android.", 1),
        ("Notification preferences", "Account", "Choose which emails and push alerts you receive.", 1),
        ("[DRAFT] Legacy billing migration runbook", "Internal", "Steps to migrate legacy accounts to the new biller.", 0),
        ("[DRAFT] Escalation contacts", "Internal", "On-call contacts for P1 incidents.", 0),
        ("[DRAFT] Refund approval thresholds", "Internal", "Agents may approve refunds up to $200.", 0),
        ("[DRAFT] Support tooling credentials", "Internal", "Where the shared tooling credentials are stored.", 0),
    ]
    rows = [(i, t, c, s, f"{s} This article walks through the full procedure with screenshots and troubleshooting tips.", p, date(2023, 2024))
            for i, (t, c, s, p) in enumerate(arts, 1)]
    db.executemany("INSERT INTO kb_articles VALUES(?,?,?,?,?,?,?)", rows)
    ppl = people(30, "clients.example")
    db.executemany("INSERT INTO users VALUES(?,?,?,?,?,?)",
                   [(i, e, f"{f} {l}", R.choice(["free", "team", "business", "enterprise"]), md5(pw()), date()) for i, (f, l, e) in enumerate(ppl, 1)])
    subj = ["Cannot log in", "Invoice looks wrong", "Export is stuck", "API returns 429", "Need SSO help", "Feature request: dark mode", "Webhook not firing"]
    db.executemany("INSERT INTO tickets VALUES(?,?,?,?,?,?)",
                   [(f"TKT-{5000 + n}", R.randint(1, 30), R.choice(subj), R.choice(["open", "pending", "closed", "closed"]),
                     R.choice(["low", "normal", "high"]), date(2024, 2024)) for n in range(1, 61)])
    db.executemany("INSERT INTO agents VALUES(?,?,?,?,?)", [
        (1, "hd_admin", "admin@nimbus.example", md5("N1mbus#Adm!n24"), "admin"),
        (2, "tier2.lead", "lead@nimbus.example", md5("Tier2Lead!2024"), "lead"),
        (3, "agent.rhea", "rhea@nimbus.example", md5(pw()), "agent"),
        (4, "agent.omar", "omar@nimbus.example", md5(pw()), "agent"),
        (5, "agent.tessa", "tessa@nimbus.example", md5(pw()), "agent")])
    db.executemany("INSERT INTO canned_responses VALUES(?,?,?)", [
        (1, "Greeting", "Hi there, thanks for contacting Nimbus support!"),
        (2, "Password reset", "Please use the reset link on the sign-in page."),
        (3, "Refund policy", "Refunds are available within 30 days of purchase."),
        (4, "Escalation", "I have escalated this to our engineering team.")])
    db.executemany("INSERT INTO api_tokens(owner,token,scope) VALUES(?,?,?)", [
        ("status-page", "nb_live_5f2a91c7d3e84b6a", "read"), ("billing-sync", "nb_live_a7c3e19d52b8f640", "billing:write"),
        ("slack-bot", "nb_live_09d4b7e2c1a85f36", "tickets:read")])
    db.executemany("INSERT INTO support_config(name,value) VALUES(?,?)", [
        ("zendesk_import_key", "zd_imp_8c21f7a94b"), ("pager_webhook", "https://hooks.nimbus.example/pager/7f3a"),
        ("flag", FLAGS["help"])])
    db.commit()
    db.close()


# ----------------------------------------------------------------------------- MySQL : clinic + hr
def seed_mysql():
    import pymysql
    root = pymysql.connect(host=C.MYSQL_HOST, port=C.MYSQL_PORT, user="root", password=C.MYSQL_ROOT_PW, autocommit=True, charset="utf8mb4")
    cur = root.cursor()
    for (dbn, user, pwd) in (C.CLINIC_DB, C.HR_DB):
        cur.execute(f"DROP DATABASE IF EXISTS {dbn}")
        cur.execute(f"CREATE DATABASE {dbn} CHARACTER SET utf8mb4")
        cur.execute(f"DROP USER IF EXISTS '{user}'@'%'")
        cur.execute(f"CREATE USER '{user}'@'%' IDENTIFIED WITH mysql_native_password BY '{pwd}'")
        cur.execute(f"GRANT SELECT ON {dbn}.* TO '{user}'@'%'")
    cur.execute("FLUSH PRIVILEGES")

    # ---- clinic
    c = pymysql.connect(host=C.MYSQL_HOST, port=C.MYSQL_PORT, user="root", password=C.MYSQL_ROOT_PW, database=C.CLINIC_DB[0], autocommit=True, charset="utf8mb4")
    k = c.cursor()
    for ddl in [
        "CREATE TABLE patients(id INT PRIMARY KEY, patient_no VARCHAR(16), full_name VARCHAR(80), dob DATE, gender VARCHAR(8), phone VARCHAR(24), email VARCHAR(90), insurance_no VARCHAR(24), address VARCHAR(120))",
        "CREATE TABLE doctors(id INT PRIMARY KEY, name VARCHAR(80), specialty VARCHAR(60), department VARCHAR(40), email VARCHAR(90), bio TEXT)",
        "CREATE TABLE appointments(id INT PRIMARY KEY, ref VARCHAR(16), patient_id INT, doctor_id INT, appt_date DATETIME, status VARCHAR(20), reason VARCHAR(120))",
        "CREATE TABLE prescriptions(id INT PRIMARY KEY, patient_id INT, doctor_id INT, medication VARCHAR(80), dosage VARCHAR(40), issued_on DATE)",
        "CREATE TABLE billing(id INT PRIMARY KEY, patient_id INT, amount DECIMAL(10,2), status VARCHAR(24), card_last4 VARCHAR(4))",
        "CREATE TABLE staff_accounts(id INT PRIMARY KEY, username VARCHAR(40), password_hash VARCHAR(64), role VARCHAR(20), email VARCHAR(90))",
        "CREATE TABLE internal_config(id INT PRIMARY KEY AUTO_INCREMENT, config_key VARCHAR(60), config_value VARCHAR(200))",
    ]:
        k.execute(ddl)
    pts = people(60, "patients.example")
    k.executemany("INSERT INTO patients VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  [(i, f"PT-{20000 + i}", f"{f} {l}", date(1950, 2005), R.choice(["F", "M"]), phone(), e, f"INS-{R.randint(10**7, 10**8 - 1)}", address())
                   for i, (f, l, e) in enumerate(pts, 1)])
    docs = [("Dr. Helena Ward", "Cardiology", "Heart Centre"), ("Dr. Rajiv Menon", "Cardiology", "Heart Centre"),
            ("Dr. Alice Fontaine", "Pediatrics", "Children's Wing"), ("Dr. Marcus Bell", "Pediatrics", "Children's Wing"),
            ("Dr. Sunita Rao", "Dermatology", "Skin Clinic"), ("Dr. Tomas Eriksen", "Orthopedics", "Bone & Joint"),
            ("Dr. Naomi Clarke", "Orthopedics", "Bone & Joint"), ("Dr. Yusuf Demir", "Neurology", "Neuro Institute"),
            ("Dr. Grace Liu", "General Practice", "Primary Care"), ("Dr. Patrick Doyle", "General Practice", "Primary Care"),
            ("Dr. Iris Moreau", "Ophthalmology", "Eye Centre"), ("Dr. Kwame Boateng", "Oncology", "Cancer Care")]
    k.executemany("INSERT INTO doctors VALUES(%s,%s,%s,%s,%s,%s)",
                  [(i, n, s, d, f"{n.split()[-1].lower()}@medcare.example", f"{n} has over {R.randint(6, 25)} years of experience in {s.lower()}.")
                   for i, (n, s, d) in enumerate(docs, 1)])
    reasons = ["Annual check-up", "Follow-up visit", "Chest pain evaluation", "Skin rash", "Knee pain", "Vaccination", "Migraine consultation", "Eye exam", "Blood test review"]
    k.executemany("INSERT INTO appointments VALUES(%s,%s,%s,%s,%s,%s,%s)",
                  [(i, f"APT-{10000 + i}", R.randint(1, 60), R.randint(1, 12), date(2024, 2025, True), R.choice(["confirmed", "completed", "pending", "cancelled"]), R.choice(reasons))
                   for i in range(1, 81)])
    meds = [("Atorvastatin", "20mg daily"), ("Amoxicillin", "500mg x3 daily"), ("Ibuprofen", "400mg as needed"), ("Metformin", "850mg twice daily"), ("Sumatriptan", "50mg as needed")]
    k.executemany("INSERT INTO prescriptions VALUES(%s,%s,%s,%s,%s,%s)",
                  [(i, R.randint(1, 60), R.randint(1, 12), *R.choice(meds), date(2024, 2025)) for i in range(1, 51)])
    k.executemany("INSERT INTO billing VALUES(%s,%s,%s,%s,%s)",
                  [(i, R.randint(1, 60), round(R.uniform(40, 1800), 2), R.choice(["paid", "unpaid", "insurance-pending"]), R.choice(TEST_CARDS)[-4:]) for i in range(1, 61)])
    k.executemany("INSERT INTO staff_accounts VALUES(%s,%s,%s,%s,%s)", [
        (1, "clinic.admin", md5("M3dC@re#Adm1n24"), "admin", "admin@medcare.example"),
        (2, "reception", md5("Welcome1"), "frontdesk", "reception@medcare.example"),
        (3, "dr.ward", md5("Heart2024!"), "doctor", "ward@medcare.example"),
        (4, "billing", md5("Billing#2024"), "billing", "billing@medcare.example"),
        (5, "lab.tech", md5("Passw0rd"), "lab", "lab@medcare.example")])
    k.executemany("INSERT INTO internal_config(config_key,config_value) VALUES(%s,%s)", [
        ("ehr_api_key", "ehr_live_3b91c07fd2a46e58"), ("sms_gateway_token", "sms_7f20ac91be3d"),
        ("hl7_endpoint", "https://hl7.medcare.example/inbound"), ("flag", FLAGS["clinic"])])
    c.close()

    # ---- hr / careers
    h = pymysql.connect(host=C.MYSQL_HOST, port=C.MYSQL_PORT, user="root", password=C.MYSQL_ROOT_PW, database=C.HR_DB[0], autocommit=True, charset="utf8mb4")
    k = h.cursor()
    for ddl in [
        "CREATE TABLE jobs(id INT PRIMARY KEY, title VARCHAR(80), department VARCHAR(40), location VARCHAR(40), salary_range VARCHAR(30), description TEXT, status VARCHAR(10))",
        "CREATE TABLE applicants(id INT PRIMARY KEY, full_name VARCHAR(80), email VARCHAR(90), phone VARCHAR(24), job_id INT, expected_salary INT, resume_url VARCHAR(120), applied_on DATE)",
        "CREATE TABLE hr_staff(id INT PRIMARY KEY, username VARCHAR(40), full_name VARCHAR(80), password_hash VARCHAR(64), role VARCHAR(20), email VARCHAR(90))",
        "CREATE TABLE salary_bands(id INT PRIMARY KEY, grade VARCHAR(6), min_salary INT, max_salary INT)",
        "CREATE TABLE interview_notes(id INT PRIMARY KEY, applicant_id INT, interviewer VARCHAR(60), note VARCHAR(200), score INT)",
        "CREATE TABLE hr_config(id INT PRIMARY KEY AUTO_INCREMENT, config_key VARCHAR(60), config_value VARCHAR(200))",
    ]:
        k.execute(ddl)
    jobs = [("Senior Backend Engineer", "Engineering", "Remote", "$130k-$160k", "open"), ("Frontend Developer", "Engineering", "Austin, TX", "$95k-$120k", "open"),
            ("DevOps Engineer", "Engineering", "Remote", "$115k-$145k", "open"), ("Product Designer", "Design", "New York, NY", "$100k-$125k", "open"),
            ("Data Analyst", "Analytics", "Chicago, IL", "$80k-$100k", "open"), ("Security Analyst", "Security", "Remote", "$105k-$135k", "open"),
            ("Customer Success Manager", "Customer Success", "Denver, CO", "$85k-$105k", "open"), ("Technical Recruiter", "People", "Remote", "$70k-$90k", "open"),
            ("VP of Engineering (confidential search)", "Executive", "Remote", "$280k-$340k", "closed"), ("Head of Finance (confidential search)", "Executive", "New York, NY", "$250k-$300k", "closed")]
    k.executemany("INSERT INTO jobs VALUES(%s,%s,%s,%s,%s,%s,%s)",
                  [(i, t, d, l, s, f"Join the {d} team at Orbit Talent as a {t}. You will work with a cross-functional group building products used by thousands of customers.", st)
                   for i, (t, d, l, s, st) in enumerate(jobs, 1)])
    aps = people(45, "jobseekers.example")
    k.executemany("INSERT INTO applicants VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                  [(i, f"{f} {l}", e, phone(), R.randint(1, 10), R.randint(60, 220) * 1000, f"https://files.orbit.example/resumes/{i:04d}.pdf", date(2024, 2025))
                   for i, (f, l, e) in enumerate(aps, 1)])
    k.executemany("INSERT INTO hr_staff VALUES(%s,%s,%s,%s,%s,%s)", [
        (1, "hr.admin", "Dana Whitfield", md5("0rb1t#HRAdm!n24"), "admin", "dana@orbit.example"),
        (2, "recruiter1", "Miguel Santos", md5("Recruit#2024"), "recruiter", "miguel@orbit.example"),
        (3, "recruiter2", "Aisha Karim", md5("Welcome1"), "recruiter", "aisha@orbit.example"),
        (4, "payroll", "Bruce Holloway", md5("Payroll@2024"), "payroll", "bruce@orbit.example")])
    k.executemany("INSERT INTO salary_bands VALUES(%s,%s,%s,%s)", [(1, "L1", 55000, 75000), (2, "L2", 70000, 95000), (3, "L3", 90000, 125000), (4, "L4", 120000, 160000), (5, "L5", 150000, 210000), (6, "EXEC", 240000, 400000)])
    notes = ["Strong communicator", "Needs deeper system design experience", "Excellent culture fit", "Salary expectations above band", "Great portfolio", "Technical screen passed"]
    k.executemany("INSERT INTO interview_notes VALUES(%s,%s,%s,%s,%s)",
                  [(i, R.randint(1, 45), R.choice(["Miguel Santos", "Aisha Karim", "Dana Whitfield"]), R.choice(notes), R.randint(1, 5)) for i in range(1, 31)])
    k.executemany("INSERT INTO hr_config(config_key,config_value) VALUES(%s,%s)", [
        ("ats_api_key", "ats_live_c41d9e07b2a85f13"), ("payroll_sftp", "sftp://payroll.orbit.example/inbound"),
        ("background_check_token", "bgc_5a7e20d9c4f1"), ("flag", FLAGS["hr"])])
    h.close()
    root.close()


# ----------------------------------------------------------------------------- MSSQL : bank
def seed_mssql():
    import pymssql
    dbn, user, pwd = C.BANK_DB
    sa = pymssql.connect(server=C.MSSQL_HOST, port=C.MSSQL_PORT, user="sa", password=C.MSSQL_SA_PW, autocommit=True, login_timeout=15)
    cur = sa.cursor()
    cur.execute(f"IF DB_ID('{dbn}') IS NOT NULL BEGIN ALTER DATABASE {dbn} SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE {dbn}; END")
    cur.execute(f"IF EXISTS (SELECT 1 FROM sys.server_principals WHERE name='{user}') DROP LOGIN {user}")
    cur.execute(f"CREATE DATABASE {dbn}")
    cur.execute(f"CREATE LOGIN {user} WITH PASSWORD='{pwd}', CHECK_POLICY=OFF, DEFAULT_DATABASE={dbn}")
    sa.close()

    db = pymssql.connect(server=C.MSSQL_HOST, port=C.MSSQL_PORT, user="sa", password=C.MSSQL_SA_PW, database=dbn, autocommit=True, login_timeout=15)
    k = db.cursor()
    k.execute(f"CREATE USER {user} FOR LOGIN {user}")
    k.execute(f"ALTER ROLE db_datareader ADD MEMBER {user}")
    for ddl in [
        "CREATE TABLE customers(id INT PRIMARY KEY, full_name VARCHAR(80), email VARCHAR(90), phone VARCHAR(24), kyc_status VARCHAR(12), address VARCHAR(120))",
        "CREATE TABLE accounts(id INT PRIMARY KEY, account_no VARCHAR(20), customer_id INT, account_type VARCHAR(12), balance DECIMAL(14,2), currency VARCHAR(3))",
        "CREATE TABLE transactions(id INT PRIMARY KEY, account_no VARCHAR(20), txn_type VARCHAR(10), amount DECIMAL(12,2), description VARCHAR(120), txn_date VARCHAR(20))",
        "CREATE TABLE beneficiaries(id INT PRIMARY KEY, account_no VARCHAR(20), name VARCHAR(80), bank_name VARCHAR(60), iban VARCHAR(34))",
        "CREATE TABLE cards(id INT PRIMARY KEY, account_no VARCHAR(20), card_number VARCHAR(20), expiry VARCHAR(7), cvv_hash VARCHAR(64))",
        "CREATE TABLE portal_users(id INT PRIMARY KEY, username VARCHAR(40), password_hash VARCHAR(64), role VARCHAR(20))",
        "CREATE TABLE api_credentials(id INT PRIMARY KEY, client_name VARCHAR(60), api_key VARCHAR(60), scope VARCHAR(40))",
        "CREATE TABLE internal_config(id INT PRIMARY KEY, config_key VARCHAR(60), config_value VARCHAR(200))",
    ]:
        k.execute(ddl)
    cs = people(25, "bankmail.example")
    k.executemany("INSERT INTO customers VALUES(%s,%s,%s,%s,%s,%s)",
                  [(i, f"{f} {l}", e, phone(), R.choice(["verified", "verified", "pending"]), address()) for i, (f, l, e) in enumerate(cs, 1)])
    accts = []
    for i in range(1, 36):
        accts.append((i, f"ACC-{100200 + i * 7}", R.randint(1, 25), R.choice(["checking", "savings", "business"]), round(R.uniform(150, 98000), 2), "USD"))
    k.executemany("INSERT INTO accounts VALUES(%s,%s,%s,%s,%s,%s)", accts)
    descs = ["Grocery Mart", "Payroll deposit", "Electric utility", "Online marketplace", "ATM withdrawal", "Rent payment", "Streaming subscription", "Wire transfer", "Insurance premium", "Restaurant"]
    txns = []
    for i in range(1, 301):
        t = R.choice(["debit", "credit"])
        txns.append((i, R.choice(accts)[1], t, round(R.uniform(5, 4200), 2), R.choice(descs), date(2024, 2025, True)))
    k.executemany("INSERT INTO transactions VALUES(%s,%s,%s,%s,%s,%s)", txns)
    k.executemany("INSERT INTO beneficiaries VALUES(%s,%s,%s,%s,%s)",
                  [(i, R.choice(accts)[1], f"{R.choice(['Atlas', 'Beacon', 'Crest', 'Delta'])} {R.choice(['Supplies', 'Holdings', 'Logistics'])} Ltd", R.choice(["First Union", "Coastal Trust", "Metro Bank"]), f"GB{R.randint(10, 99)}HXBK{R.randint(10**13, 10**14 - 1)}") for i in range(1, 41)])
    k.executemany("INSERT INTO cards VALUES(%s,%s,%s,%s,%s)",
                  [(i, accts[i][1], R.choice(TEST_CARDS), f"{R.randint(1, 12):02d}/{R.randint(26, 30)}", md5(str(R.randint(100, 999)))) for i in range(1, 26)])
    k.executemany("INSERT INTO portal_users VALUES(%s,%s,%s,%s)", [
        (1, "bank.admin", md5("H3l1x#B@nk!Adm24"), "admin"), (2, "teller01", md5("Teller#2024"), "teller"),
        (3, "auditor", md5("Audit0r@2024"), "auditor"), (4, "ops", md5("Welcome1"), "ops")])
    k.executemany("INSERT INTO api_credentials VALUES(%s,%s,%s,%s)", [
        (1, "mobile-app", "hx_live_91c0e47ab2d35f68", "accounts:read"), (2, "partner-fintech", "hx_live_3e7a52d1c9b04f86", "transactions:read"),
        (3, "core-sync", "hx_live_c2d85a1f06e973b4", "admin")])
    k.executemany("INSERT INTO internal_config VALUES(%s,%s,%s)", [
        (1, "swift_bic", "HXBKGB2L"), (2, "core_banking_dsn", "Server=core.helixbank.example;User=svc_core;Password=C0re#Sync2024"),
        (3, "flag", FLAGS["bank"])])
    db.close()


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "wait":
        wait_for_dbs()
        return
    if what in ("sqlite", "all"):
        seed_shop()
        seed_help()
    if what in ("mysql", "all"):
        seed_mysql()
    if what in ("mssql", "all"):
        seed_mssql()
    if what == "all":
        open(os.path.join(C.DATA, ".seeded"), "w").write("ok")


if __name__ == "__main__":
    main()
