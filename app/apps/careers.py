import pymysql
from flask import Blueprint, request

from common import message, mysql_conn, mysql_err, page
from config import HR_DB

bp = Blueprint("careers", __name__, url_prefix="/careers")

LIST = """{% extends 'base.html' %}{% block content %}
{% if hero %}<section class="hero"><h1>Build the future with us</h1><p>Join a team of builders, designers and problem solvers.</p></section>{% endif %}
<h2>{{ heading }}</h2>
<table><tr><th>Role</th><th>Team</th><th>Location</th><th>Salary</th></tr>
{% for j in jobs %}<tr><td><a href="/careers/job?id={{ j.id }}">{{ j.title }}</a></td><td>{{ j.department }}</td><td>{{ j.location }}</td><td>{{ j.salary_range }}</td></tr>{% endfor %}
</table>{% if not jobs %}<p class="muted">No roles found.</p>{% endif %}{% endblock %}"""

JOB = """{% extends 'base.html' %}{% block content %}
<div class="panel"><p><a href="/careers/">&larr; All roles</a></p>
<h1>{{ j.title }}</h1><p><span class="badge">{{ j.department }}</span> &middot; {{ j.location }} &middot; {{ j.salary_range }}</p>
<p>{{ j.description }}</p><a class="btn" href="/careers/apply?job={{ j.id }}">Apply now</a></div>{% endblock %}"""

APPLY = """{% extends 'base.html' %}{% block content %}<div class="panel"><h2>Apply</h2>
{% if sent %}<p>Thanks {{ name }}, your application has been received.</p>{% else %}
<form method="get" action="/careers/apply"><p><input type="text" name="name" placeholder="Full name"></p>
<p><input type="email" name="email" placeholder="Email"></p><input type="hidden" name="job" value="{{ job }}"><button>Submit</button></form>{% endif %}</div>{% endblock %}"""


def q(sql, args=None):
    con = mysql_conn(HR_DB)
    try:
        cur = con.cursor()
        cur.execute(sql, args)
        return cur.fetchall()
    finally:
        con.close()


@bp.route("/")
def index():
    dept = request.args.get("dept")
    if dept:
        jobs = q("SELECT id,title,department,location,salary_range FROM jobs WHERE status='open' AND department = %s", (dept,))
        return page(LIST, "careers", "Open roles", heading=f"Open roles in {dept}", jobs=jobs)
    jobs = q("SELECT id,title,department,location,salary_range FROM jobs WHERE status='open'")
    return page(LIST, "careers", "Open roles", hero=True, heading="Open roles", jobs=jobs)


@bp.route("/teams")
def teams():
    t = [r["department"] for r in q("SELECT DISTINCT department FROM jobs WHERE status='open'")]
    return page("""{% extends 'base.html' %}{% block content %}<h2>Teams</h2><div class="chips">{% for d in t %}<a href="/careers/?dept={{ d|urlencode }}">{{ d }}</a>{% endfor %}</div>{% endblock %}""",
                "careers", "Teams", t=t)


@bp.route("/search")
def search():
    kw = request.args.get("keyword", "").strip()
    jobs = q("SELECT id,title,department,location,salary_range FROM jobs WHERE status='open' AND title LIKE %s", (f"%{kw}%",)) if kw else []
    return page(LIST, "careers", "Search", heading=f"Roles matching “{kw}”" if kw else "Search roles", jobs=jobs)


@bp.route("/job")
def job():
    jid = request.args.get("id")
    if jid is None:
        return message("careers", "Invalid request", "Missing job id.", 400, "error")
    sql = "SELECT id, title, department, location, salary_range, description FROM jobs WHERE id = " + jid + " AND status = 'open'"
    try:
        rows = q(sql)
    except pymysql.MySQLError as e:
        return message("careers", "Database error", "This listing could not be loaded.", 500, "db", detail=mysql_err(e))
    if not rows:
        return message("careers", "Role not found", "This position is no longer available.", 404, "error")
    return page(JOB, "careers", rows[0]["title"], j=rows[0])


@bp.route("/apply")
def apply():
    name = request.args.get("name")
    return page(APPLY, "careers", "Apply", sent=bool(name), name=name, job=request.args.get("job", ""))


@bp.route("/staff/")
@bp.route("/staff")
def staff():
    return message("careers", "Restricted", "The recruiter console is only reachable from the corporate VPN.", 403, "error")
