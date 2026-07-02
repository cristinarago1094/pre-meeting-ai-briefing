import os
from flask import Flask, request, render_template_string, Response
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
latest_audio = None

HTML = """
<!doctype html>
<html>
<head>
  <title>Enterprise Meeting Copilot</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 860px; margin: 50px auto; padding: 20px; background: #f7f7f4; color: #1f2933; }
    main { background: white; padding: 32px; border-radius: 18px; border: 1px solid #e5e7eb; }
    h1 { font-size: 34px; margin-bottom: 8px; }
    label { display: block; margin-top: 18px; font-weight: 600; }
    input, textarea, select { width: 100%; padding: 12px; margin-top: 6px; font-size: 16px; border-radius: 10px; border: 1px solid #d1d5db; }
    button { margin-top: 22px; padding: 13px 20px; font-size: 16px; border-radius: 10px; border: 0; background: #111827; color: white; font-weight: 600; cursor: pointer; }
    .briefing { margin-top: 30px; padding: 24px; background: #f3f4f6; border-radius: 14px; white-space: pre-line; }
    audio { margin-top: 18px; width: 100%; }
  </style>
</head>
<body>
  <main>
    <h1>🎙 Enterprise Meeting Copilot</h1>
    <p>An AI voice copilot that helps Enterprise Account Executives prepare for executive meetings.</p>

    <form method="post">
      <label>Company</label>
      <input name="company" placeholder="Ferrari" required>

      <label>Stakeholder</label>
      <input name="stakeholder" placeholder="CIO, CTO, CHRO, CFO..." required>

      <label>Meeting objective</label>
      <textarea name="objective" placeholder="Discovery call about AI adoption, customer experience automation, internal productivity..." required></textarea>

      <label>Meeting type</label>
      <select name="meeting_type">
        <option>Discovery</option>
        <option>Executive alignment</option>
        <option>Renewal / Expansion</option>
        <option>Technical validation</option>
        <option>Negotiation</option>
      </select>

      <button type="submit">Generate Briefing</button>
    </form>

    {% if briefing %}
    <div class="briefing">
      <h2>Pre-meeting briefing</h2>
      {{ briefing }}
      <audio controls>
        <source src="/audio" type="audio/mpeg">
      </audio>
    </div>
    {% endif %}
  </main>
</body>
</html>
"""

def generate_briefing(company, stakeholder, objective, meeting_type):
    return f"""
Hi Cristina. Here is your pre-meeting briefing for {company}.

Meeting type:
{meeting_type}

Stakeholder:
You are meeting with the {stakeholder}.

Meeting objective:
{objective}

Suggested opener:
Start by anchoring the conversation around business impact rather than technology.

Discovery questions:
1. What business process are you trying to improve with AI?
2. Where are your teams still losing time in manual workflows?
3. What would need to be true for this project to become a priority this quarter?

Potential risk:
The stakeholder may be interested in AI but still lack a clear owner, budget or internal business case.

Recommended focus:
Tie the discussion to measurable business outcomes, speed of deployment and adoption.

Your goal:
Leave the meeting with a clear use case, a business owner and a next step.
"""

@app.route("/", methods=["GET", "POST"])
def home():
    global latest_audio
    briefing = None

    if request.method == "POST":
        company = request.form.get("company", "")
        stakeholder = request.form.get("stakeholder", "")
        objective = request.form.get("objective", "")
        meeting_type = request.form.get("meeting_type", "")

        briefing = generate_briefing(company, stakeholder, objective, meeting_type)

        audio = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            text=briefing[:700],
        )

        latest_audio = b"".join(audio)

    return render_template_string(HTML, briefing=briefing)

@app.route("/audio")
def audio():
    if latest_audio is None:
        return "No audio generated yet", 404
    return Response(latest_audio, mimetype="audio/mpeg")
