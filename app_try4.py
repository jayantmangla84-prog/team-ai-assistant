import os, json, uuid
from flask import Flask, request, render_template_string
from groq import Groq

# ================= MULTI-CHAT STORAGE =================
CONVO_FILE = "conversations.json"

if os.path.exists(CONVO_FILE):
    with open(CONVO_FILE, "r", encoding="utf-8") as f:
        CONVERSATIONS = json.load(f)
else:
    CONVERSATIONS = {
        "active_chat": "default",
        "chats": {
            "default": {"title": "New Chat", "history": []}
        }
    }

def get_active_chat():
    return CONVERSATIONS["chats"][CONVERSATIONS["active_chat"]]

def save_conversations():
    with open(CONVO_FILE, "w", encoding="utf-8") as f:
        json.dump(CONVERSATIONS, f, indent=2)

# ================= MEMORY =================
MEMORY_FILE = "memory.json"

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        MEMORY = json.load(f)
else:
    MEMORY = {}

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(MEMORY, f, indent=2)

# ================= BASIC CONFIG =================
MODEL = "llama-3.1-8b-instant"
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY not found")

client = Groq(api_key=API_KEY)
app = Flask(__name__)

# ================= USER DETAILS =================
USERS = {
    "jayant": {
        "name": "Jayant Mangla",
        "education": "Class 9",
        "school": "Sadhana Infinity School",
        "location": "Hyderabad, Telangana, India",
        "technical_strengths": ["Python basics", "Logical thinking", "Working with AI"],
        "experience": ["School AI project"],
        "projects": ["AI Personal Assistant"],
        "hobbies": ["Badminton", "Math problem solving"],
        "interests": ["Gadgets", "Artificial Intelligence"],
        "goal": "Learn AI and programming fundamentals"
    },
    "pranav": {
        "name": "Pranav Rayapati",
        "education": "Class 9",
        "school": "Sadhana Infinity International School",
        "location": "Telangana, India",
        "technical_strengths": ["Problem solving", "Basic coding"],
        "experience": ["School coding activities"],
        "projects": ["AI Personal Assistant"],
        "hobbies": ["Piano", "Cricket", "Football"],
        "interests": ["Cars (BMW M4 G82)"],
        "goal": "Improve coding and reasoning skills"
    },
    "pragnayan": {
        "name": "Pragnayan Kartik",
        "education": "Class 9",
        "school": "Your School Name",
        "location": "India",
        "technical_strengths": ["Research", "Creativity"],
        "experience": ["Science projects"],
        "projects": ["AI Personal Assistant"],
        "hobbies": ["Piano", "Cricket", "Football"],
        "interests": ["Cars (BMW)"],
        "goal": "Explore AI and future technology"
    }
}

