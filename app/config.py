"""Lab configuration (connection settings only - nothing here is served over HTTP)."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))

# --- MySQL (docker container, published on localhost only) ---
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 33061
MYSQL_ROOT_PW = "Lab_Root#2024"
CLINIC_DB = ("clinic_db", "clinic_app", "Cl1n1c@pp#2024")
HR_DB = ("hr_db", "hr_app", "Hr@pp#Talent24")

# --- MSSQL (docker container, published on localhost only) ---
MSSQL_HOST = "127.0.0.1"
MSSQL_PORT = 14331
MSSQL_SA_PW = "Lab_SA#2024xQz"
BANK_DB = ("HelixBank", "bank_app", "B@nkApp#2024!")
