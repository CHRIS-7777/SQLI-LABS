#!/usr/bin/env python3
from flask import Flask, Response

import config as C
from apps import bank, careers, clinic, helpdesk, shop
from common import APPS, message, page

app = Flask(__name__, static_folder="static", static_url_path="/static")
for m in (shop, clinic, bank, careers, helpdesk):
    app.register_blueprint(m.bp)

HUB = """{% extends 'base.html' %}{% block content %}
<section class="hero"><h1>Helix Group</h1><p>Internal services directory for our five subsidiaries.</p></section>
<div class="hub">{% for key, a in apps %}<div class="tile" style="--c:{{ a.accent }}">
<h3>{{ a.brand }}</h3><p>{{ a.tagline }}</p><a class="btn" style="background:{{ a.accent }}" href="{{ a.prefix }}/">Open</a></div>{% endfor %}</div>
{% endblock %}"""


@app.route("/")
def hub():
    return page(HUB, None, "Helix Group", apps=list(APPS.items()))


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nDisallow: /shop/admin\nDisallow: /clinic/portal/\nDisallow: /careers/staff/\n", mimetype="text/plain")


@app.errorhandler(404)
def nf(_):
    return message(None, "Not found", "The page you requested does not exist.", 404, "error")


@app.errorhandler(405)
def na(_):
    return message(None, "Method not allowed", "That method is not supported here.", 405, "error")


@app.errorhandler(500)
def ise(_):
    return message(None, "Server error", "Something went wrong. Please try again later.", 500, "error")


@app.after_request
def hdr(resp):
    resp.headers["Server"] = "nginx"
    return resp


if __name__ == "__main__":
    app.run(host=C.HOST, port=C.PORT, threaded=True, debug=False)