# ================= AI FUNCTION =================
def ask_llm(user_input):
    chat = get_active_chat()

    # ✅ Auto title ONLY on first message
    if chat["title"] == "New Chat" and len(chat["history"]) == 0:
        chat["title"] = user_input.strip()[:30]

    # Real memory
    if user_input.lower().startswith("remember"):
        MEMORY[str(len(MEMORY) + 1)] = user_input
        save_memory()

    members_text = "\n".join([
        f"""
- {u['name']}
  Education: {u['education']}
  School: {u['school']}
  Location: {u['location']}
  Strengths: {', '.join(u['technical_strengths'])}
  Projects: {', '.join(u['projects'])}
  Hobbies: {', '.join(u['hobbies'])}
  Interests: {', '.join(u['interests'])}
  Goal: {u['goal']}
"""
        for u in USERS.values()
    ])

    system_prompt = f"""
You are Aether, an AI assistant built as a Class 9 school project.

Team Members Details:
{members_text}

Memory:
{json.dumps(MEMORY, indent=2)}

Rules:
- Jayant Mangla is NOT the team leader
- Use only provided data
- Do NOT invent information
- Be polite and helpful
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat["history"])
    messages.append({"role": "user", "content": user_input})

    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=400
    )

    reply = completion.choices[0].message.content

    chat["history"].append({"role": "user", "content": user_input})
    chat["history"].append({"role": "assistant", "content": reply})
    save_conversations()

    return reply

# ================= ROUTES =================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        msg = request.form["message"]
        if msg.strip():
            ask_llm(msg)

    chat = get_active_chat()
    return render_template_string(
        HTML_PAGE,
        history=chat["history"],
        chats=CONVERSATIONS["chats"],
        active=CONVERSATIONS["active_chat"]
    )

@app.route("/new", methods=["POST"])
def new_chat():
    current = get_active_chat()

    # ✅ Prevent multiple empty chats
    if len(current["history"]) == 0:
        return ("", 204)

    cid = str(uuid.uuid4())[:8]
    CONVERSATIONS["chats"][cid] = {"title": "New Chat", "history": []}
    CONVERSATIONS["active_chat"] = cid
    save_conversations()
    return ("", 204)

@app.route("/switch/<cid>", methods=["POST"])
def switch_chat(cid):
    if cid in CONVERSATIONS["chats"]:
        CONVERSATIONS["active_chat"] = cid
        save_conversations()
    return ("", 204)

# ================= HTML =================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Aether AI</title>
<style>
body{margin:0;font-family:-apple-system,Segoe UI,Arial}
.app{display:flex;height:100vh}

/* SIDEBAR */
.sidebar{
  width:260px;
  background:#f3f4f6;
  padding:12px;
  border-right:1px solid #d1d5db
}
.new{
  width:100%;
  padding:12px;
  margin-bottom:14px;
  border:none;
  background:#0b5cff;
  color:#fff;
  border-radius:10px;
  font-weight:600;
  cursor:pointer
}
.chat-btn{
  width:100%;
  padding:10px;
  margin-bottom:6px;
  border:1px solid #e5e7eb;
  background:#ffffff;
  color:#111;
  text-align:left;
  border-radius:8px;
  cursor:pointer;
  font-size:14px
}
.chat-btn:hover{background:#f1f5f9}
.chat-btn.active{
  background:#dbeafe;
  border-color:#93c5fd;
  font-weight:600
}

/* MAIN */
.main{flex:1;display:flex;flex-direction:column}
.header{padding:14px;border-bottom:1px solid #ddd;text-align:center;font-weight:600}
.typing{padding:8px 20px;color:#666;animation:blink 1.2s infinite}
.chat{flex:1;padding:20px;overflow-y:auto}
.msg{display:flex;margin:10px 0;animation:slideUp .25s ease}
.user{justify-content:flex-end}
.ai{justify-content:flex-start}
.bubble{padding:12px;border-radius:12px;max-width:70%}
.user .bubble{background:#0b5cff;color:#fff}
.ai .bubble{background:#f3f3f3}
.input{border-top:1px solid #ddd;padding:14px}
form{display:flex;gap:10px}
textarea{flex:1;padding:10px;border-radius:10px}
button{padding:0 20px;border:none;background:#0b5cff;color:#fff;border-radius:10px}

@keyframes slideUp{from{opacity:0;transform:translateY(6px)}to{opacity:1}}
@keyframes blink{0%{opacity:.3}50%{opacity:1}100%{opacity:.3}}
@media(max-width:768px){.sidebar{display:none}}
</style>
</head>

<body>
<div class="app">
  <div class="sidebar">
    <form method="post" action="/new">
      <button class="new">+ New Chat</button>
    </form>
    {% for cid,c in chats.items() if c.history %}
      <form method="post" action="/switch/{{cid}}">
        <button class="chat-btn {% if cid==active %}active{% endif %}">
          {{ c.title }}
        </button>
      </form>
    {% endfor %}
  </div>

  <div class="main">
    <div class="header">🤖 Aether AI — Class 9 Project</div>
    <div id="typing" class="typing" style="display:none;">🤖 Aether is typing…</div>
    <div class="chat">
      {% for m in history %}
        <div class="msg {{'user' if m.role=='user' else 'ai'}}">
          <div class="bubble">{{ m.content }}</div>
        </div>
      {% endfor %}
    </div>
    <div class="input">
      <form method="post">
        <textarea name="message" placeholder="Message Aether..."></textarea>
        <button type="submit">Send</button>
      </form>
    </div>
  </div>
</div>

<script>
const form=document.querySelector(".input form");
const textarea=form.querySelector("textarea");
const typing=document.getElementById("typing");
const chat=document.querySelector(".chat");

textarea.addEventListener("keydown",e=>{
  if(e.key==="Enter"&&!e.shiftKey){
    e.preventDefault();
    typing.style.display="block";
    form.submit();
  }
});
form.addEventListener("submit",()=>typing.style.display="block");
chat.scrollTop=chat.scrollHeight;
</script>
</body>
</html>
"""

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
