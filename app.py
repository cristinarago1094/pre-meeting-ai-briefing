import os
from flask import Flask, request, render_template_string, Response
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = Flask(__name__)

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
latest_audio = None

HTML = """
<!doctype html>
<html>
<head>
  <title>Enterprise Meeting Copilot</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 920px; margin: 50px auto; padding: 20px; background: #f7f7f4; color: #1f2933; }
    main { background: white; padding: 32px; border-radius: 18px; border: 1px solid #e5e7eb; }
    h1 { font-size: 34px; margin-bottom: 8px; }
    p { line-height: 1.5; }
    label { display: block; margin-top: 18px; font-weight: 600; }
    input, textarea, select { width: 100%; padding: 12px; margin-top: 6px; font-size: 16px; border-radius: 10px; border: 1px solid #d1d5db; }
    button { margin-top: 22px; padding: 13px 20px; font-size: 16px; border-radius: 10px; border: 0; background: #111827; color: white; font-weight: 600; cursor: pointer; }
    .briefing { margin-top: 30px; padding: 24px; background: #f3f4f6; border-radius: 14px; white-space: pre-line; }
    audio { margin-top: 18px; width: 100%; }
    .hint { color: #6b7280; font-size: 14px; }
  </style>
</head>
<body>
  <main>
    <h1>🎙 Enterprise Meeting Copilot</h1>
    <p>An AI voice copilot that helps Enterprise Account Executives prepare for executive meetings using live company research and ElevenLabs voice generation.</p>

    <form method="post">
      <label>Company</label>
      <input name="company" placeholder="Ferrari" required>

      <label>Stakeholder</label>
      <select name="stakeholder">
        <option>CIO</option>
        <option>CTO</option>
        <option>CHRO</option>
        <option>CFO</option>
        <option>CMO</option>
        <option>CEO</option>
      </select>

      <label>Meeting objective</label>
      <textarea name="objective" placeholder="Discovery call about AI adoption, customer experience automation, internal productivity..." required></textarea>

      <button type="submit">Generate Briefing</button>
    </form>

    {% if briefing %}
    <div class="briefing">
      <h2>Executive briefing</h2>
      {{ briefing }}
      <audio controls>
        <source src="/audio" type="audio/mpeg">
      </audio>
      <p class="hint">Briefing generated with Gemini + Google Search grounding and converted to voice with ElevenLabs.</p>
    </div>
    {% endif %}
  </main>
</body>
</html>
"""

def generate_dynamic_briefing(company, stakeholder, objective):
    prompt = f"""
You are an Enterprise Account Executive meeting copilot.

Prepare a concise executive briefing for Cristina before a customer meeting.

Company: {company}
Stakeholder: {stakeholder}
Meeting objective: {objective}

Use live web research. Look specifically for:
- recent leadership changes: new CEO, CIO, CTO, CHRO, CFO, CMO
- AI, digital transformation, automation, cloud, HR, finance or customer experience initiatives
- budget or investment signals
- cost-reduction, efficiency, hiring, layoffs, acquisition or expansion signals
- business priorities that matter to the selected stakeholder

Return the briefing in this structure:

1. What changed recently
- Bullet points with the most useful recent signals.
- Mention if there is a new CEO, CIO, CHRO, CFO or other relevant executive.
- Mention any AI, HR, IT, digital transformation, budget or efficiency initiative.

2. Why it matters for a {stakeholder}
- Explain what this stakeholder is likely to care about.

3. Suggested opener
- Give Cristina a natural opening line for the meeting.

4. Discovery questions
- Give 4 strong questions tailored to the stakeholder.

5. Risks / objections
- Mention likely blockers.

6. Recommended next step
- Give one practical next step to secure after the meeting.

Keep it sharp, useful and under 450 words.
"""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )

    return response.text

@app.route("/", methods=["GET", "POST"])
def home():
    global latest_audio
    briefing = None

    if request.method == "POST":
        company = request.form.get("company", "")
        stakeholder = request.form.get("stakeholder", "")
        objective = request.form.get("objective", "")

        briefing = generate_dynamic_briefing(company, stakeholder, objective)

        audio = elevenlabs_client.text_to_speech.convert(
            voice_id=VOICE_ID,
            model_id="eleven_multilingual_v2",
            text=briefing,
        )

        latest_audio = b"".join(audio)

    return render_template_string(HTML, briefing=briefing)

@app.route("/audio")
def audio():
    if latest_audio is None:
        return "No audio generated yet", 404
    return Response(latest_audio, mimetype="audio/mpeg")
