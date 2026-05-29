from functools import wraps
from urllib.parse import unquote
import csv
import io
import json
import os

import requests
from flask import Flask, Response, flash, jsonify, redirect, render_template, request, send_file, session, url_for


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")


class SessionExpired(Exception):
    pass


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "sessionid" not in session or "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def extract_cookie_value(raw_value, name):
    for part in raw_value.split(";"):
        key, _, value = part.strip().partition("=")
        if key == name and value:
            return value.strip()
    return ""


def normalize_sessionid(raw_value):
    value = raw_value.strip()
    return extract_cookie_value(value, "sessionid") or value


def extract_user_id(sessionid, raw_cookie=""):
    ds_user_id = extract_cookie_value(raw_cookie, "ds_user_id")
    if ds_user_id:
        return ds_user_id

    decoded = unquote(sessionid)
    user_id, separator, _ = decoded.partition(":")
    if separator and user_id.isdigit():
        return user_id

    return ""


def make_instagram_session(sessionid):
    http = requests.Session()
    http.cookies.set("sessionid", sessionid, domain=".instagram.com")
    http.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/",
    })
    return http


def fetch_friendship_users(http, user_id, relation):
    users = {}
    max_id = None
    url = f"https://www.instagram.com/api/v1/friendships/{user_id}/{relation}/"

    while True:
        params = {"count": 200}
        if max_id:
            params["max_id"] = max_id

        response = http.get(url, params=params, timeout=30)
        if response.status_code in (401, 403):
            raise SessionExpired("Sessionid expirado ou sem permissão.")
        response.raise_for_status()

        payload = response.json()
        if payload.get("status") == "fail":
            raise RuntimeError(payload.get("message") or "Instagram recusou a requisição.")

        for user in payload.get("users", []):
            username = user.get("username")
            if username:
                users[username] = user.get("full_name") or username

        max_id = payload.get("next_max_id")
        if not max_id:
            return users


def build_stats_data(user_id, followers, following):
    not_following_back = [
        {"username": username, "full_name": following[username]}
        for username in following if username not in followers
    ]
    you_not_following_back = [
        {"username": username, "full_name": followers[username]}
        for username in followers if username not in following
    ]

    return {
        "username": f"id_{user_id}",
        "full_name": "Conta conectada",
        "followers_count": len(followers),
        "following_count": len(following),
        "not_following_back_count": len(not_following_back),
        "you_not_following_back_count": len(you_not_following_back),
        "not_following_back": not_following_back,
        "you_not_following_back": you_not_following_back,
        "delta_followers": None,
        "delta_following": None,
    }


def collect_profile_stats(sessionid, user_id):
    http = make_instagram_session(sessionid)
    followers = fetch_friendship_users(http, user_id, "followers")
    following = fetch_friendship_users(http, user_id, "following")
    return build_stats_data(user_id, followers, following)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "sessionid" in session and "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        raw_sessionid = request.form.get("sessionid", "")
        sessionid = normalize_sessionid(raw_sessionid)
        user_id = extract_user_id(sessionid, raw_sessionid)

        if not sessionid:
            flash("Informe o sessionid da conta já logada.", "error")
            return render_template("login.html")

        if not user_id:
            flash("Não consegui encontrar o ID da conta no sessionid. Cole o valor completo do cookie.", "error")
            return render_template("login.html")

        session["sessionid"] = sessionid
        session["user_id"] = user_id
        session["username"] = f"id_{user_id}"
        session["full_name"] = "Conta conectada"
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/api/stats/stream")
@login_required
def api_stats_stream():
    sessionid = session["sessionid"]
    user_id = session["user_id"]

    def generate():
        def event(pct, msg, data=None):
            payload = {"pct": pct, "msg": msg}
            if data is not None:
                payload["data"] = data
            return f"data: {json.dumps(payload)}\n\n"

        try:
            yield event(10, "Conectando ao Instagram...")
            http = make_instagram_session(sessionid)

            yield event(30, "Buscando seguidores...")
            followers = fetch_friendship_users(http, user_id, "followers")
            yield event(55, f"Seguidores carregados: {len(followers)}")

            yield event(70, "Buscando quem voce segue...")
            following = fetch_friendship_users(http, user_id, "following")
            yield event(85, f"Seguindo carregados: {len(following)}")

            yield event(95, "Calculando diferencas...")
            yield event(100, "Tudo pronto!", build_stats_data(user_id, followers, following))
        except SessionExpired:
            session.clear()
            yield f"data: {json.dumps({'error': 'login_required'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/export/csv")
@login_required
def export_csv():
    try:
        data = collect_profile_stats(session["sessionid"], session["user_id"])
    except SessionExpired:
        session.clear()
        return redirect(url_for("login"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["tipo", "username", "nome_completo"])
    for user in data["not_following_back"]:
        writer.writerow(["nao_te_segue_de_volta", user["username"], user["full_name"]])
    for user in data["you_not_following_back"]:
        writer.writerow(["voce_nao_segue_de_volta", user["username"], user["full_name"]])
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"insta_tracker_{session['user_id']}.csv",
    )


if __name__ == "__main__":
    app.run(debug=True)
