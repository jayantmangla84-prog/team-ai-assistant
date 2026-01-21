import os, json
from flask import Flask, request, render_template_string
from groq import Groq

# ================= BASIC CONFIG =================
MODEL = "llama-3.1-8b-instant"
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY not found. Set it first.")

client = Groq(api_key=API_KEY)
app = Flask(__name__)

HISTORY_FILE = "chat_history.json"

# ================= LOAD CHAT HISTORY =================
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        CHAT_HISTORY = json.load(f)
else:
    CHAT_HISTORY = []

# ================= TEAM & PERSONAL DETAILS =================
TEAM_PROFILE = {
    "team_name": "Team Aether",
    "grade": "Class 9",
    "school": "Your School Name",

    "members": [
        {
            "name": "Jayant Mangla",
            "role": "Team Leader & Developer",
            "strengths": ["Python", "Logic", "Problem Solving"],
            "interests": ["AI", "Technology", "Gaming"],
            "goal": "Become a software engineer"
        },
        {
            "name": "Pranav Rayapati",
            "role": "Backend & Research",
            "strengths": ["Math", "Research", "AI Concepts"],
            "interests": ["Science", "AI", "Space"],
            "goal": "Work in Artificial Intelligence"
        },
        {
            "name": "Pragnayan Kartik",
            "role": "UI & Documentation",
            "strengths": ["Design", "Creativity", "Presentation"],
            "interests": ["Design", "Technology", "Creativity"],
            "goal": "Create innovative technology solutions"
        }
    ]
}

# ================= AI FUNCTION =================
def ask_llm(user_input):
    members_text = "\n".join([
        f"- {m['name']} ({m['role']}): strengths in {', '.join(m['strengths'])}, "
        f"interests in {', '.join(m['interests'])}, goal: {m['goal']}"
        for m in TEAM_PROFILE["members"]
    ])

    system_prompt = f"""
You are a TEAM AI ASSISTANT built as a Class 9 school project.

Team Name: {TEAM_PROFILE['team_name']}
Grade: {TEAM_PROFILE['grade']}
School: {TEAM_PROFILE['school']}

Team Members:
{members_text}

Rules:
- You know details of all three members
- If asked about a member, explain their details
- If asked who made you, mention all team members
- Be polite, clear, and helpful like ChatGPT
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(CHAT_HISTORY)
    messages.append({"role": "user", "content": user_input})

    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=300
    )

    reply = completion.choices[0].message.content

    CHAT_HISTORY.append({"role": "user", "content": user_input})
    CHAT_HISTORY.append({"role": "assistant", "content": reply})

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(CHAT_HISTORY, f, indent=2)

# ================= HTML (WHITE CHATGPT STYLE) =================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Team AI Assistant</title>
<style>
body {
  margin: 0;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  color: #111;
}

.header {
  padding: 16px;
  border-bottom: 1px solid #e5e5e5;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
}

.chat-container {
  max-width: 850px;
  margin: auto;
  padding: 20px;
  padding-bottom: 140px;
}

.message {
  display: flex;
  margin: 18px 0;
}

.user { justify-content: flex-end; }
.ai { justify-content: flex-start; }

.bubble {
  max-width: 70%;
  padding: 14px 16px;
  border-radius: 14px;
  line-height: 1.6;
  font-size: 15px;
  white-space: pre-wrap;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.user .bubble {
  background: #0b5cff;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai .bubble {
  background: #f3f3f3;
  border-bottom-left-radius: 4px;
}

.input-area {
  position: fixed;
  bottom: 0;
  width: 100%;
  background: #ffffff;
  border-top: 1px solid #e5e5e5;
  padding: 16px;
}

.input-box {
  max-width: 850px;
  margin: auto;
  display: flex;
  gap: 10px;
}

textarea {
  flex: 1;
  height: 55px;
  border-radius: 12px;
  border: 1px solid #dcdcdc;
  padding: 12px 14px;
  font-size: 15px;
  resize: none;
}

textarea:focus {
  border-color: #0b5cff;
  outline: none;
}

button {
  padding: 0 20px;
  border-radius: 12px;
  border: none;
  background: #0b5cff;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
</style>
</head>

<body>

<div class="header">
🤖 Team Aether AI Assistant — Class 9 Project
</div>

<div class="chat-container" id="chat">
{% for m in history %}
  <div class="message {{ 'user' if m.role == 'user' else 'ai' }}">
    <div class="bubble">{{ m.content }}</div>
  </div>
{% endfor %}
</div>

<div class="input-area">
  <form method="post" class="input-box">
    <textarea id="msg" name="message" placeholder="Message Team AI..."></textarea>
    <button type="submit">Send</button>
  </form>
</div>

<script>
const textarea = document.getElementById("msg");

// Enter = Send | Shift+Enter = New line
textarea.addEventListener("keydown", function(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    textarea.form.submit();
  }
});

// Auto scroll to bottom
window.scrollTo(0, document.body.scrollHeight);
</script>

</body>
</html>
"""

# ================= ROUTE =================
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        msg = request.form["message"]
        if msg.strip():
            ask_llm(msg)

    return render_template_string(HTML_PAGE, history=CHAT_HISTORY)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
