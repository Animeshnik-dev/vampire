import os
from flask import Flask, request, render_template, jsonify, redirect, session, url_for
from core.builder import build_lua
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder=".", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_vampire_key")

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1561124820853329920")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "KcksrY3iT8cjhktTbNcMysn401Xp7COV")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:5000/callback")
GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL", "http://127.0.0.1:5000")
DISCORD_API = "https://discord.com/api"

ALLOWED_ENVIRONMENTS = ["Xeno", "ProjectReal", "Project-Real"]

@app.route("/")
def index(): return render_template("index.html", user=session.get("user"))

@app.route("/login")
def login():
    return redirect(f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope=identify")

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code: return "Authorization Error", 400
    data = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI}
    r = requests.post(f"{DISCORD_API}/oauth2/token", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code != 200: return "Token Error", 400
    token = r.json().get("access_token")
    user = requests.get(f"{DISCORD_API}/users/@me", headers={"Authorization": f"Bearer {token}"}).json()
    session["user"] = {
        "id": user["id"], "username": user["username"],
        "avatar": f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get("avatar") else "https://cdn.discordapp.com/embed/avatars/0.png"
    }
    return redirect(GITHUB_PAGES_URL)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/obfuscate", methods=["POST"])
def obfuscate():
    if not session.get("user"): 
        return jsonify({"error": "Unauthorized: Please login via Discord first."}), 401

    user_agent = request.headers.get("User-Agent", "")
    custom_env = request.headers.get("X-Exploit-Environment", "")
    is_allowed = any(env.lower() in user_agent.lower() or env.lower() in custom_env.lower() for env in ALLOWED_ENVIRONMENTS)
    
    if not is_allowed:
        return jsonify({
            "error": "Access Denied: This obfuscator is restricted to authorized exploit environments (Xeno, Project Real). Web browsers are not allowed."
        }), 403

    data = request.get_json()
    src = data.get("source", "")
    seed = data.get("seed")
    if not src.strip(): return jsonify({"error": "Empty script source."}), 400
    
    try:
        out, used_seed, salt = build_lua(src, int(seed) if seed else None)
        return jsonify({"output": out, "seed": used_seed, "key": salt})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"[*] Local Auth & Server running at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
