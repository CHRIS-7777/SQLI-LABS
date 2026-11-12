import pymysql
from flask import Blueprint, request

from common import message, mysql_conn, mysql_err, page
from config import CLINIC_DB

bp = Blueprint("clinic", __name__, url_prefix="/clinic")

HOME = """{% extends 'base.html' %}{% block content %}
<section class="hero"><h1>Caring for you and your family</h1><p>Book visits, meet our specialists and manage your appointments online.</p></section>
<div class="panel"><h2>Check your appointment</h2><p class="muted">Enter the reference from your confirmation email (e.g. <code>APT-10001</code>).</p>
<form method="get" action="/clinic/appointment" class="row"><input type="text" name="ref" placeholder="APT-XXXXX"><button>Check status</button></form></div>
<h2>Departments</h2><div class="chips">{% for d in depts %}<a href="/clinic/departments?name={{ d|urlencode }}">{{ d }}</a>{% endfor %}</div>
{% endblock %}"""

APPT = """{% extends 'base.html' %}{% block content %}
<div class="panel"><h2>Appointment status</h2>
<form method="get" class="row"><input type="text" name="ref" value="{{ ref }}" placeholder="APT-XXXXX"><button>Check status</button></form></div>
{% if rows %}<table><tr><th>Reference</th><th>Date</th><th>Status</th><th>Reason</th><th>Doctor</th></tr>
{% for r in rows %}<tr><td>{{ r.ref }}</td><td>{{ r.appt_date }}</td><td>{{ r.status }}</td><td>{{ r.reason }}</td><td>{{ r.doctor }}</td></tr>{% endfor %}</table>{% endif %}
{% endblock %}"""

DOCS = """{% extends 'base.html' %}{% block content %}<h2>{{ heading }}</h2>
<div class="grid">{% for d in docs %}<div class="card"><h3><a href="/clinic/doctor?id={{ d.id }}">{{ d.name }}</a></h3>
<span class="badge">{{ d.specialty }}</span><p>{{ d.department }}</p></div>{% endfor %}</div>{% endblock %}"""

DOC = """{% extends 'base.html' %}{% block content %}<div class="panel"><h1>{{ d.name }}</h1>
<p><span class="badge">{{ d.specialty }}</span> &middot; {{ d.department }}</p><p>{{ d.bio }}</p><p class="muted">{{ d.email }}</p></div>{% endblock %}"""

CONTACT = """{% extends 'base.html' %}{% block content %}<div class="panel"><h2>Contact us</h2>
<form method="get" action="/clinic/contact"><p><input type="text" name="topic" placeholder="Topic" value="{{ topic }}"></p>
<p><textarea name="msg" rows="4" style="width:100%" placeholder="How can we help?"></textarea></p><button>Send</button></form>
{% if topic %}<p class="muted">Thanks, we have received your enquiry about “{{ topic }}”. Our team will reply within two working days.</p>{% endif %}</div>{% endblock %}"""


def q(sql, args=None):
    con = mysql_conn(CLINIC_DB)
    try:
        cur = con.cursor()
        cur.execute(sql, args)
        return cur.fetchall()
    finally:
        con.close()


@bp.route("/")
def home():
    depts = [r["department"] for r in q("SELECT DISTINCT department FROM doctors ORDER BY department")]
    return page(HOME, "clinic", "Home", depts=depts)


@bp.route("/doctors")
def doctors():
    return page(DOCS, "clinic", "Our doctors", heading="Our doctors", docs=q("SELECT id,name,specialty,department FROM doctors"))


@bp.route("/departments")
def departments():
    name = request.args.get("name")
    if not name:
        names = [r["department"] for r in q("SELECT DISTINCT department FROM doctors ORDER BY department")]
        return page(HOME, "clinic", "Departments", depts=names)
    docs = q("SELECT id,name,specialty,department FROM doctors WHERE department = %s", (name,))
    if not docs:
        return message("clinic", "Department not found", "We don't have a department with that name.", 404, "error")
    return page(DOCS, "clinic", name, heading=name, docs=docs)


@bp.route("/doctor")
def doctor():
    try:
        did = int(request.args.get("id", ""))
    except ValueError:
        return message("clinic", "Invalid request", "Doctor id must be a number.", 400, "error")
    r = q("SELECT * FROM doctors WHERE id = %s", (did,))
    if not r:
        return message("clinic", "Not found", "No such doctor.", 404, "error")
    return page(DOC, "clinic", r[0]["name"], d=r[0])


@bp.route("/appointment")
def appointment():
    ref = request.args.get("ref")
    if ref is None:
        return page(APPT, "clinic", "Appointment status", ref="", rows=None)
    sql = ("SELECT a.ref AS ref, a.appt_date AS appt_date, a.status AS status, a.reason AS reason, d.name AS doctor "
           "FROM appointments a JOIN doctors d ON d.id = a.doctor_id WHERE a.ref = '" + ref + "'")
    try:
        rows = q(sql)
    except pymysql.MySQLError as e:
        return message("clinic", "Database error", "We couldn't retrieve your appointment right now.", 500, "db", detail=mysql_err(e))
    if not rows:
        return message("clinic", "Appointment not found", "No appointment matches the reference you entered.", 404, "error")
    return page(APPT, "clinic", "Appointment status", ref=ref, rows=rows)


@bp.route("/contact")
def contact():
    return page(CONTACT, "clinic", "Contact", topic=request.args.get("topic", ""))


@bp.route("/portal/")
@bp.route("/portal")
def portal():
    return message("clinic", "Restricted", "The staff portal is only available from the hospital network.", 403, "error")
