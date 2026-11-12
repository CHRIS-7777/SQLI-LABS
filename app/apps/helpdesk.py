import sqlite3

from flask import Blueprint, request

from common import message, page, sqlite_conn

bp = Blueprint("help", __name__, url_prefix="/help")
DB = "help.db"

HOME = """{% extends 'base.html' %}{% block content %}
<section class="hero"><h1>How can we help?</h1><p>Search our knowledge base or browse topics below.</p></section>
<h2>Browse topics</h2><div class="chips">{% for c in cats %}<a href="/help/category?name={{ c|urlencode }}">{{ c }}</a>{% endfor %}</div>
<h2>Popular articles</h2>{% include '_articles.html' %}{% endblock %}"""

SEARCH = """{% extends 'base.html' %}{% block content %}<h2>{{ heading }}</h2>{% include '_articles.html' %}{% endblock %}"""

ARTICLE = """{% extends 'base.html' %}{% block content %}<div class="panel"><p><a href="/help/">&larr; Help home</a></p>
<h1>{{ a.title }}</h1><p><span class="badge">{{ a.category }}</span> <span class="muted">Updated {{ a.updated }}</span></p><p>{{ a.body }}</p></div>{% endblock %}"""

TICKET = """{% extends 'base.html' %}{% block content %}<div class="panel"><h2>Ticket status</h2>
<form method="get" class="row"><input type="text" name="id" value="{{ tid }}" placeholder="TKT-XXXX"><button>Check</button></form>
{% if result %}<p>{{ result }}</p>{% endif %}</div>{% endblock %}"""


def rows(cur):
    return [dict(r) for r in cur.fetchall()]


@bp.route("/")
def home():
    con = sqlite_conn(DB)
    cats = [r[0] for r in con.execute("SELECT DISTINCT category FROM kb_articles WHERE published = 1 AND category != 'Internal' ORDER BY 1")]
    arts = rows(con.execute("SELECT id,title,category,summary,updated FROM kb_articles WHERE published = 1 ORDER BY id LIMIT 6"))
    return page(HOME, "help", "Home", cats=cats, arts=arts)


@bp.route("/category")
def category():
    name = request.args.get("name")
    con = sqlite_conn(DB)
    cats = [r[0] for r in con.execute("SELECT DISTINCT category FROM kb_articles WHERE published = 1 AND category != 'Internal' ORDER BY 1")]
    if not name:
        return page(SEARCH.replace("{% include '_articles.html' %}", '<div class="chips">{% for c in cats %}<a href="/help/category?name={{ c|urlencode }}">{{ c }}</a>{% endfor %}</div>'),
                    "help", "Topics", heading="Topics", cats=cats)
    if name not in cats:
        return message("help", "Topic not found", "That topic does not exist.", 404, "error")
    arts = rows(con.execute("SELECT id,title,category,summary,updated FROM kb_articles WHERE published = 1 AND category = ?", (name,)))
    return page(SEARCH, "help", name, heading=name, arts=arts)


@bp.route("/article")
def article():
    try:
        aid = int(request.args.get("id", ""))
    except ValueError:
        return message("help", "Invalid request", "Article id must be a number.", 400, "error")
    r = sqlite_conn(DB).execute("SELECT * FROM kb_articles WHERE id = ? AND published = 1", (aid,)).fetchone()
    if not r:
        return message("help", "Article not found", "We couldn't find that article.", 404, "error")
    return page(ARTICLE, "help", r["title"], a=dict(r))


@bp.route("/search")
def search():
    qs = request.args.get("q")
    if qs is None:
        return page(SEARCH, "help", "Search", heading="Search the knowledge base", arts=[])
    sql = ("SELECT id, title, category, summary, updated FROM kb_articles "
           "WHERE title LIKE '%" + qs + "%'")
    try:
        arts = rows(sqlite_conn(DB).execute(sql))
    except sqlite3.Error as e:
        return message("help", "Search unavailable", "Something went wrong while searching. Please try again later.", 500, "db",
                       detail=f"sqlite3.{type(e).__name__}: {e}")
    if not arts:
        return message("help", "No results", "No articles matched your search.", 200, "info")
    return page(SEARCH, "help", "Search", heading=f"Search results ({len(arts)})", arts=arts)


@bp.route("/ticket")
def ticket():
    tid = request.args.get("id", "").strip()
    res = None
    if tid:
        r = sqlite_conn(DB).execute("SELECT status, priority FROM tickets WHERE id = ?", (tid,)).fetchone()
        res = f"Ticket {tid} is {r['status']} (priority: {r['priority']})." if r else "No ticket found with that id."
    return page(TICKET, "help", "Ticket status", tid=tid, result=res)


@bp.route("/contact")
def contact():
    return page("""{% extends 'base.html' %}{% block content %}<div class="panel"><h2>Contact support</h2>
<p>Email <code>support@nimbus.example</code> and include your workspace name. Typical response time is 4 business hours.</p></div>{% endblock %}""",
                "help", "Contact")
