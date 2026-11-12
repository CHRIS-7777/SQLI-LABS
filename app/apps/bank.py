import pymssql
from flask import Blueprint, jsonify, request

from common import mssql_conn, mssql_err, page

bp = Blueprint("bank", __name__, url_prefix="/bank")

EXPLORER = """{% extends 'base.html' %}{% block content %}
<section class="hero"><h1>Helix Pay Developer Sandbox</h1><p>Explore the sandbox data set before integrating with the production API.</p></section>
<div class="panel"><h2>Transaction explorer</h2>
<p class="muted">Look up recent activity for a sandbox account, e.g. <code>ACC-100207</code>.</p>
<div class="row"><input type="text" id="acct" placeholder="ACC-XXXXXX"><button onclick="go()">Fetch</button></div>
<pre id="out" style="color:#d3f9d8">// results appear here</pre></div>
<script>
async function go(){
  const v = document.getElementById('acct').value;
  const r = await fetch('/bank/api/v1/transactions?account_no=' + encodeURIComponent(v));
  document.getElementById('out').textContent = JSON.stringify(await r.json(), null, 2);
}
</script>{% endblock %}"""

DOCS = """{% extends 'base.html' %}{% block content %}
<h1>API reference <span class="badge">v1</span></h1>
<p class="muted">All endpoints return JSON. The sandbox does not require authentication.</p>
<table><tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
<tr><td>GET</td><td><code>/bank/api/v1/accounts/{id}</code></td><td>Account summary by numeric id.</td></tr>
<tr><td>GET</td><td><code>/bank/api/v1/beneficiaries?account_no=</code></td><td>Saved payees for an account.</td></tr>
<tr><td>GET</td><td><code>/bank/api/v1/transactions?account_no=</code></td><td>Recent transactions for an account.</td></tr>
<tr><td>GET</td><td><code>/bank/api/v1/rates?currency=</code></td><td>Indicative FX rates against USD.</td></tr>
</table>{% endblock %}"""

STATUS = """{% extends 'base.html' %}{% block content %}<div class="panel"><h2>System status</h2>
<table><tr><th>Service</th><th>State</th></tr><tr><td>Sandbox API</td><td>Operational</td></tr><tr><td>Webhooks</td><td>Operational</td></tr><tr><td>Reporting</td><td>Operational</td></tr></table></div>{% endblock %}"""

RATES = {"EUR": 0.92, "GBP": 0.79, "JPY": 151.3, "INR": 83.2, "CAD": 1.36}


def err(msg, code, **extra):
    return jsonify(status="error", message=msg, **extra), code


@bp.route("/")
def explorer():
    return page(EXPLORER, "bank", "Explorer")


@bp.route("/api/docs")
def docs():
    return page(DOCS, "bank", "API docs")


@bp.route("/status")
def status():
    return page(STATUS, "bank", "Status")


@bp.route("/api/v1/accounts/<int:aid>")
def account(aid):
    con = mssql_conn()
    try:
        cur = con.cursor()
        cur.execute("SELECT account_no, account_type, currency FROM accounts WHERE id = %s", (aid,))
        r = cur.fetchone()
    finally:
        con.close()
    return jsonify(status="ok", account=r) if r else err("Account not found", 404)


@bp.route("/api/v1/beneficiaries")
def beneficiaries():
    acct = request.args.get("account_no", "")
    con = mssql_conn()
    try:
        cur = con.cursor()
        cur.execute("SELECT name, bank_name FROM beneficiaries WHERE account_no = %s", (acct,))
        rows = cur.fetchall()
    finally:
        con.close()
    return jsonify(status="ok", count=len(rows), beneficiaries=rows) if rows else err("No beneficiaries found", 404)


@bp.route("/api/v1/rates")
def rates():
    cur = request.args.get("currency", "").upper()
    if cur not in RATES:
        return err("Unsupported currency", 400, supported=sorted(RATES))
    return jsonify(status="ok", base="USD", currency=cur, rate=RATES[cur])


@bp.route("/api/v1/transactions")
def transactions():
    acct = request.args.get("account_no")
    if acct is None:
        return err("Missing required parameter: account_no", 400)
    sql = ("SELECT id, account_no, txn_type, amount, description, txn_date "
           "FROM transactions WHERE account_no = '" + acct + "'")
    con = None
    try:
        con = mssql_conn()
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
    except pymssql.Error as e:
        return err("Database error", 500, detail=mssql_err(e))
    finally:
        if con:
            con.close()
    if not rows:
        return err("No transactions found for the given account", 404)
    return jsonify(status="ok", count=len(rows), transactions=rows)
