# language: Python 3.11, file: setup.py
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def write_files():
    print("[*] Generating project (GitHub Pages site + Protected Local Backend)...")
    os.makedirs(os.path.join(BASE, "core"), exist_ok=True)
    os.makedirs(os.path.join(BASE, "static"), exist_ok=True)
    files = {}

    files["core/__init__.py"] = ""

    # Git ignore for security
    files[".gitignore"] = """.env
__pycache__/
*.py[cod]
venv/
.venv/
"""

    files[".env"] = """DISCORD_CLIENT_ID=1561124820853329920
DISCORD_CLIENT_SECRET=KcksrY3iT8cjhktTbNcMysn401Xp7COV
REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=super_secret_vampire_key
GITHUB_PAGES_URL=http://127.0.0.1:5000
"""

    files["requirements.txt"] = """flask
requests-oauthlib
requests
python-dotenv
"""

    files["README.md"] = """# 🎃 Vampire Obfuscator [Web & Protected Backend]

Closed-source Luau obfuscator with GitHub Pages frontend interface.
"""

    # --- PROTECTED BUILDER (BACKEND) ---
    files["core/builder.py"] = '''import random
import base64

def build_lua(src: str, seed: int = None) -> str:
    if seed is None: seed = random.randint(1, 2**31)
    rng = random.Random(seed)
    
    encoded = base64.b64encode(src.encode('utf-8')).decode('utf-8')
    salt = "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(8))
    
    lua_code = f"""-- Vampire Obfuscator [🎃 PROTECTED EDITION]
-- Seed: {seed}

local function base64_decode(data)
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f = '', (b:find(x) - 1)
        for i = 6, 1, -1 do r = r .. (f % 2 ^ i - f % 2 ^ (i - 1) > 0 and '1' or '0') end
        return r
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c = 0
        for i = 1, 8 do c = c + (x:sub(i, i) == '1' and 2 ^ (8 - i) or 0) end
        return string.char(c)
    end))
end

local _0xSECRET = "{encoded}"
local _0xSALT = "{salt}"

local _0xPAYLOAD = base64_decode(_0xSECRET)
local _0xRUNNER = loadstring(_0xPAYLOAD)
if _0xRUNNER then
    _0xRUNNER()
end
"""
    return lua_code, seed, salt
'''

    # --- LOCAL AUTH & SECURE API SERVER ---
    files["app.py"] = '''import os
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
'''

    # --- HTML FRONTEND (ENGLISH LABELS) ---
    files["index.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>🎃 Vampire Obfuscator | Secure Edition</title>
<link href="https://fonts.googleapis.com/css2?family=Creepster&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="fog"></div>
<div class="app">
  <header>
    <div class="brand">🎃 Vampire <span>Obfuscator</span></div>
    <div class="controls">
      {% if user %}
        <div style="display: flex; gap: 10px; align-items: center;">
          <img src="{{ user.avatar }}" style="width: 36px; height: 36px; border-radius: 50%; border: 2px solid var(--accent);">
          <a href="http://127.0.0.1:5000/logout" class="ghost" style="text-decoration:none; padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); color: var(--dim);">Logout</a>
        </div>
      {% else %}
        <a href="http://127.0.0.1:5000/login" style="background: var(--accent); border: none; color: #000; padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 700; text-decoration: none; box-shadow: 0 0 10px var(--accent);">Login with Discord</a>
      {% endif %}
      
      <input id="seed" type="text" placeholder="Seed (optional)">
      <button id="go">Obfuscate</button>
      <button id="copy" class="ghost">Copy</button>
      <button id="download" class="ghost">Download</button>
    </div>
  </header>
  <main>
    <section class="panel">
      <div class="dropzone" id="dropzone">
        <div class="icon">🦇</div>
        <div class="dz-title">Drop your script file here</div>
        <div class="dz-sub">or click to browse local files</div>
        <input type="file" id="file" hidden>
      </div>
      <textarea id="source" spellcheck="false" placeholder="-- paste Luau source here&#10;print('hello')"></textarea>
    </section>
    <section class="panel">
      <div class="output-head">
        <span id="status">// Protected environment required...</span>
        <span id="meta" class="meta"></span>
      </div>
      <textarea id="output" readonly spellcheck="false" placeholder="// Obfuscated output will appear here"></textarea>
    </section>
  </main>
</div>
<script>
const $ = s => document.querySelector(s);
const src = $("#source"), out = $("#output"), status = $("#status"), meta = $("#meta");
const dz = $("#dropzone"), file = $("#file");

dz.addEventListener("click", () => file.click());
dz.addEventListener("dragover", e => { e.preventDefault(); dz.classList.add("active"); });
dz.addEventListener("dragleave", () => dz.classList.remove("active"));
dz.addEventListener("drop", e => {
  e.preventDefault(); dz.classList.remove("active");
  if (e.dataTransfer.files.length) readFile(e.dataTransfer.files[0]);
});
file.addEventListener("change", () => { if (file.files.length) readFile(file.files[0]); });

function readFile(f) {
  const r = new FileReader();
  r.onload = () => { src.value = r.result; status.textContent = "// Loaded " + f.name; };
  r.readAsText(f);
}

$("#go").addEventListener("click", async () => {
  const body = { source: src.value, seed: $("#seed").value };
  if (!body.source.trim()) { status.textContent = "// Error: Nothing to obfuscate"; return; }
  status.textContent = "// Verifying exploit environment (Xeno / Project Real)...";
  try {
    const res = await fetch("http://127.0.0.1:5000/obfuscate", {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "X-Exploit-Environment": "Xeno" 
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (res.status === 401) { status.textContent = "// Error: Login required!"; window.location.href = "http://127.0.0.1:5000/login"; return; }
    if (res.status === 403) { status.textContent = "// Error: " + data.error; return; }
    if (data.error) { status.textContent = "// Error: " + data.error; return; }
    out.value = data.output;
    status.textContent = "// Done! Protected successfully!";
    meta.textContent = "seed=" + data.seed + " | key=" + data.key;
  } catch (e) {
    status.textContent = "// Network error: Make sure local app.py is running!";
  }
});

$("#copy").addEventListener("click", () => {
  if (!out.value) return;
  navigator.clipboard.writeText(out.value);
  status.textContent = "// Copied!";
});

$("#download").addEventListener("click", () => {
  if (!out.value) return;
  const blob = new Blob([out.value], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "obfuscated.lua";
  a.click();
});
</script>
</body>
</html>
'''

    # --- CSS STYLES ---
    files["static/style.css"] = ''':root {
  --bg: #050201; --panel: #110a06; --panel-2: #1a1009; --border: #3d1c0f;
  --text: #ffe6c7; --dim: #9e7a61; --accent: #ff5e00; --accent-2: #cc4b00;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overflow: hidden; background: var(--bg); color: var(--text); font-family: "Inter", sans-serif; font-size: 14px; }
.fog { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; background: url('https://i.imgur.com/L6yH1M2.png') repeat; opacity: 0.05; animation: fogMove 60s linear infinite; z-index: -1; }
@keyframes fogMove { 0% { background-position: 0 0; } 100% { background-position: 1000px 1000px; } }
.app { display: flex; flex-direction: column; height: 100vh; position: relative; z-index: 1; }
header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; border-bottom: 2px solid var(--border); background: rgba(17, 10, 6, 0.8); backdrop-filter: blur(5px); }
.brand { font-family: "Creepster", cursive; font-size: 28px; letter-spacing: 2px; color: var(--accent); text-shadow: 0 0 15px var(--accent), 0 0 30px #ff0000; }
.brand span { color: #fff; text-shadow: 0 0 10px #fff; }
.controls { display: flex; gap: 12px; align-items: center; }
.controls input { background: var(--panel-2); border: 2px solid var(--border); color: var(--text); padding: 10px 14px; border-radius: 8px; font-size: 13px; width: 180px; outline: none; transition: 0.3s; }
.controls input:focus { border-color: var(--accent); box-shadow: 0 0 15px rgba(255, 94, 0, 0.4); }
.controls button, .controls a { background: linear-gradient(45deg, var(--accent), var(--accent-2)); border: none; color: #000; padding: 10px 20px; border-radius: 8px; font-size: 13px; font-weight: 800; cursor: pointer; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; }
.controls button:hover, .controls a:hover { transform: scale(1.05); box-shadow: 0 0 20px var(--accent); }
.controls button.ghost, .controls a.ghost { background: transparent; border: 2px solid var(--border); color: var(--text); }
.controls button.ghost:hover, .controls a.ghost:hover { border-color: var(--accent); color: var(--accent); box-shadow: 0 0 15px rgba(255, 94, 0, 0.2); transform: none; }
main { flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 20px; min-height: 0; }
.panel { display: flex; flex-direction: column; gap: 12px; background: rgba(17, 10, 6, 0.9); border: 2px solid var(--border); border-radius: 12px; padding: 16px; min-height: 0; position: relative; overflow: hidden; box-shadow: inset 0 0 30px rgba(0,0,0,0.8), 0 0 15px rgba(255,94,0,0.1); }
.panel::before { content: "🕸️"; position: absolute; top: 0; left: 0; font-size: 40px; opacity: 0.1; pointer-events: none; }
.panel::after { content: "🕷️"; position: absolute; bottom: 10px; right: 10px; font-size: 30px; opacity: 0.1; pointer-events: none; }
.dropzone { border: 3px dashed var(--border); border-radius: 10px; padding: 30px; text-align: center; cursor: pointer; transition: 0.3s; background: rgba(0,0,0,0.3); }
.dropzone:hover { border-color: var(--accent); background: rgba(255, 94, 0, 0.1); box-shadow: inset 0 0 20px rgba(255, 94, 0, 0.2); }
.dropzone .icon { font-size: 40px; margin-bottom: 10px; animation: float 3s ease-in-out infinite; }
@keyframes float { 0% { transform: translateY(0); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0); } }
.dz-title { font-family: "Creepster", cursive; font-size: 20px; margin-bottom: 6px; color: var(--accent); }
.dz-sub { color: var(--dim); font-size: 13px; }
textarea { flex: 1; min-height: 0; resize: none; background: var(--panel-2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; color: #ffebd6; font-family: "JetBrains Mono", monospace; font-size: 13px; line-height: 1.5; outline: none; transition: 0.3s; }
textarea:focus { border-color: var(--accent); box-shadow: 0 0 15px rgba(255, 94, 0, 0.2); }
.output-head { display: flex; justify-content: space-between; align-items: center; font-family: monospace; color: var(--dim); font-size: 13px; padding-bottom: 4px; }
.meta { color: var(--accent); font-weight: bold; text-shadow: 0 0 5px var(--accent); }
'''

    for path, content in files.items():
        full = os.path.join(BASE, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Created: {path}")

    print("\n[✔] Project files successfully generated!")

if __name__ == "__main__":
    write_files()