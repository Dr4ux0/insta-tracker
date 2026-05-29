from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file, Response
from functools import wraps
import instaloader
import requests
import csv
import io
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")


# ── Decorador de autenticação ─────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Helper do Instaloader ─────────────────────────────────────────────────────

def get_loader():
    """Cria um Instaloader autenticado via sessionid salvo na sessão."""
    L = instaloader.Instaloader()
    L.context._session.cookies.set("sessionid", session["sessionid"], domain=".instagram.com")
    L.context.username = session["username"]
    return L


# ── Rotas de autenticação ─────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lstrip("@")
        password = request.form.get("password", "")

        if not username or not password:
            flash("Preencha o usuário e a senha.", "error")
            return render_template("login.html")

        try:
            L = instaloader.Instaloader()
            L.login(username, password)

            # Extrai o sessionid do cookie para reutilizar nas próximas requisições
            sessionid = L.context._session.cookies.get("sessionid", domain=".instagram.com")

            if not sessionid:
                flash("Não foi possível obter a sessão. Verifique suas credenciais.", "error")
                return render_template("login.html")

            session["sessionid"] = sessionid
            session["username"]  = username
            session["full_name"] = username
            return redirect(url_for("home"))

        except instaloader.exceptions.BadCredentialsException:
            flash("Usuário ou senha incorretos.", "error")
        except instaloader.exceptions.TwoFactorAuthRequiredException:
            flash("Sua conta tem autenticação de dois fatores ativa. Use o sessionid manualmente.", "warning")
        except instaloader.exceptions.ConnectionException as e:
            flash(f"Erro de conexão: {str(e)}", "error")
        except Exception as e:
            flash(f"Erro inesperado: {str(e)}", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def home():
    return render_template("index.html")


# ── SSE: stats com progresso em tempo real ────────────────────────────────────

@app.route("/api/stats/stream")
@login_required
def api_stats_stream():
    sessionid = session.get("sessionid")
    username  = session.get("username")

    def generate():
        def event(pct, msg, data=None):
            payload = {"pct": pct, "msg": msg}
            if data is not None:
                payload["data"] = data
            return f"data: {json.dumps(payload)}\n\n"

        try:
            yield event(10, "Conectando ao Instagram…")

            L = instaloader.Instaloader()
            L.context._session.cookies.set("sessionid", sessionid, domain=".instagram.com")
            L.context.username = username

            yield event(20, "Buscando perfil…")
            profile = instaloader.Profile.from_username(L.context, username)

            yield event(30, "Buscando seguidores…")
            try:
                followers = {p.username: p.full_name for p in profile.get_followers()}
                yield event(50, f"Seguidores carregados: {len(followers)}")
            except Exception as e:
                yield f"data: {json.dumps({'error': 'get_followers falhou: ' + str(e)})}\n\n"
                return

            yield event(65, "Buscando quem você segue…")
            try:
                following = {p.username: p.full_name for p in profile.get_followees()}
                yield event(80, f"Seguindo carregados: {len(following)}")
            except Exception as e:
                yield f"data: {json.dumps({'error': 'get_followees falhou: ' + str(e)})}\n\n"
                return

            yield event(88, "Calculando diferenças…")

            not_following_back = [
                {"username": u, "full_name": following[u]}
                for u in following if u not in followers
            ]
            you_not_following_back = [
                {"username": u, "full_name": followers[u]}
                for u in followers if u not in following
            ]

            data = {
                "username":                     profile.username,
                "full_name":                    profile.full_name,
                "followers_count":              profile.followers,
                "following_count":              profile.followees,
                "not_following_back_count":     len(not_following_back),
                "you_not_following_back_count": len(you_not_following_back),
                "not_following_back":           not_following_back,
                "you_not_following_back":       you_not_following_back,
                "delta_followers":              None,
                "delta_following":              None,
            }

            yield event(100, "Tudo pronto!", data)

        except instaloader.exceptions.LoginRequiredException:
            yield f"data: {json.dumps({'error': 'login_required'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        }
    )


# ── Endpoint legado (mantido para compatibilidade) ────────────────────────────

@app.route("/api/stats")
@login_required
def api_stats():
    try:
        L = get_loader()
        profile = instaloader.Profile.from_username(L.context, session["username"])

        followers = {p.username: p.full_name for p in profile.get_followers()}
        following = {p.username: p.full_name for p in profile.get_followees()}

        not_following_back = [
            {"username": u, "full_name": following[u]}
            for u in following if u not in followers
        ]
        you_not_following_back = [
            {"username": u, "full_name": followers[u]}
            for u in followers if u not in following
        ]

        return jsonify({
            "username":                     profile.username,
            "full_name":                    profile.full_name,
            "followers_count":              profile.followers,
            "following_count":              profile.followees,
            "not_following_back_count":     len(not_following_back),
            "you_not_following_back_count": len(you_not_following_back),
            "not_following_back":           not_following_back,
            "you_not_following_back":       you_not_following_back,
            "delta_followers":              None,
            "delta_following":              None,
        })
    except instaloader.exceptions.LoginRequiredException:
        session.clear()
        return jsonify({"error": "Sessão expirada"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Ações de seguir / deixar de seguir ───────────────────────────────────────

@app.route("/action/unfollow", methods=["POST"])
@login_required
def action_unfollow():
    data = request.get_json()
    username = data.get("username")
    if not username:
        return jsonify({"error": "username obrigatório"}), 400
    try:
        L = get_loader()
        profile = instaloader.Profile.from_username(L.context, username)
        L.unfollow(profile.userid)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/action/follow", methods=["POST"])
@login_required
def action_follow():
    data = request.get_json()
    username = data.get("username")
    if not username:
        return jsonify({"error": "username obrigatório"}), 400
    try:
        L = get_loader()
        profile = instaloader.Profile.from_username(L.context, username)
        L.follow(profile.userid)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Exportar CSV ──────────────────────────────────────────────────────────────

@app.route("/export/csv")
@login_required
def export_csv():
    try:
        L = get_loader()
        profile = instaloader.Profile.from_username(L.context, session["username"])

        followers = {p.username: p.full_name for p in profile.get_followers()}
        following = {p.username: p.full_name for p in profile.get_followees()}

        not_following_back = [
            {"username": u, "full_name": following[u]}
            for u in following if u not in followers
        ]
        you_not_following_back = [
            {"username": u, "full_name": followers[u]}
            for u in followers if u not in following
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["tipo", "username", "nome_completo"])
        for u in not_following_back:
            writer.writerow(["nao_te_segue_de_volta", u["username"], u["full_name"]])
        for u in you_not_following_back:
            writer.writerow(["voce_nao_segue_de_volta", u["username"], u["full_name"]])
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"insta_tracker_{session['username']}.csv",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)