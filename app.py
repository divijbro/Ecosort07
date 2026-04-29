import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import base64
import re

# ✅ API key
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not set")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite")

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "🌱 Ecosort AI Waste Classifier is Running!"


# ================== CLASSIFY ==================
@app.route("/classify", methods=["POST"])
def classify():
    try:
        image_bytes = request.data

        if not image_bytes:
            return jsonify({"error": "No image received"}), 400

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """
You are a waste classification AI.

Classify into:
- biodegradable
- non-biodegradable
- hazardous

Rules:
- Humans → "stop"
- Electronics → "hazardous"
- Unclear → "Fail"

Return JSON:
{"class":"biodegradable","confidence":0.95}
"""

        response = model.generate_content([
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_base64
                }
            },
            {"text": prompt}
        ])

        raw = response.text.strip()
        cleaned = raw.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        result = json.loads(match.group()) if match else {"class": "Fail"}

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================== RELAY (ESP USES THIS) ==================
@app.route("/relay", methods=["POST"])
def relay():
    try:
        image_bytes = request.data

        if not image_bytes:
            return jsonify({"error": "No image received"}), 400

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """
You are a waste classification AI.

Classify into:
- biodegradable
- non-biodegradable
- hazardous

Return ONLY JSON:
{"class":"biodegradable","confidence":0.95}
"""

        response = model.generate_content([
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_base64
                }
            },
            {"text": prompt}
        ])

        raw = response.text.strip()
        cleaned = raw.replace("```json", "").replace("```", "").strip()

        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        result = json.loads(match.group()) if match else {"class": "Fail"}

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
