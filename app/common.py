"""Shared helpers: DB connections, page rendering, per-app branding."""
import sqlite3
import os

import pymssql
import pymysql
from flask import render_template_string

import config as C

APPS = {
    "shop": dict(brand="Parcelo Marketplace", tagline="Gear for every trip", accent="#e4572e", prefix="/shop",
                 nav=[("Home", "/shop/"), ("Products", "/shop/products"), ("Featured", "/shop/featured"), ("Track order", "/shop/track")],
                 search=("/shop/search", "q", "Search products")),
    "clinic": dict(brand="MedCare Clinic", tagline="Caring for you and your family", accent="#1f8a70", prefix="/clinic",
                   nav=[("Home", "/clinic/"), ("Our doctors", "/clinic/doctors"), ("Departments", "/clinic/departments"), ("Contact", "/clinic/contact")],
                   search=None),
    "bank": dict(brand="Helix Pay", tagline="Developer sandbox", accent="#3b5bdb", prefix="/bank",
                 nav=[("Explorer", "/bank/"), ("API docs", "/bank/api/docs"), ("Status", "/bank/status")],
                 search=None),
    "careers": dict(brand="Orbit Talent", tagline="Build the future with us", accent="#7048e8", prefix="/careers",
                    nav=[("Open roles", "/careers/"), ("Teams", "/careers/teams"), ("Apply", "/careers/apply")],
                    search=("/careers/search", "keyword", "Search roles")),
    "help": dict(brand="Nimbus Help Center", tagline="How can we help?", accent="#0c8599", prefix="/help",
                 nav=[("Home", "/help/"), ("Topics", "/help/category"), ("Ticket status", "/help/ticket"), ("Contact", "/help/contact")],
                 search=("/help/search", "q", "Search articles")),
}


def page(tpl, appkey, title, status=200, **ctx):
    html = render_template_string(tpl, appkey=appkey, app=APPS.get(appkey), title=title, **ctx)
    return html, status


MESSAGE = """{% extends 'base.html' %}{% block content %}
<div class="alert {{ kind }}"><h2>{{ heading }}</h2><p>{{ message }}</p>{% if detail %}<pre>{{ detail }}</pre>{% endif %}</div>
<p><a href="javascript:history.back()">&larr; Go back</a></p>{% endblock %}"""


def message(appkey, heading, msg, status=200, kind="info", detail=None):
    return page(MESSAGE, appkey, heading, status, heading=heading, message=msg, kind=kind, detail=detail)


# ---- connections ---------------------------------------------------------------
def sqlite_conn(name):
    con = sqlite3.connect(os.path.join(C.DATA, name))
    con.row_factory = sqlite3.Row
    return con


def mysql_conn(cfg):
    dbn, user, pwd = cfg
    return pymysql.connect(host=C.MYSQL_HOST, port=C.MYSQL_PORT, user=user, password=pwd, database=dbn,
                           cursorclass=pymysql.cursors.DictCursor, autocommit=True, charset="utf8mb4", connect_timeout=8)


def mssql_conn():
    dbn, user, pwd = C.BANK_DB
    return pymssql.connect(server=C.MSSQL_HOST, port=C.MSSQL_PORT, user=user, password=pwd, database=dbn,
                           as_dict=True, autocommit=True, login_timeout=10, charset="UTF-8")


def mysql_err(e):
    """Render a pymysql error the way the mysql client prints it."""
    if len(e.args) >= 2:
        return f"ERROR {e.args[0]}: {e.args[1]}"
    return str(e)


def mssql_err(e):
    code = e.args[0] if e.args else ""
    txt = e.args[1] if len(e.args) > 1 else str(e)
    if isinstance(txt, bytes):
        txt = txt.decode("utf-8", "replace")
    txt = str(txt).split("DB-Lib error")[0].strip()
    return f"Msg {code}: {txt}"
