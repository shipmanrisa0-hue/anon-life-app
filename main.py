import os
from flask import Flask, render_template_string, request, redirect, session
import sqlite3, random, threading, time, webbrowser

app = Flask(__name__)
app.secret_key = "secret123"
DB_NAME = "anon_life.db"

# ---------- DB ----------
def db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def create_tables():
    conn=db();c=conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS profiles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        anomaly TEXT,
        personality TEXT
    )""")

    try:
        c.execute("ALTER TABLE profiles ADD COLUMN user_id INTEGER")
    except:
        pass

    c.execute("""CREATE TABLE IF NOT EXISTS updates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER,
        text TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS replies(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        story_id INTEGER,
        profile_id INTEGER,
        text TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit();conn.close()

create_tables()

# ---------- RANDOM ----------
names=["Shadow","Ghost","Wolf","Dragon","Fox","Phantom"]
personalities=["Naughty","Creepy","Mysterious"]

def gen_profile(user_id=None):
    return (
        random.choice(names)+str(random.randint(10,99)),
        "System glitch kortese 🤖",
        random.choice(personalities),
        user_id
    )

# ---------- SMART BOT ----------
def smart_story():
    lines=[
        "Kal raat ektu weird kichu holo amar sathe...",
        "Ami ekla chiltam but mone holo keu follow kortese...",
        "Phone e unknown signal ashchilo 😳",
        "Ami khub uneasy feel kortesi...",
        "Eta ki normal naki? 😶"
    ]
    return " ".join(random.sample(lines,3))

def smart_reply(text):
    text=text.lower()
    if "raat" in text: return "Raat e onek secret thake 👀"
    if "bhoy" in text: return "Dhorjo dhoro... sob thik hobe 😨"
    if "love" in text: return "Love risky jinis 😈"
    return random.choice([
        "Eta suspicious 😳",
        "Ami o emon dekhsilam 😨",
        "Careful thako 😶",
        "Aro bolo 🤫"
    ])

def bot_loop():
    while True:
        time.sleep(30)
        conn=db();c=conn.cursor()

        name, anomaly, p, _ = gen_profile()
        c.execute("INSERT INTO profiles(name,anomaly,personality) VALUES(?,?,?)",(name,anomaly,p))
        bot_id=c.lastrowid

        story=smart_story()
        c.execute("INSERT INTO updates(profile_id,text) VALUES(?,?)",(bot_id,story))
        story_id=c.lastrowid

        for _ in range(5):
            c.execute("INSERT INTO replies(story_id,profile_id,text) VALUES(?,?,?)",
                      (story_id,bot_id,smart_reply(story)))

        conn.commit();conn.close()

threading.Thread(target=bot_loop, daemon=True).start()

# ---------- STYLE ----------
STYLE="""
<style>
body{font-family:Arial;max-width:400px;margin:auto;background:#f0f0f0;text-align:center;padding:20px}
button{width:100%;padding:12px;margin:5px;border-radius:12px;border:none;background:#6a11cb;color:white}
textarea,input{width:100%;padding:10px;margin:5px;border-radius:10px}
.card{background:white;padding:10px;margin:10px;border-radius:15px;text-align:left}
</style>
"""

# ---------- START ----------
@app.route("/")
def start():
    return STYLE+"""
    <h2>Welcome / স্বাগতম</h2>
    <a href='/anonymous'><button>👻 Anonymous Chat / গোপন চ্যাট</button></a>
    <a href='/login'><button>🔐 Login / লগইন</button></a>
    <a href='/register'><button>🆕 Register / রেজিস্টার</button></a>
    """

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form['u']; p=request.form['p']
        conn=db();c=conn.cursor()
        try:
            c.execute("INSERT INTO users(username,password) VALUES(?,?)",(u,p))
            conn.commit()
            return redirect("/login")
        except:
            return "Username already ase ❌"
    return STYLE+"""
    <h3>Register / নতুন একাউন্ট</h3>
    <form method=post>
    <input name=u placeholder=Username>
    <input name=p placeholder=Password>
    <button>Register</button>
    </form>
    """

# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form['u']; p=request.form['p']
        conn=db();c=conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?",(u,))
        user=c.fetchone(); conn.close()
        if user and user[2]==p:
            session['user_id']=user[0]
            return redirect("/create_profile")
        return "Wrong login ❌"
    return STYLE+"""
    <h3>Login / লগইন</h3>
    <form method=post>
    <input name=u placeholder=Username>
    <input name=p placeholder=Password>
    <button>Login</button>
    </form>
    """

# ---------- ANON ----------
@app.route("/anonymous")
def anonymous():
    session.clear()
    return redirect("/create_profile")

# ---------- CREATE PROFILE ----------
@app.route("/create_profile")
def create_profile():
    user_id=session.get('user_id')
    name, anomaly, p, uid = gen_profile(user_id)

    conn=db();c=conn.cursor()
    c.execute("INSERT INTO profiles(name,anomaly,personality,user_id) VALUES(?,?,?,?)",
              (name,anomaly,p,uid))
    session['profile_id']=c.lastrowid
    session['profile_name']=name
    session['anomaly']=anomaly
    conn.commit();conn.close()

    return redirect("/home")

# ---------- HOME ----------
@app.route("/home")
def home():
    return STYLE+f"""
    <h2>{session.get('profile_name')}</h2>
    <a href='/add'><button>✍️ Post / লিখো</button></a>
    <a href='/view'><button>📖 View / দেখো</button></a>
    <a href='/profile'><button>👤 Profile</button></a>
    """

# ---------- ADD ----------
@app.route("/add", methods=["GET","POST"])
def add():
    if request.method=="POST":
        text=request.form['t']
        pid=session.get('profile_id')
        conn=db();c=conn.cursor()
        c.execute("INSERT INTO updates(profile_id,text) VALUES(?,?)",(pid,text))
        conn.commit();conn.close()
        return redirect("/view")

    return STYLE+"""
    <h3>Write Story / গল্প লিখো</h3>
    <form method=post>
    <textarea name=t placeholder="Tomar story likho..."></textarea>
    <button>Post</button>
    </form>
    """

# ---------- VIEW ----------
@app.route("/view")
def view():
    conn=db();c=conn.cursor()

    c.execute("""SELECT updates.id,profiles.name,updates.text
                 FROM updates JOIN profiles ON updates.profile_id=profiles.id
                 ORDER BY updates.id DESC""")
    stories=c.fetchall()

    c.execute("""SELECT replies.story_id,profiles.name,replies.text
                 FROM replies JOIN profiles ON replies.profile_id=profiles.id""")
    replies=c.fetchall()
    conn.close()

    rmap={}
    for r in replies:
        rmap.setdefault(r[0],[]).append(r)

    html=STYLE+"<h3>Stories / পোস্ট</h3>"
    for s in stories:
        html+=f"""
        <div class='card'>
        <img src='https://api.dicebear.com/7.x/identicon/svg?seed={s[1]}' width=30>
        <b>{s[1]}</b><br>{s[2]}<br>
        <a href='/reply/{s[0]}'>Reply</a>
        """

        for r in rmap.get(s[0],[]):
            html+=f"<div style='margin-left:20px'>{r[1]}: {r[2]}</div>"

        html+="</div>"

    return html+"<a href='/home'>Back</a>"

# ---------- REPLY ----------
@app.route("/reply/<int:story_id>", methods=["GET","POST"])
def reply(story_id):
    if request.method=="POST":
        text=request.form['t']
        pid=session.get('profile_id')
        conn=db();c=conn.cursor()
        c.execute("INSERT INTO replies(story_id,profile_id,text) VALUES(?,?,?)",
                  (story_id,pid,text))
        conn.commit();conn.close()
        return redirect("/view")

    return STYLE+"""
    <h3>Reply / উত্তর দাও</h3>
    <form method=post>
    <textarea name=t></textarea>
    <button>Reply</button>
    </form>
    """

# ---------- PROFILE ----------
@app.route("/profile")
def profile():
    return STYLE+f"""
    <h2>{session.get('profile_name')}</h2>
    <img src='https://api.dicebear.com/7.x/identicon/svg?seed={session.get('profile_name')}' width=80>
    <p>{session.get('anomaly')}</p>
    <a href='/home'>Back</a>
    """

# ---------- RUN ----------
def open_browser():
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)