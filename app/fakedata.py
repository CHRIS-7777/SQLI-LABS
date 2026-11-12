"""Deterministic fake data helpers used by the seeders."""
import datetime
import hashlib
import random

R = random.Random(20241111)

FIRST = ["Aiden", "Maya", "Liam", "Sofia", "Noah", "Isla", "Ethan", "Zara", "Lucas", "Priya",
         "Mateo", "Hana", "Oliver", "Amara", "Elijah", "Chloe", "Arjun", "Freya", "Daniel", "Nadia",
         "Leo", "Ingrid", "Samuel", "Leila", "Jacob", "Mei", "Caleb", "Tessa", "Omar", "Rhea",
         "Victor", "Alma", "Dev", "Clara", "Felix", "Yuki", "Hugo", "Selin", "Marco", "Beth"]
LAST = ["Anderson", "Brooks", "Chen", "Dalton", "Evans", "Fischer", "Garcia", "Hughes", "Iyer", "Jensen",
        "Kowalski", "Lopez", "Mehta", "Novak", "Okafor", "Patel", "Quinn", "Rossi", "Singh", "Tanaka",
        "Underwood", "Varga", "Walker", "Xu", "Young", "Zimmer", "Barnes", "Cooper", "Dixon", "Ellis"]
STREETS = ["Maple Ave", "Oak Street", "Harbor Rd", "Cedar Lane", "Pine Court", "Lakeview Dr", "Sunset Blvd", "Mill Street"]
CITIES = ["Springfield", "Riverton", "Fairview", "Kingston", "Brookfield", "Ashland", "Clayton", "Georgetown"]
PASSWORDS = ["Summer2024!", "Welcome1", "Passw0rd", "letmein123", "Qwerty@2024", "Spring#2023",
             "Monkey123", "Dragon2024", "Football1", "Sunshine99", "Admin@123", "Changeme1"]
TEST_CARDS = ["4111111111111111", "4242424242424242", "5555555555554444", "378282246310005", "6011111111111117"]

FLAGS = {
    "shop": "FLAG{sqlite_union_featured_9c41e2}",
    "clinic": "FLAG{mysql_error_lookup_7b03d8}",
    "bank": "FLAG{mssql_convert_leak_41ae6f}",
    "hr": "FLAG{mysql_numeric_union_d2f95a}",
    "help": "FLAG{sqlite_like_search_58c7b1}",
}


def md5(s):
    return hashlib.md5(s.encode()).hexdigest()


def sha1(s):
    return hashlib.sha1(s.encode()).hexdigest()


def people(n, domain):
    """n unique (first, last, email) tuples."""
    seen, out = set(), []
    while len(out) < n:
        f, l = R.choice(FIRST), R.choice(LAST)
        email = f"{f}.{l}@{domain}".lower()
        if email in seen:
            continue
        seen.add(email)
        out.append((f, l, email))
    return out


def phone():
    return f"+1-{R.randint(200, 989)}-555-{R.randint(1000, 9999)}"


def address():
    return f"{R.randint(10, 999)} {R.choice(STREETS)}, {R.choice(CITIES)}"


def date(y1=2022, y2=2024, with_time=False):
    d = datetime.date(R.randint(y1, y2), R.randint(1, 12), R.randint(1, 28))
    if with_time:
        return f"{d.isoformat()} {R.randint(8, 18):02d}:{R.randint(0, 59):02d}:00"
    return d.isoformat()


def pw():
    return R.choice(PASSWORDS)
