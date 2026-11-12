import sqlite3

from flask import Blueprint, request

from common import message, page, sqlite_conn

bp = Blueprint("shop", __name__, url_prefix="/shop")
DB = "shop.db"
COLS = "id,name,price,image,badge,description"

LISTING = """{% extends 'base.html' %}{% from '_macros.html' import cards %}{% block content %}
{% if hero %}<section class="hero"><h1>{{ hero }}</h1><p>Free shipping on orders over $75.</p></section>{% endif %}
{% if chips %}<div class="chips">{% for c in chips %}<a href="/shop/category?name={{ c|urlencode }}">{{ c }}</a>{% endfor %}</div>{% endif %}
<h2>{{ heading }}</h2>
{{ cards(items) }}
{% if pages and pages > 1 %}<p class="row">{% for n in range(1, pages + 1) %}<a class="btn" href="/shop/products?page={{ n }}">{{ n }}</a>{% endfor %}</p>{% endif %}
{% endblock %}"""

DETAIL = """{% extends 'base.html' %}{% block content %}
<div class="panel"><div class="row"><div class="thumb" style="font-size:80px">{{ p.image }}</div><div>
<h1>{{ p.name }}</h1><p>{{ p.description }}</p><h2>${{ p.price }}</h2><p class="muted">Category: {{ p.category }} &middot; {{ p.stock }} in stock</p>
</div></div></div>{% endblock %}"""

FORM = """{% extends 'base.html' %}{% block content %}
<div class="panel"><h2>{{ heading }}</h2><p class="muted">{{ blurb }}</p>
<form method="{{ method }}" class="row"><input type="text" name="{{ field }}" placeholder="{{ placeholder }}" value="{{ value }}"><button>{{ button }}</button></form>
{% if result %}<p>{{ result }}</p>{% endif %}</div>{% endblock %}"""


def rows(cur):
    return [dict(r) for r in cur.fetchall()]


@bp.route("/")
def home():
    con = sqlite_conn(DB)
    items = rows(con.execute(f"SELECT {COLS} FROM products ORDER BY id DESC LIMIT 8"))
    chips = [r["name"] for r in con.execute("SELECT name FROM categories")]
    return page(LISTING, "shop", "Home", hero="Gear for every trip", chips=chips, heading="Latest arrivals", items=items)


@bp.route("/products")
def products():
    try:
        pg = max(1, int(request.args.get("page", 1)))
    except ValueError:
        pg = 1
    con = sqlite_conn(DB)
    total = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    items = rows(con.execute(f"SELECT {COLS} FROM products ORDER BY id LIMIT 12 OFFSET ?", ((pg - 1) * 12,)))
    return page(LISTING, "shop", "Products", heading="All products", items=items, pages=-(-total // 12))


@bp.route("/product")
def product():
    try:
        pid = int(request.args.get("id", ""))
    except ValueError:
        return message("shop", "Invalid request", "Product id must be a number.", 400, "error")
    r = sqlite_conn(DB).execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    if not r:
        return message("shop", "Not found", "We couldn't find that product.", 404, "error")
    return page(DETAIL, "shop", r["name"], p=dict(r))


@bp.route("/category")
def category():
    name = request.args.get("name", "")
    con = sqlite_conn(DB)
    valid = [r["name"] for r in con.execute("SELECT name FROM categories")]
    if name not in valid:
        return message("shop", "Unknown category", "Please choose one of: " + ", ".join(valid) + ".", 404, "error")
    items = rows(con.execute(f"SELECT {COLS} FROM products WHERE category = ?", (name,)))
    return page(LISTING, "shop", name, heading=name, items=items)


@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    items = []
    if q:
        items = rows(sqlite_conn(DB).execute(f"SELECT {COLS} FROM products WHERE name LIKE ? OR description LIKE ?", (f"%{q}%", f"%{q}%")))
    return page(LISTING, "shop", "Search", heading=f"Results for “{q}” ({len(items)})" if q else "Search", items=items)


@bp.route("/featured")
def featured():
    sort = request.args.get("sort")
    con = sqlite_conn(DB)
    if sort is None:
        items = rows(con.execute(f"SELECT {COLS} FROM products WHERE featured = 1 ORDER BY id"))
        return page(LISTING, "shop", "Featured", heading="Featured products", items=items)
    query = f"SELECT {COLS} FROM products WHERE featured = 1 AND badge = '{sort}'"
    try:
        items = rows(con.execute(query))
    except sqlite3.Error as e:
        return message("shop", "Database error", "The featured collection could not be loaded.", 500, "db",
                       detail=f"sqlite3.{type(e).__name__}: {e}")
    if not items:
        return message("shop", "Invalid sort option", "No products match the selected collection.", 400, "error")
    return page(LISTING, "shop", "Featured", heading="Featured products", items=items)


# ---- rabbit holes -------------------------------------------------------------
@bp.route("/track")
def track():
    """Looks injectable, is not: any quote char gets a canned error (even balanced ones)."""
    o = request.args.get("order", "").strip()
    if not o:
        return page(FORM, "shop", "Track order", heading="Track your order", blurb="Enter your order number, e.g. ORD-1001.",
                    method="get", field="order", placeholder="ORD-XXXX", value="", button="Track", result=None)
    if any(ch in o for ch in "'\"`"):
        return message("shop", "Database error", "Unable to look up your order.", 500, "db",
                       detail='sqlite3.OperationalError: near "\'": syntax error')
    r = sqlite_conn(DB).execute("SELECT status, created_at FROM orders WHERE id = ?", (o,)).fetchone()
    res = f"Order {o} is {r['status']} (placed {r['created_at']})." if r else f"No order found with number {o}."
    return page(FORM, "shop", "Track order", heading="Track your order", blurb="Enter your order number.", method="get",
                field="order", placeholder="ORD-XXXX", value=o, button="Track", result=res)


@bp.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        u, p = request.form.get("username", ""), request.form.get("password", "")
        sqlite_conn(DB).execute("SELECT id FROM users WHERE username = ? AND password_hash = ? AND role = 'admin'", (u, p)).fetchone()
        return message("shop", "Access denied", "Invalid credentials.", 401, "error")
    return page("""{% extends 'base.html' %}{% block content %}<div class="panel"><h2>Admin sign-in</h2>
<form method="post"><p><input type="text" name="username" placeholder="Username"></p><p><input type="password" name="password" placeholder="Password"></p><button>Sign in</button></form></div>{% endblock %}""",
                "shop", "Admin")
